import csv
import sys
import pymysql
import os
from pathlib import Path
from dotenv import load_dotenv
from collections import defaultdict, deque

# ===============================
# ENV & DB
# ===============================
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", ""),
    "database": os.getenv("DB_NAME", "terminology"),
    "charset": "utf8mb4",
    "autocommit": False
}

conn = pymysql.connect(**DB_CONFIG)
cur = conn.cursor()

# ===============================
# CONSTANTS
# ===============================
DATA_DIR = Path("full")

IS_A = "116680003"
FSN = "900000000000003001"
SYNONYM = "900000000000013009"

FHIR_DOMAINS = {
    "Condition": {
        "domain": "diagnosis",
        "root": 404684003
    },
    "Procedure": {
        "domain": "procedure",
        "root": 71388002
    },
    "Observation": {
        "domain": "observation",
        "root": 363787002
    },
    "BodyStructure": {
        "domain": "body_structure",
        "root": 123037004
    },
    "Medication": {
        "domain": "medication",
        "root": 373873005
    }
}

BATCH_SIZE = 2000
csv.field_size_limit(sys.maxsize)

# ===============================
# LOAD IS-A GRAPH
# ===============================
def load_isa_graph():
    print("Loading IS-A relationships...")
    graph = defaultdict(set)

    path = DATA_DIR / "terminology/sct2_Relationship_Full_INT_20221231.txt"
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for r in reader:
            if r["active"] != "1":
                continue
            if r["typeId"] != IS_A:
                continue

            parent = int(r["destinationId"])
            child = int(r["sourceId"])
            graph[parent].add(child)

    print("IS-A graph loaded")
    return graph

# ===============================
# GET DESCENDANTS
# ===============================
def get_descendants(root, graph):
    visited = set()
    queue = deque([root])

    while queue:
        node = queue.popleft()
        for child in graph.get(node, []):
            if child not in visited:
                visited.add(child)
                queue.append(child)

    return visited

# ===============================
# LOAD DESCRIPTIONS
# ===============================
def load_descriptions():
    print("Loading descriptions...")
    desc = {}

    path = DATA_DIR / "terminology/sct2_Description_Full-en_INT_20221231.txt"
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for r in reader:
            if r["active"] != "1":
                continue
            if r["typeId"] not in (FSN, SYNONYM):
                continue

            cid = int(r["conceptId"])
            if cid not in desc:
                desc[cid] = {
                    "description_id": int(r["id"]),
                    "term": r["term"],
                    "effectiveTime": r["effectiveTime"],
                    "active": 1
                }

    print(f"Descriptions loaded: {len(desc)}")
    return desc

# ===============================
# LOAD ICD MAP
# ===============================
def load_icd_map():
    print("Loading ICD map...")
    icd = defaultdict(list)

    path = DATA_DIR / "refset/map/der2_iisssccRefset_ExtendedMapFull_INT_20221231.txt"
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for r in reader:
            if r["active"] != "1":
                continue
            if not r["mapTarget"]:
                continue

            cid = int(r["referencedComponentId"])
            icd[cid].append({
                "code": r["mapTarget"],
                "priority": int(r["mapPriority"])
            })

    print("ICD map loaded")
    return icd

# ===============================
# INSERT
# ===============================
def insert_batch(rows):
    cur.executemany("""
        INSERT INTO clinical_fhir_codes (
            fhir_resource,
            domain,
            snomed_root,
            concept_id,
            description_id,
            term,
            code,
            terminology,
            priority,
            effectiveTime,
            active
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, rows)

# ===============================
# MAIN
# ===============================
def main():
    print("START IMPORT")

    graph = load_isa_graph()
    descriptions = load_descriptions()
    icd_map = load_icd_map()

    cur.execute("TRUNCATE clinical_fhir_codes")
    conn.commit()

    for fhir, cfg in FHIR_DOMAINS.items():
        print(f"Processing {fhir}...")
        descendants = get_descendants(cfg["root"], graph)

        batch = []
        count = 0

        for cid in descendants:
            if cid not in descriptions:
                continue

            d = descriptions[cid]

            # SNOMED row
            batch.append((
                fhir,
                cfg["domain"],
                cfg["root"],
                cid,
                d["description_id"],
                d["term"],
                None,
                "SNOMED",
                0,
                d["effectiveTime"],
                d["active"]
            ))

            # ICD rows
            for m in icd_map.get(cid, []):
                batch.append((
                    fhir,
                    cfg["domain"],
                    cfg["root"],
                    cid,
                    d["description_id"],
                    d["term"],
                    m["code"],
                    "ICD10",
                    m["priority"],
                    d["effectiveTime"],
                    d["active"]
                ))

            if len(batch) >= BATCH_SIZE:
                insert_batch(batch)
                conn.commit()
                count += len(batch)
                batch.clear()

        if batch:
            insert_batch(batch)
            conn.commit()
            count += len(batch)

        print(f"{fhir} inserted: {count}")

    cur.close()
    conn.close()
    print("DONE")

if __name__ == "__main__":
    main()
