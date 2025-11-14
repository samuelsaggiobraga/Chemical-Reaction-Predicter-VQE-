"""
Unit tests for quantum chemistry modules
Run with: pytest tests/test_unit.py -v
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.quantum_chemistry.quantum_feature_extractor import QuantumFeatureExtractor
from backend.quantum_chemistry.reaction_training_data import ReactionTrainingExamples, ReactionMechanismClassifier
from backend.quantum_chemistry.organic_chemistry import SMILESParser, FunctionalGroupDetector, OrganicMoleculeBuilder
from backend.quantum_chemistry.result_cache import ResultCache, SmartCache
from backend.quantum_chemistry.ml_validator import ReactionValidator


class TestQuantumFeatureExtractor:
    """Test quantum feature extraction"""
    
    def test_initialization(self):
        extractor = QuantumFeatureExtractor()
        assert extractor is not None
    
    def test_feature_extraction_h2(self):
        """Test feature extraction for H2 molecule"""
        extractor = QuantumFeatureExtractor()
        
        quantum_data = {
            'vqe_energy': -1.137,
            'hf_energy': -1.116,
            'energy_improvement': 0.021,
            'nuclear_repulsion': 0.714,
            'num_electrons': 2,
            'num_atoms': 2,
            'mo_energies': [-0.578, 0.671],
            'orbital_occupations': [1.0, 0.0],
            'bond_lengths': {'H1-H2': 0.74}
        }
        
        features = extractor.extract_features(quantum_data, ['H', 'H'])
        
        assert 'stability_metrics' in features
        assert 'electronic_features' in features
        assert 'bond_analysis' in features
        assert 'reactivity_indicators' in features
        assert 'interpretation' in features
        
        # Check specific values
        assert features['stability_metrics']['is_stable'] == True
        assert features['electronic_features']['total_electrons'] == 2
        assert features['bond_analysis']['bond_count'] == 1
        assert features['reactivity_indicators']['is_radical'] == False
    
    def test_homo_lumo_gap_calculation(self):
        """Test HOMO-LUMO gap calculation"""
        extractor = QuantumFeatureExtractor()
        
        quantum_data = {
            'vqe_energy': -1.0,
            'hf_energy': -1.0,
            'nuclear_repulsion': 0.5,
            'num_electrons': 2,
            'num_atoms': 2,
            'mo_energies': [-0.5, 0.5],
            'orbital_occupations': [1.0, 0.0],
            'bond_lengths': {}
        }
        
        features = extractor.extract_features(quantum_data, ['H', 'H'])
        gap = features['electronic_features']['homo_lumo_gap']
        
        assert gap is not None
        assert gap > 0
        assert gap == 1.0  # 0.5 - (-0.5)


class TestReactionTrainingExamples:
    """Test reaction training examples and similarity matching"""
    
    def test_get_all_examples(self):
        examples = ReactionTrainingExamples.get_examples()
        assert len(examples) == 7
        assert all('reactants' in ex for ex in examples)
        assert all('products' in ex for ex in examples)
    
    def test_similarity_matching(self):
        """Test finding similar reactions"""
        test_features = {
            'homo_lumo_gap': 0.18,
            'is_radical': True,
            'electronegativity': 2.82,
            'reactivity_category': 'highly_reactive',
            'is_stable': True
        }
        
        similar = ReactionTrainingExamples.get_similar_examples(test_features, n=3)
        
        assert len(similar) <= 3
        assert all('similarity_score' in ex for ex in similar)
        # Scores should be sorted descending
        scores = [ex['similarity_score'] for ex in similar]
        assert scores == sorted(scores, reverse=True)
    
    def test_format_for_prompt(self):
        """Test formatting examples for Gemini prompt"""
        examples = ReactionTrainingExamples.get_examples()[:2]
        formatted = ReactionTrainingExamples.format_examples_for_prompt(examples)
        
        assert isinstance(formatted, str)
        assert 'EXAMPLE 1:' in formatted
        assert 'Reactants:' in formatted
        assert 'Products:' in formatted


class TestSMILESParser:
    """Test SMILES parsing"""
    
    def test_simple_molecules(self):
        """Test parsing simple molecules"""
        parser = SMILESParser()
        
        # Methane
        ch4 = parser.parse('C')
        assert ch4['molecular_formula'] == 'CH4'
        assert ch4['num_atoms'] == 1
        
        # Ethane
        c2h6 = parser.parse('CC')
        assert 'C2' in c2h6['molecular_formula']
        assert c2h6['num_bonds'] == 1
    
    def test_ethanol(self):
        """Test ethanol parsing"""
        parser = SMILESParser()
        ethanol = parser.parse('CCO')
        
        assert ethanol['num_atoms'] == 3
        assert ethanol['num_bonds'] == 2
        assert 'C' in ethanol['molecular_formula']
        assert 'O' in ethanol['molecular_formula']


class TestFunctionalGroupDetector:
    """Test functional group detection"""
    
    def test_ketone_detection(self):
        """Test ketone detection"""
        detector = FunctionalGroupDetector()
        groups = detector.detect('CC(=O)C')  # Acetone
        assert 'ketone' in groups
    
    def test_alkene_detection(self):
        """Test alkene detection"""
        detector = FunctionalGroupDetector()
        groups = detector.detect('C=C')  # Ethylene
        assert 'alkene' in groups
    
    def test_aromatic_detection(self):
        """Test aromatic detection"""
        detector = FunctionalGroupDetector()
        groups = detector.detect('c1ccccc1')  # Benzene
        assert 'aromatic' in groups


class TestResultCache:
    """Test caching system"""
    
    def test_cache_set_and_get(self):
        """Test basic cache operations"""
        cache = ResultCache(cache_dir='test_cache_unit')
        
        test_data = {'energy': -1.137, 'electrons': 2}
        cache.set(['H', 'H'], test_data)
        
        retrieved = cache.get(['H', 'H'])
        assert retrieved is not None
        assert retrieved['energy'] == test_data['energy']
        
        # Cleanup
        cache.clear()
        import shutil
        shutil.rmtree('test_cache_unit', ignore_errors=True)
    
    def test_cache_miss(self):
        """Test cache miss"""
        cache = ResultCache(cache_dir='test_cache_unit')
        result = cache.get(['X', 'Y', 'Z'])
        assert result is None
        
        import shutil
        shutil.rmtree('test_cache_unit', ignore_errors=True)
    
    def test_cache_stats(self):
        """Test cache statistics"""
        cache = ResultCache(cache_dir='test_cache_unit')
        cache.set(['H', 'H'], {'energy': -1.0})
        cache.set(['O', 'O'], {'energy': -2.0})
        
        stats = cache.get_stats()
        assert stats['total_entries'] == 2
        assert stats['total_size_bytes'] > 0
        
        cache.clear()
        import shutil
        shutil.rmtree('test_cache_unit', ignore_errors=True)


class TestReactionValidator:
    """Test ML validator"""
    
    def test_valid_prediction(self):
        """Test validation of correct prediction"""
        validator = ReactionValidator()
        
        elements = ['H', 'H']
        products = [{'formula': 'H2', 'name': 'Hydrogen', 'probability': 1.0}]
        quantum_features = {
            'stability_metrics': {'is_stable': True, 'electronic_binding_energy': -1.85},
            'electronic_features': {'homo_lumo_gap': 1.2, 'gap_category': 'stable'},
            'reactivity_indicators': {'is_radical': False}
        }
        
        result = validator.validate_prediction(elements, products, quantum_features)
        
        assert result['result'] in ['LIKELY_CORRECT', 'UNCERTAIN', 'LIKELY_INCORRECT']
        assert 0 <= result['confidence'] <= 1
        assert 'checks_passed' in result
        assert 'warnings' in result
    
    def test_mass_balance_violation(self):
        """Test detection of mass balance violation"""
        validator = ReactionValidator()
        
        elements = ['H', 'H']
        # Wrong product - doesn't conserve mass
        products = [{'formula': 'H2O', 'name': 'Water', 'probability': 1.0}]
        quantum_features = {
            'stability_metrics': {'is_stable': True, 'electronic_binding_energy': -1.0},
            'electronic_features': {'homo_lumo_gap': 0.5, 'gap_category': 'stable'},
            'reactivity_indicators': {'is_radical': False}
        }
        
        result = validator.validate_prediction(elements, products, quantum_features)
        
        assert 'Mass balance violated' in ' '.join(result['warnings'])
    
    def test_probability_sum_check(self):
        """Test probability sum validation"""
        validator = ReactionValidator()
        
        elements = ['H', 'H']
        # Probabilities don't sum to 1.0
        products = [
            {'formula': 'H2', 'name': 'Hydrogen', 'probability': 0.5},
            {'formula': 'H', 'name': 'Hydrogen atom', 'probability': 0.3}
        ]
        quantum_features = {
            'stability_metrics': {'is_stable': True, 'electronic_binding_energy': -1.0},
            'electronic_features': {'homo_lumo_gap': 0.5, 'gap_category': 'stable'},
            'reactivity_indicators': {'is_radical': False}
        }
        
        result = validator.validate_prediction(elements, products, quantum_features)
        
        assert result['confidence'] < 1.0


class TestOrganicMoleculeBuilder:
    """Test organic molecule builder"""
    
    def test_get_smiles(self):
        """Test retrieving SMILES for common molecules"""
        assert OrganicMoleculeBuilder.get_smiles('ethanol') == 'CCO'
        assert OrganicMoleculeBuilder.get_smiles('benzene') == 'c1ccccc1'
        assert OrganicMoleculeBuilder.get_smiles('methane') == 'C'
    
    def test_smiles_to_geometry(self):
        """Test SMILES to geometry conversion"""
        geometry = OrganicMoleculeBuilder.smiles_to_geometry('CCO')
        
        assert isinstance(geometry, list)
        assert len(geometry) > 0
        assert all(len(atom) == 2 for atom in geometry)
        assert all(isinstance(atom[1], tuple) and len(atom[1]) == 3 for atom in geometry)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
