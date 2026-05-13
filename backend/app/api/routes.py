from fastapi import APIRouter, UploadFile, File, HTTPException, Body, Form
from typing import List, Optional
import uuid
import sys
import os
import json
import re
from datetime import datetime

# Add Graph_engine to path so we can import db and services
sys.path.append(os.path.join(os.getcwd(), "Graph_engine", "Graph_engine"))

try:
    from db import get_session
    from graph_service import process_case
except ImportError:
    # Fallback or manual path if nested
    sys.path.append(os.path.join(os.getcwd(), "backend", "Graph_engine", "Graph_engine"))
    from db import get_session
    from graph_service import process_case

from app.models.schemas import (
    EvidenceUploadResponse, EvidenceProcessResponse, ProcessedOutput,
    FileFormat
)
from app.services.evidence_processor import EvidenceProcessor
from app.services.file_parser import FileParser

router = APIRouter()
evidence_processor = EvidenceProcessor()
evidence_storage = {}
analysis_reconciled_cases = set()


def _watchlist_path() -> str:
    return os.path.join(os.getcwd(), "watchlist_overrides.json")


def _load_manual_watchlist() -> dict:
    path = _watchlist_path()
    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        print(f"Unable to read manual watchlist: {exc}")
        return {}


def _save_manual_watchlist(data: dict) -> None:
    with open(_watchlist_path(), "w") as f:
        json.dump(data, f, indent=2)


def _collab_path() -> str:
    return os.path.join(os.getcwd(), "collab_comments.json")


def _load_collab_comments() -> dict:
    path = _collab_path()
    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        print(f"Unable to read collab comments: {exc}")
        return {}


def _save_collab_comments(data: dict) -> None:
    with open(_collab_path(), "w") as f:
        json.dump(data, f, indent=2)


def _case_registry_path() -> str:
    return os.path.join(os.getcwd(), "case_registry.json")


def _load_case_registry() -> dict:
    path = _case_registry_path()
    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        print(f"Unable to read case registry: {exc}")
        return {}


def _save_case_registry(data: dict) -> None:
    with open(_case_registry_path(), "w") as f:
        json.dump(data, f, indent=2)


def _upsert_case_registry(case_id: str, metadata: dict) -> dict:
    registry = _load_case_registry()
    existing = registry.get(case_id, {})
    item = {
        **existing,
        **metadata,
        "id": case_id,
        "updated_at": datetime.now().isoformat()
    }
    item.setdefault("created_at", datetime.now().isoformat())
    item.setdefault("status", "INVESTIGATION")
    item.setdefault("stage", "COMPLAINT")
    item.setdefault("assignedTo", "Lead Investigator")
    registry[case_id] = item
    _save_case_registry(registry)
    return item


def _audit_path() -> str:
    return os.path.join(os.getcwd(), "audit_events.json")


def _load_audit_events() -> List[dict]:
    path = _audit_path()
    if not os.path.exists(path):
        return []

    try:
        with open(path, "r") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception as exc:
        print(f"Unable to read audit events: {exc}")
        return []


def _append_audit_event(action: str, detail: str, severity: str = "LOW", user: str = "Lead Investigator") -> dict:
    events = _load_audit_events()
    event = {
        "time": datetime.now().isoformat(),
        "user": user,
        "action": action,
        "detail": detail,
        "severity": severity
    }
    events.append(event)
    with open(_audit_path(), "w") as f:
        json.dump(events, f, indent=2)
    return event


def _output_dir() -> str:
    path = os.path.join(os.getcwd(), "output")
    os.makedirs(path, exist_ok=True)
    return path


def _load_processed_cases(case_id: Optional[str] = None) -> List[dict]:
    cases = []
    output_dir = _output_dir()
    for filename in os.listdir(output_dir):
        if not filename.endswith("_processed.json"):
            continue
        try:
            with open(os.path.join(output_dir, filename), "r") as f:
                data = json.load(f)
            if case_id is None or data.get("case_id") == case_id:
                data["_output_file"] = filename
                cases.append(data)
        except Exception as exc:
            print(f"Unable to read processed output {filename}: {exc}")
    return sorted(cases, key=lambda item: item.get("timestamp", ""), reverse=True)


def _merge_entities(outputs: List[dict]) -> dict:
    merged = {"wallets": [], "emails": [], "phones": [], "urls": [], "names": []}
    seen = {key: set() for key in merged}

    for output in outputs:
        for key in merged:
            for value in output.get("entities", {}).get(key, []):
                if value not in seen[key]:
                    seen[key].add(value)
                    merged[key].append(value)

    return merged


def _load_pipeline_results(case_id: str) -> List[dict]:
    pipeline_file = os.path.join(os.getcwd(), "pipeline_test_results.json")
    if not os.path.exists(pipeline_file):
        return []

    try:
        with open(pipeline_file, "r") as f:
            pipeline_data = json.load(f)
        return [
            result for result in pipeline_data.get("module2_results", [])
            if result.get("case_id") == case_id
        ]
    except Exception as exc:
        print(f"Unable to read pipeline results: {exc}")
        return []


def _load_all_pipeline_results() -> List[dict]:
    pipeline_file = os.path.join(os.getcwd(), "pipeline_test_results.json")
    if not os.path.exists(pipeline_file):
        return []

    try:
        with open(pipeline_file, "r") as f:
            pipeline_data = json.load(f)
        return pipeline_data.get("module2_results", [])
    except Exception as exc:
        print(f"Unable to read pipeline results: {exc}")
        return []


def _load_case_pipeline_results(case_id: str, outputs: Optional[List[dict]] = None) -> List[dict]:
    direct_matches = _load_pipeline_results(case_id)
    if direct_matches:
        return direct_matches

    outputs = outputs if outputs is not None else _load_processed_cases(case_id)
    source_files = {output.get("source_file") for output in outputs if output.get("source_file")}
    if not source_files:
        return []

    # Older seeded cases were written with one case_id in output/*.json and a
    # different generated case_id in pipeline_test_results.json. Source file is
    # the stable join key for those fixtures.
    return [
        result for result in _load_all_pipeline_results()
        if result.get("source_file") in source_files
    ]


def _case_intelligence_results(case_id: str, outputs: Optional[List[dict]] = None) -> List[dict]:
    outputs = outputs if outputs is not None else _load_processed_cases(case_id)
    pipeline_results = _load_case_pipeline_results(case_id, outputs)
    if pipeline_results:
        return pipeline_results

    return [
        _derive_intelligence_from_processed(output, "derived_from_processed_evidence")
        for output in outputs
    ]


def _remove_pipeline_result(case_id: str, source_file: str, evidence_hash: str) -> int:
    pipeline_file = os.path.join(os.getcwd(), "pipeline_test_results.json")
    if not os.path.exists(pipeline_file):
        return 0

    try:
        with open(pipeline_file, "r") as f:
            pipeline_data = json.load(f)
        module_results = pipeline_data.get("module2_results", [])
        before = len(module_results)
        pipeline_data["module2_results"] = [
            item for item in module_results
            if not (
                item.get("case_id") == case_id
                and (
                    item.get("source_file") == source_file
                    or item.get("hash") == evidence_hash
                )
            )
        ]
        with open(pipeline_file, "w") as f:
            json.dump(pipeline_data, f, indent=2)
        return before - len(pipeline_data["module2_results"])
    except Exception as exc:
        print(f"Unable to update pipeline results: {exc}")
        return 0


