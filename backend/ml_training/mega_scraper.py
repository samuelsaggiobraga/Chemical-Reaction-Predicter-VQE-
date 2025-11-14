#!/usr/bin/env python3
"""
Mega scraper for 50,000+ diverse chemical reactions
Includes: common, rare, organic, inorganic, transition metals, noble gases
"""

import json
from typing import List, Dict
from collections import Counter

class MegaReactionScraper:
    """Generate massive diverse reaction dataset"""
    
    def __init__(self):
        self.reactions = []
    
    def generate_all_reactions(self):
        """Generate comprehensive reaction database"""
        print("🌐 MEGA REACTION DATABASE GENERATION")
        print("=" * 70)
        
        # 1. Common reactions (high weight)
        print("\n1️⃣  Common reactions...")
        self.reactions.extend(self._generate_common_reactions())
        
        # 2. Organic chemistry (large molecules)
        print("2️⃣  Organic chemistry...")
        self.reactions.extend(self._generate_organic_reactions())
        
        # 3. Inorganic chemistry (all combinations)
        print("3️⃣  Inorganic chemistry...")
        self.reactions.extend(self._generate_inorganic_reactions())
        
        # 4. Transition metal complexes
        print("4️⃣  Transition metal complexes...")
        self.reactions.extend(self._generate_transition_metal_complexes())
        
        # 5. Noble gas compounds (rare but real)
        print("5️⃣  Noble gas compounds...")
        self.reactions.extend(self._generate_noble_gas_compounds())
        
        # 6. Ambiguous/multi-product reactions
        print("6️⃣  Ambiguous reactions...")
        self.reactions.extend(self._generate_ambiguous_reactions())
        
        print(f"\n✅ Generated {len(self.reactions)} total reactions")
        return self.reactions
    
    def _generate_common_reactions(self) -> List[Dict]:
        """Top 100 most common reactions with very high weights"""
        reactions = []
        
        common = [
            # Diatomics (1000x weight for 50K scale)
            (['H','H'], 'H2', 1000),
            (['O','O'], 'O2', 1000),
            (['N','N'], 'N2', 1000),
            (['F','F'], 'F2', 600),
            (['Cl','Cl'], 'Cl2', 600),
            (['Br','Br'], 'Br2', 400),
            (['I','I'], 'I2', 400),
            
            # Critical compounds (1500x)
            (['H','H','O'], 'H2O', 1500),
            (['C','H','H','H','H'], 'CH4', 1200),
            (['C','O','O'], 'CO2', 1200),
            (['N','H','H','H'], 'NH3', 1000),
            (['Na','Cl'], 'NaCl', 900),
            (['H','Cl'], 'HCl', 800),
            (['C','O'], 'CO', 800),
            
            # Common inorganics (500-700x)
            (['S','O','O'], 'SO2', 700),
            (['H','H','S'], 'H2S', 500),
            (['N','O','O'], 'NO2', 500),
            (['N','O'], 'NO', 400),
            (['S','O','O','O'], 'SO3', 350),
            (['P','O','O','O','O'], 'P2O5', 300),
        ]
        
        for reactants, product, weight in common:
            for _ in range(weight):
                reactions.append({
                    'reactants': reactants,
                    'products': [product],
                    'type': 'common',
                    'difficulty': 'easy'
                })
        
        print(f"   Generated {len(reactions)} common reactions")
        return reactions
    
    def _generate_organic_reactions(self) -> List[Dict]:
        """Comprehensive organic chemistry C1-C20"""
        reactions = []
        
        # Alkanes C1-C20 (with isomers) - scale up 3x
        for n in range(1, 21):
            c, h = n, 2*n+2
            weight = max(300 - n*10, 30)  # More weight for smaller molecules
            
            # Linear alkane
            for _ in range(weight):
                formula = f"C{c}H{h}" if c > 1 else f"CH{h}"
                reactions.append({
                    'reactants': ['C']*c + ['H']*h,
                    'products': [formula],
                    'type': 'alkane',
                    'difficulty': 'easy' if n <= 4 else 'medium'
                })
            
            # Branched isomers for C4+
            if n >= 4:
                for _ in range(weight // 2):
                    reactions.append({
                        'reactants': ['C']*c + ['H']*h,
                        'products': [f"C{c}H{h}_iso"],  # Isomer notation
                        'type': 'alkane_branched',
                        'difficulty': 'medium'
                    })
        
        # Alkenes C2-C15 - scale up 3x
        for n in range(2, 16):
            c, h = n, 2*n
            weight = max(240 - n*10, 30)
            for _ in range(weight):
                reactions.append({
                    'reactants': ['C']*c + ['H']*h,
                    'products': [f"C{c}H{h}"],
                    'type': 'alkene',
                    'difficulty': 'medium'
                })
        
        # Alcohols C1-C10 - scale up 3x
        for n in range(1, 11):
            c, h, o = n, 2*n+2, 1
            weight = max(300 - n*20, 60)
            for _ in range(weight):
                formula = f"C{c}H{h}O" if c > 1 else f"CH{h}O"
                reactions.append({
                    'reactants': ['C']*c + ['H']*h + ['O']*o,
                    'products': [formula],
                    'type': 'alcohol',
                    'difficulty': 'medium'
                })
        
        # Carboxylic acids C1-C10
        for n in range(1, 11):
            c, h, o = n, 2*n, 2
            weight = max(80 - n*6, 15)
            for _ in range(weight):
                formula = f"C{c}H{h}O2" if c > 1 else f"CH{h}O2"
                reactions.append({
                    'reactants': ['C']*c + ['H']*h + ['O']*o,
                    'products': [formula],
                    'type': 'carboxylic_acid',
                    'difficulty': 'medium'
                })
        
        # Aromatic compounds
        aromatics = [
            (['C']*6 + ['H']*6, 'C6H6', 80, 'benzene'),  # Benzene
            (['C']*7 + ['H']*8, 'C7H8', 60, 'toluene'),  # Toluene
            (['C']*8 + ['H']*10, 'C8H10', 40, 'xylene'), # Xylene
            (['C']*10 + ['H']*8, 'C10H8', 50, 'naphthalene'),  # Naphthalene
        ]
        
        for reactants, product, weight, name in aromatics:
            for _ in range(weight):
                reactions.append({
                    'reactants': reactants,
                    'products': [product],
                    'type': 'aromatic',
                    'difficulty': 'hard'
                })
        
        print(f"   Generated {len(reactions)} organic reactions")
        return reactions
    
    def _generate_inorganic_reactions(self) -> List[Dict]:
        """All metal + nonmetal combinations"""
        reactions = []
        
        metals = ['Li','Na','K','Rb','Cs','Be','Mg','Ca','Sr','Ba',
                 'Al','Ga','Zn','Cd','Sn','Pb','Ag','Cu','Fe','Ni','Co']
        nonmetals = ['F','Cl','Br','I','O','S','N','P','H']
        
        for metal in metals:
            for nonmetal in nonmetals:
                # Common oxidation states
                for ratio_m, ratio_n in [(1,1), (2,1), (1,2), (1,3), (3,2)]:
                    weight = 15 if metal in ['Na','K','Ca','Mg','Fe','Cu','Zn'] else 8
                    
                    for _ in range(weight):
                        formula = f"{metal}{ratio_m if ratio_m>1 else ''}{nonmetal}{ratio_n if ratio_n>1 else ''}"
                        reactions.append({
                            'reactants': [metal]*ratio_m + [nonmetal]*ratio_n,
                            'products': [formula],
                            'type': 'binary_inorganic',
                            'difficulty': 'easy'
                        })
        
        print(f"   Generated {len(reactions)} inorganic reactions")
        return reactions
    
    def _generate_transition_metal_complexes(self) -> List[Dict]:
        """Coordination complexes and organometallics"""
        reactions = []
        
        # Metal carbonyls
        carbonyls = [
            (['Fe'] + ['C','O']*5, 'Fe(CO)5', 50),
            (['Ni'] + ['C','O']*4, 'Ni(CO)4', 50),
            (['Cr'] + ['C','O']*6, 'Cr(CO)6', 40),
            (['Mo'] + ['C','O']*6, 'Mo(CO)6', 30),
            (['W'] + ['C','O']*6, 'W(CO)6', 30),
            (['Co'] + ['C','O']*4, 'Co2(CO)8', 30),
        ]
        
        for reactants, product, weight in carbonyls:
            for _ in range(weight):
                reactions.append({
                    'reactants': reactants,
                    'products': [product],
                    'type': 'metal_carbonyl',
                    'difficulty': 'hard'
                })
        
        # Metal halides
        metals = ['Fe','Co','Ni','Cu','Zn','Cr','Mn','Ti','V']
        halogens = ['F','Cl','Br','I']
        
        for metal in metals:
            for halogen in halogens:
                for n in [2, 3]:
                    weight = 20 if metal in ['Fe','Cu','Zn'] else 10
                    for _ in range(weight):
                        reactions.append({
                            'reactants': [metal] + [halogen]*n,
                            'products': [f"{metal}{halogen}{n}"],
                            'type': 'metal_halide',
                            'difficulty': 'medium'
                        })
        
        print(f"   Generated {len(reactions)} transition metal reactions")
        return reactions
    
    def _generate_noble_gas_compounds(self) -> List[Dict]:
        """Rare but real noble gas compounds"""
        reactions = []
        
        noble_gas_compounds = [
            (['Xe','F','F'], 'XeF2', 40),
            (['Xe','F','F','F','F'], 'XeF4', 40),
            (['Xe','F','F','F','F','F','F'], 'XeF6', 30),
            (['Kr','F','F'], 'KrF2', 30),
            (['Xe','O','O','O'], 'XeO3', 25),
            (['Xe','O','O','O','O'], 'XeO4', 20),
            (['Rn','F','F'], 'RnF2', 15),
        ]
        
        for reactants, product, weight in noble_gas_compounds:
            for _ in range(weight):
                reactions.append({
                    'reactants': reactants,
                    'products': [product],
                    'type': 'noble_gas',
                    'difficulty': 'hard'
                })
        
        print(f"   Generated {len(reactions)} noble gas reactions")
        return reactions
    
    def _generate_ambiguous_reactions(self) -> List[Dict]:
        """Reactions with multiple possible products"""
        reactions = []
        
        # These will have multiple product possibilities
        ambiguous = [
            # Could form CH3OH or CH2O + H2
            (['C','H','H','H','O'], ['CH4O', 'CH2O'], 50),
            # Could form C2H6O or C2H4O2
            (['C','C','H','H','H','H','O'], ['C2H6O', 'C2H4O'], 50),
            # Combustion - multiple CO/CO2 ratios
            (['C','C','O','O','O'], ['CO2', 'CO'], 40),
        ]
        
        for reactants, products, weight in ambiguous:
            for _ in range(weight):
                # Add reaction for each possible product
                for product in products:
                    reactions.append({
                        'reactants': reactants,
                        'products': [product],
                        'type': 'ambiguous',
                        'difficulty': 'hard',
                        'note': f'Competes with {products}'
                    })
        
        print(f"   Generated {len(reactions)} ambiguous reactions")
        return reactions
    
    def save_dataset(self, filename='mega_training_data.json'):
        """Save massive dataset"""
        unique_products = set(r['products'][0] for r in self.reactions)
        
        # Count by difficulty
        difficulty_counts = Counter(r.get('difficulty', 'unknown') for r in self.reactions)
        
        data = {
            'reactions': self.reactions,
            'count': len(self.reactions),
            'unique_products': len(unique_products),
            'difficulty_distribution': dict(difficulty_counts),
            'generated_at': '2024-11-14'
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n{'='*70}")
        print(f"💾 Saved {len(self.reactions)} reactions to {filename}")
        print(f"   Unique products: {len(unique_products)}")
        print(f"   Difficulty: {dict(difficulty_counts)}")
        print(f"   Avg samples/product: {len(self.reactions)/len(unique_products):.1f}")
        print(f"{'='*70}")

if __name__ == '__main__':
    scraper = MegaReactionScraper()
    scraper.generate_all_reactions()
    scraper.save_dataset()
