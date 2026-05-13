"""
List all Graph Engine files and validate completeness
"""

import os
from pathlib import Path


def show_graph_engine_structure():
    """Display complete Graph_engine directory structure with file sizes"""
    
    print("\n" + "█" * 70)
    print("GRAPH ENGINE FILE STRUCTURE & VALIDATION")
    print("█" * 70)
    
    base_path = Path("Graph_engine")
    
    print(f"\nLocation: {base_path.resolve()}")
    print(f"Status: {'✓ EXISTS' if base_path.exists() else '✗ NOT FOUND'}")
    
    if not base_path.exists():
        print("ERROR: Graph_engine directory not found!")
        return
    
    # Core engine files
    print("\n" + "="*70)
    print("CORE ENGINE (6 files)")
    print("="*70)
    
    core_files = [
        ("db.py", "Neo4j connection layer"),
        ("models.py", "Entity normalization"),
        ("graph_builder.py", "Graph node/relationship creation"),
        ("alert_engine.py", "Alert trigger logic"),
        ("graph_service.py", "Pipeline executor"),
        ("main.py", "FastAPI web server"),
    ]
    
    total_core_bytes = 0
    for filename, description in core_files:
        filepath = base_path / filename
        if filepath.exists():
            size = filepath.stat().st_size
            lines = len(filepath.read_text().split('\n'))
            total_core_bytes += size
            print(f"✓ {filename:<25} {size:>7,} bytes  {lines:>4} lines  - {description}")
        else:
            print(f"✗ {filename:<25} MISSING")
    
    # Testing files
    print("\n" + "="*70)
    print("TESTING (1 file)")
    print("="*70)
    
    test_files = [
        ("test_graph_engine.py", "Comprehensive test suite (6 tests)"),
    ]
    
    total_test_bytes = 0
    for filename, description in test_files:
        filepath = base_path / filename
        if filepath.exists():
            size = filepath.stat().st_size
            lines = len(filepath.read_text().split('\n'))
            total_test_bytes += size
            print(f"✓ {filename:<25} {size:>7,} bytes  {lines:>4} lines  - {description}")
        else:
            print(f"✗ {filename:<25} MISSING")
    
    # Integration files
    print("\n" + "="*70)
    print("INTEGRATION (1 file)")
    print("="*70)
    
    integration_files = [
        ("integration_example.py", "Module 1 → Module 2 → Graph_engine pipeline"),
    ]
    
    total_integration_bytes = 0
    for filename, description in integration_files:
        filepath = base_path / filename
        if filepath.exists():
            size = filepath.stat().st_size
            lines = len(filepath.read_text().split('\n'))
            total_integration_bytes += size
            print(f"✓ {filename:<25} {size:>7,} bytes  {lines:>4} lines  - {description}")
        else:
            print(f"✗ {filename:<25} MISSING")
    
    # Documentation files
    print("\n" + "="*70)
    print("DOCUMENTATION (4 files)")
    print("="*70)
    
    doc_files = [
        ("README.md", "Complete documentation"),
        ("QUICKSTART.md", "5-minute quick start guide"),
        ("requirements.txt", "Python dependencies"),
        ("verify_setup.py", "Setup verification script"),
    ]
    
    total_doc_bytes = 0
    for filename, description in doc_files:
        filepath = base_path / filename
        if filepath.exists():
            size = filepath.stat().st_size
            lines = len(filepath.read_text().split('\n'))
            total_doc_bytes += size
            print(f"✓ {filename:<25} {size:>7,} bytes  {lines:>4} lines  - {description}")
        else:
            print(f"✗ {filename:<25} MISSING")
    
    # Module marker
    print("\n" + "="*70)
    print("MODULE MARKER (1 file)")
    print("="*70)
    
    init_file = base_path / "__init__.py"
    if init_file.exists():
        size = init_file.stat().st_size
        lines = len(init_file.read_text().split('\n'))
        print(f"✓ {'__init__.py':<25} {size:>7,} bytes  {lines:>4} lines  - Module marker")
    else:
        print(f"✗ {'__init__.py':<25} MISSING")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    all_files = core_files + test_files + integration_files + doc_files + [("__init__.py", "Module marker")]
    total_files = len(all_files)
    existing_files = sum(1 for f, _ in all_files if (base_path / f).exists())
    
    total_bytes = total_core_bytes + total_test_bytes + total_integration_bytes + total_doc_bytes
    
    print(f"\nFiles Created: {existing_files}/{total_files}")
    print(f"Total Size: {total_bytes:,} bytes ({total_bytes/1024:.1f} KB)")
    
    print(f"\nBreakdown:")
    print(f"  Core Engine:    {total_core_bytes:>8,} bytes")
    print(f"  Testing:        {total_test_bytes:>8,} bytes")
    print(f"  Integration:    {total_integration_bytes:>8,} bytes")
    print(f"  Documentation:  {total_doc_bytes:>8,} bytes")
    
    if existing_files == total_files:
        print(f"\n✓ ✓ ✓ ALL FILES CREATED SUCCESSFULLY ✓ ✓ ✓")
    else:
        print(f"\n⚠ {total_files - existing_files} file(s) missing")
    
    # File listing for reference
    print("\n" + "="*70)
    print("COMPLETE FILE LISTING")
    print("="*70)
    
    for filepath in sorted(base_path.glob("*")):
        if filepath.is_file():
            name = filepath.name
            size = filepath.stat().st_size
            print(f"  {name:<30} {size:>8,} bytes")
    
    print("\n" + "="*70 + "\n")


