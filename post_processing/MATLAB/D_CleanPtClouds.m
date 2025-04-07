% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-11-15

clear; clc; close all;

addpath('functions/');

%% Filepath

path = uigetdir('../../../FSR/stereo_cam/DATA/','Select path to session to clean ptClouds'); % load path to dir to clean ptClouds

matDir = [path '/L1/mats'];
if ~exist(matDir, 'dir')
    disp('No mats/ directory in this session.');
    return;
end

%% Process ptClouds

cleanFlag = 1; 
while cleanFlag
    % Choose point cloud
    file = uigetfile([path '/figs/Rectified_Images/*.png'],'Select file to view point cloud');
    file = file(1:end-9);
    
    % Load mat
    matFile = [matDir '/' file '.mat'];
    fprintf('Processing file: %s\n', matFile);
    load(matFile);

    [points3D, colors] = manualClean(points3D, colors);

    % Remove rows where any of the columns in points3D have NaNs
    validRows = all(~isnan(points3D), 2);  % Find rows where all x, y, z values are non-NaN
    
    % Keep only the valid rows in points3D and corresponding colors
    points3D = points3D(validRows, :);  % Remove rows with NaNs in points3D
    colors = colors(validRows, :);  % Keep corresponding color rows
    
    % Write updated point cloud
    ptCloud = pointCloud(points3D, 'Color', colors);

    answer = questdlg('Save changes?', ...
    'Save changes', ...
    'Yes','No','Yes');
    switch answer
        case 'Yes'
            % Save updates
            clean = 1;
            save(matFile); 
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