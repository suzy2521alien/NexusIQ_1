import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.file_parser import FileParser
from app.services.text_preprocessor import TextPreprocessor
from app.services.regex_extractor import RegexEntityExtractor
from app.services.nlp_extractor import NLPEntityExtractor
from app.services.evidence_processor import EvidenceProcessor
from app.models.schemas import FileFormat


def test_file_parser():
    print("Testing FileParser...")

    text_content = b"Hello, this is a test message.\nIt has multiple lines."
    text, metadata = FileParser.parse(text_content, FileFormat.TEXT, "test.txt")
    assert "test message" in text
    print("  [OK] Text parsing works")

    csv_content = b"name,age,city\nJohn,30,NYC"
    csv_text, csv_meta = FileParser.parse(csv_content, FileFormat.CSV, "test.csv")
    assert "John" in csv_text
    assert csv_meta["row_count"] == 1
    print("  [OK] CSV parsing works")

    json_content = b'{"name": "John", "message": "Hello world"}'
    json_text, json_meta = FileParser.parse(json_content, FileFormat.JSON, "test.json")
    assert "John" in json_text
    print("  [OK] JSON parsing works")

    detected_format = FileParser.detect_format("test.txt")
    assert detected_format == FileFormat.TEXT
    print("  [OK] Format detection works")


def test_text_preprocessor():
    print("\nTesting TextPreprocessor...")

    preprocessor = TextPreprocessor()
    text = "  Hello   world  \n\nThis is    a test.  "
    cleaned, stats = preprocessor.preprocess(text)

    assert "  " not in cleaned
    assert "\n\n" not in cleaned
    print("  [OK] Whitespace normalization works")

    text_with_url = "Visit https://example.com for more info"
    cleaned_url, _ = preprocessor.preprocess(text_with_url)
    assert "https://" not in cleaned_url
    print("  [OK] URL removal works")


def test_regex_extractor():
    print("\nTesting RegexEntityExtractor...")

    extractor = RegexEntityExtractor()
    text = "Contact john@example.com or call 123-456-7890. Wallet: 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"
    entities = extractor.extract(text)

    emails = [e.value for e in entities if e.type == 'email']
    phones = [e.value for e in entities if e.type == 'phone']
    wallets = [e.value for e in entities if e.type == 'wallet']

    assert "john@example.com" in emails
    assert "1234567890" in phones  # normalized
    assert "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2" in wallets
    print("  [OK] Regex extraction works")


def test_nlp_extractor():
    print("\nTesting NLPEntityExtractor...")

    extractor = NLPEntityExtractor()
    text = "John Doe visited New York last week."
    entities = extractor.extract_entities(text)

    persons = [e.value for e in entities if e.type == 'person']
    assert "John Doe" in persons
    print("  [OK] NLP extraction works")


def test_evidence_processor_csv():
    print("\nTesting EvidenceProcessor with CSV...")

    processor = EvidenceProcessor()
    csv_content = b"sender,receiver,amount\nAlice,Bob,100\nCharlie,David,200"
    result = processor.process_file(csv_content, "transactions.csv", FileFormat.CSV)

    assert result.source_file == "transactions.csv"
    assert "alice" in result.raw_text
    assert result.entities["emails"] == []  # no emails in this CSV
    assert result.hash  # should have hash
    assert result.case_id.startswith("CASE-")
    assert "Z" in result.timestamp  # ISO format
    print("  [OK] CSV processing works")


def test_evidence_processor_txt():
    print("\nTesting EvidenceProcessor with TXT...")

    processor = EvidenceProcessor()
    txt_content = b"Chat log:\nJohn: Hi, my email is john@example.com\nJane: My phone is 555-123-4567"
    result = processor.process_file(txt_content, "chat.txt", FileFormat.TEXT)

    assert result.source_file == "chat.txt"
    assert "john@example.com" in result.entities["emails"]
    assert "5551234567" in result.entities["phones"]  # normalized
    assert result.hash
    print("  [OK] TXT processing works")


def test_output_structure():
    print("\nTesting Output Structure...")

    processor = EvidenceProcessor()
    content = b"Test file with john@example.com"
    result = processor.process_file(content, "test.txt", FileFormat.TEXT)

    # Check structure
    assert "case_id" in result.dict()
    assert "source_file" in result.dict()
    assert "entities" in result.dict()
    assert isinstance(result.entities, dict)
    assert "wallets" in result.entities
    assert "emails" in result.entities
    assert "phones" in result.entities
    assert "urls" in result.entities
    assert "names" in result.entities
    assert "raw_text" in result.dict()
    assert "timestamp" in result.dict()
    assert "hash" in result.dict()

    # Check file saved
    output_file = "output/test_processed.json"
    assert os.path.exists(output_file)
    with open(output_file, 'r') as f:
        saved_data = json.load(f)
        assert saved_data["case_id"] == result.case_id
    print("  [OK] Output structure and saving works")


if __name__ == "__main__":
    print("Running tests...\n")

    test_file_parser()
    test_text_preprocessor()
    test_regex_extractor()
    test_nlp_extractor()
    test_evidence_processor_csv()
    test_evidence_processor_txt()
    test_output_structure()

    print("\n✅ All tests passed!")
