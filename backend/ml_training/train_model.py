"""
Train actual ML model on reaction data to predict chemical products
This model acts as an AI assistant to Gemini, validating and augmenting predictions
"""
import json
import pickle
from collections import Counter
from typing import List, Dict, Tuple
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

class ReactionMLModel:
    """ML model that predicts reaction products from reactants"""
    
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.element_to_idx = {}
        self.product_to_idx = {}
        self.idx_to_product = {}
        
    def _featurize_reactants(self, reactants: List[str]) -> np.ndarray:
        """Convert reactant list to feature vector"""
        # Count each element
        elem_counts = Counter(reactants)
        
        # Create feature vector (118 elements max)
        features = np.zeros(118)
        for elem, count in elem_counts.items():
            if elem in self.element_to_idx:
                features[self.element_to_idx[elem]] = count
        
        # Additional features
        total_atoms = len(reactants)
        num_unique = len(elem_counts)
        
        # Add aggregate features
        extra_features = [
            total_atoms,
            num_unique,
            max(elem_counts.values()),  # max count of any element
            1 if 'H' in elem_counts else 0,
            1 if 'O' in elem_counts else 0,
            1 if 'C' in elem_counts else 0,
            1 if 'N' in elem_counts else 0,
        ]
        
        return np.concatenate([features, extra_features])
    
    def train(self, reactions: List[Dict]):
        """Train model on reaction data"""
        print("🎓 Training ML model...")
        
        # Build element vocabulary
        all_elements = set()
        for r in reactions:
            all_elements.update(r['reactants'])
        self.element_to_idx = {elem: i for i, elem in enumerate(sorted(all_elements))}
        
        # Build product vocabulary
        all_products = set()
        for r in reactions:
            all_products.update(r['products'])
        self.product_to_idx = {prod: i for i, prod in enumerate(sorted(all_products))}
        self.idx_to_product = {i: prod for prod, i in self.product_to_idx.items()}
        
        print(f"   Elements: {len(self.element_to_idx)}")
        print(f"   Products: {len(self.product_to_idx)}")
        
        # Create training data
        X = []
        y = []
        
        for reaction in reactions:
            features = self._featurize_reactants(reaction['reactants'])
            X.append(features)
            
            # For simplicity, predict first product only
            if reaction['products']:
                product = reaction['products'][0]
                if product in self.product_to_idx:
                    y.append(self.product_to_idx[product])
        
        X = np.array(X)
        y = np.array(y)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        print(f"   Training samples: {len(X_train)}")
        print(f"   Test samples: {len(X_test)}")
        
        # Train
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"   ✅ Training complete!")
        print(f"   Accuracy: {accuracy:.2%}")
        
        return accuracy
    
    def predict(self, reactants: List[str], top_k=3) -> List[Tuple[str, float]]:
        """Predict most likely products"""
        features = self._featurize_reactants(reactants).reshape(1, -1)
        
        # Get probabilities for all classes
        probabilities = self.model.predict_proba(features)[0]
        
        # Get top k predictions
        top_indices = np.argsort(probabilities)[-top_k:][::-1]
        
        predictions = []
        for idx in top_indices:
            if idx in self.idx_to_product:
                product = self.idx_to_product[idx]
                prob = probabilities[idx]
                predictions.append((product, prob))
        
        return predictions
    
    def validate_gemini_prediction(self, reactants: List[str], gemini_products: List[Dict]) -> Dict:
        """
        Validate Gemini's prediction using ML model
        Returns validation score and suggestions
        """
        ml_predictions = self.predict(reactants, top_k=5)
        ml_products = [p[0] for p in ml_predictions]
        ml_probs = {p[0]: p[1] for p in ml_predictions}
        
        # Check if Gemini's prediction matches ML
        gemini_formulas = [p['formula'] for p in gemini_products]
        
        matches = []
        for gem_formula in gemini_formulas:
            if gem_formula in ml_products:
                ml_confidence = ml_probs[gem_formula]
                matches.append({
                    "formula": gem_formula,
                    "ml_confidence": ml_confidence,
                    "match": True
                })
        
        # Overall validation
        match_rate = len(matches) / len(gemini_formulas) if gemini_formulas else 0
        
        return {
            "validated": match_rate > 0.5,
            "match_rate": match_rate,
            "ml_predictions": ml_predictions,
            "matches": matches,
            "recommendation": "High confidence" if match_rate > 0.7 else "Review recommended"
        }
    
    def save(self, filename="reaction_model.pkl"):
        """Save trained model"""
        with open(filename, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'element_to_idx': self.element_to_idx,
                'product_to_idx': self.product_to_idx,
                'idx_to_product': self.idx_to_product
            }, f)
        print(f"💾 Model saved to {filename}")
    
    @staticmethod
    def load(filename="reaction_model.pkl"):
        """Load trained model"""
        with open(filename, 'rb') as f:
            data = pickle.load(f)
        
        model = ReactionMLModel()
        model.model = data['model']
        model.element_to_idx = data['element_to_idx']
        model.product_to_idx = data['product_to_idx']
        model.idx_to_product = data['idx_to_product']
        return model


def main():
    print("="*60)
    print("ML MODEL TRAINING")
    print("="*60)
    
    # Load training data
    print("\n📁 Loading training data...")
    try:
        with open("reaction_training_data.json", 'r') as f:
            data = json.load(f)
        reactions = data['reactions']
        print(f"   Loaded {len(reactions)} reactions")
    except FileNotFoundError:
        print("❌ Training data not found!")
        print("Run: python backend/ml_training/scrape_reactions.py")
        return
    
    # Train model
    model = ReactionMLModel()
    accuracy = model.train(reactions)
    
    # Save model
    model.save()
    
    # Test predictions
    print("\n🧪 Testing predictions...")
    test_cases = [
        ["H", "H"],
        ["H", "H", "O"],
        ["Na", "Cl"],
        ["C", "H", "H", "H", "H"],
    ]
    
    for reactants in test_cases:
        predictions = model.predict(reactants, top_k=3)
        reactants_str = ' + '.join(reactants)
        print(f"\n   {reactants_str} →")
        for i, (product, prob) in enumerate(predictions, 1):
            print(f"      {i}. {product} ({prob:.1%})")
    
    print("\n" + "="*60)
    print(f"✅ Model trained with {accuracy:.1%} accuracy")
    print("="*60)


if __name__ == "__main__":
    main()
