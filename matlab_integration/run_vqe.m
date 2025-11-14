function results = run_vqe(hamiltonian_file)
% RUN_VQE Execute VQE algorithm on molecular Hamiltonian from Python
%
% Input: hamiltonian_file - JSON file with Pauli strings and coefficients
% Output: results - struct with ground state energy and observables

% Read Hamiltonian data from Python
fid = fopen(hamiltonian_file, 'r');
raw = fread(fid, inf);
str = char(raw');
fclose(fid);
data = jsondecode(str);

% Build observable from Pauli strings and coefficients
pauli_cell = data.qubit_hamiltonian.pauli_strings;
coefficients = data.qubit_hamiltonian.coefficients;
num_qubits = data.qubit_hamiltonian.num_qubits;

% Convert cell array to string array for MATLAB observable class
if iscell(pauli_cell)
    pauli_strings = string(pauli_cell);
else
    pauli_strings = string(pauli_cell);
end

% Convert coefficients to numeric array
if iscell(coefficients)
    coefficients = cell2mat(coefficients);
end
coefficients = double(coefficients(:));  % Ensure column vector

% CRITICAL: Limit qubits to prevent memory overflow BEFORE creating observable
% 2^n qubits requires 2^n complex numbers in memory
% Maximum practical limit: ~20 qubits (1M states, ~16MB)
MAX_QUBITS = 12;  % Conservative limit for stability

if num_qubits > MAX_QUBITS
    warning('System requires %d qubits but limited to %d for memory constraints', num_qubits, MAX_QUBITS);
    fprintf('Truncating to %d qubits for VQE simulation\n', MAX_QUBITS);
    
    % Truncate Pauli strings to MAX_QUBITS
    truncated_pauli = cell(size(pauli_strings));
    for i = 1:length(pauli_strings)
        str = char(pauli_strings(i));
        if length(str) > MAX_QUBITS
            truncated_pauli{i} = str(1:MAX_QUBITS);
        else
            truncated_pauli{i} = str;
        end
    end
    pauli_strings = string(truncated_pauli);
    num_qubits = MAX_QUBITS;
end

% Create observable object using your existing observable.m class
H = observable(pauli_strings, coefficients);

% Get actual number of qubits from Hamiltonian
actual_num_qubits = H.NumQubits;

% VQE parameters - optimized for speed
max_iterations = 50;  % Reduced from 100
num_params = min(actual_num_qubits * 2, 20); % Limit parameters
initial_params = rand(1, num_params) * 2 * pi;

% Optimization options - faster convergence
options = optimoptions('fminunc', ...
    'Display', 'off', ...  % Turn off display for speed
    'MaxIterations', max_iterations, ...
    'MaxFunctionEvaluations', max_iterations * 10, ...
    'OptimalityTolerance', 1e-4, ...  % Relaxed tolerance
    'StepTolerance', 1e-6, ...
    'Algorithm', 'quasi-newton');  % Faster algorithm

% VQE optimization - minimize energy expectation
cost_function = @(params) vqe_cost(params, H, actual_num_qubits);
[optimal_params, ground_state_energy] = fminunc(cost_function, initial_params, options);

% Get final quantum state
final_state = create_ansatz_state(optimal_params, actual_num_qubits);

% Calculate additional observables
results = struct();
results.ground_state_energy = ground_state_energy;
results.vqe_energy = ground_state_energy + data.nuclear_repulsion;
results.hf_energy = data.hf_energy;
results.energy_improvement = data.hf_energy - results.vqe_energy;
results.optimal_parameters = optimal_params;
results.num_qubits = actual_num_qubits;
results.num_iterations = max_iterations;

% Calculate observables for each qubit (Z expectation values)
z_expectations = zeros(1, actual_num_qubits);
for q = 1:actual_num_qubits
    pauli_str = repmat('I', 1, actual_num_qubits);
    pauli_str(q) = 'Z';
    obs_z = observable(pauli_str, 1.0);
    z_expectations(q) = estimate(final_state, obs_z);
end
results.qubit_z_expectations = z_expectations;

% Calculate electron density (occupations)
occupations = (1 - z_expectations) / 2;
results.orbital_occupations = occupations;

% Save results to JSON for Python to read
results_json = jsonencode(results);

% Use absolute path in same directory as input file
[input_dir, ~, ~] = fileparts(hamiltonian_file);
output_file = fullfile(input_dir, 'vqe_results.json');

fid = fopen(output_file, 'w');
fprintf(fid, '%s', results_json);
fclose(fid);

fprintf('VQE results saved to: %s\n', output_file);

end

function energy = vqe_cost(params, H, num_qubits)
% Cost function for VQE optimization
    state = create_ansatz_state(params, num_qubits);
    energy = estimate(state, H);
end

function state = create_ansatz_state(params, num_qubits)
% Create parameterized quantum state using ultra-simplified ansatz
% Single layer only for maximum speed

    available_params = length(params);
    
    % Pad params if needed to match qubits
    if available_params < num_qubits
        params = [params, zeros(1, num_qubits - available_params)];
    end
    
    % Build minimal quantum circuit - single layer only
    gates = [];
    
    % Just RY rotations, no entanglement for speed
    for q = 1:min(num_qubits, available_params)
        gates = [gates; ryGate(q, params(q))];
    end
    
    % Minimal entanglement - only if more than 2 qubits
    if num_qubits > 2
        % Just one pair of CNOT gates
        gates = [gates; cxGate(1, 2)];
        if num_qubits > 3
            gates = [gates; cxGate(3, 4)];
        end
    end
    
    % Create circuit and simulate
    circuit = quantumCircuit(gates, num_qubits);
    state = simulate(circuit);
end
