"""
Reaction Training Data - Curated examples of reactions with quantum features
for few-shot learning with Gemini
"""
from typing import Dict, List, Any


class ReactionTrainingExamples:
    """Database of known reactions with quantum features for training/prompting"""
    
    # Curated examples of reactions with their quantum signatures
    TRAINING_EXAMPLES = [
        {
            "reactants": ["H", "H"],
            "quantum_features": {
                "homo_lumo_gap": 0.45,
                "is_radical": False,
                "electronegativity": 2.20,
                "reactivity_category": "stable",
                "binding_energy": -1.17,
                "is_stable": True
            },
            "products": [
                {"formula": "H2", "name": "Hydrogen gas", "probability": 1.0}
            ],
            "mechanism": "Two hydrogen atoms form covalent bond via orbital overlap, sharing electron pair",
            "thermodynamics": "Feasible, spontaneous. Exothermic with ΔH = -436 kJ/mol",
            "reaction_type": "radical_combination"
        },
        {
            "reactants": ["H", "H", "O"],
            "quantum_features": {
                "homo_lumo_gap": 0.25,
                "is_radical": True,
                "electronegativity": 2.63,
                "reactivity_category": "reactive",
                "binding_energy": -2.45,
                "is_stable": True
            },
            "products": [
                {"formula": "H2O", "name": "Water", "probability": 0.85},
                {"formula": "OH", "name": "Hydroxyl radical", "probability": 0.10},
                {"formula": "H2", "name": "Hydrogen gas", "probability": 0.05}
            ],
            "mechanism": "Oxygen forms two bonds with hydrogen atoms. Bent geometry due to lone pairs. May form OH radical intermediate",
            "thermodynamics": "Feasible, highly exothermic. ΔH = -242 kJ/mol per H2O formed",
            "reaction_type": "combination"
        },
        {
            "reactants": ["O", "H"],
            "quantum_features": {
                "homo_lumo_gap": 0.18,
                "is_radical": True,
                "electronegativity": 2.82,
                "reactivity_category": "highly_reactive",
                "binding_energy": -0.92,
                "is_stable": True
            },
            "products": [
                {"formula": "OH", "name": "Hydroxyl radical", "probability": 1.0}
            ],
            "mechanism": "Radical oxygen (2 unpaired) bonds with hydrogen radical. Forms highly reactive OH radical",
            "thermodynamics": "Feasible. OH radical is stable but reactive intermediate",
            "reaction_type": "radical_combination"
        },
        {
            "reactants": ["C", "H", "H", "H", "H"],
            "quantum_features": {
                "homo_lumo_gap": 0.35,
                "is_radical": False,
                "electronegativity": 2.48,
                "reactivity_category": "moderately_reactive",
                "binding_energy": -4.56,
                "is_stable": True
            },
            "products": [
                {"formula": "CH4", "name": "Methane", "probability": 1.0}
            ],
            "mechanism": "Carbon forms 4 sp3 hybrid orbitals, each bonds with one H. Tetrahedral geometry",
            "thermodynamics": "Feasible, exothermic. ΔH = -75 kJ/mol",
            "reaction_type": "combination"
        },
        {
            "reactants": ["Na", "Cl"],
            "quantum_features": {
                "homo_lumo_gap": 0.05,
                "is_radical": False,
                "electronegativity": 2.05,
                "reactivity_category": "highly_reactive",
                "binding_energy": -1.23,
                "is_stable": True
            },
            "products": [
                {"formula": "NaCl", "name": "Sodium chloride", "probability": 1.0}
            ],
            "mechanism": "Electron transfer from Na to Cl. Ionic bond between Na+ and Cl-",
            "thermodynamics": "Feasible, highly exothermic. ΔH = -411 kJ/mol",
            "reaction_type": "ionic"
        },
        {
            "reactants": ["O", "O"],
            "quantum_features": {
                "homo_lumo_gap": 0.12,
                "is_radical": False,
                "electronegativity": 3.44,
                "reactivity_category": "reactive",
                "binding_energy": -2.13,
                "is_stable": True
            },
            "products": [
                {"formula": "O2", "name": "Oxygen gas", "probability": 1.0}
            ],
            "mechanism": "Two oxygen atoms form double bond. Paramagnetic due to unpaired electrons in π* orbitals",
            "thermodynamics": "Feasible. O2 is stable diatomic molecule",
            "reaction_type": "combination"
        },
        {
            "reactants": ["C", "O", "O"],
            "quantum_features": {
                "homo_lumo_gap": 0.28,
                "is_radical": False,
                "electronegativity": 3.14,
                "reactivity_category": "moderately_reactive",
                "binding_energy": -5.67,
                "is_stable": True
            },
            "products": [
                {"formula": "CO2", "name": "Carbon dioxide", "probability": 0.95},
                {"formula": "CO", "name": "Carbon monoxide", "probability": 0.05}
            ],
            "mechanism": "Carbon forms two double bonds with oxygen atoms. Linear geometry, sp hybridization",
            "thermodynamics": "Feasible, exothermic. ΔH = -394 kJ/mol for CO2",
            "reaction_type": "combination"
        }
    ]
    
    @classmethod
    def get_examples(cls) -> List[Dict[str, Any]]:
        """Get all training examples"""
        return cls.TRAINING_EXAMPLES
    
    @classmethod
    def get_similar_examples(cls, quantum_features: Dict, n: int = 3) -> List[Dict]:
        """
        Find most similar training examples based on quantum features
        
        Args:
            quantum_features: Quantum features from current calculation
            n: Number of similar examples to return
            
        Returns:
            List of most similar training examples
        """
        examples = cls.TRAINING_EXAMPLES.copy()
        
        # Calculate similarity scores
        for example in examples:
            score = cls._calculate_similarity(quantum_features, example['quantum_features'])
            example['similarity_score'] = score
        
        # Sort by similarity and return top n
        examples.sort(key=lambda x: x['similarity_score'], reverse=True)
        return examples[:n]
    
    @classmethod
    def _calculate_similarity(cls, features1: Dict, features2: Dict) -> float:
        """Calculate similarity between two quantum feature sets"""
        score = 0.0
        weights = {
            'homo_lumo_gap': 2.0,
            'is_radical': 3.0,
            'electronegativity': 1.5,
            'reactivity_category': 2.0,
            'is_stable': 1.0
        }
        
        # HOMO-LUMO gap similarity
        if 'homo_lumo_gap' in features1 and 'homo_lumo_gap' in features2:
            gap1 = features1['homo_lumo_gap']
            gap2 = features2['homo_lumo_gap']
            if gap1 and gap2:
                gap_diff = abs(gap1 - gap2)
                score += weights['homo_lumo_gap'] * (1.0 / (1.0 + gap_diff))
        
        # Radical character match
        if features1.get('is_radical') == features2.get('is_radical'):
            score += weights['is_radical']
        
        # Electronegativity similarity
        if 'average_electronegativity' in features1 and 'electronegativity' in features2:
            en_diff = abs(features1['average_electronegativity'] - features2['electronegativity'])
            score += weights['electronegativity'] * (1.0 / (1.0 + en_diff))
        
        # Reactivity category match
        if features1.get('gap_category') == features2.get('reactivity_category'):
            score += weights['reactivity_category']
        
        # Stability match
        if features1.get('is_stable') == features2.get('is_stable'):
            score += weights['is_stable']
        
        return score
    
    @classmethod
    def format_examples_for_prompt(cls, examples: List[Dict]) -> str:
        """Format training examples for inclusion in Gemini prompt"""
        formatted = []
        
        for i, ex in enumerate(examples, 1):
            formatted.append(f"EXAMPLE {i}:")
            formatted.append(f"  Reactants: {' + '.join(ex['reactants'])}")
            formatted.append(f"  Quantum Features: HOMO-LUMO gap={ex['quantum_features']['homo_lumo_gap']:.3f}, "
                           f"Radical={ex['quantum_features']['is_radical']}, "
                           f"EN={ex['quantum_features']['electronegativity']:.2f}")
            formatted.append(f"  Products: {', '.join([p['formula'] for p in ex['products']])}")
            formatted.append(f"  Mechanism: {ex['mechanism']}")
            formatted.append(f"  Type: {ex['reaction_type']}")
            formatted.append("")
        
        return '\n'.join(formatted)


