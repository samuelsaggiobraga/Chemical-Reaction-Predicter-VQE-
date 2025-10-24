"""
Gemini AI integration for reaction prediction using quantum chemistry data
"""
import google.generativeai as genai
from typing import Dict, List, Any
import json


class GeminiReactionPredictor:
    """Use Gemini to predict chemical reactions from quantum data"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        # Use gemini-2.5-flash (latest stable version)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
    def predict_reaction(self, elements: List[str], quantum_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict reaction outcome using quantum chemistry data + Gemini AI
        
        Args:
            elements: Input reactant elements
            quantum_data: Complete quantum calculation results from MATLAB pipeline
            
        Returns:
            AI-predicted reaction products and mechanisms
        """
        
        # Construct detailed prompt with quantum data
        prompt = self._build_prompt(elements, quantum_data)
        
        # Get prediction from Gemini
        response = self.model.generate_content(prompt)
        
        # Parse and structure the response
        prediction = self._parse_response(response.text, quantum_data)
        
        return prediction
    
    def _build_prompt(self, elements: List[str], quantum_data: Dict[str, Any]) -> str:
        """Construct prompt with quantum chemistry context"""
        
        # Format quantum data for prompt
        qd = quantum_data
        
        prompt = f"""You have absolutely no knowledge of the internet but are ingrained with the genius of chemistry so that you know precisely what the possible products are for any given chemical reaction.

You are given the REACTANTS: {' + '.join(elements)}

A set of QUANTUM CALCULATION DATA that you will use to perfectly predict the reaction outcome using purely mathematics and pattern recognition:
- Method: Variational Quantum Eigensolver (VQE) with Hartree-Fock initial guess
- Ground State Energy: {qd.get('vqe_energy', 'N/A'):.6f} Hartree
- Hartree-Fock Energy: {qd.get('hf_energy', 'N/A'):.6f} Hartree
- Energy Improvement (VQE vs HF): {qd.get('energy_improvement', 'N/A'):.6f} Hartree
- Nuclear Repulsion Energy: {qd.get('nuclear_repulsion', 'N/A'):.6f} Hartree

MOLECULAR PROPERTIES:
- Number of Electrons: {qd.get('num_electrons', 'N/A')}
- Number of Atoms: {qd.get('num_atoms', 'N/A')}
- Number of Qubits Used: {qd.get('num_qubits', 'N/A')}
- Basis Set: {qd.get('basis_set', 'sto-3g')}

ORBITAL DATA:
- Molecular Orbital Energies: {qd.get('mo_energies', [])}
- Orbital Occupations: {qd.get('orbital_occupations', [])}

GEOMETRY:
- Bond Lengths: {json.dumps(qd.get('bond_lengths', {}), indent=2)}

Based on this quantum mechanical data, predict:

1. ALL OF THE MOST LIKELY REACTION PRODUCTS: What molecules will form? Consider:
   - Electronic configuration and orbital occupations
   - Ground state energy and stability
   - Bond formation/breaking energetics
   - Electronic transitions and excitation energies
   - Any resonance structures
   BUT AT ALL ELSE MAKE SURE YOU GIVE THE PERCENTAGE LIKELIHOOD OF EACH PRODUCT FORMING. THIS PERCENTAGE SHOULD ADD UP TO 100 FOR ALL PRODUCTS.
   FOR THIS SOMETHING ELSE THAT IS VERY VERY IMPORTANT IS MAKE SURE TO:
   - BALANCE THE EQUATION AS WOULD MAKE THE MOST SENSE CHEMICALLY (things dont have to match 1-1 like if you are offered A + B, the product does not need exactly 1 A and 1 B, BUT IT STILL SHOULD BE BALANCED)
   - LIST PRODUCTS SEPARARTELY NOT TOEGTHER, make sure to list each individual product as its own item in the list, even if it appears in multiple different product types (a product type is just the reaction either producing A_1+A_2+A_2+...+A_n or B_1+B_2+B_2+...+B_n where A_k,B_k not necessarily distinct)
   - MAKE THE PERCENTAGES AS ACCURATE AS POSSIBLE ACCOUNTING FOR PRODUCT OVERLAPS

2. REACTION MECHANISM:
    - Step-by step description of how the reaction forms the intermediates that forms the products, just a list

3. THERMODYNAMIC FEASIBILITY:
   - Is this reaction possible in nature, and is it spontaneous?
   - Look explicitly at the quantum data to justify your answer.
   - Use any other chemistry concepts that are known about the molecules as you have infinite chemical knowledge (aside from knowing the exact reactions memorized)
   

4. CONFIDENCE LEVEL: Rate your prediction confidence (0-100%) based on:
   - Quality of quantum data
   - Complexity of system
   - Known chemical principles

Provide your response in the following EXPLICIT JSON format, DO NOT FALTER FROM THIS FORMAT, JUST CLEAR LISTING MAKE ANSWERS NO LONGER THAN 50 WORDS EACH:
{{
  "products": [
    {{"formula": "H2O", "name": "Water", "probability": 0.85}},
    {{"formula": "O2", "name": "Oxygen", "probability": 0.15}}
  ],
  "mechanism": "The Description",
  "thermodynamics": "Just say if it is Feasible yes or no, MINIMAL WHY, AT MOST ONE SENTENCE",
  "confidence": "percentage value",
  "reasoning": "Cited precise numbers that gave the reasoning"
}}

IMPORTANT: Each product MUST have "formula" (chemical formula like H2O), "name" (common name), and "probability" (decimal from 0-1, all probabilities must sum to 1.0).
"""
        
        return prompt
    
    def _parse_response(self, response_text: str, quantum_data: Dict) -> Dict[str, Any]:
        """Parse Gemini response into structured format"""
        
        try:
            # Try to extract JSON from response - handle markdown code blocks
            # Remove markdown code blocks if present
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