def validate_content():
    """Validate critical content in key files"""
    
    print("VALIDATING FILE CONTENT")
    print("="*70)
    
    base_path = Path("Graph_engine")
    validations = []
    
    # Check db.py has credentials
    db_file = base_path / "db.py"
    if db_file.exists():
        content = db_file.read_text()
        has_uri = "URI" in content
        has_user = "USER" in content
        has_password = "PASSWORD" in content
        print(f"✓ db.py: Neo4j credentials {'✓ configured' if all([has_uri, has_user, has_password]) else '✗ INCOMPLETE'}")
        validations.append(all([has_uri, has_user, has_password]))
    
    # Check graph_builder has required functions
    builder_file = base_path / "graph_builder.py"
    if builder_file.exists():
        content = builder_file.read_text()
        functions = [
            "create_case",
            "create_entity",
            "link_entity_to_case",
            "link_entities",
            "check_entity_cases"
        ]
        all_present = all(f in content for f in functions)
        print(f"✓ graph_builder.py: Core functions {'✓ all present' if all_present else '✗ MISSING'} ({len(functions)} required)")
        validations.append(all_present)
    
    # Check alert_engine has alert rules
    alert_file = base_path / "alert_engine.py"
    if alert_file.exists():
        content = alert_file.read_text()
        has_high_risk = "HIGH_RISK_CASE" in content
        has_reappearance = "REAPPEARANCE" in content
        print(f"✓ alert_engine.py: Alert rules {'✓ both present' if all([has_high_risk, has_reappearance]) else '✗ MISSING'}")
        validations.append(all([has_high_risk, has_reappearance]))
    
    # Check main.py has endpoints
    main_file = base_path / "main.py"
    if main_file.exists():
        content = main_file.read_text()
        endpoints = [
            "/graph/process",
            "/graph/batch-process",
            "/graph/health"
        ]
        all_present = all(ep in content for ep in endpoints)
        print(f"✓ main.py: API endpoints {'✓ all present' if all_present else '✗ MISSING'} ({len(endpoints)} required)")
        validations.append(all_present)
    
    # Check test_graph_engine has tests
    test_file = base_path / "test_graph_engine.py"
    if test_file.exists():
        content = test_file.read_text()
        tests = [
            "test_single_case",
            "test_high_risk_alert",
            "test_medium_risk_no_alert",
            "test_batch_processing",
            "test_entity_normalization",
            "test_empty_entities"
        ]
        all_present = all(t in content for t in tests)
        print(f"✓ test_graph_engine.py: Test cases {'✓ all present' if all_present else '✗ MISSING'} ({len(tests)} required)")
        validations.append(all_present)
    
    # Check requirements.txt has dependencies
    req_file = base_path / "requirements.txt"
    if req_file.exists():
        content = req_file.read_text()
        deps = ["neo4j", "fastapi", "uvicorn", "pydantic", "requests"]
        all_present = all(d in content for d in deps)
        print(f"✓ requirements.txt: Dependencies {'✓ all present' if all_present else '✗ MISSING'} ({len(deps)} required)")
        validations.append(all_present)
    
    print("\n" + "="*70)
    if all(validations):
        print("✓ ✓ ✓ ALL CONTENT VALIDATIONS PASSED ✓ ✓ ✓")
    else:
        print("⚠ Some content validations failed")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    show_graph_engine_structure()
    validate_content()
    
    print("\n📌 NEXT STEPS:")
    print("-" * 70)
    print("1. Install dependencies:")
    print("   pip install -r Graph_engine/requirements.txt")
    print("\n2. Verify setup:")
    print("   python Graph_engine/verify_setup.py")
    print("\n3. Start server:")
    print("   uvicorn Graph_engine.main:app --reload --port 8001")
    print("\n4. Run tests:")
    print("   python Graph_engine/test_graph_engine.py")
    print("\n5. See documentation:")
    print("   - Quick Start: Graph_engine/QUICKSTART.md")
    print("   - Full Docs: Graph_engine/README.md")
    print("\n" + "="*70 + "\n")