class ReactionMechanismClassifier:
    """Classify reactions by mechanism type"""
    
    MECHANISM_TYPES = {
        'radical_combination': {
            'description': 'Two radicals combine to form bond',
            'indicators': ['is_radical', 'small_homo_lumo_gap'],
            'typical_products': 'Single molecule from radical species'
        },
        'ionic': {
            'description': 'Electron transfer, ion formation',
            'indicators': ['large_electronegativity_difference', 'metal_nonmetal'],
            'typical_products': 'Ionic compound'
        },
        'combination': {
            'description': 'Multiple atoms/molecules form single product',
            'indicators': ['complementary_electronegativities', 'stable_product'],
            'typical_products': 'Stable molecule'
        },
        'substitution': {
            'description': 'One atom/group replaces another',
            'indicators': ['good_leaving_group', 'nucleophile_present'],
            'typical_products': 'Substituted molecule + leaving group'
        },
        'addition': {
            'description': 'Addition to multiple bond',
            'indicators': ['unsaturated_bond', 'electrophile_nucleophile_pair'],
            'typical_products': 'Saturated molecule'
        },
        'elimination': {
            'description': 'Loss of small molecule to form double bond',
            'indicators': ['beta_hydrogen', 'leaving_group'],
            'typical_products': 'Alkene + small molecule'
        }
    }
    
    @classmethod
    def predict_mechanism_type(cls, quantum_features: Dict, elements: List[str]) -> str:
        """Predict most likely reaction mechanism"""
        
        # Simple heuristics based on quantum features
        is_radical = quantum_features.get('is_radical', False)
        en_avg = quantum_features.get('average_electronegativity', 2.5)
        gap = quantum_features.get('homo_lumo_gap')
        
        # Check for metal + nonmetal (ionic)
        metals = ['Na', 'K', 'Li', 'Ca', 'Mg']
        nonmetals = ['Cl', 'F', 'O', 'S']
        has_metal = any(e in metals for e in elements)
        has_nonmetal = any(e in nonmetals for e in elements)
        
        if has_metal and has_nonmetal:
            return 'ionic'
        elif is_radical:
            return 'radical_combination'
        else:
            return 'combination'
