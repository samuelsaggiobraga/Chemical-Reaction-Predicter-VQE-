#!/usr/bin/env python3
"""
Focused reaction scraper - ONLY the most common reactions with HIGH repetition
Goal: 5000+ samples from ~100 unique products = 50+ samples/product
"""

import json

def generate_focused_dataset():
    """Generate dataset focused on top 100 most common chemical reactions"""
    reactions = []
    
    # TOP 50 MOST COMMON COMPOUNDS with massive weights
    # Format: (reactants_list, product, weight)
    common_reactions = [
        # ===== Top 10 - CRITICAL (500-300 samples each) =====
        (['H', 'H', 'O'], 'H2O', 600),
        (['H', 'H'], 'H2', 500),
        (['O', 'O'], 'O2', 500),
        (['N', 'N'], 'N2', 500),
        (['C','H','H','H','H'], 'CH4', 400),
        (['C','O','O'], 'CO2', 400),
        (['N','H','H','H'], 'NH3', 350),
        (['C','O'], 'CO', 300),
        (['Na','Cl'], 'NaCl', 300),
        (['H','Cl'], 'HCl', 300),
        
        # ===== Common 11-30 (200-100 samples) =====
        (['S','O','O'], 'SO2', 250),
        (['H','H','S'], 'H2S', 200),
        (['N','O','O'], 'NO2', 200),
        (['N','O'], 'NO', 150),
        (['H','F'], 'HF', 150),
        (['H','Br'], 'HBr', 150),
        (['H','I'], 'HI', 150),
        (['F','F'], 'F2', 150),
        (['Cl','Cl'], 'Cl2', 150),
        (['Br','Br'], 'Br2', 120),
        (['I','I'], 'I2', 120),
        (['K','Cl'], 'KCl', 150),
        (['Ca','O'], 'CaO', 130),
        (['Mg','O'], 'MgO', 130),
        (['Fe','O'], 'FeO', 110),
        (['Cu','O'], 'CuO', 100),
        (['Na','O','H'], 'NaOH', 130),
        (['S','O','O','O'], 'SO3', 100),
        (['Ca','C','O','O','O'], 'CaCO3', 120),
        (['C','H','H'], 'CH2', 80),
        
        # ===== Common 31-60 (80-50 samples) =====
        (['Mg','Cl','Cl'], 'MgCl2', 80),
        (['Al','Cl','Cl','Cl'], 'AlCl3', 70),
        (['Fe','Cl','Cl'], 'FeCl2', 70),
        (['Fe','Cl','Cl','Cl'], 'FeCl3', 70),
        (['Cu','S'], 'CuS', 60),
        (['Zn','O'], 'ZnO', 80),
        (['Zn','S'], 'ZnS', 60),
        (['Pb','O'], 'PbO', 50),
        (['Ag','Cl'], 'AgCl', 70),
        (['K','O','H'], 'KOH', 80),
        (['Ba','O'], 'BaO', 50),
        (['Sr','O'], 'SrO', 50),
        (['Li','Cl'], 'LiCl', 80),
        (['Li','F'], 'LiF', 60),
        (['Na','F'], 'NaF', 70),
        (['K','F'], 'KF', 60),
        (['Ca','Cl','Cl'], 'CaCl2', 80),
        (['Ca','F','F'], 'CaF2', 60),
        (['Al','O','O','O'], 'Al2O3', 80),
        (['Fe','O','O','O'], 'Fe2O3', 70),
        
        # ===== Common organic (70-40 samples) =====
        (['C','C','H','H','H','H','H','H'], 'C2H6', 70),  # Ethane
        (['C','C','H','H','H','H'], 'C2H4', 70),          # Ethylene
        (['C','C','H','H'], 'C2H2', 60),                  # Acetylene
        (['C','C','C','H','H','H','H','H','H','H','H'], 'C3H8', 60),  # Propane
        (['C','C','H','H','H','O'], 'C2H6O', 60),         # Ethanol
        (['C','H','H','O'], 'CH2O', 70),                  # Formaldehyde
        (['C','C','H','H','H','H','O'], 'C2H4O', 50),     # Acetaldehyde
        (['C','C','H','H','H','O','O'], 'C2H4O2', 50),    # Acetic acid
        (['C','H','H','H','O'], 'CH4O', 60),              # Methanol
        (['C','C','C','H','H','H','H','H','O'], 'C3H8O', 40),  # Propanol
        
        # ===== Acids & bases (60-40 samples) =====
        (['H','N','O','O','O'], 'HNO3', 80),              # Nitric acid
        (['H','H','S','O','O','O','O'], 'H2SO4', 80),     # Sulfuric acid
        (['H','C','O','O'], 'HCO2', 50),                  # Formic acid
        (['H','H','C','O','O','O'], 'H2CO3', 60),         # Carbonic acid
        (['H','P','O','O','O'], 'H3PO4', 50),             # Phosphoric acid
        
        # ===== Salts (50-30 samples) =====
        (['K','Br'], 'KBr', 60),
        (['K','I'], 'KI', 60),
        (['Na','Br'], 'NaBr', 60),
        (['Na','I'], 'NaI', 60),
        (['Ca','S'], 'CaS', 50),
        (['Mg','S'], 'MgS', 50),
        (['Na','Na','S'], 'Na2S', 50),
        (['K','K','S'], 'K2S', 50),
        (['Ba','Cl','Cl'], 'BaCl2', 50),
        (['Sr','Cl','Cl'], 'SrCl2', 40),
        (['Al','F','F','F'], 'AlF3', 40),
        (['Si','O','O'], 'SiO2', 70),
        (['Ti','O','O'], 'TiO2', 50),
        (['Mn','O','O'], 'MnO2', 40),
        (['Cr','O','O','O'], 'CrO3', 40),
        
        # ===== Small organics (40-30 samples) =====
        (['C','C','C','C','H','H','H','H','H','H','H','H','H','H'], 'C4H10', 40),  # Butane
        (['C','C','C','C','H','H','H','H','H','H','H','H'], 'C4H8', 30),           # Butene
        (['C','C','C','H','H','H','H','H','H'], 'C3H6', 40),                       # Propylene
        (['C','H','Cl','Cl','Cl'], 'CHCl3', 40),                                   # Chloroform
        (['C','Cl','Cl','Cl','Cl'], 'CCl4', 40),                                   # Carbon tetrachloride
        (['C','C','Cl','Cl','Cl','Cl'], 'C2Cl4', 30),                              # Tetrachloroethylene
    ]
    
    # Generate reactions with specified weights
    for reactants, product, weight in common_reactions:
        for _ in range(weight):
            reactions.append({
                "reactants": reactants,
                "products": [product],
                "type": "common"
            })
    
    # Save to JSON
    with open('reaction_training_data.json', 'w') as f:
        json.dump({
            "reactions": reactions,
            "count": len(reactions),
            "unique_products": len(set(r['products'][0] for r in reactions)),
            "sources": ["Curated Common Reactions"],
            "generated_at": "2024-11-14"
        }, f, indent=2)
    
    print(f"✅ Generated {len(reactions)} reactions")
    print(f"   Unique products: {len(set(r['products'][0] for r in reactions))}")
    print(f"   Avg samples/product: {len(reactions)/len(set(r['products'][0] for r in reactions)):.1f}")

if __name__ == "__main__":
    generate_focused_dataset()
