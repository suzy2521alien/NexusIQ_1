"""
Verification script - Check Graph Engine setup and dependencies
Run this to verify the complete installation
"""

import os
import sys
from pathlib import Path


def check_file(filepath, name):
    """Check if a file exists"""
    if Path(filepath).exists():
        size = Path(filepath).stat().st_size
        print(f"✓ {name:<40} {size:>8,} bytes")
        return True
    else:
        print(f"✗ {name:<40} MISSING")
        return False


def check_module_imports():
    """Check if required modules can be imported"""
    print("\n" + "="*60)
    print("CHECKING MODULE IMPORTS")
    print("="*60)
    
    modules = [
        ("neo4j", "Neo4j Driver"),
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pydantic", "Pydantic"),
        ("requests", "Requests"),
    ]
    
    all_ok = True
    for module_name, display_name in modules:
        try:
            __import__(module_name)
            print(f"✓ {display_name:<40} installed")
        except ImportError:
            print(f"✗ {display_name:<40} NOT INSTALLED")
            all_ok = False
    
    return all_ok


def check_graph_engine_files():
    """Check if all Graph_engine files are present"""
    print("\n" + "="*60)
    print("CHECKING GRAPH ENGINE FILES")
    print("="*60)
    
    base_path = Path("Graph_engine")
    
    required_files = [
        ("__init__.py", "Module init"),
        ("db.py", "Neo4j connection"),
        ("models.py", "Entity normalization"),
        ("graph_builder.py", "Graph logic"),
        ("alert_engine.py", "Alert rules"),
        ("graph_service.py", "Pipeline executor"),
        ("main.py", "FastAPI server"),
        ("test_graph_engine.py", "Test suite"),
        ("integration_example.py", "Integration demo"),
        ("README.md", "Documentation"),
        ("QUICKSTART.md", "Quick start guide"),
        ("requirements.txt", "Dependencies"),
    ]
    
    all_ok = True
    for filename, name in required_files:
        filepath = base_path / filename
        if not check_file(filepath, name):
            all_ok = False
    
    return all_ok


def check_directory_structure():
    """Check if directory structure exists"""
    print("\n" + "="*60)
    print("CHECKING DIRECTORY STRUCTURE")
    print("="*60)
    
    dirs = [
        ("Graph_engine", "Graph Engine root"),
        ("Graph_engine", "Graph Engine module"),
        ("app", "Module 1: Forensics"),
        ("person2_ai_engine", "Module 2: AI Engine"),
        ("output", "Output directory"),
    ]
    
    all_ok = True
    for dirname, name in dirs:
        if Path(dirname).exists():
            print(f"✓ {name:<40} exists")
        else:
            print(f"✗ {name:<40} MISSING")
            all_ok = False
    
    return all_ok


def check_neo4j_config():
    """Check Neo4j configuration in db.py"""
    print("\n" + "="*60)
    print("CHECKING NEO4J CONFIGURATION")
    print("="*60)
    
    try:
        db_file = Path("Graph_engine/db.py")
        if not db_file.exists():
            print("✗ db.py not found")
            return False
        
        content = db_file.read_text()
        
        checks = [
            ("URI = ", "URI configured"),
            ("USER = ", "Username configured"),
            ("PASSWORD = ", "Password configured"),
            ("DATABASE = ", "Database configured"),
            ("driver = GraphDatabase.driver", "Driver initialization"),
        ]
        
        all_ok = True
        for check_str, name in checks:
            if check_str in content:
                print(f"✓ {name:<40}")
            else:
                print(f"✗ {name:<40} MISSING")
                all_ok = False
        
        return all_ok
    except Exception as e:
        print(f"✗ Error checking config: {e}")
        return False


def check_endpoints():
    """Check if FastAPI endpoints are defined"""
    print("\n" + "="*60)
    print("CHECKING API ENDPOINTS")
    print("="*60)
    
    try:
        main_file = Path("Graph_engine/main.py")
        if not main_file.exists():
            print("✗ main.py not found")
            return False
        
        content = main_file.read_text()
        
        endpoints = [
            ('@app.post("/graph/process")', "/graph/process"),
            ('@app.post("/graph/batch-process")', "/graph/batch-process"),
            ('@app.get("/graph/health")', "/graph/health"),
            ('@app.get("/")', "Root endpoint"),
        ]
        
        all_ok = True
        for endpoint_str, name in endpoints:
            if endpoint_str in content:
                print(f"✓ {name:<40} defined")
            else:
                print(f"✗ {name:<40} NOT FOUND")
                all_ok = False
        
        return all_ok
    except Exception as e:
        print(f"✗ Error checking endpoints: {e}")
        return False


def print_summary(results):
    """Print summary and recommendations"""
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    checks_passed = sum(results.values())
    total_checks = len(results)
    
    print(f"\nChecks Passed: {checks_passed}/{total_checks}")
    
    if all(results.values()):
        print("\n✓ ✓ ✓ ALL CHECKS PASSED ✓ ✓ ✓")
        print("\n📌 Next Steps:")
        print("  1. pip install -r Graph_engine/requirements.txt")
        print("  2. uvicorn Graph_engine.main:app --reload --port 8001")
        print("  3. python Graph_engine/test_graph_engine.py")
        print("  4. python Graph_engine/integration_example.py")
        print("  5. Check http://localhost:8001/docs")
    else:
        print("\n⚠ Some checks failed. See details above.")
        print("\n📌 To fix:")
        if not results.get("Modules", True):
            print("  - pip install -r Graph_engine/requirements.txt")
        if not results.get("Files", True):
            print("  - Verify all files in Graph_engine/")
        if not results.get("Directory", True):
            print("  - Check directory structure")
    
    print("\n" + "="*60 + "\n")


def main():
    """Run all verification checks"""
    print("\n")
    print("█" * 60)
    print("GRAPH ENGINE VERIFICATION")
    print("█" * 60)
    
    results = {
        "Directory": check_directory_structure(),
        "Files": check_graph_engine_files(),
        "Neo4j Config": check_neo4j_config(),
        "Endpoints": check_endpoints(),
        "Modules": check_module_imports(),
    }
    
    print_summary(results)


if __name__ == "__main__":
    main()
