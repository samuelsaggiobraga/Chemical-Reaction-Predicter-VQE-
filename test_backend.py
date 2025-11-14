#!/usr/bin/env python3
"""
Test script to debug the backend without MATLAB
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.quantum_chemistry.hamiltonian_builder import HamiltonianBuilder

def test_molecule(elements):
    print(f"\n{'='*60}")
    print(f"Testing: {' + '.join(elements)}")
    print(f"{'='*60}")
    
    try:
        builder = HamiltonianBuilder()
        result = builder.build_molecule(elements)
        
        print(f"✅ SUCCESS!")
        print(f"   HF Energy: {result['hf_energy']:.6f} Ha")
        print(f"   Electrons: {result['num_electrons']}")
        print(f"   Orbitals: {result['num_orbitals']}")
        print(f"   Qubits needed: {result['qubit_hamiltonian']['num_qubits']}")
        print(f"   Pauli terms: {len(result['qubit_hamiltonian']['pauli_strings'])}")
        print(f"   Nuclear repulsion: {result['nuclear_repulsion']:.6f} Ha")
        print(f"   Bond lengths: {result['bond_lengths']}")
        return True
        
    except Exception as e:
        print(f"❌ FAILED!")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("\n" + "="*60)
    print("BACKEND DEBUGGING - Testing Quantum Chemistry")
    print("="*60)
    
    test_cases = [
        ['H', 'H'],      # Simple diatomic
        ['H'],           # Single atom (odd electrons)
        ['Li'],          # Odd electrons
        ['He', 'He'],    # Noble gas
        ['H', 'O'],      # Mixed
    ]
    
    passed = 0
    failed = 0
    
    for elements in test_cases:
        if test_molecule(elements):
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"RESULTS: {passed} passed, {failed} failed")
    print(f"{'='*60}\n")
    
    sys.exit(0 if failed == 0 else 1)
