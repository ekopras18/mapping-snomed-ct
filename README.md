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
9. Result will be stored in `clinical_codes` table.

   | id | domain | snomed\_root | concept\_id | display | icd\_code | icd\_system | priority | active |
   | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
   | 1 | diagnosis | 404684003 | 126813005 | Neoplasm of anterior aspect of epiglottis \(disorder\) | D37.0 | ICD10 | 1 | 1 |
   | 2 | diagnosis | 404684003 | 126814004 | Neoplasm of junctional region of epiglottis \(disorder\) | D38.0 | ICD10 | 1 | 1 |
   | 3 | diagnosis | 404684003 | 126815003 | Neoplasm of lateral wall of oropharynx \(disorder\) | D37.0 | ICD10 | 1 | 1 |
   | 4 | diagnosis | 404684003 | 126816002 | Neoplasm of posterior wall of oropharynx \(disorder\) | D37.0 | ICD10 | 1 | 1 |
   | 5 | diagnosis | 404684003 | 126817006 | Neoplasm of esophagus \(disorder\) | D37.7 | ICD10 | 1 | 1 |
   | 6 | diagnosis | 404684003 | 126818001 | Neoplasm of cervical esophagus \(disorder\) | D37.7 | ICD10 | 1 | 1 |
   | 7 | diagnosis | 404684003 | 126819009 | Neoplasm of thoracic esophagus \(disorder\) | D37.7 | ICD10 | 1 | 1 |
   | 8 | diagnosis | 404684003 | 126820003 | Neoplasm of abdominal esophagus \(disorder\) | D37.7 | ICD10 | 1 | 1 |
   | 9 | diagnosis | 404684003 | 126822006 | Neoplasm of middle third of esophagus \(disorder\) | D37.7 | ICD10 | 1 | 1 |
   | 10 | diagnosis | 404684003 | 126823001 | Neoplasm of lower third of esophagus \(disorder\) | D37.7 | ICD10 | 1 | 1 |



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
3. Result will be stored in `clinical_fhir_codes` table.

   | id | fhir\_resource | domain | snomed\_root | concept\_id | description\_id | term | code | terminology | priority | effectiveTime | active |
   | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
   | 1 | Condition | diagnosis | 404684003 | 131072002 | 210756015 | Increased pregnanediol level | null | SNOMED | 0 | 2002-01-31 | 1 |
   | 2 | Condition | diagnosis | 404684003 | 65536004 | 108892018 | FIGO VM stage III | null | SNOMED | 0 | 2002-01-31 | 1 |
   | 3 | Condition | diagnosis | 404684003 | 293077004 | 433261014 | Hydrazide antituberculosis drug adverse reaction | null | SNOMED | 0 | 2002-01-31 | 1 |
   | 4 | Condition | diagnosis | 404684003 | 293077004 | 433261014 | Hydrazide antituberculosis drug adverse reaction | Y41.1 | ICD10 | 1 | 2002-01-31 | 1 |
   | 5 | Condition | diagnosis | 404684003 | 293077004 | 433261014 | Hydrazide antituberculosis drug adverse reaction | T88.7 | ICD10 | 1 | 2002-01-31 | 1 |
   | 6 | Condition | diagnosis | 404684003 | 162005007 | 252512014 | No tooth problem | null | SNOMED | 0 | 2002-01-31 | 1 |
   | 7 | Condition | diagnosis | 404684003 | 61866006 | 102834014 | Infection by Porocephalus crotali | null | SNOMED | 0 | 2002-01-31 | 1 |
   | 8 | Condition | diagnosis | 404684003 | 61866006 | 102834014 | Infection by Porocephalus crotali | B88.8 | ICD10 | 1 | 2002-01-31 | 1 |
   | 9 | Condition | diagnosis | 404684003 | 127402007 | 690015 | Erythrocyte life span finding | null | SNOMED | 0 | 2002-01-31 | 1 |
   | 10 | Condition | diagnosis | 404684003 | 289407003 | 429292013 | Sagittal suture in oblique diameter | null | SNOMED | 0 | 2002-01-31 | 1 |