def _rebuild_case_graph(case_id: str) -> dict:
    remaining_outputs = _load_processed_cases(case_id)
    risk_results = _case_intelligence_results(case_id, remaining_outputs)
    highest_risk = max(
        [result.get("risk_assessment", {}) for result in risk_results],
        key=lambda risk: risk.get("score", 0),
        default={}
    )

    try:
        with get_session() as session:
            session.run("MATCH (c:Case {id: $case_id}) DETACH DELETE c", case_id=case_id)
    except Exception as exc:
        return {"status": "graph_cleanup_failed", "error": str(exc)}

    if not remaining_outputs:
        return {"status": "case_graph_removed", "entities_processed": 0}

    try:
        result = process_case({
            "case_id": case_id,
            "risk_score": highest_risk.get("score", 0),
            "entities": _merge_entities(remaining_outputs)
        })
        return result
    except Exception as exc:
        return {"status": "graph_rebuild_failed", "error": str(exc)}


def _derive_intelligence_from_processed(processed: dict, error: Optional[str] = None) -> dict:
    entities = processed.get("entities", {})
    raw_text = processed.get("raw_text", "")
    lower_text = raw_text.lower()

    wallet_count = len(entities.get("wallets", []))
    email_count = len(entities.get("emails", []))
    phone_count = len(entities.get("phones", []))
    url_count = len(entities.get("urls", []))
    urgency_words = ["urgent", "immediately", "within", "frozen", "critical"]
    investment_words = ["btc", "wallet", "transfer", "fund", "investment", "cold storage"]
    
    urgency_matches = [word for word in urgency_words if word in lower_text]
    investment_matches = [word for word in investment_words if word in lower_text]

    urgency_hits = sum(lower_text.count(word) for word in urgency_matches)
    investment_hits = sum(lower_text.count(word) for word in investment_matches)

    score = min(100, wallet_count * 25 + url_count * 15 + email_count * 5 + phone_count * 5 + urgency_hits * 6 + investment_hits * 4)
    if score >= 85:
        level = "CRITICAL"
    elif score >= 60:
        level = "HIGH"
    elif score >= 30:
        level = "MEDIUM"
    else:
        level = "LOW"

    labels = []
    if any(word in lower_text for word in ["wallet", "btc", "transfer", "fund", "cold storage"]):
        labels.append("crypto_fraud")
    if any(word in lower_text for word in ["login", "account", "security", "frozen"]):
        labels.append("phishing")
    if not labels:
        labels.append("general_fraud")

    reasons = []
    trigger_words = []
    if wallet_count:
        reasons.append(f"{wallet_count} wallet(s) detected")
        trigger_words.extend(entities.get("wallets", []))
    if url_count:
        reasons.append(f"{url_count} URL(s) detected")
        trigger_words.extend(entities.get("urls", []))
    if urgency_hits:
        reasons.append(f"Urgency language detected ({urgency_hits} instances)")
        trigger_words.extend(urgency_matches)
    if investment_hits:
        reasons.append(f"Crypto/funds transfer language detected ({investment_hits} instances)")
        trigger_words.extend(investment_matches)
    if not reasons:
        reasons.append("No high-risk extracted signals found")

    enriched = processed.copy()
    enriched.update({
        "intent": {
            "labels": labels,
            "confidence": 0.75 if score >= 60 else 0.55
        },
        "risk_assessment": {
            "score": score,
            "level": level,
            "reasons": reasons,
            "trigger_words": list(set(trigger_words))
        },
        "entity_counts": {
            "wallets": wallet_count,
            "emails": email_count,
            "phones": phone_count,
            "urls": url_count,
            "names": len(entities.get("names", []))
        },
        "ai_metadata": {
            "model": "backend-rule-scorer",
            "version": "1.0",
            "fallback_reason": error
        }
    })
    return enriched


def _write_pipeline_result(enriched: dict) -> dict:
    pipeline_file = os.path.join(os.getcwd(), "pipeline_test_results.json")
    pipeline_data = {"module2_results": []}

    if os.path.exists(pipeline_file):
        with open(pipeline_file, "r") as f:
            existing = json.load(f)
            if isinstance(existing, dict):
                pipeline_data.update(existing)

    module_results = pipeline_data.setdefault("module2_results", [])
    module_results[:] = [
        item for item in module_results
        if not (
            item.get("case_id") == enriched.get("case_id")
            and item.get("source_file") == enriched.get("source_file")
        )
    ]
    module_results.append(enriched)

    with open(pipeline_file, "w") as f:
        json.dump(pipeline_data, f, indent=2)

    return enriched


def _upsert_pipeline_result(processed: dict) -> Optional[dict]:
    try:
        engine_path = os.path.join(os.getcwd(), "person2_ai_engine")
        if engine_path not in sys.path:
            sys.path.insert(0, engine_path)
        loaded_models = sys.modules.get("models")
        if loaded_models is not None and not hasattr(loaded_models, "__path__"):
            sys.modules.pop("models", None)
        from pipeline.intelligence_processor import IntelligenceProcessor

        enriched = IntelligenceProcessor().process_intelligence(processed)
        return _write_pipeline_result(enriched)
    except Exception as exc:
        print(f"Intelligence pipeline failed: {exc}")
        return _write_pipeline_result(_derive_intelligence_from_processed(processed, str(exc)))


def _has_exact_pipeline_result(case_id: str, source_file: str, evidence_hash: str = "") -> bool:
    for result in _load_pipeline_results(case_id):
        if source_file and result.get("source_file") == source_file:
            return True
        if evidence_hash and result.get("hash") == evidence_hash:
            return True
    return False


def _ensure_case_analysis(case_id: str, outputs: Optional[List[dict]] = None, force: bool = False) -> dict:
    if not case_id:
        return {"case_id": case_id, "status": "skipped", "reason": "missing_case_id"}

    outputs = outputs if outputs is not None else _load_processed_cases(case_id)
    if not outputs:
        return {"case_id": case_id, "status": "skipped", "reason": "no_processed_evidence"}

    cache_key = f"{case_id}:{len(outputs)}:{max((output.get('timestamp', '') for output in outputs), default='')}"
    if not force and cache_key in analysis_reconciled_cases:
        return {"case_id": case_id, "status": "already_reconciled"}

    pipeline_written = 0
    pipeline_errors = []
    for output in outputs:
        source_file = output.get("source_file", "")
        evidence_hash = output.get("hash", "")
        if _has_exact_pipeline_result(case_id, source_file, evidence_hash):
            continue

        try:
            normalized_output = output.copy()
            normalized_output["case_id"] = case_id
            _upsert_pipeline_result(normalized_output)
            pipeline_written += 1
        except Exception as exc:
            pipeline_errors.append(f"{source_file or evidence_hash}: {exc}")

    if pipeline_written == 0 and not force:
        analysis_reconciled_cases.add(cache_key)
        return {
            "case_id": case_id,
            "status": "already_materialized",
            "pipeline_written": 0,
            "pipeline_errors": pipeline_errors,
            "graph_result": {"status": "skipped", "reason": "pipeline_already_exists"}
        }

    pipeline_results = _case_intelligence_results(case_id, outputs)
    risk = max(
        [result.get("risk_assessment", {}) for result in pipeline_results],
        key=lambda item: item.get("score", 0),
        default={}
    )

    graph_result = None
    try:
        graph_result = process_case({
            "case_id": case_id,
            "risk_score": risk.get("score", 0),
            "entities": _merge_entities(outputs),
            "intent": next((result.get("intent", {}) for result in pipeline_results if result.get("intent")), {})
        })
    except Exception as exc:
        graph_result = {"status": "graph_ingestion_failed", "error": str(exc)}

    analysis_reconciled_cases.add(cache_key)
    return {
        "case_id": case_id,
        "status": "reconciled",
        "pipeline_written": pipeline_written,
        "pipeline_errors": pipeline_errors,
        "graph_result": graph_result
    }


# --- Authentication APIs ---
@router.post("/auth/login", tags=["auth"])
async def login(credentials: dict = Body(...)):
    return {"status": "success", "token": "jwt_token_here", "mfa_required": True}

@router.post("/auth/verify-yubikey", tags=["auth"])
async def verify_yubikey(token: str = Body(...)):
    return {"status": "success", "verified": True}

