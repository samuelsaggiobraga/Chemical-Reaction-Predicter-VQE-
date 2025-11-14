classdef observable
    %OBSERVABLE observable of a quantum state, represented as a
    %   Hermitian matrix or set of Pauli strings and weights. Each Pauli
    %   string represents the Kronecker product of the corresponding Pauli
    %   matrices, such that the weighted sum is a Hermitian matrix.
    %
    %   obs = observable(pauli, weights) takes a string array or char matrix
    %   pauli and numeric array weights of the same length. All elements in
    %   the input pauli must be "X", "Y", "Z", or "I" and all numbers in
    %   input weights must be real.
    %
    %   obs = observable(matrix) takes a Hermitian matrix of size
    %   2^N by 2^N, where N is the number of qubits. The Pauli strings and
    %   weights are computed from the input matrix.
    %
    %   Example:
    %       % Construct an observable for 2 qubits, where X is observed on
    %       the 1st and 2nd qubit with weight 2.4, and Z is observed on
    %       the first qubit with weight -1.2. Get the Hermitian matrix of
    %       this observable.
    %       obs = observable(["XX" "ZI"], [2.4 -1.2]);
    %       H = getMatrix(obs);
    %
    %   Example:
    %       % Construct an observable for 1 qubit described by a Hermitian
    %       matrix.
    %       H = [2.5 0.3-1.2j; 0.3+1.2j -2.3]
    %       obs = observable(H);

    %   Copyright 2024 The MathWorks, Inc.
    properties
        Paulis
        Weights
        NumQubits
    end

    properties(Access=private)
        Matrix
    end

    methods
        function obj = observable(varargin)
            if nargin==1
                % Hermitian matrix
                H = varargin{1};

                assert(ishermitian(H), 'Input matrix must be Hermitian.')

                N = log2(size(H,1));

                assert(fix(N) == N)

                obj.Matrix = H;

                % Pauli matrices form an orthogonal basis for all Hermitian
                % matrices. Reshape the input matrix to be projected.
                vecH = ipermute(reshape(H, 2*ones(1, 2*N)), [1:2:2*N 2:2:2*N]);
                allWeights = reshape(vecH, [], 1);

                % Set U=reshape(cat(3, I, X, Y, Z), 4, 4)/2, where X,Y,Z
                % and I are the 2-by-2 Pauli matrices. The map follows this
                % order to build the Pauli strings.
                U = [0.5 0 0 0.5; 0 0.5 0.5j 0; 0 0.5 -0.5j 0; 0.5 0 0 -0.5];
                map = 'IXYZ';
                for ii=1:N
                    allWeights = applyMat2Dim(allWeights, U', ii);
                end

                % Remove Pauli strings with an absolute weight close to 0.
                thres = 2^N*eps(class(allWeights));
                linIdx = find(abs(allWeights)>=thres);

                if N==1
                    mapIdx = linIdx;
                    pauliChar = map(mapIdx).';
                else
                    cc = cell(1, N);
                    [cc{:}] = ind2sub(4*ones(1, N), linIdx);
                    mapIdx = horzcat(cc{end:-1:1});
                    pauliChar = map(mapIdx);
                end

                pauli = string(pauliChar);
                weights = allWeights(linIdx);

            else
                % Pauli strings and weights
                pauli = varargin{1};
                weights = varargin{2};

                assert(isfloat(weights) && isreal(weights) && all(isfinite(weights)) && isvector(weights))
                assert(ischar(pauli) || isstring(pauli))

                pauli = upper(pauli);

                if isstring(pauli)
                    assert(isvector(pauli) && all(~ismissing(pauli)))
                    % Number of qubits for each string element. They must
                    % all be the same.
                    N = strlength(pauli);
                    if ~isscalar(N)
                        N = unique(N);
                        assert(isscalar(N), 'Input pauli string must have the same length for each element.')
                    end
                    % Convert to char for input checking below.
                    pauli = char(reshape(pauli, [], 1));
                else
                    assert(ismatrix(pauli), 'Input pauli char must be a matrix.')
                    % Number of qubits for each char row is the same.
                    N = size(pauli, 2);
                end

                % Verify each character of the char matrix
                assert(all(ismember(pauli, 'IXYZ'), 'all'), 'Input pauli must contain only "X","Y","Z" or "I" characters.')

                % Convert to string array and verify each string element
                % has a weight
                pauli = string(pauli);
                weights = reshape(weights, [], 1);
                assert(length(pauli)==length(weights), 'Input pauli and weights must have the same number of elements.')
            end

            % The Pauli strings are unique and follow the map order
            [pauli, ~, idx] = unique(pauli);
            weights = accumarray(idx, weights);

            obj.Paulis = pauli;
            obj.Weights = weights;
            obj.NumQubits = N;
        end

        function H = getMatrix(obj)

            if ~isempty(obj.Matrix)
                H = obj.Matrix;
                return
            end

            N = obj.NumQubits;

            % Index of each Pauli character into map
            map = 'IXYZ';
            [~, mapIdx] = ismember(char(obj.Paulis), map);

            % Index of each term into the reshaped matrix
            if N==1
                linIdx = mapIdx;
            else
                mapIdx = num2cell(fliplr(mapIdx), 1);
                linIdx = sub2ind(4*ones(1,N), mapIdx{:});
            end

            allWeights = zeros(4^N,1);
            allWeights(linIdx) = obj.Weights;

            % Undo transformation of Pauli basis on each dimension by
            % applying 2*U to account for overall 2^N factor.
            U = [0.5 0 0 0.5; 0 0.5 0.5j 0; 0 0.5 -0.5j 0; 0.5 0 0 -0.5];
            for ii=1:N
                allWeights = applyMat2Dim(allWeights, 2*U, ii);
            end

            allWeights = permute(reshape(allWeights, 2*ones(1, 2*N)), [1:2:2*N 2:2:2*N]);
            H = reshape(allWeights, [2^N 2^N]);
        end
    end
end


function X = applyMat2Dim(X, U, dim)
if dim==1
    X = U*reshape(X, 4, []);
else
    X = reshape(X, 4^(dim-1), 4, []);
    X = pagemtimes(X, U.');
end
X = X(:);
end