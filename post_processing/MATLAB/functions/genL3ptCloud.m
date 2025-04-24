% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2025-04-23

function genL3ptCloud(waveDir)
% Concatenates all ptCloud objects from L2 .mat files
% into a single ptCloud and saves it to L3ptCloud.mat.

    % Define L2 path and list all .mat files
    L2Dir = fullfile(waveDir, 'L2');
    matFiles = dir(fullfile(L2Dir, '*.mat'));

    if isempty(matFiles)
        error('No .mat files found in L2 directory: %s', L2Dir);
    end

    % Initialize a cell array to hold ptClouds
    ptClouds = {};

    % Loop over .mat files to load ptClouds
    for i = 1:length(matFiles)
        data = load(fullfile(L2Dir, matFiles(i).name));
        if isfield(data, 'ptCloud')
            ptClouds{end + 1} = data.ptCloud; %#ok<AGROW>
        else
            warning('No ptCloud found in %s', matFiles(i).name);
        end
    end

    if isempty(ptClouds)
        error('No valid ptClouds found to concatenate.');
    end

    % Concatenate all point clouds
    ptCloud = ptClouds{1};
    for i = 2:length(ptClouds)
        ptCloud = pccat([ptCloud, ptClouds{i}]);
    end

    % Save the combined ptCloud to L3ptCloud.mat
    save(fullfile(waveDir, 'L3ptCloud.mat'), 'ptCloud');
    fprintf('Saved concatenated ptCloud to %s\n', fullfile(waveDir, 'L3ptCloud.mat'));
end