# --- Evidence Upload APIs ---
@router.post("/evidence/upload", response_model=EvidenceUploadResponse, tags=["evidence"])
async def upload_evidence(
    files: List[UploadFile] = File(...),
    case_id: str = Form(...),
    officer: str = Form("Lead Investigator"),
    source: str = Form("Unspecified")
):
    uploaded_files = []
    for file in files:
        content = await file.read()
        evidence_id = str(uuid.uuid4())
        file_format = FileParser.detect_format(file.filename, content)
        
        # Process evidence (hash, parse, extract entities, save case-scoped output)
        processed = evidence_processor.process_file(content, file.filename, file_format, case_id=case_id)
        processed_dict = processed.dict()
        processed_dict["chain_of_custody"] = {
            "officer": officer,
            "source": source
        }
        _upsert_case_registry(processed.case_id, {
            "status": "INVESTIGATION",
            "stage": "INVESTIGATION",
            "assignedTo": officer
        })
        safe_case_id = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in processed.case_id)
        base_name = os.path.splitext(file.filename)[0]
        with open(os.path.join(_output_dir(), f"{safe_case_id}_{base_name}_processed.json"), "w") as f:
            json.dump(processed_dict, f, indent=2)

        enriched = _upsert_pipeline_result(processed_dict)
        graph_payload = enriched or processed_dict
        risk_score = graph_payload.get("risk_assessment", {}).get("score", 0)
        
        # Ingest into Neo4j Graph
        graph_result = None
        try:
            graph_result = process_case({
                "case_id": processed.case_id,
                "risk_score": risk_score,
                "entities": processed.entities,
                "intent": graph_payload.get("intent", {})
            })
            message = f"Uploaded and Ingested into Graph: {graph_result['status']}"
        except Exception as e:
            message = f"Uploaded but Graph Ingestion failed: {str(e)}"
        
        evidence_storage[evidence_id] = {"content": content, "filename": file.filename, "format": file_format, "case_id": processed.case_id}
        uploaded_files.append(EvidenceUploadResponse(
            success=True, 
            evidence_id=evidence_id, 
            filename=file.filename, 
            format=file_format, 
            message=message,
            case_id=processed.case_id,
            hash=processed.hash,
            processed_output=processed,
            graph_result=graph_result
        ))
    return uploaded_files[0]


@router.get("/evidence/results/{case_id}", tags=["evidence"])
async def get_evidence_results(case_id: str):
    files = []
    for idx, data in enumerate(_load_processed_cases(case_id)):
        source_file = data.get("source_file", "unknown")
        files.append({
            "id": data.get("hash", f"EV-{idx}")[:12],
            "name": source_file,
            "type": os.path.splitext(source_file)[1].replace(".", "") or "file",
            "size": f"{len(data.get('raw_text', ''))} chars",
            "date": data.get("timestamp", ""),
            "status": "ANALYZED",
            "uploader": data.get("chain_of_custody", {}).get("officer", "Backend Pipeline"),
            "hash": data.get("hash", ""),
            "caseId": data.get("case_id"),
            "entities": data.get("entities", {}),
            "message": "Processed output loaded from backend"
        })
    return {"case_id": case_id, "files": files}


@router.delete("/evidence/{case_id}/{evidence_id}", tags=["evidence"])
async def delete_evidence(case_id: str, evidence_id: str):
    matches = []
    normalized_id = evidence_id.lower()

    for data in _load_processed_cases(case_id):
        evidence_hash = data.get("hash", "")
        output_file = data.get("_output_file", "")
        source_file = data.get("source_file", "")
        if (
            evidence_hash.lower().startswith(normalized_id)
            or output_file.lower() == normalized_id
            or source_file.lower() == normalized_id
        ):
            matches.append(data)

    if not matches:
        raise HTTPException(status_code=404, detail=f"Evidence {evidence_id} not found for {case_id}")

    deleted = []
    removed_pipeline_results = 0
    for data in matches:
        output_file = os.path.basename(data.get("_output_file", ""))
        output_path = os.path.join(_output_dir(), output_file)
        source_file = data.get("source_file", output_file)
        evidence_hash = data.get("hash", "")

        if output_file and os.path.exists(output_path):
            os.remove(output_path)

        removed_pipeline_results += _remove_pipeline_result(case_id, source_file, evidence_hash)
        deleted.append({
            "id": evidence_hash[:12] if evidence_hash else output_file,
            "name": source_file,
            "hash": evidence_hash,
            "output_file": output_file
        })

    for storage_id, item in list(evidence_storage.items()):
        if item.get("case_id") == case_id and any(item.get("filename") == record["name"] for record in deleted):
            evidence_storage.pop(storage_id, None)

    graph_result = _rebuild_case_graph(case_id)
    names = ", ".join(record["name"] for record in deleted)
    _append_audit_event(
        "Evidence Deletion",
        f"{names} deleted from {case_id}; graph and pipeline recomputed",
        "HIGH"
    )

    return {
        "success": True,
        "case_id": case_id,
        "deleted": deleted,
        "removed_pipeline_results": removed_pipeline_results,
        "graph_result": graph_result
    }

# --- Case Management APIs ---
@router.get("/cases/list", tags=["cases"])
async def list_cases():
    cases_by_id = {}

    for case_id, metadata in _load_case_registry().items():
        cases_by_id[case_id] = {
            "id": case_id,
            "title": metadata.get("title") or f"Forensic Case: {case_id.split('-')[-1]}",
            "risk_score": metadata.get("risk_score", 0),
            "status": metadata.get("status", "INVESTIGATION"),
            "stage": metadata.get("stage", "COMPLAINT"),
            "assignedTo": metadata.get("assignedTo", "Lead Investigator"),
            "entity_count": metadata.get("entity_count", 0),
            "linked_cases": metadata.get("linked_cases", 0),
            "created_at": metadata.get("created_at"),
            "updated_at": metadata.get("updated_at")
        }

    try:
        with get_session() as session:
            result = session.run("MATCH (c:Case) RETURN c.id as id, c.risk_score as risk_score ORDER BY c.id DESC LIMIT 100")
            for record in result:
                case_id = record["id"]
                cases_by_id.setdefault(case_id, {
                    "id": case_id,
                    "title": f"Forensic Case: {case_id.split('-')[-1]}",
                    "risk_score": 0,
                    "status": "INVESTIGATION",
                    "stage": "INVESTIGATION",
                    "assignedTo": "Lead Investigator",
                    "entity_count": 0,
                    "linked_cases": 0,
                    "created_at": None,
                    "updated_at": None
                })
                cases_by_id[case_id]["risk_score"] = record["risk_score"] or cases_by_id[case_id]["risk_score"]
    except Exception as e:
        print(f"Neo4j Query Failed: {e}")

    for case_id in {output.get("case_id") for output in _load_processed_cases() if output.get("case_id")}:
        outputs = _load_processed_cases(case_id)
        _ensure_case_analysis(case_id, outputs)
        pipeline_results = _case_intelligence_results(case_id, outputs)
        risk = max(
            [result.get("risk_assessment", {}) for result in pipeline_results],
            key=lambda item: item.get("score", 0),
            default={}
        )
        entities = _merge_entities(outputs)
        cases_by_id.setdefault(case_id, {
            "id": case_id,
            "title": f"Forensic Case: {case_id.split('-')[-1]}",
            "risk_score": 0,
            "status": "INVESTIGATION",
            "stage": "INVESTIGATION",
            "assignedTo": "Lead Investigator",
            "entity_count": 0,
            "linked_cases": 0,
            "created_at": outputs[-1].get("timestamp") if outputs else None,
            "updated_at": outputs[0].get("timestamp") if outputs else None
        })
        cases_by_id[case_id].update({
            "risk_score": risk.get("score", cases_by_id[case_id].get("risk_score", 0)),
            "stage": "INVESTIGATION" if risk.get("score", 0) >= 60 else cases_by_id[case_id].get("stage", "REVIEW"),
            "status": "INVESTIGATION",
            "entity_count": sum(len(values) for values in entities.values()),
            "updated_at": outputs[0].get("timestamp") if outputs else cases_by_id[case_id].get("updated_at")
        })
    
    if cases_by_id:
        return {
            "cases": sorted(
                cases_by_id.values(),
                key=lambda item: item.get("updated_at") or item.get("created_at") or "",
                reverse=True
            )
        }

    return {
        "cases": [
            {"id": "CASE-20260510-F150", "risk_score": 92, "status": "INVESTIGATION", "stage": "INVESTIGATION", "assignedTo": "Lead Investigator", "entity_count": 42},
            {"id": "CASE-20260509-X992", "risk_score": 45, "status": "INVESTIGATION", "stage": "REVIEW", "assignedTo": "Lead Investigator", "entity_count": 18},
            {"id": "COMP-20260511-S001", "risk_score": 22, "status": "COMPLAINT", "stage": "COMPLAINT", "assignedTo": "Unassigned", "entity_count": 5}
        ]
    }


