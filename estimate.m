function expval = estimate(state, obs, NameValueArgs)
%ESTIMATE Expected value of an observable measured from the quantum state.
%
%   expval = ESTIMATE(state, obs) computes the expected value of measuring
%   the observable obs from the quantum state. The value is computed using
%
%                               <s|O|s>
%
%   where |s> and O are respectively the input state and observable
%   representing the same number of qubits.
%
%   expval = ESTIMATE(..., NumShots=nshots) approximates the expected value
%   using the specified number of shots.
%
%   Example:
%       % Compute exact expectation of the observable on a random state.
%       state = quantum.gate.QuantumState(rand(8,1));
%       obs = observable("ZZZ", 0.4);
%       expval = estimate(state, obs);
%
%   Example:
%       % Approximate expectation of the obs on a random state.
%       state = quantum.gate.QuantumState(rand(8,1));
%       obs = observable("ZZZ", 0.4);
%       expval = estimate(state, obs, NumShots=1000);
%
%   Copyright 2024 The MathWorks, Inc.
arguments
    state quantum.gate.QuantumState
    obs observable
    NameValueArgs.NumShots {mustBeNumeric, mustBePositive} = Inf
end

numQubits = state.NumQubits;
numTerms = length(obs.Paulis);

assert(numQubits==obs.NumQubits, 'Input state and obs must have the same number of qubits.')
assert(isscalar(NameValueArgs.NumShots))

doExact = isinf(NameValueArgs.NumShots);
% Use performance heuristic based on the number of qubits and terms
useFullHermitian = doExact && ( (numQubits<=6) || (2^numQubits/numQubits<=numTerms) );

s = state.Amplitudes;

if useFullHermitian
    H = getMatrix(obs);
    % Remove complex round-off
    expval = real(s'*H*s);
    return
end

terms = obs.Paulis;
weights = obs.Weights;

expval = 0;
for ii = 1:numTerms

    pstr = terms(ii);
    iX = strfind(pstr, "X");
    iY = strfind(pstr, "Y");
    iZ = strfind(pstr, "Z");

    if doExact
        obsGates = quantumCircuit([xGate(iX); yGate(iY); zGate(iZ)], numQubits);
        stateObs = simulate(obsGates, state);
        % Remove complex round-off
        ev = weights(ii)*real(s'*stateObs.Amplitudes);
    else
        qubits = [iX iY iZ];
        if isempty(qubits)
            ev = weights(ii);
        else
            % Apply gates to rotate from Z basis to desired Pauli basis
            rotGates = quantumCircuit([hGate(iX); siGate(iY); hGate(iY)], numQubits);
            stateRot = simulate(rotGates, state);

            % Sample and determine eigenvalues by parity check
            meas = randsample(stateRot, NameValueArgs.NumShots);
            [states, probs] = querystates(meas, qubits);
            eigvals = (-1).^count(states, "1");
            ev = weights(ii)*probs.'*eigvals;
        end
    end
    % Add contribution for this Pauli string
    expval = expval + ev;
end
end