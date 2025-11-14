"""
Organic Chemistry Module - SMILES parsing, functional group detection, and organic reaction mechanisms
"""
import re
from typing import Dict, List, Tuple, Set, Any
from collections import defaultdict


class SMILESParser:
    """Parse SMILES strings and extract molecular information"""
    
    # Atomic symbols (organic subset)
    ORGANIC_ATOMS = ['C', 'N', 'O', 'P', 'S', 'F', 'Cl', 'Br', 'I', 'H']
    
    def __init__(self):
        pass
    
    def parse(self, smiles: str) -> Dict[str, Any]:
        """
        Parse SMILES string and extract molecular information
        
        Args:
            smiles: SMILES string (e.g., 'CCO' for ethanol)
            
        Returns:
            Dictionary with molecular formula, atoms, bonds, etc.
        """
        # Remove spaces and validate
        smiles = smiles.strip().replace(' ', '')
        
        atoms = []
        bonds = []
        rings = defaultdict(list)
        branches = []
        
        i = 0
        atom_idx = 0
        prev_atom_idx = None
        
        while i < len(smiles):
            char = smiles[i]
            
            # Branch opening
            if char == '(':
                branches.append(prev_atom_idx)
                i += 1
                continue
            
            # Branch closing
            elif char == ')':
                if branches:
                    prev_atom_idx = branches.pop()
                i += 1
                continue
            
            # Ring number
            elif char.isdigit():
                ring_num = int(char)
                if ring_num in rings and len(rings[ring_num]) == 1:
                    # Close ring
                    bonds.append((rings[ring_num][0], prev_atom_idx, 'single'))
                    del rings[ring_num]
                else:
                    # Open ring
                    rings[ring_num].append(prev_atom_idx)
                i += 1
                continue
            
            # Bond notation
            elif char in ['=', '#', '-']:
                bond_type = {'=': 'double', '#': 'triple', '-': 'single'}[char]
                i += 1
                continue
            else:
                bond_type = 'single'
            
            # Atom
            if char == '[':
                # Bracketed atom
                end = smiles.find(']', i)
                atom_str = smiles[i+1:end]
                element = self._parse_bracketed_atom(atom_str)
                i = end + 1
            elif char.isupper():
                # Organic subset atom
                if i + 1 < len(smiles) and smiles[i+1].islower():
                    element = char + smiles[i+1]
                    i += 2
                else:
                    element = char
                    i += 1
            else:
                i += 1
                continue
            
            atoms.append({
                'index': atom_idx,
                'element': element,
                'implicit_h': self._count_implicit_hydrogens(element, len([b for b in bonds if atom_idx in b[:2]]))
            })
            
            # Add bond to previous atom
            if prev_atom_idx is not None:
                bonds.append((prev_atom_idx, atom_idx, bond_type))
            
            prev_atom_idx = atom_idx
            atom_idx += 1
        
        molecular_formula = self._calculate_formula(atoms)
        
        return {
            'smiles': smiles,
            'atoms': atoms,
            'bonds': bonds,
            'molecular_formula': molecular_formula,
            'num_atoms': len(atoms),
            'num_bonds': len(bonds),
            'has_rings': len(rings) == 0 and any('ring' in b for b in bonds)
        }
    
    def _parse_bracketed_atom(self, atom_str: str) -> str:
        """Parse bracketed atom notation like [OH], [NH3+], etc."""
        # Extract element symbol
        element = ''.join([c for c in atom_str if c.isalpha()])
        return element
    
    def _count_implicit_hydrogens(self, element: str, num_bonds: int) -> int:
        """Count implicit hydrogens based on element and bonding"""
        valences = {'C': 4, 'N': 3, 'O': 2, 'P': 3, 'S': 2, 'F': 1, 'Cl': 1, 'Br': 1, 'I': 1}
        valence = valences.get(element, 0)
        return max(0, valence - num_bonds)
    
    def _calculate_formula(self, atoms: List[Dict]) -> str:
        """Calculate molecular formula from atoms"""
        element_counts = defaultdict(int)
        
        for atom in atoms:
            element_counts[atom['element']] += 1
            element_counts['H'] += atom['implicit_h']
        
        # Sort by Hill system (C, H, then alphabetical)
        formula_parts = []
        if 'C' in element_counts:
            formula_parts.append(f"C{element_counts['C']}" if element_counts['C'] > 1 else 'C')
            del element_counts['C']
        if 'H' in element_counts:
            formula_parts.append(f"H{element_counts['H']}" if element_counts['H'] > 1 else 'H')
            del element_counts['H']
        
        for elem in sorted(element_counts.keys()):
            count = element_counts[elem]
            formula_parts.append(f"{elem}{count}" if count > 1 else elem)
        
        return ''.join(formula_parts)