@router.post("/cases/create", tags=["cases"])
async def create_case(payload: dict = Body(...)):
    raw_case_id = (payload.get("case_id") or "").strip()
    if raw_case_id:
        case_id = raw_case_id
    else:
        case_id = f"CASE-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"

    if not re.match(r"^[A-Za-z0-9_-]+$", case_id):
        raise HTTPException(status_code=400, detail="Case ID can only contain letters, numbers, hyphen, and underscore")

    if case_id in _load_case_registry() or _load_processed_cases(case_id):
        raise HTTPException(status_code=409, detail=f"Case {case_id} already exists")

    metadata = _upsert_case_registry(case_id, {
        "title": (payload.get("title") or f"Forensic Case: {case_id.split('-')[-1]}").strip(),
        "status": payload.get("status") or "INVESTIGATION",
        "stage": payload.get("stage") or "COMPLAINT",
        "assignedTo": payload.get("assignedTo") or "Lead Investigator",
        "priority": payload.get("priority") or "MEDIUM",
        "notes": payload.get("notes") or "",
        "created_by": payload.get("created_by") or "Lead Investigator",
        "risk_score": 0,
        "entity_count": 0
    })

    graph_result = None
    try:
        with get_session() as session:
            session.run(
                """
                MERGE (c:Case {id: $case_id})
                SET c.risk_score = coalesce(c.risk_score, 0),
                    c.status = $status,
                    c.stage = $stage,
                    c.title = $title,
                    c.assigned_to = $assigned_to,
                    c.created_at = coalesce(c.created_at, $created_at),
                    c.updated_at = $updated_at
                RETURN c
                """,
                case_id=case_id,
                status=metadata["status"],
                stage=metadata["stage"],
                title=metadata["title"],
                assigned_to=metadata["assignedTo"],
                created_at=metadata["created_at"],
                updated_at=metadata["updated_at"]
            )
        graph_result = {"status": "case_registered"}
    except Exception as exc:
        graph_result = {"status": "registry_only", "error": str(exc)}

    _append_audit_event(
        "Case Created",
        f"{case_id} created with stage {metadata['stage']} and assigned to {metadata['assignedTo']}",
        "MEDIUM",
        metadata.get("created_by", "Lead Investigator")
    )

    return {"success": True, "case": metadata, "graph_result": graph_result}

# --- Graph APIs ---
@router.get("/graph/{case_id}", tags=["graph"])
async def get_graph(case_id: str):
    _ensure_case_analysis(case_id)

    # Try Neo4j first
    try:
        with get_session() as session:
            case_record = session.run("""
                MATCH (c:Case {id: $case_id})
                RETURN c.id AS id, c.risk_score AS risk_score, c.created_at AS created_at
            """, case_id=case_id).single()

            if case_record:
                nodes = [{
                    "id": f"case:{case_record['id']}",
                    "label": "Case",
                    "properties": {
                        "id": case_record["id"],
                        "value": case_record["id"],
                        "risk_score": case_record["risk_score"] or 0,
                        "created_at": str(case_record["created_at"]) if case_record["created_at"] else None,
                    }
                }]
                edges = []
                node_ids = {nodes[0]["id"]}
                edge_ids = set()

                entity_result = session.run("""
                    MATCH (c:Case {id: $case_id})<-[rel:INVOLVED_IN]-(e)
                    OPTIONAL MATCH (e)-[:INVOLVED_IN]->(other:Case)
                    RETURN DISTINCT elementId(e) AS eid,
                           labels(e)[0] AS label,
                           e.value AS value,
                           COUNT(DISTINCT other) AS case_count
                    ORDER BY label, value
                """, case_id=case_id)

                for record in entity_result:
                    node_id = f"entity:{record['eid']}"
                    if node_id not in node_ids:
                        nodes.append({
                            "id": node_id,
                            "label": record["label"] or "Entity",
                            "properties": {
                                "value": record["value"],
                                "case_count": record["case_count"] or 1,
                            }
                        })
                        node_ids.add(node_id)

                    edge_id = f"involved:{node_id}:case:{case_id}"
                    if edge_id not in edge_ids:
                        edges.append({
                            "id": edge_id,
                            "source": node_id,
                            "target": f"case:{case_id}",
                            "type": "INVOLVED_IN"
                        })
                        edge_ids.add(edge_id)

                connection_result = session.run("""
                    MATCH (c:Case {id: $case_id})<-[:INVOLVED_IN]-(e1)-[rel:CONNECTED_TO]-(e2)-[:INVOLVED_IN]->(c)
                    RETURN DISTINCT elementId(e1) AS source, elementId(e2) AS target, type(rel) AS type
                """, case_id=case_id)

                for record in connection_result:
                    source = f"entity:{record['source']}"
                    target = f"entity:{record['target']}"
                    if source == target:
                        continue
                    ordered = sorted([source, target])
                    edge_id = f"connected:{ordered[0]}:{ordered[1]}"
                    if edge_id not in edge_ids:
                        edges.append({
                            "id": edge_id,
                            "source": source,
                            "target": target,
                            "type": record["type"] or "CONNECTED_TO"
                        })
                        edge_ids.add(edge_id)

                related_result = session.run("""
                    MATCH (c:Case {id: $case_id})-[rel:RELATED_TO]-(other:Case)
                    OPTIONAL MATCH (c)<-[:INVOLVED_IN]-(e)-[:INVOLVED_IN]->(other)
                    RETURN DISTINCT other.id AS id, other.risk_score AS risk_score, rel.score AS score, collect(DISTINCT e.value) AS shared_entities
                    ORDER BY score DESC
                    LIMIT 8
                """, case_id=case_id)

                for record in related_result:
                    related_id = f"case:{record['id']}"
                    if related_id not in node_ids:
                        nodes.append({
                            "id": related_id,
                            "label": "Case",
                            "properties": {
                                "id": record["id"],
                                "value": record["id"],
                                "risk_score": record["risk_score"] or 0,
                                "related": True,
                                "similarity": record["score"] or 0,
                                "shared_entities": record["shared_entities"]
                            }
                        })
                        node_ids.add(related_id)

                    edge_id = f"related:case:{case_id}:{related_id}"
                    if edge_id not in edge_ids:
                        edges.append({
                            "id": edge_id,
                            "source": f"case:{case_id}",
                            "target": related_id,
                            "type": "RELATED_TO",
                            "score": record["score"] or 0,
                            "shared_entities": record["shared_entities"]
                        })
                        edge_ids.add(edge_id)

                return {"nodes": nodes, "edges": edges}
    except Exception as e:
        print(f"Graph Database Error: {e}")
        
    # Dynamic fallback: Build graph from all processed JSON for this case.
    nodes = [{"id": "case_node", "label": "Case", "properties": {"id": case_id, "title": "Active Investigation"}}]
    edges = []
    node_counter = 1

    entities = _merge_entities(_load_processed_cases(case_id))
    for w in entities.get("wallets", []):
        nid = f"n{node_counter}"
        nodes.append({"id": nid, "label": "Wallet", "properties": {"address": w, "value": w, "risk": "HIGH"}})
        edges.append({"id": f"e{node_counter}", "source": "case_node", "target": nid, "type": "HAS_ENTITY"})
        node_counter += 1
    for e in entities.get("emails", []):
        nid = f"n{node_counter}"
        nodes.append({"id": nid, "label": "Email", "properties": {"address": e, "value": e}})
        edges.append({"id": f"e{node_counter}", "source": "case_node", "target": nid, "type": "HAS_ENTITY"})
        node_counter += 1
    for p in entities.get("phones", []):
        nid = f"n{node_counter}"
        nodes.append({"id": nid, "label": "Phone", "properties": {"number": p, "value": p}})
        edges.append({"id": f"e{node_counter}", "source": "case_node", "target": nid, "type": "HAS_ENTITY"})
        node_counter += 1
    for u in entities.get("urls", []):
        nid = f"n{node_counter}"
        nodes.append({"id": nid, "label": "IP_Address", "properties": {"ip": u, "value": u}})
        edges.append({"id": f"e{node_counter}", "source": "case_node", "target": nid, "type": "HAS_ENTITY"})
        node_counter += 1
    for name in entities.get("names", []):
        nid = f"n{node_counter}"
        nodes.append({"id": nid, "label": "Person", "properties": {"name": name, "value": name}})
        edges.append({"id": f"e{node_counter}", "source": "case_node", "target": nid, "type": "HAS_ENTITY"})
        node_counter += 1
                
    if len(nodes) == 1:
        # Fallback if case doesn't exist yet
        nodes.append({"id": "n_pending", "label": "Unknown", "properties": {"status": "Pending Data Extraction"}})
        edges.append({"id": "e_pending", "source": "case_node", "target": "n_pending", "type": "AWAITING_UPLOAD"})

    return { "nodes": nodes, "edges": edges }

