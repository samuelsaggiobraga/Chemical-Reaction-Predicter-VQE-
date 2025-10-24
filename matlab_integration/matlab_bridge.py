"""
Bridge between Python and MATLAB for VQE calculations
"""
import subprocess
import json
import os
from typing import Dict, List, Any
import sys

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.quantum_chemistry.hamiltonian_builder import HamiltonianBuilder


class MatlabQuantumBridge:
    """Orchestrate Python → MATLAB → Python pipeline for quantum calculations"""
    
    def __init__(self, matlab_path: str = "/Applications/MATLAB_R2025b.app/bin/matlab"):
        self.matlab_path = matlab_path
        self.hamiltonian_builder = HamiltonianBuilder()
        
    def calculate_molecule_properties(self, elements: List[str], geometry: Dict = None) -> Dict[str, Any]:
        """
        Full pipeline: Python builds Hamiltonian → MATLAB runs VQE → Python collects results
        
        Args:
            elements: List of element symbols (e.g., ['H', 'H'])
            geometry: Optional molecular geometry
            
        Returns:
            Complete quantum chemistry data for Gemini
        """
        
        print(f"[1/3] Building Hamiltonian for {elements}...")
        
        # Step 1: Python generates Hamiltonian using PySCF
        molecular_data = self.hamiltonian_builder.build_molecule(elements, geometry)
        
        # Save for MATLAB
        hamiltonian_file = 'hamiltonian_data.json'
        self.hamiltonian_builder.save_for_matlab(molecular_data, hamiltonian_file)
        
        print(f"[2/3] Running MATLAB VQE...")
        
        # Step 2: MATLAB runs VQE algorithm
        vqe_results = self._run_matlab_vqe(hamiltonian_file)
        
        print(f"[3/3] Packaging results...")
        
        # Step 3: Combine all data for Gemini
        complete_results = {
            **molecular_data,
            **vqe_results,
            'calculation_method': 'VQE',
            'basis_set': 'sto-3g',
            'ansatz': 'hardware-efficient'
        }
        
        # Cleanup temp files
        results_file = os.path.join(os.path.dirname(os.path.abspath(hamiltonian_file)), 'vqe_results.json')
        self._cleanup([hamiltonian_file, results_file])
        
        return complete_results
    
    def _run_matlab_vqe(self, hamiltonian_file: str) -> Dict[str, Any]:
        """Execute MATLAB VQE script"""
        
        # Get path to MATLAB scripts
        matlab_script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # MATLAB command to execute directly
        matlab_cmd = f"cd('{matlab_script_dir}'); addpath('{os.path.dirname(matlab_script_dir)}'); run_vqe('{os.path.abspath(hamiltonian_file)}');"
        
        try:
            # Execute MATLAB in batch mode
            process = subprocess.run(
                [self.matlab_path, '-batch', matlab_cmd],
                capture_output=True,
                text=True,
                timeout=None,  # No timeout - let it run as long as needed
                cwd=matlab_script_dir
            )
            
            print(f"MATLAB stdout: {process.stdout}")
            print(f"MATLAB stderr: {process.stderr}")
            print(f"MATLAB return code: {process.returncode}")
            
            if process.returncode != 0:
                raise RuntimeError(f"MATLAB execution failed (return code {process.returncode}): {process.stderr}")
            
            # Read results from JSON (in same directory as hamiltonian file)
            results_file = os.path.join(os.path.dirname(os.path.abspath(hamiltonian_file)), 'vqe_results.json')
            with open(results_file, 'r') as f:
                results = json.load(f)
            
            return results
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("MATLAB VQE calculation timed out (this shouldn't happen - no timeout set)")
        except FileNotFoundError as e:
            if 'vqe_results.json' in str(e):
                raise RuntimeError(f"MATLAB did not produce output file. Check MATLAB errors above. Process stderr: {process.stderr if 'process' in locals() else 'N/A'}")
            else:
                raise RuntimeError(f"MATLAB executable not found at {self.matlab_path}")
        finally:
            pass  # No cleanup needed for direct command
    
    def _cleanup(self, files: List[str]):
        """Remove temporary files"""
        for f in files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception as e:
                    print(f"Warning: Could not remove {f}: {e}")


# Test function
if __name__ == '__main__':
    # Test with H2 molecule
    bridge = MatlabQuantumBridge()
    results = bridge.calculate_molecule_properties(['H', 'H'])
    
    print("\n=== Results ===")
    print(f"HF Energy: {results['hf_energy']:.6f} Ha")
    print(f"VQE Energy: {results['vqe_energy']:.6f} Ha")
    print(f"Energy Improvement: {results['energy_improvement']:.6f} Ha")
    print(f"Bond Lengths: {results['bond_lengths']}")
    print(f"Orbital Occupations: {results['orbital_occupations']}")