class FunctionalGroupDetector:
    """Detect functional groups in molecules"""
    
    # Functional group SMARTS patterns (simplified)
    FUNCTIONAL_GROUPS = {
        'alcohol': r'O[H]?',
        'aldehyde': r'C=O',
        'ketone': r'C(=O)C',
        'carboxylic_acid': r'C(=O)O[H]?',
        'ester': r'C(=O)O',
        'amine': r'N[H]?',
        'amide': r'C(=O)N',
        'alkene': r'C=C',
        'alkyne': r'C#C',
        'aromatic': r'c',  # lowercase indicates aromatic
        'halide': r'[F,Cl,Br,I]',
        'thiol': r'S[H]?',
        'ether': r'COC',
        'nitrile': r'C#N',
        'nitro': r'N(=O)=O'
    }
    
    def detect(self, smiles: str) -> List[str]:
        """
        Detect functional groups in SMILES string
        
        Args:
            smiles: SMILES string
            
        Returns:
            List of detected functional group names
        """
        detected = []
        
        # Simple pattern matching (can be improved with proper SMARTS)
        for group, pattern in self.FUNCTIONAL_GROUPS.items():
            if self._contains_pattern(smiles, pattern):
                detected.append(group)
        
        return detected
    
    def _contains_pattern(self, smiles: str, pattern: str) -> bool:
        """Check if SMILES contains pattern (simplified)"""
        # This is a very simplified version - proper implementation would use RDKit
        return pattern.replace('[', '').replace(']', '').replace('?', '') in smiles


class OrganicReactionClassifier:
    """Classify organic reaction types"""
    
    REACTION_TYPES = {
        'substitution_nucleophilic': {
            'description': 'Nucleophile replaces leaving group',
            'requires': ['leaving_group', 'nucleophile'],
            'examples': ['R-X + Nu⁻ → R-Nu + X⁻']
        },
        'substitution_electrophilic': {
            'description': 'Electrophile replaces H on aromatic ring',
            'requires': ['aromatic', 'electrophile'],
            'examples': ['Ar-H + E⁺ → Ar-E + H⁺']
        },
        'addition': {
            'description': 'Addition to C=C or C=O',
            'requires': ['unsaturated_bond'],
            'examples': ['C=C + H2 → C-C']
        },
        'elimination': {
            'description': 'Formation of C=C with loss of small molecule',
            'requires': ['beta_hydrogen', 'leaving_group'],
            'examples': ['R-CH2-CH2-X + Base → R-CH=CH2 + HX']
        },
        'oxidation': {
            'description': 'Increase in oxidation state',
            'requires': ['alcohol', 'aldehyde', 'or_ketone'],
            'examples': ['R-OH → R=O']
        },
        'reduction': {
            'description': 'Decrease in oxidation state',
            'requires': ['carbonyl', 'or_carboxylic_acid'],
            'examples': ['R=O → R-OH']
        },
        'condensation': {
            'description': 'Two molecules combine with loss of water',
            'requires': ['carbonyl', 'amine_or_alcohol'],
            'examples': ['R-COOH + R-NH2 → R-CO-NH-R + H2O']
        },
        'esterification': {
            'description': 'Carboxylic acid + alcohol → ester',
            'requires': ['carboxylic_acid', 'alcohol'],
            'examples': ['R-COOH + R-OH → R-COO-R + H2O']
        }
    }
    
    def predict_mechanism(self, functional_groups: List[str], quantum_features: Dict) -> Dict[str, Any]:
        """
        Predict likely reaction mechanism based on functional groups and quantum data
        
        Args:
            functional_groups: List of detected functional groups
            quantum_features: Quantum mechanical features
            
        Returns:
            Dictionary with mechanism predictions
        """
        predictions = []
        
        # Check for substitution reactions
        if 'halide' in functional_groups:
            if quantum_features.get('reactivity_indicators', {}).get('likely_nucleophile'):
                predictions.append({
                    'type': 'substitution_nucleophilic',
                    'confidence': 0.8,
                    'description': 'SN2 or SN1 nucleophilic substitution likely due to halide leaving group'
                })
        
        # Check for addition reactions
        if 'alkene' in functional_groups or 'alkyne' in functional_groups:
            predictions.append({
                'type': 'addition',
                'confidence': 0.7,
                'description': 'Addition to unsaturated bond possible'
            })
        
        # Check for elimination reactions
        if 'halide' in functional_groups and quantum_features.get('stability_metrics', {}).get('is_stable'):
            predictions.append({
                'type': 'elimination',
                'confidence': 0.6,
                'description': 'E2 or E1 elimination possible with strong base'
            })
        
        # Check for oxidation/reduction
        if 'alcohol' in functional_groups:
            predictions.append({
                'type': 'oxidation',
                'confidence': 0.7,
                'description': 'Alcohol can be oxidized to aldehyde/ketone or carboxylic acid'
            })
        
        if 'aldehyde' in functional_groups or 'ketone' in functional_groups:
            predictions.append({
                'type': 'reduction',
                'confidence': 0.7,
                'description': 'Carbonyl can be reduced to alcohol'
            })
        
        # Check for condensation
        if 'carboxylic_acid' in functional_groups and 'amine' in functional_groups:
            predictions.append({
                'type': 'condensation',
                'confidence': 0.9,
                'description': 'Amide formation via condensation reaction'
            })
        
        if 'carboxylic_acid' in functional_groups and 'alcohol' in functional_groups:
            predictions.append({
                'type': 'esterification',
                'confidence': 0.9,
                'description': 'Ester formation (Fischer esterification)'
            })
        
        # Sort by confidence
        predictions.sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            'predicted_mechanisms': predictions[:3],  # Top 3
            'functional_groups_present': functional_groups,
            'most_likely_mechanism': predictions[0] if predictions else None
        }


