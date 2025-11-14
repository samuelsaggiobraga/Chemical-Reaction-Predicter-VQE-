"""
Benchmark test suite - validates prediction accuracy against known reactions
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from typing import Dict, List
import time

# Known reaction test cases with ground truth
GROUND_TRUTH_REACTIONS = [
    {
        "name": "Hydrogen formation",
        "elements": ["H", "H"],
        "expected_products": ["H2"],
        "expected_formula": "H2",
        "confidence_threshold": 0.8
    },
    {
        "name": "Water formation",
        "elements": ["H", "H", "O"],
        "expected_products": ["H2O"],
        "expected_formula": "H2O",
        "confidence_threshold": 0.7
    },
    {
        "name": "Methane formation",
        "elements": ["C", "H", "H", "H", "H"],
        "expected_products": ["CH4"],
        "expected_formula": "CH4",
        "confidence_threshold": 0.6
    },
    {
        "name": "Sodium chloride",
        "elements": ["Na", "Cl"],
        "expected_products": ["NaCl"],
        "expected_formula": "NaCl",
        "confidence_threshold": 0.8
    },
    {
        "name": "Ammonia formation",
        "elements": ["N", "H", "H", "H"],
        "expected_products": ["NH3"],
        "expected_formula": "NH3",
        "confidence_threshold": 0.6
    },
    {
        "name": "Carbon dioxide",
        "elements": ["C", "O", "O"],
        "expected_products": ["CO2"],
        "expected_formula": "CO2",
        "confidence_threshold": 0.7
    },
    {
        "name": "Hydrogen fluoride",
        "elements": ["H", "F"],
        "expected_products": ["HF"],
        "expected_formula": "HF",
        "confidence_threshold": 0.8
    },
    {
        "name": "Nitrogen molecule",
        "elements": ["N", "N"],
        "expected_products": ["N2"],
        "expected_formula": "N2",
        "confidence_threshold": 0.8
    },
    {
        "name": "Oxygen molecule",
        "elements": ["O", "O"],
        "expected_products": ["O2"],
        "expected_formula": "O2",
        "confidence_threshold": 0.8
    },
    {
        "name": "Hydroxyl radical",
        "elements": ["O", "H"],
        "expected_products": ["OH"],
        "expected_formula": "OH",
        "confidence_threshold": 0.7
    }
]


class BenchmarkTester:
    def __init__(self, api_url="http://localhost:5001"):
        self.api_url = api_url
        self.results = []
        
    def test_reaction(self, test_case: Dict) -> Dict:
        """Test a single reaction and compare to ground truth"""
        print(f"\n🧪 Testing: {test_case['name']}")
        print(f"   Elements: {' + '.join(test_case['elements'])}")
        
        try:
            # Make prediction
            response = requests.post(
                f"{self.api_url}/api/predict-reaction",
                json={"elements": test_case["elements"]},
                timeout=120
            )
            
            if not response.ok:
                return {
                    "test_case": test_case["name"],
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "passed": False
                }
            
            data = response.json()
            
            if not data.get("success"):
                return {
                    "test_case": test_case["name"],
                    "success": False,
                    "error": data.get("error", "Unknown error"),
                    "passed": False
                }
            
            # Extract predictions
            predicted_products = data["ai_prediction"]["products"]
            predicted_formulas = [p["formula"] for p in predicted_products]
            
            # Check if expected product is in predictions
            expected = test_case["expected_formula"]
            found = expected in predicted_formulas
            
            # Get confidence for the expected product
            confidence = 0.0
            if found:
                matching_product = next(p for p in predicted_products if p["formula"] == expected)
                confidence = matching_product.get("probability", 0.0)
            
            # Determine if test passed
            passed = found and confidence >= test_case["confidence_threshold"]
            
            # Validation results
            validation = data["ai_prediction"].get("validation", {})
            
            result = {
                "test_case": test_case["name"],
                "success": True,
                "expected": expected,
                "predicted": predicted_formulas,
                "found": found,
                "confidence": confidence,
                "passed": passed,
                "validation_result": validation.get("result"),
                "validation_confidence": validation.get("confidence"),
                "quantum_data": {
                    "vqe_energy": data["quantum_data"].get("vqe_energy"),
                    "hf_energy": data["quantum_data"].get("hf_energy"),
                    "improvement": data["quantum_data"].get("energy_improvement")
                }
            }
            
            # Print result
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {status}")
            print(f"   Expected: {expected}")
            print(f"   Got: {predicted_formulas}")
            if found:
                print(f"   Confidence: {confidence:.2%}")
            
            return result
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            return {
                "test_case": test_case["name"],
                "success": False,
                "error": str(e),
                "passed": False
            }
    
    def run_all_tests(self, max_tests=None):
        """Run all benchmark tests"""
        print("="*60)
        print("🔬 REACTION PREDICTION BENCHMARK")
        print("="*60)
        
        test_cases = GROUND_TRUTH_REACTIONS[:max_tests] if max_tests else GROUND_TRUTH_REACTIONS
        
        for i, test_case in enumerate(test_cases):
            print(f"\n[{i+1}/{len(test_cases)}]", end=" ")
            result = self.test_reaction(test_case)
            self.results.append(result)
            
            # Rate limiting
            time.sleep(2)
        
        self.print_summary()
        return self.results
    
    def print_summary(self):
        """Print benchmark summary statistics"""
        print("\n" + "="*60)
        print("📊 BENCHMARK SUMMARY")
        print("="*60)
        
        total = len(self.results)
        successful_requests = sum(1 for r in self.results if r["success"])
        passed = sum(1 for r in self.results if r.get("passed", False))
        found = sum(1 for r in self.results if r.get("found", False))
        
        print(f"\nTotal tests: {total}")
        print(f"Successful API calls: {successful_requests}/{total} ({successful_requests/total:.1%})")
        print(f"Expected product found: {found}/{total} ({found/total:.1%})")
        print(f"Tests passed (found + confidence): {passed}/{total} ({passed/total:.1%})")
        
        # Average confidence for correct predictions
        correct_confidences = [r["confidence"] for r in self.results if r.get("found", False)]
        if correct_confidences:
            avg_confidence = sum(correct_confidences) / len(correct_confidences)
            print(f"Average confidence (correct): {avg_confidence:.2%}")
        
        # List failures
        failures = [r for r in self.results if r["success"] and not r.get("passed", False)]
        if failures:
            print(f"\n❌ Failed tests ({len(failures)}):")
            for f in failures:
                print(f"   • {f['test_case']}")
                print(f"     Expected: {f.get('expected')}")
                print(f"     Got: {f.get('predicted', [])}")
                if f.get('found', False):
                    print(f"     (Found but confidence too low: {f.get('confidence', 0):.2%})")
        
        # Save results to file
        output_file = "benchmark_results.json"
        with open(output_file, 'w') as f:
            json.dump({
                "summary": {
                    "total": total,
                    "successful": successful_requests,
                    "found": found,
                    "passed": passed,
                    "accuracy": passed/total if total > 0 else 0,
                    "found_rate": found/total if total > 0 else 0
                },
                "results": self.results
            }, f, indent=2)
        
        print(f"\n📁 Results saved to: {output_file}")
        print("="*60)


def main():
    """Run benchmark suite"""
    tester = BenchmarkTester()
    
    # Check server is running
    try:
        response = requests.get(f"{tester.api_url}/api/health", timeout=5)
        if not response.ok:
            print("❌ Server not responding. Start with: python backend/api/server.py")
            return
    except Exception as e:
        print(f"❌ Server not running: {e}")
        print("Start with: python backend/api/server.py")
        return
    
    # Run tests
    results = tester.run_all_tests()
    
    # Return pass/fail status
    passed = sum(1 for r in results if r.get("passed", False))
    total = len(results)
    
    if passed == total:
        print(f"\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
