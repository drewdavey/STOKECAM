% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-06

clear; clc; close all;

addpath('functions/');

%% Inputs

path = uigetdir('../../','Select path to session to clean ptClouds'); % load path to dir to clean ptClouds
%%%%               ^^^^^^^^^^^^ Queue up multiple dirs ^^^^^^^^^^^

path = [path '/mats'];
if ~exist(path, 'dir')
    disp('No mats/ directory in this session.');
    return;
end

cleanFlag = 0; % Set to 1 for manual point cloud editing, or 0 for automatic cleaning

bounds = [-5 5 -5 5 0 30];   % [xmin xmax ymin ymax zmin zmax] for trimming points (meters)

binSize = 1;    % size of the cubic bin for stepping through points (meters)

%% Process ptClouds
    
% Get all .mat files in the path
matFiles = dir(fullfile(path, '*.mat'));

% Loop through each .mat file
for i = 1:length(matFiles)
    matFile = fullfile(path, matFiles(i).name);
    fprintf('Processing file: %s\n', matFile);
    
    % Load points3D and ptCloud
    load(matFile);

    % Reshape points3D and J1 into M-by-3 format
%     [rows, cols, ~] = size(points3D);  % Get the dimensions
%     points3D_reshaped = reshape(points3D, [], 3);  % Reshape to M-by-3
%     J1_reshaped = reshape(J1, [], 3);  % Reshape color to M-by-3

    % Save previous versions with timestamp before applying changes
    timestamp = datestr(now, 'yyyymmdd_HHMMSS');
    
    % Create new variable names with timestamps
    eval(['points3D_', timestamp, ' = points3D;']);
    eval(['ptCloud_', timestamp, ' = ptCloud;']);
    
    % Save timestamped variables to the mat file
    save(matFile, ['points3D_', timestamp], ['ptCloud_', timestamp], '-append');
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%% Apply QA/QC %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%     points3D_cleaned = trimBounds(points3D_reshaped, bounds, binSize); % Update points3D after QA/QC
%     ptCloud = pointCloud(points3D_cleaned, 'Color', J1_reshaped(1:size(points3D_cleaned, 1), :)); % Create the new point cloud
% %     points3D = trimBounds(points3D, bounds, binSize); % Update points3D after QA/QC
% %     ptCloud = pointCloud(points3D, Color=J1);

    % MATLAB Point Cloud functions

    ptCloud = pcdenoise(ptCloud);



    % Save updated points3D and ptCloud
    save(matFile, 'points3D', 'ptCloud', '-append');

    % If cleanFlag is set, manually edit the point cloud using the brush tool
    if cleanFlag
        pcshow(ptCloud); % display ptCloud
        title('Use the brush tool to manually clean the point cloud');
        h = uicontrol('Style', 'pushbutton', 'String', 'Finish Editing', ...
                      'Position', [20 20 100 40], 'Callback', 'uiresume(gcbf)');
        uiwait(gcf); % Wait for user to finish editing

        % Re-save after manual editing
        points3D = ptCloud.Location; % Extract manually cleaned points3D
        save(matFile, 'points3D', 'ptCloud', '-append');
        ptCloud = pointCloud(points3D);   % Recreate ptCloud from updated points3D
    end
end
