import uuid
from datetime import datetime
from typing import Optional
from app.models.schemas import (
    ProcessedOutput, FileFormat, Entity
)
from app.services.file_parser import FileParser
from app.services.text_preprocessor import TextPreprocessor
from app.services.regex_extractor import RegexEntityExtractor
from app.services.nlp_extractor import NLPEntityExtractor
from app.utils.hasher import generate_hash
import json
import os


class EvidenceProcessor:
    def __init__(self):
        self.file_parser = FileParser()
        self.preprocessor = TextPreprocessor()
        self.regex_extractor = RegexEntityExtractor()
        self.nlp_extractor = NLPEntityExtractor()

    def process_file(
        self,
        content: bytes,
        filename: str,
        file_format: Optional[FileFormat] = None,
        case_id: Optional[str] = None
    ) -> ProcessedOutput:
        """
        Process a file through the ingestion pipeline.

        Steps:
        1. Generate hash
        2. Parse file
        3. Extract raw text
        4. Clean text
        5. Extract entities (regex + NLP)
        6. Normalize entities
        7. Build structured JSON
        8. Save JSON to /output/
        9. Return structured output
        """
        # 1. Generate hash
        file_hash = generate_hash(content)

        # 2. Parse file
        if file_format is None:
            file_format = FileParser.detect_format(filename, content)

        text, _ = self.file_parser.parse(content, file_format, filename)

        # 3. Extract entities from raw text
        regex_entities = self.regex_extractor.extract(text)
        nlp_entities = self.nlp_extractor.extract_entities(text)
        all_entities = self._merge_entities(regex_entities, nlp_entities)

        # 4. Clean text
        cleaned_text, _ = self.preprocessor.preprocess(text)

        # 5. Group entities
        grouped_entities = self._group_entities(all_entities)

        # 6. Use the active workspace case id when provided
        case_id = case_id or self._generate_case_id()
        timestamp = datetime.now().isoformat() + 'Z'

        # 7. Build output
        output = ProcessedOutput(
            case_id=case_id,
            source_file=filename,
            entities=grouped_entities,
            raw_text=cleaned_text,
            timestamp=timestamp,
            hash=file_hash
        )

        # 8. Save to /output/
        self._save_output(output, filename)

        return output

    def _merge_entities(self, regex_entities: list, nlp_entities: list) -> list:
        seen = {}

        for entity in regex_entities + nlp_entities:
            key = (entity.type, entity.value.lower())
            if key not in seen:
                seen[key] = entity
            else:
                existing = seen[key]
                if entity.confidence > existing.confidence:
                    seen[key] = entity

        return list(seen.values())

    def _group_entities(self, entities: list) -> dict:
        grouped = {
            "wallets": [],
            "emails": [],
            "phones": [],
            "urls": [],
            "names": []
        }

        for entity in entities:
            if entity.type == 'wallet':
                grouped["wallets"].append(entity.value)
            elif entity.type == 'email':
                grouped["emails"].append(entity.value)
            elif entity.type == 'phone':
                grouped["phones"].append(entity.value)
            elif entity.type == 'url':
                grouped["urls"].append(entity.value)
            elif entity.type == 'person':
                grouped["names"].append(entity.value)

        return grouped

    def _generate_case_id(self) -> str:
        date_str = datetime.now().strftime("%Y%m%d")
        random_segment = str(uuid.uuid4())[:4].upper()
        return f"CASE-{date_str}-{random_segment}"

    def _save_output(self, output: ProcessedOutput, filename: str):
        base_name = os.path.splitext(filename)[0]
        safe_case_id = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in output.case_id)
        output_filename = f"{safe_case_id}_{base_name}_processed.json"
        output_path = os.path.join("output", output_filename)

        with open(output_path, 'w') as f:
            json.dump(output.dict(), f, indent=2)

    def process_batch(self, files: list) -> list:
        results = []
        for file_content, filename, file_format in files:
            try:
                result = self.process_file(file_content, filename, file_format)
                results.append(result)
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
                continue

        return results
