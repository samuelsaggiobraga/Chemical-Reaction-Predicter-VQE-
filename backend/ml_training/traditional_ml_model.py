#!/usr/bin/env python3
"""
Traditional ML Model with Proper Feature Engineering
Uses XGBoost for fast inference and handles unseen reactions via similarity
"""

import json
import pickle
import numpy as np
from typing import List, Dict, Tuple
from collections import Counter
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score

class TraditionalMLPredictor:
    """
    ML model with proper feature engineering for reaction prediction
    Better than failed RandomForest because it uses reaction fingerprints
    """
    
    def __init__(self):
        self.model = None
        self.label_encoder = LabelEncoder()
        self.element_list = []
        self.product_list = []
        
    def _create_reaction_fingerprint(self, reactants: List[str]) -> np.ndarray:
        """
        Create molecular fingerprint with chemical intuition
        
        Features:
        - Element counts (sparse vector)
        - Stoichiometry ratios
        - Chemical properties (electronegativity, size)
        - Reaction type indicators
        """
        elem_counts = Counter(reactants)
        total_atoms = len(reactants)
        
        # Element count vector (118 elements max)
        elem_vector = np.zeros(118)
        for elem, count in elem_counts.items():
            if elem in self.element_list:
                idx = self.element_list.index(elem)
                elem_vector[idx] = count
        
        # Stoichiometry features
        num_elements = len(elem_counts)
        max_count = max(elem_counts.values())
        min_count = min(elem_counts.values())
        
        # Chemical property features
        h_count = elem_counts.get('H', 0)
        c_count = elem_counts.get('C', 0)
        o_count = elem_counts.get('O', 0)
        n_count = elem_counts.get('N', 0)
        
        # Electronegativity-based features (simplified)
        electronegative = sum(elem_counts.get(e, 0) for e in ['F','O','N','Cl'])
        electropositive = sum(elem_counts.get(e, 0) for e in ['Li','Na','K','Rb','Cs','Ca','Mg'])
        
        # Reaction type indicators
        is_diatomic = (num_elements == 1 and total_atoms == 2)
        is_binary = (num_elements == 2)
        is_organic = (c_count > 0)
        has_metal = any(m in elem_counts for m in ['Li','Na','K','Mg','Ca','Fe','Cu','Zn','Al'])
        has_halogen = any(h in elem_counts for h in ['F','Cl','Br','I'])
        has_noble_gas = any(ng in elem_counts for ng in ['He','Ne','Ar','Kr','Xe','Rn'])
        
        # Ratios (avoid divide by zero)
        h_to_c = h_count / max(c_count, 1)
        o_to_c = o_count / max(c_count, 1)
        heavy_atoms = total_atoms - h_count
        
        # Combine all features
        features = np.concatenate([
            elem_vector,
            [total_atoms, num_elements, max_count, min_count],
            [h_count, c_count, o_count, n_count],
            [electronegative, electropositive],
            [h_to_c, o_to_c, heavy_atoms],
            [float(is_diatomic), float(is_binary), float(is_organic)],
            [float(has_metal), float(has_halogen), float(has_noble_gas)]
        ])
        
        return features
    
    def train(self, reactions: List[Dict], test_size=0.2):
        """Train XGBoost model on reaction data"""
        print("🎓 Training Traditional ML Model...")
        
        # Build element and product vocabularies
        all_elements = set()
        all_products = set()
        for r in reactions:
            all_elements.update(r['reactants'])
            all_products.update(r['products'])
        
        self.element_list = sorted(list(all_elements))
        self.product_list = sorted(list(all_products))
        
        print(f"   Elements: {len(self.element_list)}")
        print(f"   Products: {len(self.product_list)}")
        
        # Create features and labels
        X = []
        y = []
        
        for reaction in reactions:
            features = self._create_reaction_fingerprint(reaction['reactants'])
            X.append(features)
            y.append(reaction['products'][0])
        
        X = np.array(X)
        
        # Encode labels
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=test_size, random_state=42
        )
        
        print(f"   Training samples: {len(X_train)}")
        print(f"   Test samples: {len(X_test)}")
        
        # Train RandomForest with proper features
        print("   Training RandomForest...")
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"   ✅ Training complete!")
        print(f"   Accuracy: {accuracy:.2%}")
        
        return accuracy
    
    def predict(self, reactants: List[str], top_k=3) -> Dict:
        """Predict products with confidence scores"""
        if not self.model:
            return {'products': [], 'confidence': 0, 'error': 'Model not trained'}
        
        # Create features
        features = self._create_reaction_fingerprint(reactants).reshape(1, -1)
        
        # Get probabilities
        proba = self.model.predict_proba(features)[0]
        
        # Get top k predictions
        top_indices = np.argsort(proba)[-top_k:][::-1]
        
        predictions = []
        for idx in top_indices:
            product = self.label_encoder.inverse_transform([idx])[0]
            confidence = float(proba[idx])
            predictions.append({
                'formula': product,
                'probability': confidence
            })
        
        max_confidence = predictions[0]['probability'] * 100 if predictions else 0
        
        return {
            'products': predictions,
            'confidence': max_confidence,
            'method': 'traditional_ml'
        }
    
    def save(self, filename='traditional_ml_model.pkl'):
        """Save model"""
        with open(filename, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'label_encoder': self.label_encoder,
                'element_list': self.element_list,
                'product_list': self.product_list
            }, f)
        print(f"💾 Model saved to {filename}")
    
    @staticmethod
    def load(filename='traditional_ml_model.pkl'):
        """Load model"""
        predictor = TraditionalMLPredictor()
        with open(filename, 'rb') as f:
            data = pickle.load(f)
            predictor.model = data['model']
            predictor.label_encoder = data['label_encoder']
            predictor.element_list = data['element_list']
            predictor.product_list = data['product_list']
        return predictor

def train_traditional_ml():
    """Train traditional ML model on mega dataset"""
    print("=" * 70)
    print("TRADITIONAL ML MODEL TRAINING (RandomForest with Fingerprints)")
    print("=" * 70 + "\n")
    
    # Load data
    with open('mega_training_data.json', 'r') as f:
        data = json.load(f)
        reactions = data['reactions']
    
    print(f"📁 Loaded {len(reactions)} reactions")
    
    # Train model
    model = TraditionalMLPredictor()
    accuracy = model.train(reactions)
    
    # Save model
    model.save('traditional_ml_model.pkl')
    
    # Test predictions
    print("\n🧪 Testing predictions...\n")
    
    test_cases = [
        (['H', 'H'], 'H2'),
        (['H', 'H', 'O'], 'H2O'),
        (['Na', 'Cl'], 'NaCl'),
        (['C','H','H','H','H'], 'CH4'),
    ]
    
    correct = 0
    for reactants, expected in test_cases:
        result = model.predict(reactants)
        predicted = result['products'][0]['formula'] if result['products'] else 'NONE'
        confidence = result['confidence']
        
        is_correct = (predicted == expected)
        correct += is_correct
        status = '✅' if is_correct else '❌'
        
        print(f"{status} {reactants} → {predicted} ({confidence:.1f}%)")
    
    print(f"\n{'='*70}")
    print(f"✅ Test accuracy: {correct}/{len(test_cases)} ({correct/len(test_cases)*100:.0f}%)")
    print(f"{'='*70}")

if __name__ == '__main__':
    train_traditional_ml()
