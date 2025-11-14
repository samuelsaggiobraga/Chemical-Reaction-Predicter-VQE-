"""
Gemini AI integration for reaction prediction using quantum chemistry data
"""
import google.generativeai as genai
from typing import Dict, List, Any
import json
from .quantum_feature_extractor import QuantumFeatureExtractor
from .reaction_training_data import ReactionTrainingExamples, ReactionMechanismClassifier


class GeminiReactionPredictor:
    """Use Gemini to predict chemical reactions from quantum data"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        # Use gemini-2.5-flash (latest stable version)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.feature_extractor = QuantumFeatureExtractor()
        
    def predict_reaction(self, elements: List[str], quantum_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict reaction outcome using quantum chemistry data + Gemini AI
        
        Args:
            elements: Input reactant elements
            quantum_data: Complete quantum calculation results from MATLAB pipeline
            
        Returns:
            AI-predicted reaction products and mechanisms
        """
        
        # Preprocess quantum data into chemically meaningful features
        features = self.feature_extractor.extract_features(quantum_data, elements)
        
        # Few-shot examples: find similar reactions
        examples = ReactionTrainingExamples.get_similar_examples({
            'homo_lumo_gap': features.get('electronic_features', {}).get('homo_lumo_gap'),
            'is_radical': features.get('reactivity_indicators', {}).get('is_radical'),
            'electronegativity': features.get('reactivity_indicators', {}).get('average_electronegativity'),
            'reactivity_category': features.get('electronic_features', {}).get('gap_category'),
            'is_stable': features.get('stability_metrics', {}).get('is_stable')
        }, n=3)
        examples_txt = ReactionTrainingExamples.format_examples_for_prompt(examples)
        
        # Predict mechanism type (for additional guidance)
        mechanism_hint = ReactionMechanismClassifier.predict_mechanism_type({
            'is_radical': features.get('reactivity_indicators', {}).get('is_radical'),
            'average_electronegativity': features.get('reactivity_indicators', {}).get('average_electronegativity'),
            'homo_lumo_gap': features.get('electronic_features', {}).get('homo_lumo_gap')
        }, elements)
        
        # Construct detailed prompt with quantum data and features
        prompt = self._build_prompt(elements, quantum_data, features, examples_txt, mechanism_hint)
        
        # Get prediction from Gemini
        response = self.model.generate_content(prompt)
        
        # Parse and structure the response
        prediction = self._parse_response(response.text, quantum_data)
        prediction['preprocessed_features'] = features
        prediction['few_shot_examples_used'] = [e['reactants'] for e in examples]
        prediction['mechanism_hint'] = mechanism_hint
        
        return prediction
    
    def _build_prompt(self, elements: List[str], quantum_data: Dict[str, Any], features: Dict[str, Any], examples_txt: str, mechanism_hint: str) -> str:
        """Construct prompt with quantum chemistry context + preprocessed features + few-shot examples"""
        
        # Format quantum data for prompt
        qd = quantum_data
        ef = features.get('electronic_features', {})
        sm = features.get('stability_metrics', {})
        rd = features.get('reactivity_indicators', {})
        bonds = features.get('bond_analysis', {})
        
        prompt = f"""You are a chemistry expert. Predict reaction outcomes using the provided quantum-chemistry data and derived features.

REACTANTS: {' + '.join(elements)}

RAW QUANTUM DATA (Python → MATLAB VQE):
- Ground State Energy (VQE): {qd.get('vqe_energy', 'N/A')}
- Hartree-Fock Energy: {qd.get('hf_energy', 'N/A')}
- Energy Improvement (HF − VQE): {qd.get('energy_improvement', 'N/A')}
- Nuclear Repulsion Energy: {qd.get('nuclear_repulsion', 'N/A')}
- MO Energies: {qd.get('mo_energies', [])}
- Orbital Occupations: {qd.get('orbital_occupations', [])}
- Bond Lengths (Å): {json.dumps(qd.get('bond_lengths', {}))}

DERIVED FEATURES (preprocessed to guide reasoning):
- HOMO-LUMO gap: {ef.get('homo_lumo_gap')}, category: {ef.get('gap_category')}
- Stability score (per electron): {sm.get('stability_score_per_electron')}, correlation energy: {sm.get('correlation_energy')}
- Radical: {rd.get('is_radical')}, avg electronegativity: {rd.get('average_electronegativity')}
- Bonds detected: {bonds.get('bond_count')}, avg length: {bonds.get('average_bond_length')}
- Interpretation: {features.get('interpretation')}

MECHANISM HINT: {mechanism_hint}

REFERENCE EXAMPLES (few-shot guidance):
{examples_txt}

Task: Predict the most likely reaction products and mechanism.
Constraints:
- Return strict JSON with fields: products[], mechanism, thermodynamics, confidence, reasoning
- Each product: {{formula, name, probability}} with probabilities summing to 1.0
- Keep mechanism and thermodynamics concise (<50 words each)
- Balance equations logically; products may repeat across product sets but probabilities must be consistent
"""
        
        return prompt
    
    def _parse_response(self, response_text: str, quantum_data: Dict) -> Dict[str, Any]:
        """Parse Gemini response into structured format"""
        
        try:
            # Try to extract JSON from response - handle markdown code blocks
            cleaned = response_text.replace('```json', '').replace('```', '')
            
            # Try to extract JSON
            start_idx = cleaned.find('{')
            end_idx = cleaned.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = cleaned[start_idx:end_idx]
                parsed = json.loads(json_str)
                
                # Ensure required fields exist with defaults
                parsed.setdefault('products', ['Unknown'])
                parsed.setdefault('mechanism', 'Not provided')
                parsed.setdefault('thermodynamics', 'Not provided')
                parsed.setdefault('confidence', 0)
                parsed.setdefault('reasoning', 'Not provided')
            else:
                # Fallback if no JSON found
                parsed = {
                    "products": ["Unknown"],
                    "mechanism": response_text[:500],  # Truncate if too long
                    "thermodynamics": "Analysis provided in mechanism",
                    "confidence": 0,
                    "reasoning": "Could not parse structured response"
                }
            
            # Add quantum data reference
            parsed['quantum_data_summary'] = {
                'vqe_energy': quantum_data.get('vqe_energy'),
                'hf_energy': quantum_data.get('hf_energy'),
                'energy_improvement': quantum_data.get('energy_improvement'),
                'num_electrons': quantum_data.get('num_electrons')
            }
            
            return parsed
            
        except json.JSONDecodeError as e:
            # Return raw response if parsing fails
            print(f"⚠️ JSON parsing failed: {e}")
            print(f"Raw response (first 500 chars): {response_text[:500]}")
            return {
                "products": ["Parsing Error"],
                "mechanism": response_text[:1000] if len(response_text) > 1000 else response_text,
                "thermodynamics": "See mechanism for details",
                "confidence": 0,
                "reasoning": "Failed to parse AI response as JSON",
                "error": f"JSON parsing error: {str(e)}"
            }
    
    def explain_quantum_data(self, quantum_data: Dict[str, Any]) -> str:
        """Get human-readable explanation of quantum calculation results"""
        
        prompt = f"""Explain these quantum chemistry calculation results in simple terms:

Ground State Energy: {quantum_data.get('vqe_energy')} Hartree
Hartree-Fock Energy: {quantum_data.get('hf_energy')} Hartree
Orbital Occupations: {quantum_data.get('orbital_occupations')}
Bond Lengths: {quantum_data.get('bond_lengths')}

What do these numbers tell us about the molecule's properties and reactivity?
"""
        
        response = self.model.generate_content(prompt)
        return response.text
