# Quick Start Guide

## Installation

### 1. Install Python Dependencies
```bash
pip install -r backend/requirements.txt
```

### 2. Verify MATLAB Path
Your MATLAB is already configured in `config/.env`:
```
MATLAB_PATH=/Applications/MATLAB_R2025b.app/bin/matlab
GEMINI_API_KEY="your_api_key"
```

## Running the Application

### Start the Backend Server
```bash
cd /Users/samuelbraga/Downloads/upload
python backend/api/server.py
```

The server will start on `http://localhost:5000`

### Open the Frontend
Open `frontend/index.html` in your browser:
```bash
open frontend/index.html
```

## How It Works

### Complete Pipeline:

1. **Frontend** → User selects elements (e.g., H + H for H₂)

2. **Python (PySCF)** → Builds molecular Hamiltonian
   - Runs Hartree-Fock calculation
   - Generates Pauli strings and coefficients
   - Saves to JSON

3. **MATLAB** → Runs VQE algorithm
   - Reads Hamiltonian from JSON
   - Creates `observable` object
   - Optimizes quantum circuit parameters
   - Calculates ground state energy using `estimate.m`
   - Saves results to JSON

4. **Python** → Collects MATLAB results
   - Parses VQE output
   - Packages all quantum data

5. **Gemini AI** → Predicts reaction
   - Receives quantum data in prompt
   - Analyzes electronic structure
   - Predicts products and mechanism

6. **Frontend** → Displays results

## Testing

### Test H₂ Molecule
```bash
python matlab_integration/matlab_bridge.py
```

This will:
- Build H₂ Hamiltonian
- Run MATLAB VQE
- Display results

### Test API Endpoint
```bash
curl -X POST http://localhost:5000/api/predict-reaction \
  -H "Content-Type: application/json" \
  -d '{"elements": ["H", "H"]}'
```

## Project Structure

```
├── backend/
│   ├── api/
│   │   └── server.py              # Flask API
│   ├── quantum_chemistry/
│   │   ├── hamiltonian_builder.py # PySCF Hamiltonian generation
│   │   └── gemini_integration.py  # AI prediction
│   └── requirements.txt
├── matlab_integration/
│   ├── matlab_bridge.py           # Python-MATLAB interface
│   └── run_vqe.m                  # VQE algorithm
├── frontend/
│   └── index.html                 # Interactive UI
├── config/
│   └── .env                       # API keys
├── observable.m                   # Your existing MATLAB code
└── estimate.m                     # Your existing MATLAB code
```

## Troubleshooting

### MATLAB Not Found
Make sure MATLAB is in your PATH:
```bash
export PATH="/Applications/MATLAB_R2025b.app/bin:$PATH"
```

### PySCF Installation Issues
```bash
pip install --upgrade pip
pip install pyscf==2.5.0
```

### API Connection Issues
Check that the Flask server is running on port 5000:
```bash
lsof -i :5000
```

## Next Steps

1. Test with H₂ molecule first
2. Try other simple molecules (OH, H₂O)
3. Later: Add ring structures and resonance
