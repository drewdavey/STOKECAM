% Generate Point Clouds
% Drew Davey
% Last updated: 2024-03-17 

clear; clc; close all;

%% Inputs

path = uigetdir('../../','Select path to session for point cloud generation'); % load path to dir

%% File management

ptCloudDir = [path '/ptClouds'];
if ~exist(ptCloudDir, 'dir')
    mkdir(ptCloudDir); % mkdir for ptClouds
end

matDir = [path '/mats'];
dir = dir([path '/mats/*.mat']);

% Check the number of files in directory
numFiles = length(dir);

% Initialize arrays to store file paths
matFileNames = cell(numFiles, 1);

% Construct file paths for each directory
for i = 1:numFiles
    matFileNames{i} = fullfile(dir(i).folder, dir(i).name);
end

%% Generate point clouds

for i = 1:length(matFileNames)

    load(matFileNames{i});

    % Create point cloud
    points3D = reconstructScene(disparityMap, reprojectionMatrix); % for single disparity map
    points3D = points3D ./ 1000; % Convert to meters and create a pointCloud object
    ptCloud = pointCloud(points3D, Color=J1);

    % Append ptCloud to mat
    save(matFileNames{i},'ptCloud','-append');

    % Save ptCloud as .ply
    filename = matFileNames{i}(end-18:end-4);
    fullFilePath = fullfile(ptCloudDir, filename);
    pcwrite(ptCloud, fullFilePath);
    
end
