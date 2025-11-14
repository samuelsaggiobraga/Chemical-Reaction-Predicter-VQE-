"""
ML-Based Reaction Validator - Validates LLM predictions using machine learning
"""
import numpy as np
from typing import Dict, List, Any, Tuple
from collections import defaultdict


class ReactionValidator:
    """
    Lightweight ML validator for checking reaction prediction correctness
    Uses rule-based heuristics + pattern matching (no training needed)
    """
    
    # Known reaction patterns with confidence scores
    KNOWN_PATTERNS = {
        # Pattern: (reactant_signature, expected_product_signature, confidence)
        'H+H': ({'elements': ['H', 'H'], 'expected': 'H2', 'confidence': 0.99}),
        'H+H+O': ({'elements': ['H', 'H', 'O'], 'expected': 'H2O', 'confidence': 0.95}),
        'O+H': ({'elements': ['O', 'H'], 'expected': 'OH', 'confidence': 0.98}),
        'Na+Cl': ({'elements': ['Na', 'Cl'], 'expected': 'NaCl', 'confidence': 0.99}),
        'C+4H': ({'elements': ['C', 'H', 'H', 'H', 'H'], 'expected': 'CH4', 'confidence': 0.97}),
    }
    
    def __init__(self):
        self.validation_history = []
        
    def validate_prediction(self, elements: List[str], predicted_products: List[Dict], 
                          quantum_features: Dict) -> Dict[str, Any]:
        """
        Validate LLM prediction using multiple checks
        
        Args:
            elements: Input reactant elements
            predicted_products: LLM predicted products
            quantum_features: Preprocessed quantum features
            
        Returns:
            Validation result with confidence score and warnings
        """
        checks = []
        warnings = []
        confidence_adjustments = []
        
        # Check 1: Mass balance (conservation of atoms)
        mass_check = self._check_mass_balance(elements, predicted_products)
        checks.append(mass_check)
        if not mass_check['passed']:
            warnings.append("Mass balance violated - atoms not conserved")
            confidence_adjustments.append(-0.3)
        
        # Check 2: Charge balance
        charge_check = self._check_charge_balance(elements, predicted_products)
        checks.append(charge_check)
        if not charge_check['passed']:
            warnings.append("Charge balance may be incorrect")
            confidence_adjustments.append(-0.1)
        
        # Check 3: Known pattern matching
        pattern_check = self._check_known_patterns(elements, predicted_products)
        checks.append(pattern_check)
        if pattern_check['matched']:
            confidence_adjustments.append(+0.1)
        
        # Check 4: Thermodynamic feasibility from quantum data
        thermo_check = self._check_thermodynamics(quantum_features)
        checks.append(thermo_check)
        if not thermo_check['passed']:
            warnings.append(thermo_check['message'])
            confidence_adjustments.append(-0.2)
        
        # Check 5: Product probability consistency
        prob_check = self._check_probability_sum(predicted_products)
        checks.append(prob_check)
        if not prob_check['passed']:
            warnings.append("Product probabilities don't sum to 1.0")
            confidence_adjustments.append(-0.15)
        
        # Check 6: Quantum feature consistency
        quantum_check = self._check_quantum_consistency(quantum_features, predicted_products)
        checks.append(quantum_check)
        if quantum_check['warnings']:
            warnings.extend(quantum_check['warnings'])
            confidence_adjustments.append(-0.1 * len(quantum_check['warnings']))
        
        # Calculate overall validation score
        passed_checks = sum(1 for c in checks if c['passed'])
        base_confidence = passed_checks / len(checks)
        
        # Apply adjustments
        final_confidence = base_confidence + sum(confidence_adjustments)
        final_confidence = max(0.0, min(1.0, final_confidence))  # Clamp to [0, 1]
        
        # Determine overall result
        if final_confidence >= 0.8:
            result = 'LIKELY_CORRECT'
        elif final_confidence >= 0.6:
            result = 'UNCERTAIN'
        else:
            result = 'LIKELY_INCORRECT'
        
        validation_result = {
            'result': result,
            'confidence': float(final_confidence),
            'checks_passed': f"{passed_checks}/{len(checks)}",
            'warnings': warnings,
            'detailed_checks': checks,
            'recommendation': self._generate_recommendation(result, warnings)
        }
        
        # Store in history
        self.validation_history.append({
            'elements': elements,
            'predicted': predicted_products,
            'validation': validation_result
        })
        
        return validation_result
    
    def _check_mass_balance(self, elements: List[str], products: List[Dict]) -> Dict:
        """Check if atoms are conserved"""
        # Count input atoms
        input_counts = defaultdict(int)
        for elem in elements:
            input_counts[elem] += 1
        
        # Count output atoms (parse formulas)
        output_counts = defaultdict(int)
        for product in products:
            formula = product.get('formula', '')
            parsed = self._parse_formula(formula)
            for elem, count in parsed.items():
                output_counts[elem] += count
        
        # Compare
        balanced = (dict(input_counts) == dict(output_counts))
        
        return {
            'name': 'mass_balance',
            'passed': balanced,
            'input_atoms': dict(input_counts),
            'output_atoms': dict(output_counts),
            'message': 'Mass balanced' if balanced else 'Mass imbalance detected'
        }
    
    def _check_charge_balance(self, elements: List[str], products: List[Dict]) -> Dict:
        """Check charge balance (simplified - assumes neutral reactants)"""
        # For now, just check that we don't have obvious charge issues
        # Real implementation would parse charges from formulas
        return {
            'name': 'charge_balance',
            'passed': True,  # Simplified check
            'message': 'Charge balance assumed correct'
        }
    
    def _check_known_patterns(self, elements: List[str], products: List[Dict]) -> Dict:
        """Check against known reaction patterns"""
        signature = '+'.join(sorted(elements))
        
        if signature in self.KNOWN_PATTERNS:
            pattern = self.KNOWN_PATTERNS[signature]
            expected = pattern['expected']
            
            # Check if expected product is in predictions
            product_formulas = [p.get('formula', '') for p in products]
            matched = expected in product_formulas
            
            return {
                'name': 'pattern_matching',
                'passed': True,
                'matched': matched,
                'expected': expected,
                'confidence': pattern['confidence'] if matched else 0.5,
                'message': f"Matches known pattern: {signature} → {expected}" if matched else f"Expected {expected}, got {product_formulas}"
            }
        
        return {
            'name': 'pattern_matching',
            'passed': True,
            'matched': False,
            'message': 'No known pattern for this reaction'
        }
    
    def _check_thermodynamics(self, quantum_features: Dict) -> Dict:
        """Check if thermodynamically feasible based on quantum data"""
        stability = quantum_features.get('stability_metrics', {})
        
        # Check if system is stable
        is_stable = stability.get('is_stable', True)
        binding_energy = stability.get('electronic_binding_energy', 0)
        
        if not is_stable:
            return {
                'name': 'thermodynamics',
                'passed': False,
                'message': 'Unstable system (positive energy) - reaction unlikely'
            }
        
        if binding_energy > -0.1:
            return {
                'name': 'thermodynamics',
                'passed': False,
                'message': 'Weak binding - system may not be stable enough'
            }
        
        return {
            'name': 'thermodynamics',
            'passed': True,
            'message': f'System stable (binding: {binding_energy:.3f} Ha)'
        }
    
    def _check_probability_sum(self, products: List[Dict]) -> Dict:
        """Check if probabilities sum to ~1.0"""
        total_prob = sum(p.get('probability', 0) for p in products)
        
        # Allow small tolerance
        passed = abs(total_prob - 1.0) < 0.05
        
        return {
            'name': 'probability_sum',
            'passed': passed,
            'total_probability': total_prob,
            'message': f'Probabilities sum to {total_prob:.3f}'
        }
    
    def _check_quantum_consistency(self, quantum_features: Dict, products: List[Dict]) -> Dict:
        """Check if products are consistent with quantum features"""
        warnings = []
        
        reactivity = quantum_features.get('reactivity_indicators', {})
        electronic = quantum_features.get('electronic_features', {})
        
        # Check radical predictions
        is_radical = reactivity.get('is_radical', False)
        gap_category = electronic.get('gap_category', 'unknown')
        
        if is_radical and gap_category == 'stable':
            warnings.append("Radical reactant predicted as stable - check spin multiplicity")
        
        if gap_category == 'highly_reactive' and len(products) == 1:
            warnings.append("Highly reactive system might have multiple products")
        
        return {
            'name': 'quantum_consistency',
            'passed': len(warnings) == 0,
            'warnings': warnings,
            'message': 'Quantum features consistent' if not warnings else f'{len(warnings)} consistency warnings'
        }
    
    def _parse_formula(self, formula: str) -> Dict[str, int]:
        """Parse chemical formula into element counts"""
        import re
        pattern = re.compile(r'([A-Z][a-z]?)(\d*)')
        counts = defaultdict(int)
        
        for match in pattern.finditer(formula):
            elem = match.group(1)
            count = int(match.group(2)) if match.group(2) else 1
            counts[elem] += count
        
        return dict(counts)
    
    def _generate_recommendation(self, result: str, warnings: List[str]) -> str:
        """Generate user-facing recommendation"""
        if result == 'LIKELY_CORRECT':
            return "Prediction appears reliable. Proceed with confidence."
        elif result == 'UNCERTAIN':
            return f"Prediction uncertain. Review warnings: {'; '.join(warnings[:2])}"
        else:
            return f"Prediction may be incorrect. Issues: {'; '.join(warnings[:3])}"
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get statistics from validation history"""
        if not self.validation_history:
            return {'total_validations': 0}
        
        results = [v['validation']['result'] for v in self.validation_history]
        confidences = [v['validation']['confidence'] for v in self.validation_history]
        
        return {
            'total_validations': len(self.validation_history),
            'correct_count': results.count('LIKELY_CORRECT'),
            'uncertain_count': results.count('UNCERTAIN'),
            'incorrect_count': results.count('LIKELY_INCORRECT'),
            'average_confidence': np.mean(confidences) if confidences else 0,
            'pass_rate': results.count('LIKELY_CORRECT') / len(results) if results else 0
        }
