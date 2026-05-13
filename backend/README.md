# Digital Evidence Intelligence System

A two-module cybercrime forensics platform that ingests digital evidence, extracts structured entities, classifies scam intent using AI, and produces forensically-sound JSON output.

---

## Architecture Overview

```
File Upload (TXT / CSV / JSON / PDF)
        ↓
[ Module 1 — Data Ingestion & Extraction ]
  - Parse file to raw text
  - Extract entities: regex + spaCy NLP
  - Clean and normalize text
  - SHA-256 hash for chain of custody
  - Generate case ID + timestamp
  - Save structured JSON to /output/
        ↓
[ Module 2 — AI Intelligence Engine ]
  - Classify scam intent (DistilBERT / keywor
```bash
uvicorn app.main:app --reload
```

Visit `http://127.0.0.1:8000/docs` for interactive API documentation.

## API Endpoints

- `POST /evidence/upload`: Upload multiple files
- `POST /evidence/process/{evidence_id}`: Process uploaded file
- `POST /evidence/upload-evidence/`: Upload and process in one step

## Example Usage

### Upload and Process a File

```bash
curl -X POST "http://127.0.0.1:8000/evidence/upload-evidence/" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@sample.txt"
```

### Expected Output

```json
{
  "case_id": "CASE-20260502-AB12",
  "source_file": "sample.txt",
  "entities": {
    "wallets": [],
    "emails": ["user@example.com"],
    "phones": ["1234567890"],
    "urls": ["https://example.com"],
    "names": ["John Doe"]
  },
  "raw_text": "cleaned and normalized text...",
  "timestamp": "2026-05-02T14:30:00Z",
  "hash": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"
}
```

## Testing

Run unit tests:

```bash
python test_module.py
```

## Output Files

Processed results are saved as `<filename>_processed.json` in the `/output/` directory.

## Architecture

- **Parsers**: Handle file format conversion
- **Preprocessor**: Clean and normalize text
- **Extractors**: Regex and NLP entity extraction
- **Processor**: Orchestrates the pipeline
- **Schemas**: Pydantic models for validation

This module focuses solely on ingestion and basic extraction, providing clean data for downstream AI and graph systems.