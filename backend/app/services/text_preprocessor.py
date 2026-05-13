import re
from typing import Dict, Any, List, Tuple


class TextPreprocessor:
    def __init__(self):
        self.stats = {
            "original_length": 0,
            "final_length": 0,
            "lines_removed": 0,
            "special_chars_removed": 0,
            "whitespace_normalized": False,
        }

    def preprocess(self, text: str) -> Tuple[str, Dict[str, Any]]:
        self.stats["original_length"] = len(text)

        text = self._lowercase_text(text)
        text = self._remove_duplicates(text)
        text = self._remove_urls(text)
        text = self._remove_html_tags(text)
        text = self._normalize_whitespace(text)
        text = self._remove_control_characters(text)
        text = self._normalize_numbers(text)

        self.stats["final_length"] = len(text)

        return text, self.stats

    def _lowercase_text(self, text: str) -> str:
        return text.lower()

    def _remove_duplicates(self, text: str) -> str:
        # Simple duplicate line removal
        lines = text.split('\n')
        seen = set()
        unique_lines = []
        for line in lines:
            line_lower = line.lower().strip()
            if line_lower and line_lower not in seen:
                seen.add(line_lower)
                unique_lines.append(line)
        return '\n'.join(unique_lines)

    def _remove_urls(self, text: str) -> str:
        url_pattern = r'https?://\S+|www\.\S+'
        return re.sub(url_pattern, ' ', text)

    def _remove_html_tags(self, text: str) -> str:
        html_pattern = r'<[^>]+>'
        return re.sub(html_pattern, ' ', text)

    def _normalize_whitespace(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        self.stats["whitespace_normalized"] = True
        return text

    def _remove_control_characters(self, text: str) -> str:
        control_chars = re.compile(r'[\x00-\x1f\x7f-\x9f]')
        cleaned = control_chars.sub(' ', text)
        self.stats["special_chars_removed"] = self.stats["original_length"] - len(cleaned)
        return cleaned

    def _normalize_numbers(self, text: str) -> str:
        text = re.sub(r'\b\d+\.\d+\b', ' NUMBER ', text)
        text = re.sub(r'\b\d+\b', ' NUMBER ', text)
        return text

    @staticmethod
    def extract_timestamps(text: str) -> List[str]:
        patterns = [
            r'\b\d{4}-\d{2}-\d{2}\b',
            r'\b\d{2}/\d{2}/\d{4}\b',
            r'\b\d{2}-\d{2}-\d{4}\b',
            r'\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\b',
            r'\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?\b',
        ]

        timestamps = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            timestamps.extend(matches)

        return timestamps

    @staticmethod
    def split_into_sentences(text: str) -> List[str]:
        sentence_endings = re.compile(r'[.!?]+[\s\n]+')
        sentences = sentence_endings.split(text)
        return [s.strip() for s in sentences if s.strip()]

    @staticmethod
    def split_into_chunks(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            if start > 0:
                chunk = "... " + chunk

            if end < len(text):
                chunk = chunk + " ..."

            chunks.append(chunk)
            start = end - overlap

        return chunks