@router.get("/graph/{case_id}/geo", tags=["graph"])
async def get_graph_geo(case_id: str):
    import hashlib

    geo_data = []

    for data in _load_processed_cases(case_id):
        entities = data.get("entities", {})
        candidates = []
        candidates.extend(("URL", value) for value in entities.get("urls", []))
        candidates.extend(("Email", value) for value in entities.get("emails", []))
        candidates.extend(("Phone", value) for value in entities.get("phones", []))
        candidates.extend(("Wallet", value) for value in entities.get("wallets", []))

        for idx, (entity_type, value) in enumerate(candidates):
            digest = hashlib.sha256(f"{case_id}:{value}".encode("utf-8")).hexdigest()
            lat_seed = int(digest[:8], 16) / 0xFFFFFFFF
            lng_seed = int(digest[8:16], 16) / 0xFFFFFFFF
            risk = "CRITICAL" if entity_type in {"URL", "Wallet"} else "HIGH"
            geo_data.append({
                "id": f"loc-{len(geo_data)}",
                "lat": round((lat_seed * 140) - 70, 4),
                "lng": round((lng_seed * 320) - 160, 4),
                "type": entity_type,
                "value": value,
                "name": f"{entity_type} geospatial projection",
                "location_name": f"Backend-derived {entity_type} node",
                "threat_level": risk,
                "source_file": data.get("source_file")
            })

    if not geo_data:
        geo_data.append({
            "id": "loc-def",
            "lat": 38.9072,
            "lng": -77.0369,
            "type": "Case",
            "value": case_id,
            "name": "Awaiting Evidence",
            "location_name": "No extracted geospatial entities yet",
            "threat_level": "LOW"
        })

    return { "status": "success", "data": geo_data }


@router.get("/graph/timeline/{case_id}", tags=["graph"])
async def get_case_timeline(case_id: str):
    outputs = sorted(_load_processed_cases(case_id), key=lambda item: item.get("timestamp", ""))
    _ensure_case_analysis(case_id, outputs)
    pipeline_by_source = {
        result.get("source_file"): result
        for result in _case_intelligence_results(case_id, outputs)
        if result.get("source_file")
    }

    events = []

    for output in outputs:
        timestamp = output.get("timestamp", "")
        source_file = output.get("source_file", "unknown evidence")
        evidence_hash = output.get("hash", "")
        entities = output.get("entities", {})
        entity_counts = {key: len(value) for key, value in entities.items() if isinstance(value, list)}
        total_entities = sum(entity_counts.values())
        pipeline_result = pipeline_by_source.get(source_file)

        events.append({
            "id": f"{source_file}-upload",
            "timestamp": timestamp,
            "type": "EVIDENCE INGESTED",
            "kind": "evidence",
            "desc": f"{source_file} was uploaded into {case_id}.",
            "source_file": source_file,
            "hash": evidence_hash,
            "alert": False
        })

        if evidence_hash:
            events.append({
                "id": f"{source_file}-hash",
                "timestamp": timestamp,
                "type": "FORENSIC HASH GENERATED",
                "kind": "hash",
                "desc": f"SHA-256 integrity hash recorded: {evidence_hash[:16]}...",
                "source_file": source_file,
                "hash": evidence_hash,
                "alert": False
            })

        events.append({
            "id": f"{source_file}-entities",
            "timestamp": timestamp,
            "type": "ENTITIES EXTRACTED",
            "kind": "entity",
            "desc": f"Backend extractor found {total_entities} entities: {entity_counts}.",
            "source_file": source_file,
            "entities": entities,
            "alert": total_entities > 0
        })

        for entity_type, values in entities.items():
            if not isinstance(values, list):
                continue
            for value in values:
                events.append({
                    "id": f"{source_file}-{entity_type}-{value}",
                    "timestamp": timestamp,
                    "type": f"{entity_type.rstrip('s').upper()} NODE ADDED",
                    "kind": "graph",
                    "desc": f"{value} added to the {case_id} link graph from {source_file}.",
                    "source_file": source_file,
                    "entity_type": entity_type,
                    "entity": value,
                    "alert": entity_type in ["wallets", "urls"]
                })

        if pipeline_result:
            risk = pipeline_result.get("risk_assessment", {})
            intent = pipeline_result.get("intent", {})
            events.append({
                "id": f"{source_file}-risk",
                "timestamp": pipeline_result.get("timestamp", timestamp),
                "type": "RISK SCORE UPDATED",
                "kind": "risk",
                "desc": f"Risk engine classified {source_file} as {risk.get('level', 'UNKNOWN')} ({risk.get('score', 0)}/100), intent: {', '.join(intent.get('labels', [])) or 'unknown'}.",
                "source_file": source_file,
                "risk": risk,
                "intent": intent,
                "alert": risk.get("level") in ["HIGH", "CRITICAL"]
            })
        else:
            events.append({
                "id": f"{source_file}-risk-pending",
                "timestamp": timestamp,
                "type": "RISK SCORE PENDING",
                "kind": "risk",
                "desc": f"{source_file} has parsed entities but no matching risk record in pipeline_test_results.json yet.",
                "source_file": source_file,
                "alert": False
            })

    return {
        "case_id": case_id,
        "events": sorted(events, key=lambda item: item.get("timestamp", ""))
    }


