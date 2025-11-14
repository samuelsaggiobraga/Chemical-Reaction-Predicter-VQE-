"""
Quantum Feature Extractor - Preprocesses raw VQE/quantum data into chemically meaningful features
that are more useful for LLM-based reaction prediction
"""
import numpy as np
from typing import Dict, List, Any, Tuple


class QuantumFeatureExtractor:
    """Extract chemically meaningful features from quantum calculations"""
    
    def __init__(self):
        pass
    
    def extract_features(self, quantum_data: Dict[str, Any], elements: List[str]) -> Dict[str, Any]:
        """
        Convert raw quantum data into interpretable chemical features
        
        Args:
            quantum_data: Raw quantum calculation results
            elements: List of element symbols
            
        Returns:
            Dictionary of chemically meaningful features
        """
        features = {}
        
        # 1. Energy-based features
        features['stability_metrics'] = self._calculate_stability_metrics(quantum_data)
        
        # 2. Electronic structure features
        features['electronic_features'] = self._extract_electronic_features(quantum_data)
        
        # 3. Bond analysis
        features['bond_analysis'] = self._analyze_bonds(quantum_data)
        
        # 4. Reactivity indicators
        features['reactivity_indicators'] = self._calculate_reactivity_indicators(quantum_data, elements)
        
        # 5. Orbital analysis
        features['orbital_analysis'] = self._analyze_orbitals(quantum_data)
        
        # 6. Chemical interpretation summary
        features['interpretation'] = self._generate_interpretation(features)
        
        return features
    
    def _calculate_stability_metrics(self, qd: Dict) -> Dict[str, Any]:
        """Calculate molecular stability indicators"""
        vqe_energy = qd.get('vqe_energy', 0)
        hf_energy = qd.get('hf_energy', 0)
        nuclear_repulsion = qd.get('nuclear_repulsion', 0)
        
        # Electronic binding energy (more negative = more stable)
        electronic_energy = vqe_energy - nuclear_repulsion
        
        # Energy improvement from VQE vs HF (correlation energy)
        correlation_energy = hf_energy - vqe_energy
        
        # Relative stability metric
        stability_score = -electronic_energy / qd.get('num_electrons', 1)
        
        return {
            'electronic_binding_energy': float(electronic_energy),
            'correlation_energy': float(correlation_energy),
            'stability_score_per_electron': float(stability_score),
            'total_energy': float(vqe_energy),
            'is_stable': vqe_energy < 0,  # Negative energy indicates bound system
            'correlation_percentage': float(abs(correlation_energy / hf_energy * 100)) if hf_energy != 0 else 0
        }
    
    def _extract_electronic_features(self, qd: Dict) -> Dict[str, Any]:
        """Extract features related to electronic structure"""
        mo_energies = qd.get('mo_energies', [])
        orbital_occupations = qd.get('orbital_occupations', [])
        num_electrons = qd.get('num_electrons', 0)
        
        if not mo_energies:
            return {'error': 'No MO energy data available'}
        
        # HOMO-LUMO gap (key reactivity indicator)
        homo_lumo_gap = None
        homo_energy = None
        lumo_energy = None
        
        # Find HOMO (highest occupied) and LUMO (lowest unoccupied)
        if orbital_occupations:
            occupied_orbitals = [(i, e) for i, (e, occ) in enumerate(zip(mo_energies, orbital_occupations)) if occ > 0.5]
            unoccupied_orbitals = [(i, e) for i, (e, occ) in enumerate(zip(mo_energies, orbital_occupations)) if occ < 0.5]
            
            if occupied_orbitals:
                homo_idx, homo_energy = max(occupied_orbitals, key=lambda x: x[1])
            if unoccupied_orbitals:
                lumo_idx, lumo_energy = min(unoccupied_orbitals, key=lambda x: x[1])
            
            if homo_energy is not None and lumo_energy is not None:
                homo_lumo_gap = lumo_energy - homo_energy
        
        # Electron distribution analysis
        if orbital_occupations:
            total_occupation = sum(orbital_occupations)
            occupation_variance = float(np.var(orbital_occupations))
            max_occupation = max(orbital_occupations)
            min_occupation = min(orbital_occupations)
        else:
            total_occupation = num_electrons
            occupation_variance = 0
            max_occupation = 0
            min_occupation = 0
        
        return {
            'homo_energy': float(homo_energy) if homo_energy is not None else None,
            'lumo_energy': float(lumo_energy) if lumo_energy is not None else None,
            'homo_lumo_gap': float(homo_lumo_gap) if homo_lumo_gap is not None else None,
            'gap_category': self._categorize_gap(homo_lumo_gap) if homo_lumo_gap else 'unknown',
            'total_electrons': int(num_electrons),
            'electron_distribution_variance': float(occupation_variance),
            'is_closed_shell': num_electrons % 2 == 0,
            'orbital_occupation_range': [float(min_occupation), float(max_occupation)]
        }
    
    def _categorize_gap(self, gap: float) -> str:
        """Categorize HOMO-LUMO gap for reactivity"""
        if gap is None:
            return 'unknown'
        elif gap < 0.1:
            return 'highly_reactive'  # Small gap = high reactivity
        elif gap < 0.2:
            return 'reactive'
        elif gap < 0.3:
            return 'moderately_reactive'
        else:
            return 'stable'  # Large gap = low reactivity
    
    def _analyze_bonds(self, qd: Dict) -> Dict[str, Any]:
        """Analyze bond properties"""
        bond_lengths = qd.get('bond_lengths', {})
        
        if not bond_lengths:
            return {'bond_count': 0, 'bonds': []}
        
        bonds = []
        for bond_name, length in bond_lengths.items():
            # Parse bond name (e.g., "H1-H2")
            atoms = bond_name.split('-')
            
            # Classify bond type based on length (approximate)
            bond_type = self._classify_bond(atoms[0], atoms[1], length)
            
            bonds.append({
                'atoms': bond_name,
                'length_angstrom': float(length),
                'type': bond_type,
                'strength_category': self._bond_strength_category(length)
            })
        
        return {
            'bond_count': len(bonds),
            'bonds': bonds,
            'average_bond_length': float(np.mean([b['length_angstrom'] for b in bonds])),
            'bond_length_variance': float(np.var([b['length_angstrom'] for b in bonds]))
        }
    
    def _classify_bond(self, atom1: str, atom2: str, length: float) -> str:
        """Classify bond type based on atoms and length"""
        # Extract element symbols (remove numbers)
        elem1 = ''.join([c for c in atom1 if c.isalpha()])
        elem2 = ''.join([c for c in atom2 if c.isalpha()])
        
        # Approximate bond length ranges (Angstroms)
        if 'H' in [elem1, elem2]:
            if length < 1.0:
                return 'strong_single'
            elif length < 1.5:
                return 'single'
            else:
                return 'weak_single'
        else:
            if length < 1.2:
                return 'triple'
            elif length < 1.4:
                return 'double'
            elif length < 1.6:
                return 'aromatic_or_strong_single'
            elif length < 2.0:
                return 'single'
            else:
                return 'weak_or_ionic'
        
        return 'unclassified'
    
    def _bond_strength_category(self, length: float) -> str:
        """Categorize bond strength"""
        if length < 1.0:
            return 'very_strong'
        elif length < 1.5:
            return 'strong'
        elif length < 2.0:
            return 'moderate'
        else:
            return 'weak'
    
    def _calculate_reactivity_indicators(self, qd: Dict, elements: List[str]) -> Dict[str, Any]:
        """Calculate chemical reactivity indicators"""
        mo_energies = qd.get('mo_energies', [])
        num_electrons = qd.get('num_electrons', 0)
        vqe_energy = qd.get('vqe_energy', 0)
        
        # Electronegativity estimate (based on elements)
        electronegativities = {
            'H': 2.20, 'C': 2.55, 'N': 3.04, 'O': 3.44, 'F': 3.98,
            'Na': 0.93, 'Cl': 3.16, 'S': 2.58, 'P': 2.19, 'Li': 0.98
        }
        
        avg_electronegativity = np.mean([electronegativities.get(e, 2.0) for e in elements])
        
        # Radicalness indicator (odd electrons suggest radical character)
        is_radical = num_electrons % 2 == 1
        
        # Chemical hardness approximation (related to HOMO-LUMO gap)
        # Soft molecules are more reactive
        
        return {
            'is_radical': is_radical,
            'radical_character': 'high' if is_radical else 'none',
            'average_electronegativity': float(avg_electronegativity),
            'electronegativity_category': self._categorize_electronegativity(avg_electronegativity),
            'likely_electrophile': avg_electronegativity < 2.0,  # Low EN = electron donor
            'likely_nucleophile': avg_electronegativity > 3.0,   # High EN = electron acceptor
            'num_electrons': int(num_electrons),
            'electron_pair_availability': 'high' if not is_radical and avg_electronegativity > 2.5 else 'low'
        }
    
    def _categorize_electronegativity(self, en: float) -> str:
        """Categorize electronegativity"""
        if en < 1.5:
            return 'electropositive_metal'
        elif en < 2.5:
            return 'moderate'
        elif en < 3.5:
            return 'electronegative_nonmetal'
        else:
            return 'highly_electronegative'
    
    def _analyze_orbitals(self, qd: Dict) -> Dict[str, Any]:
        """Analyze molecular orbital properties"""
        mo_energies = qd.get('mo_energies', [])
        orbital_occupations = qd.get('orbital_occupations', [])
        
        if not mo_energies:
            return {'error': 'No orbital data'}
        
        # Count bonding vs antibonding (negative vs positive energies)
        bonding_orbitals = [e for e in mo_energies if e < 0]
        antibonding_orbitals = [e for e in mo_energies if e > 0]
        
        # Identify frontier orbitals (most reactive)
        sorted_energies = sorted(enumerate(mo_energies), key=lambda x: x[1])
        
        return {
            'num_bonding_orbitals': len(bonding_orbitals),
            'num_antibonding_orbitals': len(antibonding_orbitals),
            'bonding_character': 'strong' if len(bonding_orbitals) > len(antibonding_orbitals) else 'weak',
            'lowest_orbital_energy': float(mo_energies[sorted_energies[0][0]]) if sorted_energies else None,
            'highest_orbital_energy': float(mo_energies[sorted_energies[-1][0]]) if sorted_energies else None,
            'orbital_energy_spread': float(max(mo_energies) - min(mo_energies)) if mo_energies else 0
        }
    
    def _generate_interpretation(self, features: Dict) -> str:
        """Generate human-readable interpretation of quantum features"""
        lines = []
        
        # Stability interpretation
        stability = features.get('stability_metrics', {})
        if stability.get('is_stable'):
            lines.append(f"STABLE system (binding energy: {stability.get('electronic_binding_energy', 0):.3f} Ha)")
        else:
            lines.append(f"UNSTABLE system (positive energy indicates unbound state)")
        
        # Reactivity interpretation
        electronic = features.get('electronic_features', {})
        gap = electronic.get('homo_lumo_gap')
        if gap:
            lines.append(f"HOMO-LUMO gap: {gap:.3f} Ha → {electronic.get('gap_category', 'unknown')} reactivity")
        
        reactivity = features.get('reactivity_indicators', {})
        if reactivity.get('is_radical'):
            lines.append("RADICAL species → highly reactive, likely to form bonds")
        
        if reactivity.get('likely_nucleophile'):
            lines.append("NUCLEOPHILIC character → electron-rich, attacks positive centers")
        elif reactivity.get('likely_electrophile'):
            lines.append("ELECTROPHILIC character → electron-poor, attracts negative centers")
        
        # Bond interpretation
        bonds = features.get('bond_analysis', {})
        if bonds.get('bond_count', 0) > 0:
            lines.append(f"{bonds['bond_count']} bond(s) detected, avg length: {bonds.get('average_bond_length', 0):.3f} Å")
        
        return ' | '.join(lines)
