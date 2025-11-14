"""
Test suite for new improvements: quantum feature extraction, few-shot learning, and organic chemistry
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.quantum_chemistry.quantum_feature_extractor import QuantumFeatureExtractor
from backend.quantum_chemistry.reaction_training_data import ReactionTrainingExamples, ReactionMechanismClassifier
from backend.quantum_chemistry.organic_chemistry import SMILESParser, FunctionalGroupDetector, OrganicMoleculeBuilder, OrganicReactionClassifier


def test_quantum_feature_extractor():
    """Test quantum feature extraction"""
    print("\n" + "="*60)
    print("TEST 1: Quantum Feature Extractor")
    print("="*60)
    
    # Mock quantum data (H2 molecule)
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
    
    extractor = QuantumFeatureExtractor()
    features = extractor.extract_features(quantum_data, ['H', 'H'])
    
    print(f"\n✓ Stability Metrics:")
    print(f"  - Binding energy: {features['stability_metrics']['electronic_binding_energy']:.3f} Ha")
    print(f"  - Correlation energy: {features['stability_metrics']['correlation_energy']:.3f} Ha")
    print(f"  - Is stable: {features['stability_metrics']['is_stable']}")
    
    print(f"\n✓ Electronic Features:")
    print(f"  - HOMO-LUMO gap: {features['electronic_features']['homo_lumo_gap']}")
    print(f"  - Gap category: {features['electronic_features']['gap_category']}")
    print(f"  - Total electrons: {features['electronic_features']['total_electrons']}")
    
    print(f"\n✓ Reactivity Indicators:")
    print(f"  - Is radical: {features['reactivity_indicators']['is_radical']}")
    print(f"  - Avg electronegativity: {features['reactivity_indicators']['average_electronegativity']:.2f}")
    print(f"  - Likely nucleophile: {features['reactivity_indicators']['likely_nucleophile']}")
    
    print(f"\n✓ Bond Analysis:")
    print(f"  - Bond count: {features['bond_analysis']['bond_count']}")
    print(f"  - Bonds: {features['bond_analysis']['bonds']}")
    
    print(f"\n✓ Interpretation:")
    print(f"  {features['interpretation']}")
    
    return features


def test_few_shot_examples():
    """Test few-shot example retrieval"""
    print("\n" + "="*60)
    print("TEST 2: Few-Shot Learning Examples")
    print("="*60)
    
    # Test getting all examples
    all_examples = ReactionTrainingExamples.get_examples()
    print(f"\n✓ Total training examples: {len(all_examples)}")
    print(f"  Examples: {[' + '.join(ex['reactants']) for ex in all_examples]}")
    
    # Test similarity matching (radical oxygen + hydrogen)
    test_features = {
        'homo_lumo_gap': 0.18,
        'is_radical': True,
        'electronegativity': 2.82,
        'reactivity_category': 'highly_reactive',
        'is_stable': True
    }
    
    similar = ReactionTrainingExamples.get_similar_examples(test_features, n=3)
    print(f"\n✓ Top 3 similar reactions for O + H (radical):")
    for i, ex in enumerate(similar, 1):
        print(f"  {i}. {' + '.join(ex['reactants'])} → {', '.join([p['formula'] for p in ex['products']])}")
        print(f"     Similarity score: {ex['similarity_score']:.2f}")
        print(f"     Type: {ex['reaction_type']}")
    
    # Test formatted output for prompt
    formatted = ReactionTrainingExamples.format_examples_for_prompt(similar)
    print(f"\n✓ Formatted for Gemini prompt:")
    print(formatted[:300] + "...")
    
    return similar


def test_mechanism_classifier():
    """Test reaction mechanism classification"""
    print("\n" + "="*60)
    print("TEST 3: Reaction Mechanism Classification")
    print("="*60)
    
    # Test 1: Radical combination (H + H)
    mech1 = ReactionMechanismClassifier.predict_mechanism_type(
        {'is_radical': False, 'average_electronegativity': 2.20, 'homo_lumo_gap': 0.45},
        ['H', 'H']
    )
    print(f"\n✓ H + H mechanism: {mech1}")
    
    # Test 2: Ionic (Na + Cl)
    mech2 = ReactionMechanismClassifier.predict_mechanism_type(
        {'is_radical': False, 'average_electronegativity': 2.05, 'homo_lumo_gap': 0.05},
        ['Na', 'Cl']
    )
    print(f"✓ Na + Cl mechanism: {mech2}")
    
    # Test 3: Radical (O + H)
    mech3 = ReactionMechanismClassifier.predict_mechanism_type(
        {'is_radical': True, 'average_electronegativity': 2.82, 'homo_lumo_gap': 0.18},
        ['O', 'H']
    )
    print(f"✓ O + H mechanism: {mech3}")


def test_smiles_parser():
    """Test SMILES parsing"""
    print("\n" + "="*60)
    print("TEST 4: SMILES Parser")
    print("="*60)
    
    parser = SMILESParser()
    
    test_cases = [
        ('C', 'Methane'),
        ('CC', 'Ethane'),
        ('CCO', 'Ethanol'),
        ('CC(=O)C', 'Acetone'),
        ('c1ccccc1', 'Benzene'),
        ('CC(=O)O', 'Acetic acid')
    ]
    
    for smiles, name in test_cases:
        parsed = parser.parse(smiles)
        print(f"\n✓ {name} ({smiles}):")
        print(f"  - Formula: {parsed['molecular_formula']}")
        print(f"  - Atoms: {parsed['num_atoms']}")
        print(f"  - Bonds: {parsed['num_bonds']}")
        print(f"  - Atom details: {[(a['element'], a['implicit_h']) for a in parsed['atoms'][:3]]}")


def test_functional_groups():
    """Test functional group detection"""
    print("\n" + "="*60)
    print("TEST 5: Functional Group Detection")
    print("="*60)
    
    detector = FunctionalGroupDetector()
    
    test_molecules = [
        ('CCO', 'Ethanol'),
        ('CC(=O)C', 'Acetone'),
        ('CC(=O)O', 'Acetic acid'),
        ('CN', 'Methylamine'),
        ('CCCl', 'Chloroethane'),
        ('C=C', 'Ethylene'),
        ('c1ccccc1', 'Benzene')
    ]
    
    for smiles, name in test_molecules:
        groups = detector.detect(smiles)
        print(f"\n✓ {name} ({smiles}):")
        print(f"  - Functional groups: {groups if groups else 'None detected'}")


def test_organic_reactions():
    """Test organic reaction classification"""
    print("\n" + "="*60)
    print("TEST 6: Organic Reaction Classification")
    print("="*60)
    
    classifier = OrganicReactionClassifier()
    
    # Test alcohol with quantum features
    quantum_features = {
        'reactivity_indicators': {'likely_nucleophile': False},
        'stability_metrics': {'is_stable': True}
    }
    
    # Alcohol oxidation
    predictions = classifier.predict_mechanism(['alcohol'], quantum_features)
    print(f"\n✓ Alcohol reaction predictions:")
    for pred in predictions['predicted_mechanisms']:
        print(f"  - {pred['type']}: {pred['confidence']:.0%} confidence")
        print(f"    {pred['description']}")
    
    # Halide substitution/elimination
    predictions2 = classifier.predict_mechanism(['halide'], quantum_features)
    print(f"\n✓ Halide reaction predictions:")
    for pred in predictions2['predicted_mechanisms']:
        print(f"  - {pred['type']}: {pred['confidence']:.0%} confidence")
        print(f"    {pred['description']}")


def test_organic_molecule_builder():
    """Test organic molecule builder"""
    print("\n" + "="*60)
    print("TEST 7: Organic Molecule Builder")
    print("="*60)
    
    print(f"\n✓ Available molecules: {len(OrganicMoleculeBuilder.COMMON_MOLECULES)}")
    print(f"  First 10: {list(OrganicMoleculeBuilder.COMMON_MOLECULES.keys())[:10]}")
    
    # Test getting SMILES
    ethanol_smiles = OrganicMoleculeBuilder.get_smiles('ethanol')
    print(f"\n✓ Ethanol SMILES: {ethanol_smiles}")
    
    benzene_smiles = OrganicMoleculeBuilder.get_smiles('benzene')
    print(f"✓ Benzene SMILES: {benzene_smiles}")
    
    # Test SMILES to geometry
    geometry = OrganicMoleculeBuilder.smiles_to_geometry('CCO')
    print(f"\n✓ Ethanol geometry (first 5 atoms):")
    for atom in geometry[:5]:
        print(f"  - {atom[0]}: ({atom[1][0]:.2f}, {atom[1][1]:.2f}, {atom[1][2]:.2f})")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("TESTING NEW IMPROVEMENTS")
    print("="*60)
    
    try:
        test_quantum_feature_extractor()
        test_few_shot_examples()
        test_mechanism_classifier()
        test_smiles_parser()
        test_functional_groups()
        test_organic_reactions()
        test_organic_molecule_builder()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()


def test_caching_system():
    """Test result caching"""
    print("\n" + "="*60)
    print("TEST 8: Caching System")
    print("="*60)
    
    from backend.quantum_chemistry.result_cache import ResultCache, SmartCache
    
    cache = ResultCache(cache_dir='test_cache')
    
    # Test set and get
    test_data = {'energy': -1.137, 'electrons': 2}
    cache.set(['H', 'H'], test_data)
    
    retrieved = cache.get(['H', 'H'])
    print(f"\n✓ Cache set and retrieval:")
    print(f"  - Stored: {test_data}")
    print(f"  - Retrieved: {retrieved}")
    print(f"  - Match: {test_data == retrieved}")
    
    # Test stats
    stats = cache.get_stats()
    print(f"\n✓ Cache statistics:")
    print(f"  - Total entries: {stats['total_entries']}")
    print(f"  - Total size: {stats['total_size_bytes']} bytes")
    
    # Cleanup
    cache.clear()
    import shutil
    shutil.rmtree('test_cache', ignore_errors=True)


def test_ml_validator():
    """Test ML-based validator"""
    print("\n" + "="*60)
    print("TEST 9: ML Validator")
    print("="*60)
    
    from backend.quantum_chemistry.ml_validator import ReactionValidator
    
    validator = ReactionValidator()
    
    # Test H2 prediction
    elements = ['H', 'H']
    products = [{'formula': 'H2', 'name': 'Hydrogen', 'probability': 1.0}]
    quantum_features = {
        'stability_metrics': {'is_stable': True, 'electronic_binding_energy': -1.85},
        'electronic_features': {'homo_lumo_gap': 1.2, 'gap_category': 'stable'},
        'reactivity_indicators': {'is_radical': False}
    }
    
    result = validator.validate_prediction(elements, products, quantum_features)
    
    print(f"\n✓ Validation result:")
    print(f"  - Result: {result['result']}")
    print(f"  - Confidence: {result['confidence']:.2f}")
    print(f"  - Checks passed: {result['checks_passed']}")
    print(f"  - Warnings: {result['warnings']}")
    print(f"  - Recommendation: {result['recommendation']}")
    
    # Test statistics
    stats = validator.get_validation_stats()
    print(f"\n✓ Validation stats:")
    print(f"  - Total validations: {stats['total_validations']}")
    print(f"  - Pass rate: {stats['pass_rate']:.1%}")


if __name__ == '__main__':
    run_all_tests()
    test_caching_system()
    test_ml_validator()
