import csv, sys, os
import pymysql
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv

# ===============================
# ENV & DB
# ===============================
load_dotenv()

conn = pymysql.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASS", ""),
    database=os.getenv("DB_NAME", "terminology"),
    charset="utf8mb4",
    autocommit=False
)
cur = conn.cursor()

DATA_DIR = Path("full")

IS_A = 116680003
PREFERRED = 900000000000548007
SYNONYM = 900000000000013009

CLINICAL_DOMAINS = {
    "diagnosis": 404684003,
    "procedure": 71388002,
    "observation": 363787002,
    "body_structure": 123037004,
    "medication": 373873005,
    "history": 243796009,
}

csv.field_size_limit(sys.maxsize)
BATCH = 1000
# ===============================
# LOAD IS-A GRAPH
# ===============================
def load_isa_graph():
    graph = defaultdict(set)
    path = DATA_DIR / "terminology/sct2_Relationship_Full_INT_20221231.txt"

    with open(path, encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            if row["active"] == "1" and int(row["typeId"]) == IS_A:
                graph[int(row["sourceId"])].add(int(row["destinationId"]))
    return graph

# ===============================
# RESOLVE DOMAIN (TRANSITIVE)
# ===============================
def resolve_domain(cid, graph, cache):
    if cid in cache:
        return cache[cid]

    stack = [cid]
    visited = set()

    while stack:
        cur_id = stack.pop()
        if cur_id in visited:
            continue
        visited.add(cur_id)

        for name, root in CLINICAL_DOMAINS.items():
            if cur_id == root:
                cache[cid] = (name, root)
                return cache[cid]

        stack.extend(graph.get(cur_id, []))

    cache[cid] = None
    return None

# ===============================
# LOAD PREFERRED TERMS
# ===============================
def load_preferred_terms():
    desc = {}
    lang = set()

    # language refset
    path_lang = DATA_DIR / "refset/language/der2_cRefset_LanguageFull-en_INT_20221231.txt"
    with open(path_lang, encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            if row["active"] == "1" and int(row["acceptabilityId"]) == PREFERRED:
                lang.add(int(row["referencedComponentId"]))

    # descriptions
    path_desc = DATA_DIR / "terminology/sct2_Description_Full-en_INT_20221231.txt"
    with open(path_desc, encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            if row["active"] == "1" and int(row["id"]) in lang:
                desc[int(row["conceptId"])] = row["term"]

    return desc

# ===============================
# LOAD ICD MAP
# ===============================
def load_icd_map():
    icd = {}
    path = DATA_DIR / "refset/map/der2_iisssccRefset_ExtendedMapFull_INT_20221231.txt"

    with open(path, encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            if row["active"] == "1" and row["mapTarget"]:
                cid = int(row["referencedComponentId"])
                icd[cid] = row["mapTarget"]

    return icd

# ===============================
# BUILD & INSERT
# ===============================
def build():
    graph = load_isa_graph()
    pref = load_preferred_terms()
    icd = load_icd_map()

    cache = {}
    batch = []

    cur.execute("TRUNCATE clinical_codes")
    conn.commit()

    for cid, display in pref.items():
        domain = resolve_domain(cid, graph, cache)
        if not domain:
            continue

        name, root = domain

        batch.append((
            name,
            root,
            cid,
            display,
            icd.get(cid),
            "ICD10" if cid in icd else "SNOMED",
            1,
            1
        ))

        if len(batch) >= BATCH:
            cur.executemany("""
                INSERT INTO clinical_codes
                (domain, snomed_root, concept_id, display,
                 icd_code, icd_system, priority, active)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, batch)
            conn.commit()
            batch.clear()

    if batch:
        cur.executemany("""INSERT INTO clinical_codes
        (domain, snomed_root, concept_id, display,
         icd_code, icd_system, priority, active)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, batch)
        conn.commit()

# ===============================
# MAIN
# ===============================
if __name__ == "__main__":
    build()
    cur.close()
    conn.close()
