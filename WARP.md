# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a quantum chemistry reaction predictor that combines quantum computing (VQE), computational chemistry (PySCF), and AI (Google Gemini) to predict chemical reactions. The system builds molecular Hamiltonians in Python, runs VQE optimization in MATLAB, and uses Gemini to predict reaction outcomes from the quantum data.

## Key Commands

### Development Setup
```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Verify MATLAB path (should be in config/.env)
echo $MATLAB_PATH  # Should be /Applications/MATLAB_R2025b.app/bin/matlab
```

### Running the Application
```bash
# Start the Flask API server (runs on port 5001)
python backend/api/server.py

# Open frontend in browser
open frontend/index.html
```

### Testing
```bash
# Test H₂ molecule end-to-end (Python → MATLAB → Python)
python matlab_integration/matlab_bridge.py

# Test API endpoint with curl
curl -X POST http://localhost:5001/api/predict-reaction \
  -H "Content-Type: application/json" \
  -d '{"elements": ["H", "H"]}'

# Test Gemini integration only
python test_gemini.py

# Test backend components
python test_backend.py
```

## Architecture

### Data Flow Pipeline
The system follows a 5-stage pipeline:

1. **Frontend** (`frontend/index.html`) → User selects elements from periodic table
2. **Python/PySCF** (`backend/quantum_chemistry/hamiltonian_builder.py`) → Builds molecular Hamiltonian using Hartree-Fock, outputs JSON with Pauli strings and coefficients
3. **MATLAB** (`matlab_integration/run_vqe.m`) → Reads JSON, runs VQE optimization using `observable.m` and `estimate.m`, saves results to JSON
4. **Python** (`matlab_integration/matlab_bridge.py`) → Collects MATLAB results and packages quantum data
5. **Gemini AI** (`backend/quantum_chemistry/gemini_integration.py`) → Receives quantum data, predicts reaction products and mechanisms
6. **Frontend** → Displays results to user

### Key Components

**Backend (`backend/`)**
- `api/server.py`: Flask REST API with endpoints `/api/predict-reaction`, `/api/health`, `/api/explain-quantum-data`
- `quantum_chemistry/hamiltonian_builder.py`: Converts elements to molecular Hamiltonians using PySCF, performs Hartree-Fock calculations, handles both RHF (closed-shell) and UHF (open-shell) systems
- `quantum_chemistry/gemini_integration.py`: Interfaces with Google Gemini API, constructs detailed prompts with quantum data
- `quantum_chemistry/molecular_geometries.py`: Database of optimized molecular structures (H2O, CH4, NH3, etc.)

**MATLAB Integration (`matlab_integration/`)**
- `matlab_bridge.py`: Python-MATLAB bridge using subprocess to execute MATLAB in batch mode
- `run_vqe.m`: Main VQE algorithm with qubit truncation (max 12 qubits for memory constraints), uses `fminunc` for optimization

**MATLAB Quantum Classes (root directory)**
- `observable.m`: MATLAB class representing quantum observables as Pauli strings (from MATLAB Quantum Computing Support Package)
- `estimate.m`: Calculates expectation values of observables on quantum states

**Frontend (`frontend/`)**
- `index.html`: Interactive periodic table UI
- `periodic_table.js`: Element selection logic
- `styles.css`: UI styling

### Configuration
- `config/.env`: Contains `GEMINI_API_KEY` and `MATLAB_PATH`
- MATLAB path must be `/Applications/MATLAB_R2025b.app/bin/matlab`

## Important Technical Details

### Qubit Limitations
- VQE is limited to **12 qubits maximum** to prevent memory overflow (see `run_vqe.m` line 35)
- Larger molecules will be truncated with a warning
- This affects accuracy for complex systems but is necessary for computational feasibility

### Basis Sets and Heavy Elements
- Uses `sto-3g` basis by default for light elements (Z ≤ 36)
- Automatically switches to mixed basis (`lanl2dz` with ECPs) for heavy elements (Z > 36)
- See `hamiltonian_builder.py` lines 42-62

