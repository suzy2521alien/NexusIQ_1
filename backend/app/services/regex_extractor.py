import re
from typing import List, Dict, Tuple
from app.models.schemas import Entity


class RegexEntityExtractor:
    def __init__(self):
        self.patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        patterns = {
            'email': re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                re.IGNORECASE
            ),
            'phone_us': re.compile(
                r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
            ),
            'phone_international': re.compile(
                r'\b\+?\d{1,4}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b'
            ),
            'wallet_bitcoin': re.compile(
                r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b'
            ),
            'wallet_ethereum': re.compile(
                r'\b0x[a-fA-F0-9]{40}\b'
            ),
            'wallet_generic': re.compile(
                r'\b(?:wallet|id|address)[:\s]*([a-zA-Z0-9]{20,64})\b',
                re.IGNORECASE
            ),
            'ip_address': re.compile(
                r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
            ),
            'mac_address': re.compile(
                r'\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\b'
            ),
            'url': re.compile(
                r'https?://\S+|www\.\S+',
                re.IGNORECASE
            ),
            'aadhar': re.compile(
                r'\b\d{4}\s?\d{4}\s?\d{4}\b'
            ),
            'credit_card': re.compile(
                r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
            ),
            'upi_id': re.compile(
                r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\b',
                re.IGNORECASE
            ),
            'ifsc_code': re.compile(
                r'\b[A-Z]{4}0[A-Z0-9]{6}\b'
            ),
            'bank_account': re.compile(
                r'\b\d{9,18}\b'
            ),
        }
        return patterns

    def extract(self, text: str) -> List[Entity]:
        entities = []

        entity_types = [
            ('email', 'email'),
            ('phone_us', 'phone'),
            ('phone_international', 'phone'),
            ('wallet_bitcoin', 'wallet'),
            ('url', 'url'),
        ]

        seen_values = set()

        for pattern_name, entity_type in entity_types:
            pattern = self.patterns.get(pattern_name)
            if not pattern:
                continue

            matches = pattern.findall(text)
            for match in matches:
                value = match.strip() if isinstance(match, str) else match
                if value:
                    # Normalize
                    if entity_type == 'email':
                        value = value.lower()
                    elif entity_type == 'phone':
                        value = re.sub(r'[\s\-]', '', value)
                    normalized_value = value.lower()
                    if normalized_value not in seen_values:
                        seen_values.add(normalized_value)
                        entities.append(Entity(
                            type=entity_type,
                            value=value,
                            confidence=0.95,
                            source='regex'
                        ))

        return entities

    def extract_with_context(self, text: str, window: int = 50) -> List[Tuple[Entity, str]]:
        entities = self.extract(text)
        results = []

        for entity in entities:
            pattern = re.escape(entity.value)
            matches = list(re.finditer(pattern, text, re.IGNORECASE))

            for match in matches:
                start = max(0, match.start() - window)
                end = min(len(text), match.end() + window)
                context = text[start:end]
                results.append((entity, context))
                break

        return results
