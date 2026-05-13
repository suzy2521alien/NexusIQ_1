from typing import List, Optional
from app.models.schemas import Entity


class NLPEntityExtractor:
    _instance = None
    _nlp = None
    _spacy_available = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._nlp = None
        self._spacy_available = False

        try:
            import spacy
            try:
                self._nlp = spacy.load("en_core_web_sm")
                self._spacy_available = True
            except OSError:
                import subprocess
                result = subprocess.run(
                    ["python", "-m", "spacy", "download", "en_core_web_sm"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    self._nlp = spacy.load("en_core_web_sm")
                    self._spacy_available = True
        except Exception:
            self._spacy_available = False

        self._initialized = True

    def extract_entities(self, text: str, min_confidence: float = 0.0) -> List[Entity]:
        if not text or not text.strip():
            return []

        if not self._spacy_available or self._nlp is None:
            return self._fallback_extract(text)

        try:
            return self._extract_with_spacy(text, min_confidence)
        except Exception:
            return self._fallback_extract(text)

    def _extract_with_spacy(self, text: str, min_confidence: float) -> List[Entity]:
        import spacy

        if isinstance(self._nlp, type(None)):
            try:
                self._nlp = spacy.load("en_core_web_sm")
            except Exception:
                return self._fallback_extract(text)

        doc = self._nlp(text)
        entities = []

        entity_type_mapping = {
            "PERSON": "person",
        }

        seen_values = set()

        for ent in doc.ents:
            entity_type = entity_type_mapping.get(ent.label_, None)
            if not entity_type or entity_type != "person":
                continue

            value_lower = ent.text.lower()
            if value_lower in seen_values:
                continue
            seen_values.add(value_lower)

            confidence = self._estimate_confidence(ent)

            if confidence >= min_confidence:
                entities.append(Entity(
                    type=entity_type,
                    value=ent.text,
                    confidence=confidence,
                    source='nlp'
                ))

        return entities

    def _fallback_extract(self, text: str) -> List[Entity]:
        import re

        entities = []
        seen = set()

        name_patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b',
            r'\bMr\.\s+[A-Z][a-z]+\b',
            r'\bMrs\.\s+[A-Z][a-z]+\b',
            r'\bMs\.\s+[A-Z][a-z]+\b',
            r'\bDr\.\s+[A-Z][a-z]+\b',
        ]

        for pattern in name_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if match.lower() not in seen:
                    seen.add(match.lower())
                    entities.append(Entity(
                        type="person",
                        value=match,
                        confidence=0.6,
                        source='nlp_fallback'
                    ))

        location_patterns = [
            r'\b(?:New York|Los Angeles|Chicago|Houston|Phoenix|Philadelphia|San Antonio|San Diego|Dallas|San Jose|London|Paris|Tokyo|Sydney|Berlin|Mumbai|Delhi|Shanghai|Beijing|Singapore|Dubai|Mumbai)\b',
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b(?:city|town|country|state|province|region|district|area)\b',
        ]

        for pattern in location_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if match.lower() not in seen:
                    seen.add(match.lower())
                    entities.append(Entity(
                        type="location",
                        value=match,
                        confidence=0.5,
                        source='nlp_fallback'
                    ))

        return entities

    def _estimate_confidence(self, ent) -> float:
        base_confidence = 0.7

        if ent.label_ in ("PERSON", "GPE", "ORG"):
            base_confidence = 0.85

        if len(ent.text) < 2:
            base_confidence -= 0.2
        elif len(ent.text) > 5:
            base_confidence += 0.1

        return min(1.0, max(0.0, base_confidence))

    def extract_relationships(self, text: str) -> List[dict]:
        if not self._spacy_available:
            return []

        try:
            doc = self._nlp(text)
            relationships = []

            for token in doc:
                if token.dep_ in ("nsubj", "nsubjpass"):
                    subject = token.text
                    for child in token.children:
                        if child.dep_ == "prep":
                            for ob in child.children:
                                if ob.dep_ in ("pobj", "dobj"):
                                    relationships.append({
                                        "subject": subject,
                                        "relation": child.text,
                                        "object": ob.text
                                    })

            return relationships
        except Exception:
            return []

    def get_entities_by_type(self, text: str, entity_type: str) -> List[str]:
        entities = self.extract_entities(text)
        return [e.value for e in entities if e.type == entity_type]

    def process_batch(self, texts: list, batch_size: int = 100) -> List[List[Entity]]:
        if not self._spacy_available:
            return [[] for _ in texts]

        try:
            all_entities = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                for doc in self._nlp.pipe(batch, disable=["tagger", "parser", "lemmatizer"]):
                    entities = []
                    for ent in doc.ents:
                        entities.append(Entity(
                            type=ent.label_.lower(),
                            value=ent.text,
                            confidence=0.8,
                            source='nlp'
                        ))
                    all_entities.append(entities)

            return all_entities
        except Exception:
            return [[] for _ in texts]
