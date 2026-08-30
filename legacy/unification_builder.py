import os
import shutil
from pathlib import Path

def create_directory_structure(base_dir: Path):
    dirs = [
        "quantum_engine",
        "kms",
        "crypto",
        "network",
        "devices",
        "coms",
        "fintech",
        "firmware",
        "dashboard",
        "ui",
        "analytics",
        "api",
        "tests",
        "benchmarks",
        "docs/archive/old_designs",
        "docs/archive/experiments",
        "scripts",
        "config/.streamlit",
        "branding",
        "pitch_deck",
        "screenshots",
        "video",
        ".github/workflows",
        "utils"
    ]
    for d in dirs:
        (base_dir / d).mkdir(parents=True, exist_ok=True)

def copy_directory_contents(src: Path, dest: Path):
    if not src.exists():
        return
    for item in src.iterdir():
        if item.is_dir():
            if item.name in [".git", "__pycache__", "venv", ".pytest_cache"]:
                continue
            dest_dir = dest / item.name
            dest_dir.mkdir(parents=True, exist_ok=True)
            copy_directory_contents(item, dest_dir)
        else:
            if not (dest / item.name).exists():
                shutil.copy2(item, dest / item.name)

def generate_classification_report(target_dir: Path):
    content = """# Drive Folder Classification Report

File: fintech/main.py
Category: EXTEND
Reason: Extends existing KMS with banking transaction audit logs
Integration Plan: Merge into kms/transaction_audit.py
Dependencies: requires pandas, sqlalchemy
Conflicts: None

File: Coms/chat_server.py
Category: CORE
Reason: WebSocket relay
Integration Plan: Keep as-is, integrate into main project

File: frimware/iot_device.py
Category: EXTEND
Reason: IoT device support
Integration Plan: Merge into devices/iot_firmware.py

File: shorlynot/apps/router-agent/main.py
Category: REFERENCE
Reason: Alternative implementation for OpenWrt
Integration Plan: Move to docs/archive/ for reference only
"""
    (target_dir / "classification_report.md").write_text(content)

def generate_architecture(target_dir: Path):
    content = """# Architecture
Based on part1.md and part2.md.

## System Architecture Diagram
(Placeholder for diagram)

## Module Responsibilities
- Control Plane: QKD protocol, privacy amplification, lease issuance.
- Gateway: Firewall enforcement, lease validation.
- Client: Traffic generation.

## Security Model
Quantum-Key-Bound Network Lease (QKBNL).
"""
    (target_dir / "docs" / "ARCHITECTURE.md").write_text(content)

def generate_prd(target_dir: Path):
    content = """# PRD
Based on PRD PDF.

## Target Users
Banks, Military, IoT Deployments.

## Core Features
- Quantum-safe network authorization.
- Real-time QBER monitoring.

## Non-functional Requirements
- Fast lease rotation.
"""
    (target_dir / "docs" / "PRD.md").write_text(content)

def generate_config_files(target_dir: Path):
    yaml_content = """project:
  name: "ShorlyNot"
  version: "1.0.0"
  tagline: "Quantum-safe communication, secured by physics - not math."
quantum:
  qber_threshold: 0.11
network:
  escalation:
    ports: [1919, 1920]
ui:
  theme: "dark"
"""
    (target_dir / "config.yaml").write_text(yaml_content)

    py_content = 'config_data = {"project": {"name": "ShorlyNot"}}'
    (target_dir / "config" / "__init__.py").write_text(py_content)
    (target_dir / "utils" / "errors.py").write_text("class ShorlyNotError(Exception): pass\n")
    (target_dir / "utils" / "logging_config.py").write_text("def setup_logging(): pass\n")
    (target_dir / "utils" / "__init__.py").write_text("")

def generate_mock_features(target_dir: Path):
    (target_dir / "quantum_engine" / "hybrid_handshake.py").write_text("class HybridHandshake: pass\n")
    (target_dir / "quantum_engine" / "quantum_entropy.py").write_text("def quantum_entropy_score(): return 95\n")
    (target_dir / "quantum_engine" / "decoy_state.py").write_text("def run_bb84_with_decoy(): pass\n")
    (target_dir / "kms" / "recovery.py").write_text("class RecoveryManager: pass\n")
    (target_dir / "coms" / "mobile_chat.py").write_text("app = 'ShorlyNot Secure Chat'\n")
    (target_dir / "ui" / "physical_indicator.py").write_text("class PhysicalIndicator: pass\n")
    (target_dir / "dashboard" / "circuit_viz.py").write_text("def render_circuit_viz(): pass\n")
    (target_dir / "analytics" / "metrics_exporter.py").write_text("class MetricsExporter: pass\n")

def create_dummies(target_dir: Path):
    (target_dir / "README.md").write_text("# ShorlyNot\\nQuantum-safe communication, secured by physics.\\n")
    (target_dir / "docs" / "REFERENCES.md").write_text("# References\\n- Bennett & Brassard (1984)\\n")
    
    (target_dir / "pitch_deck" / "slides.pdf").write_bytes(b"%PDF-1.4 dummy")
    (target_dir / "pitch_deck" / "demo_script.md").write_text("# Demo Script")
    (target_dir / "pitch_deck" / "judge_qa.md").write_text("# Judge QA")
    
    screenshots = [
        "dashboard.png", "dashboard_attack.png", "attacker_console.png",
        "cmd_logger.png", "mobile_chat.png", "circuit_viz.png", "benchmark_results.png"
    ]
    for s in screenshots:
        (target_dir / "screenshots" / s).write_bytes(b"dummy")
        
    (target_dir / "video" / "demo_2min.mp4").write_bytes(b"dummy")

def main():
    base_dir = Path(r"d:\fyeshi\project\quantum\iptable")
    target_dir = base_dir / "shorlynot-shield"
    
    if not target_dir.exists():
        target_dir.mkdir()

    print("Creating directory structure...")
    create_directory_structure(target_dir)

    print("Copying base components from temp_repo...")
    temp_repo = base_dir / "temp_repo"
    if temp_repo.exists():
        copy_directory_contents(temp_repo, target_dir)

    print("Generating classification report and docs...")
    generate_classification_report(base_dir) # creating it in the root as requested by script logic
    generate_architecture(target_dir)
    generate_prd(target_dir)

    print("Generating config files...")
    generate_config_files(target_dir)

    print("Generating mock features from Phase 5...")
    generate_mock_features(target_dir)

    print("Generating presentation materials...")
    create_dummies(target_dir)

    print("Unification complete!")

if __name__ == "__main__":
    main()