### Spin Handling
- Odd-electron systems use UHF (Unrestricted Hartree-Fock)
- Even-electron systems use RHF (Restricted Hartree-Fock)
- Spin is set automatically based on total electron count

### MATLAB Execution
- MATLAB runs in batch mode via subprocess (non-interactive)
- Scripts must use absolute paths for file I/O
- Communication via JSON files: `hamiltonian_data.json` (input) and `vqe_results.json` (output)
- Both files are created in the repository root directory

### Gemini Prompt Structure
The Gemini prompt (`gemini_integration.py` lines 46-111) is carefully structured to:
- Provide complete quantum data (VQE energy, HF energy, orbital data, bond lengths)
- Request specific JSON format with products (formula, name, probability), mechanism, thermodynamics, confidence, and reasoning
- Products must be listed separately with probabilities summing to 1.0
- Chemical equations should be balanced but don't require 1:1 stoichiometry

## File Locations and Temporary Files

### Working Directory
All commands should be run from repository root: `/Users/samuelbraga/Reaction Predicter`

### Generated Files
- `hamiltonian_data.json`: Created by PySCF, consumed by MATLAB (temporary)
- `vqe_results.json`: Created by MATLAB, consumed by Python (temporary)
- Both files are cleaned up after successful pipeline execution
- If debugging, these files persist on error

## Common Development Patterns

### Adding New Molecules
1. Add optimized geometry to `MOLECULAR_GEOMETRIES` dict in `molecular_geometries.py`
2. Geometry format: list of tuples `(element_symbol, (x, y, z))` in Angstroms
3. Test with API: `{"molecules": [{"formula": "NEW_MOLECULE"}]}`

### Modifying VQE Parameters
Edit `run_vqe.m` lines 62-73:
- `max_iterations`: Number of optimization steps
- `num_params`: Circuit parameters (affects ansatz complexity)
- `OptimalityTolerance`: Convergence threshold
- Trade-off between accuracy and speed

### Testing Single Components
- Test Hamiltonian builder: `python -c "from backend.quantum_chemistry.hamiltonian_builder import HamiltonianBuilder; hb = HamiltonianBuilder(); print(hb.build_molecule(['H', 'H']))"`
- Test MATLAB VQE: Create `hamiltonian_data.json` manually, then run `matlab -batch "addpath(pwd); run_vqe('hamiltonian_data.json')"`
- Test Gemini: Use `test_gemini.py` with mock quantum data

## Dependencies

### Python
- Flask/Flask-CORS: REST API
- PySCF ≥2.3.0: Quantum chemistry calculations
- NumPy/SciPy: Numerical operations
- google-generativeai: Gemini API
- python-dotenv: Environment variable management

### MATLAB
- MATLAB R2025b required
- Quantum Computing Support Package required for `quantumCircuit`, `observable`, `estimate` functions
- Optimization Toolbox required for `fminunc`

### Frontend
- Pure HTML/CSS/JavaScript (no build step)
- No npm dependencies currently

## Troubleshooting

### MATLAB Not Found
- Verify `MATLAB_PATH` in `config/.env`
- Check PATH: `echo $PATH | grep MATLAB`
- Test MATLAB: `matlab -batch "disp('Hello')"`

### PySCF Convergence Issues
- Try simpler molecules first (H₂, OH)
- Check geometry with `molecular_geometries.py`
- Use UHF for radicals (automatic)

### Memory Errors in VQE
- System requires too many qubits (>12)
- MATLAB will truncate automatically with warning
- Consider using smaller molecules or adjusting `MAX_QUBITS` in `run_vqe.m`

### Gemini API Errors
- Verify `GEMINI_API_KEY` in `config/.env`
- Check API quota/limits
- Model version: `gemini-2.5-flash` (hardcoded in `gemini_integration.py` line 15)

### JSON Parsing Errors
- Gemini sometimes returns malformed JSON
- Parser strips markdown code blocks automatically
- Falls back to raw text if JSON extraction fails
- Check `gemini_integration.py` lines 115-168

## Model Versions
- Gemini model: `gemini-2.5-flash` (latest stable as of implementation)
- PySCF version: ≥2.3.0
- MATLAB: R2025b with Quantum Computing Support Package
