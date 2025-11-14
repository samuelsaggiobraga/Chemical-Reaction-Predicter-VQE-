"""
Flask API server for quantum chemistry reaction prediction
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
from dotenv import load_dotenv

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from matlab_integration.matlab_bridge import MatlabQuantumBridge
from backend.quantum_chemistry.gemini_integration import GeminiReactionPredictor
from backend.quantum_chemistry.molecular_geometries import get_molecule_geometry, parse_molecular_formula
from backend.quantum_chemistry.organic_chemistry import (
    SMILESParser, FunctionalGroupDetector, OrganicMoleculeBuilder, OrganicReactionClassifier
)
# Import hierarchical predictor
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ml_training'))
from hierarchical_predictor import HierarchicalReactionPredictor

# Load environment variables from project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(project_root, 'config', '.env'))

app = Flask(__name__)
CORS(app)

# Initialize services
matlab_bridge = MatlabQuantumBridge(
    matlab_path=os.getenv('MATLAB_PATH', '/Applications/MATLAB_R2025b.app/bin/matlab')
)

# Load hierarchical predictor (4-level ensemble)
try:
    os.chdir(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ml_training'))
    hierarchical_predictor = HierarchicalReactionPredictor(use_quantum=False)  # Enable quantum if needed
    os.chdir(os.path.dirname(os.path.abspath(__file__)))  # Return to API dir
    print("✅ Hierarchical predictor loaded successfully")
except Exception as e:
    print(f"⚠️  Hierarchical predictor failed to load: {e}")
    hierarchical_predictor = None

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'quantum-chemistry-api',
        'matlab_configured': bool(os.getenv('MATLAB_PATH')),
        'gemini_configured': bool(os.getenv('GEMINI_API_KEY'))
    })

@app.route('/api/predict-reaction', methods=['POST'])
def predict_reaction():
    """
    Predict reaction outcome from input elements or molecules
    
    Request body:
    {
        "elements": ["H", "O"],  // For individual atoms
        "molecules": [{"formula": "H2O", "geometry": "optimized"}],  // For pre-formed molecules
        "geometry": null  // optional custom geometry
    }
    
    Response:
    {
        "input_elements": ["H", "O"],
        "quantum_data": { ... },
        "ai_prediction": { ... }
    }
    """
    try:
        data = request.json
        elements = data.get('elements', [])
        molecules = data.get('molecules', [])
        smiles = data.get('smiles', None)
        geometry = data.get('geometry', None)
        
        # Handle SMILES input for organic molecules
        if smiles:
            print(f"Parsing SMILES: {smiles}")
            geometry = OrganicMoleculeBuilder.smiles_to_geometry(smiles)
            parser = SMILESParser()
            parsed_smiles = parser.parse(smiles)
            elements = [atom['element'] for atom in parsed_smiles['atoms']]
            print(f"SMILES parsed: {parsed_smiles['molecular_formula']}")
        
        # Process molecules with proper geometries
        if molecules:
            for mol in molecules:
                formula = mol.get('formula', '')
                # Try to get optimized geometry
                mol_geom = get_molecule_geometry(formula)
                if mol_geom and not geometry:  # Use molecular geometry if available
                    print(f"Using optimized geometry for {formula}")
                    geometry = mol_geom
                    elements = [elem for elem, _ in mol_geom]
                else:
                    # Fall back to parsing formula
                    elements.extend(parse_molecular_formula(formula))
        
        if not elements or len(elements) < 1:
            return jsonify({'error': 'At least 1 element or molecule required'}), 400
        
        print(f"\n{'='*50}")
        print(f"Predicting reaction for: {elements}")
        print(f"{'='*50}")
        
        # Step 1: Run quantum calculations (Python → MATLAB → Python)
        print("\nStep 1: Running quantum calculations...")
        quantum_data = matlab_bridge.calculate_molecule_properties(elements, geometry)
        
        # Step 2: Use hierarchical predictor (4-level ensemble)
        print("\nStep 2: Using hierarchical predictor...")
        if hierarchical_predictor:
            # Hierarchical predictor handles routing automatically
            prediction_result = hierarchical_predictor.predict(elements, quantum_data)
            
            print(f"   ✅ Prediction via {prediction_result['method']} ({prediction_result['speed']})")
            
            # Convert to API format
            ai_prediction = {
                'products': prediction_result['products'],
                'confidence': prediction_result['confidence'],
                'reasoning': prediction_result.get('reasoning', ''),
                'method': prediction_result['method'],
                'speed': prediction_result['speed']
            }
        else:
            # Fallback to basic Gemini if hierarchical fails
            print("\nStep 2: Fallback to Gemini (hierarchical unavailable)...")
            from quantum_chemistry.gemini_integration import GeminiReactionPredictor
            gemini_predictor = GeminiReactionPredictor(api_key=os.getenv('GEMINI_API_KEY'))
            ai_prediction = gemini_predictor.predict_reaction(elements, quantum_data)
            ai_prediction['method'] = 'gemini_fallback'
        
        response = {
            'input_elements': elements,
            'quantum_data': {
                'vqe_energy': quantum_data.get('vqe_energy'),
                'hf_energy': quantum_data.get('hf_energy'),
                'energy_improvement': quantum_data.get('energy_improvement'),
                'num_electrons': quantum_data.get('num_electrons'),
                'num_qubits': quantum_data.get('num_qubits'),
                'bond_lengths': quantum_data.get('bond_lengths'),
                'orbital_occupations': quantum_data.get('orbital_occupations'),
                'mo_energies': quantum_data.get('mo_energies')
            },
            'ai_prediction': ai_prediction,
            'success': True
        }
        
        print(f"\n{'='*50}")
        print(f"Prediction complete!")
        print(f"Products: {ai_prediction.get('products', [])}")
        print(f"Confidence: {ai_prediction.get('confidence', 0)}%")
        print(f"{'='*50}\n")
        
        return jsonify(response)
        
    except Exception as e:
        print(f"\n{'='*50}")
        print(f"ERROR: {str(e)}")
        print(f"{'='*50}")
        import traceback
        traceback.print_exc()
        print(f"{'='*50}\n")
        
        # Provide helpful error messages
        error_msg = str(e)
        if "MATLAB" in error_msg:
            error_msg += "\n\nMATLAB execution failed. Check MATLAB installation."
        elif "PySCF" in error_msg or "einsum" in error_msg:
            error_msg += "\n\nQuantum chemistry calculation failed. Try simpler molecules (e.g., H+H)."
        
        return jsonify({
            'error': error_msg,
            'success': False,
            'traceback': traceback.format_exc() if app.debug else None
        }), 500

@app.route('/api/explain-quantum-data', methods=['POST'])
def explain_quantum_data():
    """Get human-readable explanation of quantum data"""
    try:
        data = request.json
        quantum_data = data.get('quantum_data', {})
        
        if not quantum_data:
            return jsonify({'error': 'quantum_data required'}), 400
        
        explanation = gemini_predictor.explain_quantum_data(quantum_data)
        
        return jsonify({
            'explanation': explanation,
            'success': True
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/api/elements', methods=['GET'])
def get_elements():
    """Get list of supported elements"""
    # For now, support common elements
    elements = [
        {'symbol': 'H', 'name': 'Hydrogen', 'number': 1},
        {'symbol': 'He', 'name': 'Helium', 'number': 2},
        {'symbol': 'Li', 'name': 'Lithium', 'number': 3},
        {'symbol': 'C', 'name': 'Carbon', 'number': 6},
        {'symbol': 'N', 'name': 'Nitrogen', 'number': 7},
        {'symbol': 'O', 'name': 'Oxygen', 'number': 8},
        {'symbol': 'F', 'name': 'Fluorine', 'number': 9},
        {'symbol': 'Na', 'name': 'Sodium', 'number': 11},
        {'symbol': 'Cl', 'name': 'Chlorine', 'number': 17}
    ]
    return jsonify({'elements': elements})

if __name__ == '__main__':
    print("\n" + "="*50)
    print("Quantum Chemistry Reaction Predictor API")
    print("="*50)
    print(f"MATLAB Path: {os.getenv('MATLAB_PATH')}")
    print(f"Gemini API: {'Configured' if os.getenv('GEMINI_API_KEY') else 'Not configured'}")
    print("="*50 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
