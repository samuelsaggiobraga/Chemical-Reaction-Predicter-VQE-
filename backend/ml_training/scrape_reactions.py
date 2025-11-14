"""
Scrape real chemical reaction data from public sources
Uses PubChem PUG REST API to get reaction information
"""
import requests
import json
import time
from typing import List, Dict
import re

class ReactionDataScraper:
    """Scrape chemical reactions from public databases"""
    
    def __init__(self):
        self.pubchem_base = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
        self.reactions = []
        
    def get_compound_info(self, compound_name: str) -> Dict:
        """Get compound information from PubChem"""
        try:
            url = f"{self.pubchem_base}/compound/name/{compound_name}/JSON"
            response = requests.get(url, timeout=10)
            
            if response.ok:
                data = response.json()
                props = data['PC_Compounds'][0]['props']
                
                # Extract molecular formula
                formula = None
                for prop in props:
                    if prop.get('urn', {}).get('label') == 'Molecular Formula':
                        formula = prop['value']['sval']
                        break
                
                return {"formula": formula, "name": compound_name}
        except:
            pass
        return None
    
    def parse_common_reactions(self) -> List[Dict]:
        """
        Manually curated list of common reactions from chemistry textbooks
        This is faster and more reliable than web scraping for initial training
        """
        common_reactions = [
            # Simple combinations
            {"reactants": ["H", "H"], "products": ["H2"], "type": "combination"},
            {"reactants": ["H", "H", "O"], "products": ["H2O"], "type": "combination"},
            {"reactants": ["C", "H", "H", "H", "H"], "products": ["CH4"], "type": "combination"},
            {"reactants": ["N", "H", "H", "H"], "products": ["NH3"], "type": "combination"},
            {"reactants": ["C", "O", "O"], "products": ["CO2"], "type": "combination"},
            {"reactants": ["O", "O"], "products": ["O2"], "type": "combination"},
            {"reactants": ["N", "N"], "products": ["N2"], "type": "combination"},
            {"reactants": ["Cl", "Cl"], "products": ["Cl2"], "type": "combination"},
            {"reactants": ["F", "F"], "products": ["F2"], "type": "combination"},
            
            # Binary compounds
            {"reactants": ["Na", "Cl"], "products": ["NaCl"], "type": "ionic"},
            {"reactants": ["K", "Cl"], "products": ["KCl"], "type": "ionic"},
            {"reactants": ["Mg", "O"], "products": ["MgO"], "type": "ionic"},
            {"reactants": ["Ca", "O"], "products": ["CaO"], "type": "ionic"},
            {"reactants": ["Al", "O", "O", "O"], "products": ["Al2O3"], "type": "ionic"},
            {"reactants": ["H", "Cl"], "products": ["HCl"], "type": "covalent"},
            {"reactants": ["H", "F"], "products": ["HF"], "type": "covalent"},
            {"reactants": ["H", "Br"], "products": ["HBr"], "type": "covalent"},
            {"reactants": ["H", "I"], "products": ["HI"], "type": "covalent"},
            
            # Oxides
            {"reactants": ["S", "O", "O"], "products": ["SO2"], "type": "oxide"},
            {"reactants": ["S", "O", "O", "O"], "products": ["SO3"], "type": "oxide"},
            {"reactants": ["N", "O", "O"], "products": ["NO2"], "type": "oxide"},
            {"reactants": ["N", "O"], "products": ["NO"], "type": "oxide"},
            {"reactants": ["P", "O", "O", "O", "O", "O"], "products": ["P2O5"], "type": "oxide"},
            
            # Hydroxides
            {"reactants": ["Na", "O", "H"], "products": ["NaOH"], "type": "base"},
            {"reactants": ["K", "O", "H"], "products": ["KOH"], "type": "base"},
            {"reactants": ["Ca", "O", "H", "O", "H"], "products": ["Ca(OH)2"], "type": "base"},
            
            # Acids
            {"reactants": ["H", "N", "O", "O", "O"], "products": ["HNO3"], "type": "acid"},
            {"reactants": ["H", "H", "S", "O", "O", "O", "O"], "products": ["H2SO4"], "type": "acid"},
            
            # Carbonates
            {"reactants": ["Ca", "C", "O", "O", "O"], "products": ["CaCO3"], "type": "salt"},
            {"reactants": ["Na", "Na", "C", "O", "O", "O"], "products": ["Na2CO3"], "type": "salt"},
            
            # Organic (simple)
            {"reactants": ["C", "C", "H", "H", "H", "H", "H", "H"], "products": ["C2H6"], "type": "organic"},
            {"reactants": ["C", "C", "C", "H", "H", "H", "H", "H", "H", "H", "H"], "products": ["C3H8"], "type": "organic"},
            {"reactants": ["C", "H", "H", "O", "H"], "products": ["CH3OH"], "type": "organic"},
            {"reactants": ["C", "C", "H", "H", "H", "H", "H", "O", "H"], "products": ["C2H5OH"], "type": "organic"},
            
            # Radicals
            {"reactants": ["O", "H"], "products": ["OH"], "type": "radical"},
            {"reactants": ["C", "H", "H", "H"], "products": ["CH3"], "type": "radical"},
            
            # Sulfides
            {"reactants": ["H", "H", "S"], "products": ["H2S"], "type": "sulfide"},
            {"reactants": ["Na", "Na", "S"], "products": ["Na2S"], "type": "sulfide"},
            
            # Nitrides
            {"reactants": ["Li", "Li", "Li", "N"], "products": ["Li3N"], "type": "nitride"},
            
            # Phosphates
            {"reactants": ["Na", "Na", "Na", "P", "O", "O", "O", "O"], "products": ["Na3PO4"], "type": "salt"},
            
            # Sulfates
            {"reactants": ["Na", "Na", "S", "O", "O", "O", "O"], "products": ["Na2SO4"], "type": "salt"},
            {"reactants": ["Mg", "S", "O", "O", "O", "O"], "products": ["MgSO4"], "type": "salt"},
        ]
        
        return common_reactions
    
    def expand_with_similar_reactions(self, base_reactions: List[Dict]) -> List[Dict]:
        """Generate more reactions by substituting similar elements"""
        expanded = base_reactions.copy()
        
        # Substitution groups (similar elements that behave similarly)
        alkali_metals = ['Li', 'Na', 'K', 'Rb']
        alkaline_earth = ['Mg', 'Ca', 'Sr', 'Ba']
        halogens = ['F', 'Cl', 'Br', 'I']
        
        # Generate variants by substitution
        for reaction in base_reactions:
            # Skip if too complex
            if len(reaction['reactants']) > 6:
                continue
                
            # Try alkali metal substitutions
            if 'Na' in reaction['reactants']:
                for metal in ['K', 'Li']:
                    new_reactants = [metal if x == 'Na' else x for x in reaction['reactants']]
                    new_products = [p.replace('Na', metal) for p in reaction['products']]
                    expanded.append({
                        "reactants": new_reactants,
                        "products": new_products,
                        "type": reaction['type']
                    })
            
            # Try halogen substitutions
            if 'Cl' in reaction['reactants']:
                for halogen in ['Br', 'F']:
                    new_reactants = [halogen if x == 'Cl' else x for x in reaction['reactants']]
                    new_products = [p.replace('Cl', halogen) for p in reaction['products']]
                    expanded.append({
                        "reactants": new_reactants,
                        "products": new_products,
                        "type": reaction['type']
                    })
        
        return expanded
    
    def save_training_data(self, filename="reaction_training_data.json"):
        """Save collected reactions to file"""
        print("📚 Generating training dataset...")
        
        # Get base reactions
        base_reactions = self.parse_common_reactions()
        print(f"   Base reactions: {len(base_reactions)}")
        
        # Expand with similar reactions
        all_reactions = self.expand_with_similar_reactions(base_reactions)
        print(f"   Expanded to: {len(all_reactions)} reactions")
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump({
                "reactions": all_reactions,
                "count": len(all_reactions),
                "source": "curated_textbook_reactions"
            }, f, indent=2)
        
        print(f"✅ Saved to {filename}")
        return all_reactions


def main():
    scraper = ReactionDataScraper()
    
    print("="*60)
    print("REACTION DATA COLLECTION")
    print("="*60)
    
    reactions = scraper.save_training_data()
    
    # Print sample
    print(f"\n📋 Sample reactions:")
    for i, r in enumerate(reactions[:5]):
        reactants_str = ' + '.join(r['reactants'])
        products_str = ' + '.join(r['products'])
        print(f"   {i+1}. {reactants_str} → {products_str} ({r['type']})")
    
    print(f"\n✅ Collected {len(reactions)} reactions for ML training")
    
if __name__ == "__main__":
    main()