@router.get("/cases/{case_id}", tags=["cases"])
async def get_case_details(case_id: str):
    metadata = _load_case_registry().get(case_id, {})
    outputs = _load_processed_cases(case_id)
    if outputs:
        _ensure_case_analysis(case_id, outputs)
        pipeline_results = _case_intelligence_results(case_id, outputs)
        risk_results = [result.get("risk_assessment", {}) for result in pipeline_results]
        highest_risk = max(risk_results, key=lambda risk: risk.get("score", 0), default=None)
        intent = next((result.get("intent") for result in pipeline_results if result.get("intent")), None)

        return {
            "case_id": case_id,
            "title": metadata.get("title"),
            "status": metadata.get("status", "INVESTIGATION"),
            "stage": metadata.get("stage", "INVESTIGATION"),
            "assignedTo": metadata.get("assignedTo", "Lead Investigator"),
            "source_file": outputs[0].get("source_file"),
            "evidence_count": len(outputs),
            "entities": _merge_entities(outputs),
            "raw_text": "\n\n".join(output.get("raw_text", "") for output in outputs),
            "timestamp": outputs[0].get("timestamp"),
            "hashes": [output.get("hash") for output in outputs if output.get("hash")],
            "risk_assessment": highest_risk or {"score": 0, "level": "LOW", "reasons": ["Evidence uploaded; risk scoring pending."]},
            "intent": intent or {"labels": ["awaiting_analysis"], "confidence": 0.0}
        }
    
    return {
        "case_id": case_id,
        "title": metadata.get("title") or f"Forensic Case: {case_id.split('-')[-1]}",
        "status": metadata.get("status", "INVESTIGATION"),
        "stage": metadata.get("stage", "COMPLAINT"),
        "assignedTo": metadata.get("assignedTo", "Lead Investigator"),
        "evidence_count": 0,
        "risk_assessment": {"score": 0, "level": "LOW", "reasons": ["No processed data found. Please upload evidence."]},
        "intent": {"labels": ["awaiting_upload"], "confidence": 0.0},
        "entities": {"wallets": [], "emails": [], "phones": [], "urls": []},
        "raw_text": "Waiting for forensic evidence payload to be uploaded..."
    }

@router.get("/intelligence/inference/{case_id}", tags=["intelligence"])
async def get_case_inference(case_id: str):
    outputs = _load_processed_cases(case_id)
    if not outputs:
        return {"inference": "Insufficient data to draw inference. Please upload forensic evidence."}

    _ensure_case_analysis(case_id, outputs)
    pipeline_results = _case_intelligence_results(case_id, outputs)
    
    entities = _merge_entities(outputs)
    wallet_count = len(entities.get("wallets", []))
    url_count = len(entities.get("urls", []))
    email_count = len(entities.get("emails", []))
    
    highest_risk = max((res.get("risk_assessment", {}) for res in pipeline_results), key=lambda r: r.get("score", 0), default={"level": "LOW", "score": 0, "reasons": []})
    
    intent_labels = []
    for res in pipeline_results:
        intent_labels.extend(res.get("intent", {}).get("labels", []))
    unique_intents = list(set(intent_labels))
    intent_str = ", ".join(unique_intents).replace("_", " ").title() if unique_intents else "Unknown Activity"

    inference = f"NexusIQ AI has analyzed {len(outputs)} evidence files for {case_id}."
    inference += f" The overall risk level is {highest_risk['level']} (Score: {highest_risk['score']}/100)."
    inference += f" The primary operational intent is classified as '{intent_str}'."
    
    if wallet_count > 0 or url_count > 0:
        inference += f" The system extracted {wallet_count} cryptocurrency wallets and {url_count} suspicious URLs."
    
    reasons = highest_risk.get("reasons", [])
    if reasons:
        inference += f" Key risk indicators include: {', '.join(reasons)}."
        
    if highest_risk['level'] in ['HIGH', 'CRITICAL']:
        if wallet_count > 0:
            inference += " Recommendation: Issue immediate subpoenas for identified wallet addresses and trace funds via chain analysis."
        else:
            inference += " Recommendation: Escalate to Cyber Crimes unit for immediate review."
    else:
        inference += " Recommendation: Continue standard evidence collection and monitoring."

    return {"inference": inference}

@router.get("/intelligence/risk-targets", tags=["intelligence"])
async def get_risk_targets(case_id: str = None):
    case_entities = _merge_entities(_load_processed_cases(case_id)) if case_id else {"wallets": [], "emails": [], "phones": [], "names": [], "urls": []}
    outputs = _load_processed_cases(case_id) if case_id else []
    if case_id:
        _ensure_case_analysis(case_id, outputs)
    pipeline_results = _case_intelligence_results(case_id, outputs) if case_id else []
    case_risk = max(
        pipeline_results,
        key=lambda result: result.get("risk_assessment", {}).get("score", 0),
        default=None
    )

    targets = []
    
    # If we found real ML data for this case, build the targets dynamically!
    if case_risk and any(case_entities.values()):
        risk_data = case_risk.get("risk_assessment", {})
        reasons = risk_data.get("reasons", [])
        
        # We will create a "Target" for the top extracted entities
        # Prioritize Wallets, then Emails, then Phones
        target_entities = []
        for w in case_entities.get("wallets", []): target_entities.append({"id": w, "type": "Wallet"})
        for e in case_entities.get("emails", []): target_entities.append({"id": e, "type": "Email"})
        for p in case_entities.get("phones", []): target_entities.append({"id": p, "type": "Phone"})
        
        if not target_entities:
            target_entities.append({"id": "Unknown Actor", "type": "Entity"})

        primary_target = target_entities[0]
        
        factors = []
        for reason in reasons:
            factors.append({
                "label": "AI Assessment",
                "score": risk_data.get("score", 50),
                "trend": "up",
                "reason": reason
            })
            
        targets.append({
            "id": primary_target["id"],
            "name": f"Suspect: {primary_target['id']}",
            "alias": primary_target["type"],
            "score": risk_data.get("score", 50),
            "level": risk_data.get("level", "MEDIUM"),
            "factors": factors,
            "entities": { 
                "wallets": len(case_entities.get("wallets", [])), 
                "phones": len(case_entities.get("phones", [])), 
                "cases": 1 
            }
        })
        
    else:
        # Fallback if no specific ML data found for this case
        targets.append({
            "id": "System Default",
            "name": "Awaiting Pipeline Processing",
            "alias": "Pending",
            "score": 0,
            "level": "LOW",
            "factors": [{"label": "Status", "score": 0, "trend": "stable", "reason": "No extracted entities or risk factors found in the backend output."}],
            "entities": { "wallets": 0, "phones": 0, "cases": 0 }
        })

    return { "targets": targets }

@router.get("/watchlist/list/{case_id}", tags=["watchlist"])
async def get_watchlist(case_id: str):
    entities_list = []

    seen = set()
    for data in _load_processed_cases(case_id):
        date_str = data.get("timestamp", "2024-05-11").split("T")[0]
        for w in data.get("entities", {}).get("wallets", []):
            key = ("Wallet", w)
            if key not in seen:
                seen.add(key)
                entities_list.append({"id": f"W-{w[:4]}", "value": w, "type": "Wallet", "date": date_str, "status": "Triggered", "addedBy": "System AI"})
        for e in data.get("entities", {}).get("emails", []):
            key = ("Email", e)
            if key not in seen:
                seen.add(key)
                entities_list.append({"id": f"E-{e[:4]}", "value": e, "type": "Email", "date": date_str, "status": "Active", "addedBy": "System AI"})
        for p in data.get("entities", {}).get("phones", []):
            key = ("Phone", p)
            if key not in seen:
                seen.add(key)
                entities_list.append({"id": f"P-{p[-4:]}", "value": p, "type": "Phone", "date": date_str, "status": "Active", "addedBy": "System AI"})

    for item in _load_manual_watchlist().get(case_id, []):
        key = (item.get("type"), item.get("value"))
        if key not in seen:
            seen.add(key)
            entities_list.append(item)

    if not entities_list:
        entities_list.append({ "id": "SYS-1", "value": "Awaiting Pipeline Extraction", "type": "System", "date": "N/A", "status": "Pending", "addedBy": "System" })

    return { "entities": entities_list }


