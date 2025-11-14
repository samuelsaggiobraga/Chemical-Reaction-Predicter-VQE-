# Quantum Chemistry Reaction Predictor

An interactive system for predicting chemical reactions using quantum computing algorithms (VQE) and AI-assisted prediction.

## Architecture

```
├── frontend/              # Interactive periodic table UI
├── backend/
│   ├── api/              # REST API for reaction prediction
│   └── quantum_chemistry/ # VQE, Hartree-Fock implementations
├── matlab_integration/    # MATLAB quantum computing bridge
└── config/               # API keys and configuration
```

## Technology Stack

- **Frontend**: Interactive periodic table for element selection
- **Backend**: Python (Flask/FastAPI) with PySCF/Psi4 for quantum chemistry
- **Quantum Computing**: MATLAB Quantum Computing Support Package
- **AI**: Google Gemini API for generative reaction prediction
- **Algorithms**:
  - Variational Quantum Eigensolver (VQE)
  - Hartree-Fock method
  - Future: Symmetric group theory for resonance structures

## Roadmap

### Phase 1 (Current)
- [ ] Basic periodic table UI
- [ ] Element combination interface
- [ ] VQE implementation with MATLAB backend
- [ ] Hartree-Fock initial guess
- [ ] Gemini API integration

### Phase 2 (Future)
- [ ] Ring structure functionality
- [ ] Symmetric group theory for resonance structures
- [ ] Advanced molecular visualization

## Setup

### Prerequisites
- MATLAB with Quantum Computing Support Package (R2025b)
- Python 3.8+
- Node.js (for frontend)
- Google Gemini API key

### MATLAB Path Configuration
MATLAB installation location: `/Applications/MATLAB_R2025b.app/bin/matlab`

To add MATLAB to your PATH, add this to `~/.zshrc`:
```bash
export PATH="/Applications/MATLAB_R2025b.app/bin:$PATH"
```

Then reload: `source ~/.zshrc`

### Installation
```bash
# Backend dependencies
pip install -r backend/requirements.txt

# Frontend dependencies
cd frontend && npm install
```

### Configuration
Create `config/.env`:
```
GEMINI_API_KEY="your_api_key"
MATLAB_PATH=/Applications/MATLAB_R2025b.app/bin/matlab
```

## Usage

1. Start backend server
2. Launch frontend
3. Select elements from periodic table
4. System predicts reaction outcomes using quantum algorithms + AI
