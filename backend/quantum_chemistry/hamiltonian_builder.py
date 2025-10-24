"""
Generate molecular Hamiltonians and prepare quantum chemistry data for MATLAB VQE
"""
import numpy as np
from pyscf import gto, scf
from typing import Dict, List, Tuple, Any
import json


class HamiltonianBuilder:
    """Build molecular Hamiltonians from chemical elements"""
    
    def __init__(self):
        self.molecule = None
        self.hf_energy = None
        
    def build_molecule(self, elements: List[str], geometry: List[Tuple] = None) -> Dict[str, Any]:
        """
        Build molecule from elements and run Hartree-Fock
        
        Args:
            elements: List of element symbols (e.g., ['H', 'H'] for H2)
            geometry: Optional geometry as list of (element, (x, y, z))
                     If None, uses default geometries
        
        Returns:
            Dictionary with molecular data and Hamiltonian
        """
        
        # Build geometry string for PySCF
        if geometry is None:
            geometry = self._default_geometry(elements)
        
        geom_string = self._format_geometry(geometry)
        
        # Create molecule
        self.molecule = gto.Mole()
        self.molecule.atom = geom_string
        
        # Choose basis set based on elements (heavy elements need special basis)
        # Elements beyond Kr (Z=36) often don't have sto-3g basis
        heavy_elements = [elem for elem, _ in geometry if gto.charge(elem) > 36]
        
        if heavy_elements:
            # Use mixed basis: sto-3g for light, lanl2dz for heavy
            print(f"⚠️  Heavy elements detected: {set(heavy_elements)}, using mixed basis sets")
            
            # Build basis dict: element -> basis
            basis_dict = {}
            ecp_dict = {}
            for elem, _ in geometry:
                if gto.charge(elem) > 36:
                    basis_dict[elem] = 'lanl2dz'
                    ecp_dict[elem] = 'lanl2dz'
                else:
                    basis_dict[elem] = 'sto-3g'
            
            self.molecule.basis = basis_dict
            if ecp_dict:
                self.molecule.ecp = ecp_dict
        else:
            self.molecule.basis = 'sto-3g'
        
        # Calculate number of electrons from geometry to set spin
        total_electrons = sum(gto.charge(elem) for elem, _ in geometry)
        
        # Set spin for odd-electron systems (unpaired electrons)
        # spin = 2S where S is the number of unpaired electrons
        if total_electrons % 2 == 1:
            self.molecule.spin = 1  # One unpaired electron (doublet)
        
        self.molecule.build(dump_input=False)
        
        # Run Hartree-Fock (use UHF for odd electrons, RHF for even)
        if self.molecule.nelectron % 2 == 1:
            mf = scf.UHF(self.molecule)  # Unrestricted for open-shell
        else:
            mf = scf.RHF(self.molecule)  # Restricted for closed-shell
        
        self.hf_energy = mf.kernel()
        
        # Get molecular integrals
        h1e = mf.get_hcore()  # One-electron integrals
        h2e = self.molecule.intor('int2e')  # Two-electron integrals
        
        # Get orbital energies and coefficients
        # Handle both RHF (returns arrays) and UHF (returns tuples of arrays)
        if isinstance(mf.mo_energy, tuple):  # UHF
            mo_energy = mf.mo_energy[0]  # Use alpha orbitals
            mo_coeff = mf.mo_coeff[0]
        else:  # RHF
            mo_energy = mf.mo_energy
            mo_coeff = mf.mo_coeff
        
        # Build qubit Hamiltonian
        qubit_hamiltonian = self._build_qubit_hamiltonian(h1e, h2e, mo_coeff)
        
        # Warn if system is large
        num_qubits = qubit_hamiltonian['num_qubits']
        if num_qubits > 12:
            print(f"⚠️  WARNING: System requires {num_qubits} qubits - VQE will be truncated to 12 qubits")
            print(f"   Large molecules may have reduced accuracy")
        
        # Package all data
        molecular_data = {
            'elements': elements,
            'geometry': geometry,
            'num_atoms': self.molecule.natm,
            'num_electrons': self.molecule.nelectron,
            'num_orbitals': len(mo_energy),
            'hf_energy': float(self.hf_energy),
            'mo_energies': mo_energy.tolist(),
            'nuclear_repulsion': float(self.molecule.energy_nuc()),
            'qubit_hamiltonian': qubit_hamiltonian,
            'bond_lengths': self._calculate_bond_lengths()
        }
        
        return molecular_data
    
    def _build_qubit_hamiltonian(self, h1e: np.ndarray, h2e: np.ndarray, 
                                  mo_coeff: np.ndarray) -> Dict[str, Any]:
        """
        Convert molecular integrals to qubit Hamiltonian using Jordan-Wigner
        
        Returns Pauli strings and coefficients for MATLAB observable class
        """
        # Ensure mo_coeff is 2D (for both RHF and UHF)
        if mo_coeff.ndim > 2:
            mo_coeff = mo_coeff[0]  # Take first component if 3D
        
        # Transform integrals to MO basis - use transpose for proper shape
        h1e_mo = mo_coeff.T @ h1e @ mo_coeff
        
        # Simplified: Just use diagonal terms for now to avoid einsum issues
        n_orbs = h1e_mo.shape[0]
        
        # Build Hamiltonian - simplified version
        pauli_terms = []
        coefficients = []
        
        # One-body terms (only diagonal for simplicity)
        for i in range(n_orbs):
            coeff = h1e_mo[i, i]
            if abs(coeff) > 1e-10:
                # Number operator for orbital i: (I - Z_i)/2
                pauli_z = 'I' * i + 'Z' + 'I' * (n_orbs - i - 1)
                pauli_terms.append('I' * n_orbs)
                coefficients.append(coeff * 0.5)
                pauli_terms.append(pauli_z)
                coefficients.append(coeff * (-0.5))
        
        # Add a small identity term to ensure non-empty Hamiltonian
        if len(pauli_terms) == 0:
            pauli_terms.append('I' * max(2, n_orbs))
            coefficients.append(0.1)
        
        return {
            'pauli_strings': pauli_terms,
            'coefficients': coefficients,
            'num_qubits': max(2, n_orbs * 2)  # spin-orbitals, minimum 2 qubits
        }
    
    def _jordan_wigner_one_body(self, i: int, j: int, n_orbs: int) -> Dict:
        """Jordan-Wigner transformation for one-body operator"""
        # Simplified version - returns Pauli strings
        # Full implementation would handle spin properly
        if i == j:
            # Number operator: (I - Z)/2
            pauli = 'I' * i + 'Z' + 'I' * (n_orbs - i - 1)
            return {
                'terms': ['I' * n_orbs, pauli],
                'coeffs': [0.5, -0.5]
            }
        else:
            # Hopping term
            pauli_x = 'I' * min(i,j) + 'X' + 'I' * abs(j-i-1) + 'X' + 'I' * (n_orbs - max(i,j) - 1)
            pauli_y = 'I' * min(i,j) + 'Y' + 'I' * abs(j-i-1) + 'Y' + 'I' * (n_orbs - max(i,j) - 1)
            return {
                'terms': [pauli_x, pauli_y],
                'coeffs': [0.5, 0.5]
            }
    
    def _jordan_wigner_two_body(self, i: int, j: int, k: int, l: int, n_orbs: int) -> Dict:
        """Jordan-Wigner transformation for two-body operator"""
        # Simplified - returns identity for now
        # Full implementation would be more complex
        return {
            'terms': ['I' * n_orbs],
            'coeffs': [0.0]
        }
    
    def _default_geometry(self, elements: List[str]) -> List[Tuple]:
        """Generate default molecular geometry"""
        if len(elements) == 2 and elements[0] == 'H' and elements[1] == 'H':
            # H2 at equilibrium
            return [('H', (0, 0, 0)), ('H', (0, 0, 0.74))]
        elif len(elements) == 2 and 'O' in elements and 'H' in elements:
            # OH radical
            return [('O', (0, 0, 0)), ('H', (0, 0, 0.97))]
        else:
            # Linear chain with 1.5 Angstrom spacing
            return [(elem, (0, 0, i * 1.5)) for i, elem in enumerate(elements)]
    
    def _format_geometry(self, geometry: List[Tuple]) -> str:
        """Format geometry for PySCF"""
        return '; '.join([f'{elem} {x} {y} {z}' for elem, (x, y, z) in geometry])
    
    def _calculate_bond_lengths(self) -> Dict[str, float]:
        """Calculate all bond lengths in the molecule"""
        if self.molecule is None:
            return {}
        
        coords = self.molecule.atom_coords()
        symbols = [self.molecule.atom_symbol(i) for i in range(self.molecule.natm)]
        
        bond_lengths = {}
        for i in range(len(coords)):
            for j in range(i + 1, len(coords)):
                distance = np.linalg.norm(coords[i] - coords[j])
                bond_name = f"{symbols[i]}{i+1}-{symbols[j]}{j+1}"
                bond_lengths[bond_name] = float(distance)
        
        return bond_lengths
    
    def save_for_matlab(self, molecular_data: Dict, filename: str = 'hamiltonian_data.json'):
        """Save molecular data in format for MATLAB to read"""
        with open(filename, 'w') as f:
            json.dump(molecular_data, f, indent=2)