@router.post("/watchlist/add", tags=["watchlist"])
async def add_watchlist_entity(payload: dict = Body(...)):
    case_id = payload.get("case_id")
    value = (payload.get("value") or "").strip()
    entity_type = payload.get("type", "Entity")
    policy = payload.get("policy", "Any Activity")

    if not case_id or not value:
        raise HTTPException(status_code=400, detail="case_id and value are required")

    watchlist = _load_manual_watchlist()
    case_items = watchlist.setdefault(case_id, [])
    normalized_type = entity_type.replace(" Address", "").replace(" Number", "")

    existing = next((item for item in case_items if item.get("type") == normalized_type and item.get("value") == value), None)
    if existing:
        existing["policy"] = policy
        existing["status"] = "Active"
        saved_item = existing
    else:
        saved_item = {
            "id": f"MAN-{uuid.uuid4().hex[:8]}",
            "value": value,
            "type": normalized_type,
            "date": datetime.now().date().isoformat(),
            "status": "Active",
            "addedBy": "Lead Investigator",
            "policy": policy
        }
        case_items.append(saved_item)

    _save_manual_watchlist(watchlist)
    return {"success": True, "entity": saved_item}


@router.delete("/watchlist/{case_id}/{entity_id}", tags=["watchlist"])
async def delete_watchlist_entity(case_id: str, entity_id: str):
    watchlist = _load_manual_watchlist()
    case_items = watchlist.get(case_id, [])
    next_items = [item for item in case_items if item.get("id") != entity_id]
    watchlist[case_id] = next_items
    _save_manual_watchlist(watchlist)
    return {"success": True, "removed": len(case_items) - len(next_items)}

@router.get("/alerts/live/{case_id}", tags=["watchlist"])
async def get_live_alerts(case_id: str):
    alerts = []

    for result in _case_intelligence_results(case_id):
        reasons = result.get("risk_assessment", {}).get("reasons", [])
        level = result.get("risk_assessment", {}).get("level", "HIGH")
        for idx, reason in enumerate(reasons):
            alerts.append({
                "id": f"AL-{len(alerts)}",
                "entity": result.get("source_file", "Unknown Target"),
                "trigger": reason,
                "time": "Just now",
                "priority": level
            })

    if not alerts:
        alerts.append({ "id": "AL-NONE", "entity": "System", "trigger": "No active risk factors detected.", "time": "Now", "priority": "LOW" })

    return { "alerts": alerts }

@router.get("/admin/audit-log", tags=["admin"])
async def get_audit_log():
    logs = []

    for output in _load_processed_cases():
        logs.append({
            "time": output.get("timestamp", ""),
            "user": output.get("chain_of_custody", {}).get("officer", "Backend Pipeline"),
            "action": "Evidence Ingest",
            "detail": f"{output.get('source_file')} processed for {output.get('case_id')} with hash {output.get('hash', '')[:12]}...",
            "severity": "MEDIUM"
        })

    for result in _case_intelligence_results("CASE-20260510-F020"):
        risk = result.get("risk_assessment", {})
        logs.append({
            "time": result.get("timestamp", ""),
            "user": "Risk Engine",
            "action": "Risk Assessment",
            "detail": f"{result.get('source_file')} scored {risk.get('score', 0)}/100 ({risk.get('level', 'LOW')})",
            "severity": "HIGH" if risk.get("level") in ["HIGH", "CRITICAL"] else "LOW"
        })

    comments = _load_collab_comments()
    for case_id, case_comments in comments.items():
        for comment in case_comments:
            logs.append({
                "time": comment.get("time", ""),
                "user": comment.get("user", "Lead Investigator"),
                "action": "Collaboration Comment",
                "detail": f"{case_id}: {comment.get('text', '')[:120]}",
                "severity": "LOW"
            })

    logs.extend(_load_audit_events())

    return {"logs": sorted(logs, key=lambda item: item.get("time", ""), reverse=True)}


@router.post("/admin/reconcile-analysis", tags=["admin"])
async def reconcile_analysis(payload: dict = Body(default={})):
    force = bool(payload.get("force", False))
    outputs_by_case = {}
    for output in _load_processed_cases():
        case_id = output.get("case_id")
        if not case_id:
            continue
        outputs_by_case.setdefault(case_id, []).append(output)

    results = [
        _ensure_case_analysis(case_id, outputs, force=force)
        for case_id, outputs in sorted(outputs_by_case.items())
    ]

    return {
        "success": True,
        "cases_checked": len(results),
        "pipeline_written": sum(result.get("pipeline_written", 0) for result in results),
        "graph_ingested": sum(
            1 for result in results
            if (result.get("graph_result") or {}).get("status") == "success"
        ),
        "results": results
    }


@router.get("/admin/system-health", tags=["admin"])
async def get_system_health():
    outputs = _load_processed_cases()
    entity_totals = _merge_entities(outputs)
    evidence_count = len(outputs)
    case_ids = sorted({output.get("case_id") for output in outputs if output.get("case_id")})
    pipeline_results = []
    for case_id in case_ids:
        pipeline_results.extend(_case_intelligence_results(case_id))

    neo4j_status = "Online"
    try:
        with get_session() as session:
            session.run("RETURN 1 AS ok").single()
    except Exception as exc:
        neo4j_status = f"Unavailable: {str(exc)[:80]}"

    return {
        "database": {
            "neo4j": neo4j_status,
            "processed_cases": len(case_ids),
            "evidence_files": evidence_count,
            "entity_nodes": sum(len(values) for values in entity_totals.values())
        },
        "api": {
            "status": "Online",
            "routes": {
                "evidence": "/evidence/upload",
                "graph": "/graph/{case_id}",
                "semantic_search": "/intelligence/semantic-search",
                "risk": "/intelligence/risk-targets",
                "collab": "/collab/{case_id}/data"
            },
            "pipeline_results": len(pipeline_results)
        },
        "security": {
            "storage_hashing": "SHA-256",
            "auth_mode": "Single investigator login",
            "chain_of_custody": "Enabled",
            "manual_watchlist_store": os.path.exists(_watchlist_path())
        }
    }

