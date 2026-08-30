# ShorlyNot: Quantum-Key-Bound Network Lease Enforcement Platform

SHORLYNOT is a quantum-aware network authorization and enforcement platform.
The core security primitive is the Quantum-Key-Bound Network Lease (QKBNL), which binds physical quantum key distribution security guarantees to localized router-level firewall enforcement.

## Features
- **Quantum Backends**: Supports Qiskit simulation (Aer) and real IBM Quantum Hardware execution.
- **Protocols**: BB84, B92, E91, Decoy-State BB84.
- **Physical Enforcement**: Dynamic iptables/OpenWRT firewall enforcement.
- **Security Event Monitoring**: Real-time detection of QBER threshold violations.
- **PQC Recovery**: Automated Post-Quantum Cryptography (ML-KEM-768) handshake for lease restoration during channel compromise.

## Execution Modes

SHORLYNOT supports three core execution modes. Set `SHORLYNOT_EXECUTION_MODE` in your `.env`.

### 1. SIMULATION
* `SHORLYNOT_EXECUTION_MODE=simulation`
* Uses local Qiskit Aer for quantum circuit execution.
* Uses mock/simulated interfaces for Arduino serial telemetry and Router enforcement.
* This is the default mode for development and local UI testing.

### 2. REAL
* `SHORLYNOT_EXECUTION_MODE=real`
* **Requires**: `IBM_QUANTUM_TOKEN` for real quantum execution.
* **Requires**: Real OpenWRT/Linux router API connection.
* **Requires**: Real Arduino serial connection for optical telemetry.
* Executes actual circuits on IBM hardware and manipulates live firewall rules.

### 3. REPLAY
* `SHORLYNOT_EXECUTION_MODE=replay`
* Uses previously stored immutable evidence records to replay a past execution sequence.

## Setup Instructions

### Native Windows Setup

1. **Install Python and Node.js**: Ensure Python 3.12+ and Node.js 20+ are installed.
2. **Install Python Dependencies**:
   ```powershell
   cd shorlynot
   python -m venv venv
   .\venv\Scripts\activate
   pip install -e .
   pip install fastapi uvicorn sqlalchemy alembic aiosqlite pydantic-settings httpx websockets cryptography qiskit qiskit-aer
   ```
3. **Configure Environment**:
   ```powershell
   Copy-Item .env.example .env
   # Edit .env with your settings
   ```
4. **Start the Dashboard**:
   ```powershell
   cd apps/dashboard
   npm install
   npm run build
   npm run dev
   ```

### Native Linux Setup

1. **Install Python and Node.js**:
   ```bash
   sudo apt update
   sudo apt install python3.12 python3.12-venv nodejs npm
   ```
2. **Install Python Dependencies**:
   ```bash
   cd shorlynot
   python3 -m venv venv
   source venv/bin/activate
   pip install -e .
   pip install fastapi uvicorn sqlalchemy alembic aiosqlite pydantic-settings httpx websockets cryptography qiskit qiskit-aer
   ```
3. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```
4. **Start the Dashboard**:
   ```bash
   cd apps/dashboard
   npm install
   npm run build
   npm run dev
   ```

## Development and Testing
- **Run Unit Tests**: `python -m pytest tests/unit -v`
- **Run Integration Tests**: `python -m pytest tests/integration -v`
- **Run System Tests**: `python -m pytest tests/system -v`
