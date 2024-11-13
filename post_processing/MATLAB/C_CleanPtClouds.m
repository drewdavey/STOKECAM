% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-10

clear; clc; close all;

addpath('functions/');

%% Inputs

trimFlag = 1;       % trim to refined polygon
basicFlag = 1;      % basic QC and trim to bbox        
colorFlag = 0;      % filter by RGB thresholds
manualFlag = 1;     % manually clean 

bounds = [-10 10 -10 10 0 30];   % [xmin xmax ymin ymax zmin zmax] for trimming points (meters)

%% Filepath

path = uigetdir('../../../FSR/stereo_cam/DATA/','Select path to session to clean ptClouds'); % load path to dir to clean ptClouds

matDir = [path '/mats'];
if ~exist(matDir, 'dir')
    disp('No mats/ directory in this session.');
    return;
end

%% Process ptClouds

cleanFlag = 1; 
while cleanFlag
    % Choose point cloud
    file = uigetfile([path '/Rectified_Images/*.png'],'Select file to view point cloud');
    file = file(1:end-9);
    
    % Load mat
    matFile = [matDir '/' file '.mat'];
    fprintf('Processing file: %s\n', matFile);
    load(matFile);

    % Timestamp prior to changes
    timestamp = datestr(datetime('now'), 'yyyymmdd_HHMMSS');
    
    % Create new variable names with timestamps
    data.(['points3D_', timestamp]) = data.points3D;
    data.(['ptCloud_', timestamp]) = data.ptCloud;
    data.(['colors_', timestamp]) = data.colors;
    data.bounds = bounds;

    %%%%%%%%%%%%%%%%%%%%%%%%%%% Apply QA/QC %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    if trimFlag
        [data.points3D, data.colors] = refinedTrim(J1, data.points3D, data.colors);
        
        % Write updated point cloud
        data.ptCloud = pointCloud(data.points3D, 'Color', data.colors);
        data.clean = 1;
    end

    if basicFlag
        [data.points3D, data.colors] = trimBounds(data.points3D, data.colors, data.bounds); % Trim to bounds
    
        % Remove rows where any of the columns in points3D have NaNs
        validRows = all(~isnan(data.points3D), 2);  % Find rows where all x, y, z values are non-NaN
    
        % Keep only the valid rows in points3D and corresponding colors
        data.points3D = data.points3D(validRows, :);  % Remove rows with NaNs in points3D
        data.colors = data.colors(validRows, :);  % Keep corresponding color rows
    
        data.ptCloud = pointCloud(data.points3D, 'Color', data.colors);
        data.ptCloud = pcdenoise(data.ptCloud);
    end

    if colorFlag
        [data.points3D, data.colors] = colorThresh(J1, data.points3D, data.colors);
        
        % Write updated point cloud
        data.ptCloud = pointCloud(data.points3D, 'Color', data.colors);
        data.clean = 1;
    end

    if manualFlag
        [data.points3D, data.colors] = manualClean(data.points3D, data.colors);
        
        % points3D(:,2) = -points3D(:,2);  % Flip the sign of the Y dimension
        % points3D(:,1) = -points3D(:,1);  % Flip the sign of the X dimension
        
        % Write updated ptCloud
        data.ptCloud = pointCloud(data.points3D, 'Color', data.colors);
        data.clean = 1;
    end

    answer = questdlg('Save changes?', ...
    'Save changes', ...
    'Yes','No','Yes');
    switch answer
        case 'Yes'
            % Save updates
            save(matFile, 'data', '-append'); 
        case 'No'
            return 
    end

    answer = questdlg('Clean another point cloud?', ...
    'Clean another point cloud', ...
    'Yes','No','Yes');
    switch answer
        case 'Yes'
            cleanFlag = 1; 
        case 'No'
            cleanFlag = 0; 
    end
end