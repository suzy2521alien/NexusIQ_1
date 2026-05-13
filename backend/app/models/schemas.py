from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class FileFormat(str, Enum):
    TEXT = "text"
    CSV = "csv"
    JSON = "json"
    PDF = "pdf"


class Entity(BaseModel):
    type: str
    value: str
    confidence: float = Field(ge=0.0, le=1.0)
    source: str = Field(default="regex")


class ProcessedOutput(BaseModel):
    case_id: str
    source_file: str
    entities: Dict[str, List[str]] = Field(default_factory=lambda: {
        "wallets": [],
        "emails": [],
        "phones": [],
        "urls": [],
        "names": []
    })
    raw_text: str
    timestamp: str
    hash: str


class EvidenceUploadResponse(BaseModel):
    success: bool
    evidence_id: str
    filename: str
    format: FileFormat
    message: str
    case_id: Optional[str] = None
    hash: Optional[str] = None
    processed_output: Optional[ProcessedOutput] = None
    graph_result: Optional[Dict[str, Any]] = None


class EvidenceProcessResponse(BaseModel):
    success: bool
    evidence_id: str
    processed_output: ProcessedOutput
    message: str
