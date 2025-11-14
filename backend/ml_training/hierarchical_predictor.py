#!/usr/bin/env python3
"""
Hierarchical Reaction Predictor - 4-Level Ensemble System

Level 1: Hybrid ML Lookup (instant, 100% accurate for known reactions)
Level 2: Traditional ML Model (fast pattern matching)
Level 3: Gemini API (novel/complex reactions)
Level 4: Fallback to chemical rules

Routes predictions based on confidence scores for optimal speed/accuracy.
"""

import sys
import os
from typing import List, Dict, Tuple, Optional
import numpy as np

# Import all prediction models
from hybrid_model import HybridReactionPredictor
from traditional_ml_model import TraditionalMLPredictor

class HierarchicalReactionPredictor:
    """
    Multi-level ensemble predictor with intelligent routing
    """
    
    def __init__(self, use_quantum=False):
        self.use_quantum = use_quantum
        
        # Level 1: Hybrid lookup (always available)
        try:
            self.hybrid_model = HybridReactionPredictor.load('hybrid_model_mega.pkl')
            print(f"✅ Level 1: Hybrid lookup loaded ({self.hybrid_model.unique_reactant_combos} reactions)")
        except:
            try:
                self.hybrid_model = HybridReactionPredictor.load('hybrid_model.pkl')
                print(f"✅ Level 1: Hybrid lookup loaded ({self.hybrid_model.unique_reactant_combos} reactions) [fallback]")
            except:
                print("⚠️  Level 1: Hybrid model not found")
                self.hybrid_model = None
        
        # Level 2: Traditional ML
        try:
            self.ml_model = TraditionalMLPredictor.load('traditional_ml_model.pkl')
            print(f"✅ Level 2: Traditional ML loaded ({len(self.ml_model.product_list)} products)")
        except:
            print("⚠️  Level 2: Traditional ML not found")
            self.ml_model = None
        
        # Level 3: Gemini (lazy load)
        self.gemini_predictor = None
        print("⚠️  Level 3: Gemini will load on first use")
        
        # Statistics
        self.stats = {
            'level1_hits': 0,
            'level2_hits': 0,
            'level3_hits': 0,
            'level4_hits': 0,
            'total_predictions': 0
        }
    
    def predict(self, reactants: List[str], quantum_data: Optional[Dict] = None) -> Dict:
        """
        Route prediction through hierarchical system
        
        Returns:
            {
                'products': [...],
                'confidence': float,
                'method': 'level1_hybrid' | 'level2_ml' | 'level3_gemini' | 'level4_fallback',
                'speed': 'instant' | 'fast' | 'slow',
                'reasoning': str
            }
        """
        self.stats['total_predictions'] += 1
        
        # LEVEL 1: Try hybrid lookup first (instant, 100% accurate)
        if self.hybrid_model:
            result = self.hybrid_model.predict_with_fallback(reactants, top_k=3)
            
            if result['method'] == 'exact_match':
                self.stats['level1_hits'] += 1
                return {
                    'products': [{'formula': p[0], 'probability': p[1]} for p in result['predictions']],
                    'confidence': 100,
                    'method': 'level1_hybrid',
                    'speed': 'instant',
                    'reasoning': f"Known reaction from {result['training_examples']} training examples",
                    'training_examples': result['training_examples']
                }
        
        # LEVEL 2: Try traditional ML (fast pattern matching)
        if self.ml_model:
            ml_result = self.ml_model.predict(reactants)
            confidence = ml_result.get('confidence', 0)
            
            if confidence > 70:  # High confidence threshold
                self.stats['level2_hits'] += 1
                return {
                    'products': ml_result['products'],
                    'confidence': confidence,
                    'method': 'level2_ml',
                    'speed': 'fast',
                    'reasoning': f"ML pattern matching ({confidence:.0f}% confidence)"
                }
        
        # LEVEL 3: Use Gemini for novel/complex reactions (slow but accurate)
        try:
            # Lazy load Gemini
            if not self.gemini_predictor:
                from dotenv import load_dotenv
                load_dotenv('../../config/.env')
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from quantum_chemistry.gemini_integration import GeminiReactionPredictor
                self.gemini_predictor = GeminiReactionPredictor(os.getenv('GEMINI_API_KEY'))
            
            # Use minimal quantum data if not provided or quantum disabled
            if not quantum_data or not self.use_quantum:
                quantum_data = {
                    'vqe_energy': 0, 'hf_energy': 0, 'energy_improvement': 0,
                    'nuclear_repulsion': 0, 'mo_energies': [], 'orbital_occupations': [],
                    'bond_lengths': {}, 'num_electrons': 0
                }
            
            gemini_result = self.gemini_predictor.predict_reaction(reactants, quantum_data)
            self.stats['level3_hits'] += 1
            
            return {
                'products': gemini_result.get('products', []),
                'confidence': gemini_result.get('confidence', 80),
                'method': 'level3_gemini',
                'speed': 'slow',
                'reasoning': gemini_result.get('reasoning', 'AI prediction for novel reaction'),
                'mechanism': gemini_result.get('mechanism', 'Not provided')
            }
        
        except Exception as e:
            print(f"⚠️  Gemini failed: {e}")
        
        # LEVEL 4: Fallback to chemical rules
        self.stats['level4_hits'] += 1
        return self._fallback_prediction(reactants)
    
    def _fallback_prediction(self, reactants: List[str]) -> Dict:
        """
        Simple chemical rules as last resort
        """
        from collections import Counter
        elem_counts = Counter(reactants)
        
        # Rule 1: Diatomic molecules
        if len(set(reactants)) == 1 and len(reactants) == 2:
            elem = reactants[0]
            return {
                'products': [{'formula': f'{elem}2', 'probability': 0.8}],
                'confidence': 80,
                'method': 'level4_fallback',
                'speed': 'instant',
                'reasoning': 'Diatomic molecule rule'
            }
        
        # Rule 2: Binary compounds (2 elements)
        if len(set(reactants)) == 2:
            elems = sorted(set(reactants), key=lambda e: elem_counts[e], reverse=True)
            counts = [elem_counts[e] for e in elems]
            formula = f"{elems[0]}{counts[0] if counts[0]>1 else ''}{elems[1]}{counts[1] if counts[1]>1 else ''}"
            return {
                'products': [{'formula': formula, 'probability': 0.6}],
                'confidence': 60,
                'method': 'level4_fallback',
                'speed': 'instant',
                'reasoning': 'Binary compound rule'
            }
        
        # Rule 3: No idea - return unknown
        return {
            'products': [{'formula': 'UNKNOWN', 'probability': 0}],
            'confidence': 0,
            'method': 'level4_fallback',
            'speed': 'instant',
            'reasoning': 'No applicable chemical rules found'
        }
    
    def get_stats(self) -> Dict:
        """Get prediction statistics"""
        total = self.stats['total_predictions']
        if total == 0:
            return self.stats
        
        return {
            **self.stats,
            'level1_percentage': self.stats['level1_hits'] / total * 100,
            'level2_percentage': self.stats['level2_hits'] / total * 100,
            'level3_percentage': self.stats['level3_hits'] / total * 100,
            'level4_percentage': self.stats['level4_hits'] / total * 100
        }
    
    def print_stats(self):
        """Print prediction statistics"""
        stats = self.get_stats()
        total = stats['total_predictions']
        
        print("\n" + "=" * 70)
        print("HIERARCHICAL PREDICTOR STATISTICS")
        print("=" * 70)
        print(f"Total predictions: {total}")
        print(f"\nLevel 1 (Hybrid lookup):  {stats['level1_hits']:4} ({stats.get('level1_percentage', 0):5.1f}%) - instant")
        print(f"Level 2 (ML patterns):    {stats['level2_hits']:4} ({stats.get('level2_percentage', 0):5.1f}%) - fast")
        print(f"Level 3 (Gemini AI):      {stats['level3_hits']:4} ({stats.get('level3_percentage', 0):5.1f}%) - slow")
        print(f"Level 4 (Fallback rules): {stats['level4_hits']:4} ({stats.get('level4_percentage', 0):5.1f}%) - instant")
        print("=" * 70)

if __name__ == '__main__':
    # Test the hierarchical system
    predictor = HierarchicalReactionPredictor(use_quantum=False)
    
    test_cases = [
        (['H', 'H'], 'H2'),
        (['H', 'H', 'O'], 'H2O'),
        (['Na', 'Cl'], 'NaCl'),
        (['Xe', 'F', 'F'], 'XeF2'),  # Not in training
        (['Au', 'Au'], 'Au2'),  # Exotic
    ]
    
    print("\n🧪 Testing Hierarchical Predictor:")
    print("=" * 70)
    
    for reactants, expected in test_cases:
        result = predictor.predict(reactants)
        predicted = result['products'][0]['formula'] if result['products'] else 'NONE'
        status = '✅' if predicted == expected else '❌'
        
        print(f"\n{status} {reactants} → {predicted}")
        print(f"   Method: {result['method']} ({result['speed']})")
        print(f"   Confidence: {result['confidence']}%")
    
    predictor.print_stats()
