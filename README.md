# Pilih mapping SNOMED CT 1 dan 2 sesuai kebutuhan Anda.

## 1. SNOMED CT to FHIR Clinical Codes Mapping
### Installation Instructions
1. Copy file from ```SnomedCT_InternationalRF2_PRODUCTION_20221231T120000Z``` to full directory.
2. Create a new database for the clinical codes.
3. Run the following SQL script to create the necessary table.
    ```bash
    CREATE TABLE clinical_codes (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
    
        domain VARCHAR(30),        -- diagnosis | procedure | observation | etc
        snomed_root BIGINT,        -- root conceptId (404684003, dll)
    
        concept_id BIGINT,         -- SNOMED code
        display VARCHAR(500),      -- Preferred Term
    
        icd_code VARCHAR(20),      -- nullable
        icd_system VARCHAR(20),    -- ICD10 | ICD9CM | SNOMED
    
        priority INT,
        active TINYINT,
    
        INDEX idx_concept (concept_id),
        INDEX idx_domain (domain),
        INDEX idx_icd (icd_code)
    );
    ```
4. Configure your application to connect to the database. Copy the `.env.example` file to `.env` and update the database settings.
5. set up environment python:
    ```bash
    python3 -m venv venv  
    ```
6. Activate the virtual environment:
    ```bash
    source venv/bin/activate  
    # On Windows use `venv\Scripts\activate
   ```
7. Install required packages:
    ```bash
    pip install -r requirements.txt
    ```
8. Run mapping script to populate the database:
    ```bash
    python snomed.py
    ```


## 2. SPLIT PER FHIR RESOURCE (SESUAI SATUSEHAT)
| FHIR Resource | SNOMED Root | Domain         |
| ------------- | ----------- | -------------- |
| Condition     | 404684003   | diagnosis      |
| Procedure     | 71388002    | procedure      |
| Observation   | 363787002   | observation    |
| BodyStructure | 123037004   | body_structure |
| Medication    | 373873005   | medication     |

Compaitible with:
- HL7 FHIR
- SATUSEHAT
- Praktik terminologi global

### Database Table Structure for FHIR Clinical Codes

1. Create a new table for FHIR clinical codes mapping:
   ```bash
      CREATE TABLE clinical_fhir_codes (
          id BIGINT AUTO_INCREMENT PRIMARY KEY,
      
          -- FHIR & domain
          fhir_resource VARCHAR(30),   -- Condition / Procedure / Observation / BodyStructure / Medication
          domain VARCHAR(30),          -- diagnosis / procedure / observation / body_structure / medication
          snomed_root BIGINT,          -- root SNOMED concept
      
          -- SNOMED
          concept_id BIGINT,
          description_id BIGINT,
          term VARCHAR(500),
      
          -- Mapping
          code VARCHAR(20),            -- ICD code
          terminology VARCHAR(30),     -- SNOMED / ICD10
          priority INT,
      
          effectiveTime DATE,
          active TINYINT,
      
          INDEX idx_fhir (fhir_resource),
          INDEX idx_domain (domain),
          INDEX idx_root (snomed_root),
          INDEX idx_concept (concept_id),
          INDEX idx_code (code)
      );
   ```
2. Run mapping script to populate the database:
    ```bash
    python snomed_fhir.py
    ```