@router.post("/intelligence/semantic-search", tags=["intelligence"])
async def semantic_search(request: dict = Body(...)):
    query = request.get("query", "")
    case_id = request.get("case_id", "GLOBAL")

    def lexical_results(error: Optional[Exception] = None):
        semantic_map = {
            "romance": ["love", "beautiful", "widowed", "doctor", "feelings", "gifts", "daughter", "school fees"],
            "crypto": ["btc", "bitcoin", "wallet", "cold storage", "funds", "transfer", "assets"],
            "phishing": ["login", "account", "security", "frozen", "verify", "portal", "password"],
            "urgency": ["urgent", "immediately", "critical", "within", "hours", "permanently"],
            "threat": ["do not contact", "authorities", "loss", "frozen", "critical"],
            "contact": ["email", "phone", "whatsapp", "proton", "gmail"],
            "url": ["http", "https", "onion", "portal", "login"],
            "wallet": ["wallet", "btc", "bitcoin", "address", "cold storage"]
        }

        raw_terms = [term.lower() for term in re.findall(r"[a-zA-Z0-9@._:/+-]+", query) if len(term) > 2]
        concepts = [concept for concept, words in semantic_map.items() if concept in raw_terms or any(word in " ".join(raw_terms) for word in words)]
        terms = list(dict.fromkeys(raw_terms + [word for concept in concepts for word in semantic_map[concept]]))
        outputs = _load_processed_cases(case_id if case_id != "GLOBAL" else None)
        results = []

        for idx, data in enumerate(outputs):
            raw = data.get("raw_text", "")
            lower_raw = raw.lower()
            entities = data.get("entities", {})
            entity_values = [str(value) for values in entities.values() if isinstance(values, list) for value in values]
            entity_blob = " ".join(entity_values).lower()

            term_hits = sum(lower_raw.count(term) for term in terms)
            entity_hits = sum(1 for term in raw_terms if term in entity_blob)
            concept_hits = sum(1 for concept in concepts if any(word in lower_raw for word in semantic_map[concept]))
            exact_entity_hits = sum(1 for value in entity_values if query.lower() and query.lower() in value.lower())
            score = (term_hits * 7) + (entity_hits * 18) + (concept_hits * 15) + (exact_entity_hits * 25)

            if query and score == 0:
                continue

            first_hit_positions = [lower_raw.find(term) for term in terms if lower_raw.find(term) >= 0]
            start = max(min(first_hit_positions) - 80, 0) if first_hit_positions else 0
            snippet_text = raw[start:start + 320]
            if start > 0:
                snippet_text = "..." + snippet_text
            if start + 320 < len(raw):
                snippet_text = snippet_text + "..."
            for term in sorted(raw_terms[:8], key=len, reverse=True):
                snippet_text = re.sub(f"({re.escape(term)})", r"<mark class='bg-blue-500/30 text-white px-1'>\1</mark>", snippet_text, flags=re.IGNORECASE)

            relevance = min(0.99, 0.35 + score / 100)
            results.append({
                "id": idx + 1,
                "title": f"Evidence Match: {data.get('source_file', data.get('case_id'))}",
                "relevance": round(relevance, 2),
                "snippet": f"[FORENSIC NLP] {snippet_text}",
                "date": data.get("timestamp", "2024-05-11").split("T")[0],
                "entities": [f"Hash: {data.get('hash', 'N/A')[:8]}..."] + entity_values[:4],
                "case": data.get("case_id"),
                "signals": concepts,
                "matched_terms": [term for term in raw_terms if term in lower_raw or term in entity_blob][:8]
            })

        return {"results": sorted(results, key=lambda item: item["relevance"], reverse=True)[:5]}

    if not request.get("use_vector"):
        return lexical_results()
    
    try:
        # Dynamically append the AI engine path
        engine_path = os.path.join(os.getcwd(), "person2_ai_engine")
        if engine_path not in sys.path:
            sys.path.insert(0, engine_path)
        loaded_models = sys.modules.get("models")
        if loaded_models is not None and not hasattr(loaded_models, "__path__"):
            sys.modules.pop("models", None)
            
        from services.embedding_service import EmbeddingService
        from utils.similarity import SimilarityFinder
        import glob
        import time
        
        print("Initializing NLP Engine for Semantic Search...")
        emb_service = EmbeddingService()
        sim_finder = SimilarityFinder()
        
        case_data = {}
        stored_embeddings = {}
        
        print(f"Reading corpus for {case_id}")
        for idx, data in enumerate(_load_processed_cases(case_id if case_id != "GLOBAL" else None)):
            if "case_id" in data and "raw_text" in data:
                evidence_key = f"{data['case_id']}::{data.get('source_file', idx)}::{idx}"
                case_data[evidence_key] = data
                stored_embeddings[evidence_key] = emb_service.generate_embedding(data["raw_text"])
                    
        if not stored_embeddings:
            raise ValueError("No processed evidence found to search against.")
            
        # Find top 3 most similar cases using Cosine Similarity
        top_matches = sim_finder.find_similar_cases(query, stored_embeddings, top_k=3)
        
        results = []
        for idx, (cid, score) in enumerate(top_matches):
            data = case_data[cid]
            # Create a highlight-friendly snippet
            raw = data["raw_text"]
            snippet = (raw[:150] + "...") if len(raw) > 150 else raw
            
            results.append({
                "id": idx + 1,
                "title": f"Vector Match: {data.get('source_file', cid)}",
                "relevance": round(float(score), 2),
                "snippet": f"[AI MATCH] {snippet}",
                "date": data.get("timestamp", "2024-05-11").split("T")[0],
                "entities": [f"Hash: {data.get('hash', 'N/A')[:8]}..."],
                "case": cid
            })
            
        return {"results": results}

    except Exception as e:
        print(f"NLP Search Error: {e}. Falling back to backend lexical evidence search.")
        return lexical_results(e)

@router.get("/collab/{case_id}/data", tags=["collaboration"])
async def get_collab_data(case_id: str):
    current_case_entities = _merge_entities(_load_processed_cases(case_id))
    all_other_cases = {}

    for data in _load_processed_cases():
        cid = data.get("case_id")
        if not cid or cid == case_id:
            continue
        all_other_cases.setdefault(cid, {"wallets": [], "emails": [], "phones": [], "urls": [], "names": []})
        all_other_cases[cid] = _merge_entities([
            {"entities": all_other_cases[cid]},
            data
        ])

    # 2. Compute dynamic overlap
    overlap = []
    
    for entity_type, entities in current_case_entities.items():
        if not isinstance(entities, list): continue
        for entity in entities:
            for other_cid, other_entities in all_other_cases.items():
                if entity in other_entities.get(entity_type, []):
                    # Found an overlap!
                    overlap.append({
                        "entity": entity,
                        "type": entity_type.capitalize().rstrip('s'),
                        "otherCase": other_cid,
                        "agency": "SYSTEM_AI_FLAG",
                        "risk": "HIGH"
                    })

    # Default UI payload
    active_users = [
        { "name": "Lead Investigator", "agency": "Nexus HQ", "status": "viewing Case Data", "active": True },
        { "name": "System AI", "agency": "Backend Pipeline", "status": f"{sum(len(v) for v in current_case_entities.values())} entities indexed", "active": True }
    ]
    
    system_comments = [
        { "user": "System AI", "time": "Just now", "text": f"Scanned case {case_id} and found {len(overlap)} overlaps with existing investigations." }
    ]
    comments = system_comments + _load_collab_comments().get(case_id, [])

    return {
        "active_users": active_users,
        "overlap": overlap,
        "comments": comments
    }


@router.post("/collab/{case_id}/comment", tags=["collaboration"])
async def add_collab_comment(case_id: str, payload: dict = Body(...)):
    text = (payload.get("text") or "").strip()
    user = payload.get("user", "Lead Investigator")
    if not text:
        raise HTTPException(status_code=400, detail="Comment text is required")

    comments = _load_collab_comments()
    item = {
        "id": f"COM-{uuid.uuid4().hex[:8]}",
        "user": user,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "text": text
    }
    comments.setdefault(case_id, []).append(item)
    _save_collab_comments(comments)
    return {"success": True, "comment": item}


@router.post("/collab/{case_id}/deconflict", tags=["collaboration"])
async def request_deconflict(case_id: str, payload: dict = Body(default={})):
    overlap_count = len((await get_collab_data(case_id))["overlap"])
    comments = _load_collab_comments()
    item = {
        "id": f"DCF-{uuid.uuid4().hex[:8]}",
        "user": "System AI",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "text": f"De-confliction request queued for {case_id}. {overlap_count} overlap(s) attached for review."
    }
    comments.setdefault(case_id, []).append(item)
    _save_collab_comments(comments)
    return {"success": True, "request": item}

# --- Maintain backward compatibility ---




@router.post("/process/{evidence_id}", response_model=EvidenceProcessResponse, tags=["evidence"])
async def process_evidence(evidence_id: str):
    if evidence_id not in evidence_storage:
        raise HTTPException(status_code=404, detail="Evidence not found")
    evidence_data = evidence_storage[evidence_id]
    processed = evidence_processor.process_file(evidence_data["content"], evidence_data["filename"], evidence_data["format"])
    return EvidenceProcessResponse(success=True, evidence_id=evidence_id, processed_output=processed, message="Processed")
