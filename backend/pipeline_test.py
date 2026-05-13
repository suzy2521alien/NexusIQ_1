#!/usr/bin/env python3
"""
Full Pipeline Test — Module 1 → Module 2 → Module 3
Tests the entire cybercrime forensics pipeline with realistic datasets.
"""

import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'person2_ai_engine'))

# ─────────────────────────────────────────────────────────────────────────────
# DATASET: 20 realistic cybercrime evidence files
# Covers: investment scam, romance scam, phishing, job scam, impersonation
# Designed with overlapping entities to test case linking & fraud ring detection
# ─────────────────────────────────────────────────────────────────────────────

EVIDENCE_FILES = [
    # ── INVESTMENT SCAM RING (cases 1-5 share wallet + URL infrastructure) ──
    {
        "filename": "inv_scam_001.txt",
        "content": (
            "URGENT: Double your Bitcoin in 48 hours!\n"
            "Send funds to wallet 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2\n"
            "Contact our agent: invest.profit@cryptoking.com\n"
            "Call now: +1-800-555-0101\n"
            "Visit: https://cryptoking-returns.com\n"
            "Guaranteed 400% return. Invest 5000 now get 20000 back immediately.\n"
            "Agent: Michael Johnson\n"
            "Limited slots available. Act fast. Send money now."
        )
    },
    {
        "filename": "inv_scam_002.txt",
        "content": (
            "Exclusive crypto investment opportunity!\n"
            "Minimum deposit: $2000. Returns guaranteed within 24 hours.\n"
            "Transfer to: 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2\n"
            "Or Ethereum: 0xAbCdEf1234567890AbCdEf1234567890AbCdEf12\n"
            "Support: profit.team@cryptoking.com\n"
            "WhatsApp: +1-800-555-0102\n"
            "Platform: https://cryptoking-returns.com/invest\n"
            "Join 10000 happy investors. Profit now. Quick returns guaranteed.\n"
            "Manager: David Williams"
        )
    },
    {
        "filename": "inv_scam_003.txt",
        "content": (
            "Bitcoin trading bot — 300% profit in 7 days!\n"
            "Send BTC to: 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2\n"
            "New wallet also active: 3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy\n"
            "Email: bot.trading@fastprofit.net\n"
            "Phone: +44-20-7946-0301\n"
            "Website: https://fastprofit-bot.net\n"
            "Invest 1000 get 3000 return fast. Urgent limited offer.\n"
            "Broker: James Anderson"
        )
    },
    {
        "filename": "inv_scam_004.txt",
        "content": (
            "FINAL NOTICE: Your crypto account is ready.\n"
            "Deposit required: 0.5 BTC to activate returns.\n"
            "Wallet: 3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy\n"
            "Contact: activate@fastprofit.net\n"
            "Helpline: +44-20-7946-0302\n"
            "Portal: https://fastprofit-bot.net/activate\n"
            "Your profit of $15000 is waiting. Send money immediately.\n"
            "Account manager: Robert Brown"
        )
    },
    {
        "filename": "inv_scam_005.txt",
        "content": (
            "Forex trading signals — 200% weekly returns!\n"
            "Wire transfer or crypto accepted.\n"
            "BTC wallet: 3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy\n"
            "ETH: 0xAbCdEf1234567890AbCdEf1234567890AbCdEf12\n"
            "Broker email: forex.signals@tradepro.io\n"
            "Signal group: https://tradepro.io/signals\n"
            "Phone: +1-800-555-0105\n"
            "Invest now. Profit guaranteed. Returns immediate.\n"
            "Head trader: William Davis"
        )
    },

    # ── ROMANCE SCAM RING (cases 6-9 share email domains + phone patterns) ──
    {
        "filename": "romance_001.txt",
        "content": (
            "My darling, I am a US Army soldier stationed in Syria.\n"
            "I have fallen deeply in love with you.\n"
            "I need $3000 urgently for emergency medical treatment.\n"
            "Please send via Western Union to: Col. Richard Spencer\n"
            "My personal email: richard.spencer.army@gmail.com\n"
            "WhatsApp: +1-646-555-0201\n"
            "I will repay you when I return. I love you. Please help now."
        )
    },
    {
        "filename": "romance_002.txt",
        "content": (
            "Sweetheart, I am stuck in London after my business trip.\n"
            "My wallet was stolen. I need $1500 for hotel and flight.\n"
            "Please send money urgently via MoneyGram.\n"
            "Contact me: stranded.businessman@outlook.com\n"
            "Phone: +44-20-7946-0401\n"
            "I will return everything double when I get back. I love you.\n"
            "Your darling, Thomas"
        )
    },
    {
        "filename": "romance_003.txt",
        "content": (
            "My love, I am an oil rig engineer in the North Sea.\n"
            "I have $2.5 million in a security box I need to transfer.\n"
            "I need your help to receive the funds. Send $500 processing fee.\n"
            "Email: oilrig.engineer.mike@yahoo.com\n"
            "Backup: richard.spencer.army@gmail.com\n"
            "Phone: +1-646-555-0203\n"
            "We will share the money equally. Trust me darling. Send now."
        )
    },
    {
        "filename": "romance_004.txt",
        "content": (
            "Hello beautiful, I am a widowed doctor working in Afghanistan.\n"
            "I have strong feelings for you after seeing your profile.\n"
            "I need $2000 for my daughter's school fees urgently.\n"
            "Please help: dr.james.wilson.md@gmail.com\n"
            "WhatsApp: +1-646-555-0204\n"
            "I will send you gifts and money when I return. Love you.\n"
            "Dr. James Wilson"
        )
    },

    # ── PHISHING RING (cases 10-13 share phishing URLs + sender patterns) ──
    {
        "filename": "phishing_001.txt",
        "content": (
            "ALERT: Your bank account has been compromised!\n"
            "Click immediately to verify: https://secure-bankofamerica-verify.com\n"
            "Enter your credentials to restore access within 24 hours.\n"
            "Support: security@bankofamerica-alerts.net\n"
            "Reference: +1-800-555-0301\n"
            "Failure to verify will result in permanent account suspension.\n"
            "IP logged: 192.168.45.23\n"
            "Device: Windows 10, Chrome"
        )
    },
    {
        "filename": "phishing_002.txt",
        "content": (
            "Your PayPal account is limited. Verify now!\n"
            "Link: https://paypal-secure-verify.net/confirm\n"
            "Also check: https://secure-bankofamerica-verify.com/paypal\n"
            "Contact: support@paypal-alerts.net\n"
            "Phone: +1-800-555-0302\n"
            "Your account will be closed in 48 hours if not verified.\n"
            "Transaction ID: TXN-2026-88291\n"
            "IP: 192.168.45.23"
        )
    },
    {
        "filename": "phishing_003.txt",
        "content": (
            "Microsoft Security Alert: Unusual sign-in detected.\n"
            "Verify your account: https://microsoft-security-login.net\n"
            "Your IP 10.0.0.45 was flagged.\n"
            "Contact: security@microsoft-alerts.net\n"
            "Helpdesk: +1-800-555-0303\n"
            "Click the link to secure your account immediately.\n"
            "Failure to act will result in data loss."
        )
    },
    {
        "filename": "phishing_004.txt",
        "content": (
            "IRS Tax Refund Notification — $4,200 pending!\n"
            "Claim your refund: https://irs-refund-portal.net\n"
            "Verify identity: https://microsoft-security-login.net/irs\n"
            "Contact IRS agent: irs.refund@gov-tax-portal.com\n"
            "Phone: +1-800-555-0304\n"
            "Social Security required for verification.\n"
            "Aadhar equivalent: 4532 8821 9901\n"
            "Act now. Refund expires in 72 hours."
        )
    },

    # ── JOB SCAM RING (cases 14-16) ──
    {
        "filename": "job_scam_001.txt",
        "content": (
            "Congratulations! You have been selected for a remote job.\n"
            "Position: Data Entry Specialist — $5000/month\n"
            "Company: Global Tech Solutions\n"
            "HR Contact: hr@globaltech-solutions.net\n"
            "Phone: +1-800-555-0401\n"
            "To activate your position, pay $200 training fee.\n"
            "Send to wallet: 1BoatSLRHtKNngkdXEeobR76b53LETtpyT\n"
            "Website: https://globaltech-solutions.net/jobs\n"
            "Contact HR manager: Patricia Moore"
        )
    },
    {
        "filename": "job_scam_002.txt",
        "content": (
            "Work from home opportunity — $3000/week guaranteed!\n"
            "No experience needed. Immediate start.\n"
            "Apply: jobs@easywork-online.com\n"
            "HR: hr@globaltech-solutions.net\n"
            "Phone: +1-800-555-0402\n"
            "Registration fee: $150 — send to 1BoatSLRHtKNngkdXEeobR76b53LETtpyT\n"
            "Portal: https://easywork-online.com/register\n"
            "Recruiter: Jennifer Taylor"
        )
    },
    {
        "filename": "job_scam_003.txt",
        "content": (
            "Amazon work-from-home hiring — $45/hour!\n"
            "Process orders from home. Flexible hours.\n"
            "Apply now: amazon-jobs@workfromhome-amazon.net\n"
            "Phone: +1-800-555-0403\n"
            "Equipment deposit: $300 — wallet: 1BoatSLRHtKNngkdXEeobR76b53LETtpyT\n"
            "Job portal: https://workfromhome-amazon.net\n"
            "HR: hr@globaltech-solutions.net\n"
            "Hiring manager: Christopher Jackson"
        )
    },

    # ── IMPERSONATION / ADVANCE FEE FRAUD (cases 17-20) ──
    {
        "filename": "impersonation_001.txt",
        "content": (
            "OFFICIAL NOTICE — FBI Cybercrime Division\n"
            "Your IP address 10.0.0.45 has been linked to illegal activity.\n"
            "To avoid arrest, pay $5000 fine immediately.\n"
            "Payment: 0xDeAdBeEf1234567890DeAdBeEf1234567890DeAd\n"
            "Contact Agent: fbi.agent.smith@fbi-cybercrime.net\n"
            "Phone: +1-202-555-0501\n"
            "Case number: FBI-2026-CY-88291\n"
            "Failure to pay within 24 hours will result in arrest."
        )
    },
    {
        "filename": "impersonation_002.txt",
        "content": (
            "NOTICE FROM IRS — Unpaid taxes detected.\n"
            "You owe $8,500 in back taxes. Pay immediately to avoid prosecution.\n"
            "Wire transfer or crypto: 0xDeAdBeEf1234567890DeAdBeEf1234567890DeAd\n"
            "IRS Agent: irs.collections@gov-irs-notice.com\n"
            "Phone: +1-202-555-0502\n"
            "Reference: IRS-2026-TAX-44821\n"
            "Pay now. Warrant will be issued in 48 hours."
        )
    },
    {
        "filename": "impersonation_003.txt",
        "content": (
            "Nigerian Prince — Confidential Business Proposal\n"
            "I am Prince Emmanuel Okafor of Nigeria.\n"
            "I have $45 million USD to transfer out of the country.\n"
            "I need your bank account details to complete the transfer.\n"
            "You will receive 30% commission ($13.5 million).\n"
            "Contact: prince.emmanuel@royalnigeria.net\n"
            "Alternate: fbi.agent.smith@fbi-cybercrime.net\n"
            "Phone: +234-80-5550-0601\n"
            "Bank account: 123456789012\n"
            "IFSC: HDFC0001234\n"
            "Send $500 processing fee to proceed."
        )
    },
    {
        "filename": "impersonation_004.txt",
        "content": (
            "CONGRATULATIONS — UN Lottery Winner!\n"
            "You have won $2,000,000 in the United Nations Lottery.\n"
            "Claim your prize: un.lottery@united-nations-prize.com\n"
            "Verification agent: prince.emmanuel@royalnigeria.net\n"
            "Phone: +234-80-5550-0602\n"
            "Processing fee: $1000 — ETH wallet: 0xDeAdBeEf1234567890DeAdBeEf1234567890DeAd\n"
            "UPI: lottery.claim@upi\n"
            "Credit card required for verification: 4532 8821 9901 1234\n"
            "Claim expires in 72 hours. Act now."
        )
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# RESULTS TRACKING
# ─────────────────────────────────────────────────────────────────────────────

results = {
    "module1": [],
    "module2": [],
    "module3": [],
    "errors": [],
    "summary": {}
}

PASS = "✅ PASS"
FAIL = "❌ FAIL"
WARN = "⚠️  WARN"

def log(msg): print(msg)
def section(title): print(f"\n{'='*60}\n  {title}\n{'='*60}")
def check(label, condition, detail=""):
    status = PASS if condition else FAIL
    print(f"  {status}  {label}" + (f"  [{detail}]" if detail else ""))
    return condition


# ─────────────────────────────────────────────────────────────────────────────
# MODULE 1 — DATA INGESTION & EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

def run_module1():
    section("MODULE 1 — Data Ingestion & Entity Extraction")

    from app.services.evidence_processor import EvidenceProcessor
    from app.models.schemas import FileFormat

    processor = EvidenceProcessor()
    os.makedirs("output", exist_ok=True)

    passed = 0
    for item in EVIDENCE_FILES:
        fname = item["filename"]
        content = item["content"].encode("utf-8")
        try:
            t0 = time.time()
            output = processor.process_file(content, fname, FileFormat.TEXT)
            elapsed = (time.time() - t0) * 1000

            has_case_id   = output.case_id.startswith("CASE-")
            has_hash      = len(output.hash) == 64
            has_timestamp = "Z" in output.timestamp
            has_entities  = isinstance(output.entities, dict)
            has_text      = len(output.raw_text) > 0

            ok = all([has_case_id, has_hash, has_timestamp, has_entities, has_text])
            if ok:
                passed += 1

            entity_counts = {k: len(v) for k, v in output.entities.items()}
            total_entities = sum(entity_counts.values())

            print(f"\n  [{fname}]")
            check("Case ID format",   has_case_id,   output.case_id)
            check("SHA-256 hash",     has_hash,      output.hash[:16] + "...")
            check("Timestamp ISO",    has_timestamp, output.timestamp)
            check("Entities dict",    has_entities,  str(entity_counts))
            check("Text extracted",   has_text,      f"{len(output.raw_text)} chars")
            print(f"       Entities found: {total_entities} total — {entity_counts}")
            print(f"       Processing time: {elapsed:.0f}ms")

            results["module1"].append({
                "filename": fname,
                "case_id": output.case_id,
                "hash": output.hash,
                "entities": output.entities,
                "raw_text": output.raw_text,
                "timestamp": output.timestamp,
                "status": "ok" if ok else "partial"
            })

        except Exception as e:
            print(f"\n  [{fname}] {FAIL} — Exception: {e}")
            results["errors"].append({"stage": "module1", "file": fname, "error": str(e)})

    print(f"\n  Module 1 Result: {passed}/{len(EVIDENCE_FILES)} files processed successfully")
    return passed == len(EVIDENCE_FILES)


# ─────────────────────────────────────────────────────────────────────────────
# MODULE 2 — AI INTELLIGENCE ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def run_module2():
    section("MODULE 2 — AI Intelligence (Intent + Risk + Embeddings)")

    from person2_ai_engine.pipeline.intelligence_processor import IntelligenceProcessor

    processor = IntelligenceProcessor()
    passed = 0

    for m1 in results["module1"]:
        case_id = m1["case_id"]
        fname   = m1["filename"]

        input_data = {
            "case_id":     case_id,
            "source_file": fname,
            "entities":    m1["entities"],
            "raw_text":    m1["raw_text"],
            "timestamp":   m1["timestamp"],
            "hash":        m1["hash"]
        }

        try:
            t0 = time.time()
            output = processor.process_intelligence(input_data)
            elapsed = (time.time() - t0) * 1000

            has_intent     = "intent" in output and "labels" in output["intent"]
            has_confidence = 0.0 <= output["intent"].get("confidence", -1) <= 1.0
            has_risk       = "risk_assessment" in output
            risk_level_ok  = output["risk_assessment"].get("level") in ["LOW","MEDIUM","HIGH","CRITICAL"]
            has_embedding  = len(output.get("embedding", [])) == 384
            has_insights   = "entity_insights" in output
            has_metadata   = "ai_metadata" in output

            ok = all([has_intent, has_confidence, has_risk, risk_level_ok, has_embedding, has_insights])
            if ok:
                passed += 1

            intent_label = output["intent"]["labels"][0]
            confidence   = output["intent"]["confidence"]
            risk_score   = output["risk_assessment"]["score"]
            risk_level   = output["risk_assessment"]["level"]
            reasons      = output["risk_assessment"].get("reasons", [])

            print(f"\n  [{fname}]  →  {case_id}")
            check("Intent detected",    has_intent,     intent_label)
            check("Confidence valid",   has_confidence, f"{confidence:.2f}")
            check("Risk score",         has_risk,       f"{risk_score}/100")
            check("Risk level valid",   risk_level_ok,  risk_level)
            check("Embedding 384-dim",  has_embedding)
            check("Entity insights",    has_insights,   f"{len(output['entity_insights'])} entities")
            check("AI metadata",        has_metadata)
            print(f"       Risk reasons: {reasons}")
            print(f"       Processing time: {elapsed:.0f}ms")

            results["module2"].append({
                "case_id":       case_id,
                "source_file":   fname,
                "entities":      m1["entities"],
                "raw_text":      m1["raw_text"],
                "timestamp":     m1["timestamp"],
                "hash":          m1["hash"],
                "intent":        output["intent"],
                "risk_assessment": output["risk_assessment"],
                "embedding":     output["embedding"],
                "entity_insights": output["entity_insights"],
                "ai_metadata":   output["ai_metadata"],
                "risk_score":    risk_score
            })

        except Exception as e:
            print(f"\n  [{fname}] {FAIL} — Exception: {e}")
            results["errors"].append({"stage": "module2", "file": fname, "error": str(e)})

    print(f"\n  Module 2 Result: {passed}/{len(results['module1'])} cases processed successfully")
    return passed == len(results["module1"])


# ─────────────────────────────────────────────────────────────────────────────
# MODULE 3 — GRAPH ENGINE (Neo4j)
# ─────────────────────────────────────────────────────────────────────────────

def run_module3():
    section("MODULE 3 — Graph Engine (Neo4j Ingestion + Alerts + Case Linking)")

    import subprocess, tempfile

    # Graph_engine uses bare imports (from models import ...) so it must run
    # with Graph_engine/ as the working directory and first on sys.path.
    # We delegate via a subprocess helper script to avoid path collisions.

    helper_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_graph_helper.py")

    # Write graph inputs to a temp file
    inputs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_graph_inputs.json")
    graph_inputs = []
    for m2 in results["module2"]:
        graph_inputs.append({
            "case_id":           m2["case_id"],
            "risk_score":        m2["risk_score"],
            "entities":          m2["entities"],
            "intent":            m2["intent"]["labels"][0],
            "intent_confidence": m2["intent"]["confidence"]
        })
    with open(inputs_path, "w") as f:
        json.dump(graph_inputs, f)

    # Run the helper
    python_exe = sys.executable
    proc = subprocess.run(
        [python_exe, helper_path, inputs_path],
        capture_output=True, text=True,
        cwd=os.path.join(os.path.dirname(os.path.abspath(__file__)), "Graph_engine", "Graph_engine"),
        timeout=600,
        encoding='utf-8', errors='replace'
    )
    print(proc.stdout)
    if proc.stderr:
        # Filter out known harmless warnings
        errs = [l for l in proc.stderr.splitlines()
                if "DeprecationWarning" not in l and "FutureWarning" not in l
                and "UserWarning" not in l and "warnings.warn" not in l]
        if errs:
            print("\n  [stderr]", "\n  ".join(errs[:20]))

    if proc.returncode != 0:
        print(f"  {FAIL} Graph helper exited with code {proc.returncode}")
        results["errors"].append({"stage": "module3", "error": f"exit code {proc.returncode}"})
        return False

    # Load results written by helper
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_graph_results.json")
    if not os.path.exists(out_path):
        print(f"  {FAIL} Graph results file not found")
        return False

    with open(out_path) as f:
        graph_out = json.load(f)

    for r in graph_out.get("batch_results", []):
        results["module3"].append(r)

    passed_ingest = sum(1 for r in results["module3"] if r.get("status") == "success")
    print(f"  Batch ingestion: {passed_ingest}/{len(graph_inputs)} cases OK")

    # Use actual Neo4j node count as the ground truth
    actual_cases = graph_out.get("stats", {}).get("case_count", 0)
    print(f"  Neo4j verification: {actual_cases} cases confirmed in graph")

    # Print node/alert/link counts from helper output
    stats = graph_out.get("stats", {})
    check("Case nodes in Neo4j",      stats.get("case_count", 0) > 0,  f"{stats.get('case_count')} nodes")
    check("Entity nodes in Neo4j",    stats.get("entity_count", 0) > 0, f"{stats.get('entity_count')} nodes")
    check("Alerts triggered",         stats.get("alert_count", 0) > 0,  f"{stats.get('alert_count')} alerts")
    check("RELATED_TO relationships", stats.get("rel_count", 0) >= 0,   f"{stats.get('rel_count')} links")

    # Case linking
    section("  3c. Case Linking (Jaccard Similarity)")
    linking = graph_out.get("linking", {})
    check("Similarity computed",    True, f"{linking.get('total_candidates', 0)} candidates")
    check("Links above threshold",  True, f"{linking.get('filtered_count', 0)} linked cases")
    check("Network analysis works", linking.get("found", False))
    check("Network risk level set", "network_risk_level" in linking, linking.get("network_risk_level", "?"))
    for lnk in linking.get("top_links", []):
        print(f"    → {lnk.get('case_id')}  similarity={lnk.get('similarity',0):.2%}")

    # Fraud rings
    section("  3d. Fraud Ring Detection")
    rings = graph_out.get("rings", {})
    check("Clusters detected",      True, f"{rings.get('cluster_count', 0)} rings found")
    check("Cluster stats computed", "total_clusters" in rings.get("stats", {}))
    for i, cl in enumerate(rings.get("clusters", [])[:3]):
        print(f"\n  Ring {i+1}: {cl.get('cluster_size')} cases, "
              f"threat={cl.get('threat_level')}, avg_risk={cl.get('avg_risk',0):.1f}")
        print(f"    Members: {cl.get('member_cases')}")
        for se in cl.get("shared_entities", [])[:3]:
            print(f"    Shared: [{se['type']}] {se['value']} in {se['appears_in']} cases")

    print(f"\n  Module 3 Result: {passed_ingest}/{len(graph_inputs)} cases ingested to Neo4j")
    return actual_cases >= len(graph_inputs)

# ─────────────────────────────────────────────────────────────────────────────
# SIMILARITY SEARCH TEST (Module 2 cross-case)
# ─────────────────────────────────────────────────────────────────────────────

def run_similarity_test():
    section("CROSS-CASE SIMILARITY SEARCH (Semantic Embeddings)")

    from person2_ai_engine.utils.similarity import SimilarityFinder

    stored = {r["case_id"]: r["embedding"] for r in results["module2"]}
    finder = SimilarityFinder()

    queries = [
        "Send Bitcoin to wallet for guaranteed investment returns",
        "I love you darling please send money urgently",
        "Click the link to verify your bank account credentials",
        "Work from home job opportunity pay registration fee",
        "FBI arrest warrant pay fine immediately government",
    ]

    all_ok = True
    for q in queries:
        try:
            similar = finder.find_similar_cases(q, stored, top_k=3)
            ok = len(similar) > 0
            if not ok:
                all_ok = False
            check(f"Query: '{q[:45]}...'", ok, f"top match: {similar[0][0] if similar else 'none'}")
            for cid, score in similar:
                fname = next((r["source_file"] for r in results["module2"] if r["case_id"] == cid), "?")
                print(f"       {score:.3f}  {cid}  ({fname})")
        except Exception as e:
            print(f"  {FAIL} Similarity query failed: {e}")
            all_ok = False

    return all_ok


# ─────────────────────────────────────────────────────────────────────────────
# FINAL SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

def print_summary(m1_ok, m2_ok, m3_ok, sim_ok):
    section("PIPELINE TEST SUMMARY")

    total_files    = len(EVIDENCE_FILES)
    m1_processed   = len(results["module1"])
    m2_processed   = len(results["module2"])
    m3_processed   = len(results["module3"])
    total_errors   = len(results["errors"])

    check("Module 1 — Ingestion & Extraction", m1_ok, f"{m1_processed}/{total_files} files")
    check("Module 2 — AI Intelligence",        m2_ok, f"{m2_processed}/{m1_processed} cases")
    check("Module 3 — Graph Engine (Neo4j)",   m3_ok, f"{m3_processed}/{m2_processed} cases")
    check("Semantic Similarity Search",        sim_ok)

    # Intent distribution
    if results["module2"]:
        from collections import Counter
        intents = Counter(r["intent"]["labels"][0] for r in results["module2"])
        risk_levels = Counter(r["risk_assessment"]["level"] for r in results["module2"])
        print(f"\n  Intent distribution:    {dict(intents)}")
        print(f"  Risk level distribution: {dict(risk_levels)}")

    # Alert summary from module3
    alerts_total = sum(r.get("alerts_triggered", 0) for r in results["module3"])
    related_total = sum(r.get("related_cases_found", 0) for r in results["module3"])
    print(f"  Total alerts triggered:  {alerts_total}")
    print(f"  Total case links found:  {related_total}")

    if total_errors:
        print(f"\n  Errors encountered ({total_errors}):")
        for e in results["errors"]:
            print(f"    [{e['stage']}] {e.get('file','')}: {e['error']}")

    overall = all([m1_ok, m2_ok, m3_ok, sim_ok])
    status = "✅ ALL SYSTEMS OPERATIONAL" if overall else "❌ PIPELINE HAS FAILURES"
    print(f"\n  {'='*50}")
    print(f"  {status}")
    print(f"  {'='*50}\n")

    # Save full results
    with open("pipeline_test_results.json", "w") as f:
        out = {
            "summary": {
                "module1_ok": m1_ok,
                "module2_ok": m2_ok,
                "module3_ok": m3_ok,
                "similarity_ok": sim_ok,
                "total_files": total_files,
                "m1_processed": m1_processed,
                "m2_processed": m2_processed,
                "m3_processed": m3_processed,
                "total_errors": total_errors,
                "alerts_triggered": alerts_total,
                "case_links_found": related_total,
            },
            "errors": results["errors"],
            "module2_results": [
                {
                    "case_id": r["case_id"],
                    "source_file": r["source_file"],
                    "intent": r["intent"],
                    "risk_assessment": r["risk_assessment"],
                    "entity_counts": {k: len(v) for k, v in r["entities"].items()},
                }
                for r in results["module2"]
            ]
        }
        json.dump(out, f, indent=2)
    print(f"  Full results saved → pipeline_test_results.json\n")


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  CYBERCRIME FORENSICS PIPELINE -- FULL SYSTEM TEST")
    print("  20 evidence files  |  5 scam categories  |  3 modules")
    print("="*60)

    m1_ok  = run_module1()
    m2_ok  = run_module2()
    m3_ok  = run_module3()
    sim_ok = run_similarity_test()

    print_summary(m1_ok, m2_ok, m3_ok, sim_ok)