class OrganicMoleculeBuilder:
    """Build organic molecules from common names or SMILES"""
    
    COMMON_MOLECULES = {
        'methane': 'C',
        'ethane': 'CC',
        'propane': 'CCC',
        'butane': 'CCCC',
        'methanol': 'CO',
        'ethanol': 'CCO',
        'propanol': 'CCCO',
        'acetone': 'CC(=O)C',
        'acetic_acid': 'CC(=O)O',
        'benzene': 'c1ccccc1',
        'toluene': 'Cc1ccccc1',
        'phenol': 'Oc1ccccc1',
        'aniline': 'Nc1ccccc1',
        'acetaldehyde': 'CC=O',
        'formaldehyde': 'C=O',
        'ethylene': 'C=C',
        'acetylene': 'C#C',
        'chloromethane': 'CCl',
        'dichloromethane': 'C(Cl)Cl',
        'chloroform': 'C(Cl)(Cl)Cl',
        'methylamine': 'CN',
        'dimethylamine': 'CNC',
        'trimethylamine': 'CN(C)C'
    }
    
    @classmethod
    def get_smiles(cls, name: str) -> str:
        """Get SMILES string for common molecule name"""
        return cls.COMMON_MOLECULES.get(name.lower())
    
    @classmethod
    def smiles_to_geometry(cls, smiles: str) -> List[Tuple]:
        """
        Convert SMILES to 3D geometry (simplified - returns approximate coordinates)
        
        Args:
            smiles: SMILES string
            
        Returns:
            List of (element, (x, y, z)) tuples
        """
        parser = SMILESParser()
        parsed = parser.parse(smiles)
        
        # Simple linear geometry as placeholder
        # (Proper implementation would use RDKit or Open Babel for 3D coordinate generation)
        geometry = []
        spacing = 1.5  # Angstroms
        
        for i, atom in enumerate(parsed['atoms']):
            element = atom['element']
            # Linear arrangement as placeholder
            geometry.append((element, (i * spacing, 0.0, 0.0)))
            
            # Add explicit hydrogens
            for j in range(atom['implicit_h']):
                geometry.append(('H', (i * spacing, (j+1) * 1.0, 0.5)))
        
        return geometry
