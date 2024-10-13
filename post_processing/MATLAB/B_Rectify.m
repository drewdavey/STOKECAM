% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-10

clear; clc; close all;

addpath('functions/');

%% Inputs

def_calib = 0;   % default calib (0) or select calib (1)
BM_SGBM = 0;     % default semi-global block matching? (0) use block matching? (1) 
specs = 0;       % default specs (0) or input specs (1)
plys = 0;        % save .plys seperate in a 'ptCloud' directory?

DisparityRange = [0 64];       % only applied if specs
BlockSize = 11;                % only applied if specs
ContrastThreshold = 0.5;       % only applied if specs
UniquenessThreshold = 15;      % only applied if specs
DistanceThreshold = 20;        % only applied if specs
TextureThreshold = 0.00002;    % only applied if specs

path = uigetdir('../../','Select path to session for reconstruction'); % load path to dir to reconstruct
%%%%               ^^^^^^^^^^^^ Queue up multiple dirs ^^^^^^^^^^^

dir1 = dir([path '/cam1/*.jpg']); % THESE ARE FLIPPED
dir2 = dir([path '/cam0/*.jpg']); % THESE ARE FLIPPED

%% Load calibration and create dirs

if def_calib
    calib_path = uigetdir('../../','Select path to calibration session'); % load path to calibration session
else
    calib_path = 'C:\Users\drew\OneDrive - UC San Diego\FSR\stereo_cam\DATA\calibrations\calib2_SIO'; 
end

load([calib_path '/calib.mat']); uiwait(gcf); uiwait(gcf); 

matDir = [path '/mats'];
rectifiedImagesDir = [path '/Rectified_Images']; 
ptCloudDir = [path '/ptClouds'];

if ~exist(rectifiedImagesDir, 'dir')
    mkdir(rectifiedImagesDir); % mkdir for rectified images
end
if plys && ~exist(ptCloudDir, 'dir')
    mkdir(ptCloudDir); % mkdir for ptClouds
end
if ~exist(matDir, 'dir')
    mkdir(matDir); % mkdir for .mats
else 
    answer = questdlg('Overwrite?', ...
    'Overwrite existing directories? ', ...
    'Yes','No','Yes');
    switch answer
        case 'Yes'
            disp('Overwriting previous files...'); 
        case 'No'
            disp('Exiting.'); 
            return;
    end
end

%% Parse data
 
% Check the number of files in each directory
numFiles = min(length(dir1), length(dir2));

% Initialize arrays to store file paths
imageFileNames1 = cell(numFiles, 1);
imageFileNames2 = cell(numFiles, 1);

% Construct file paths for each directory
for i = 1:numFiles
    imageFileNames1{i} = fullfile(dir1(i).folder, dir1(i).name);
    imageFileNames2{i} = fullfile(dir2(i).folder, dir2(i).name);
end

% Loop through each frame
for i = 1:length(imageFileNames1)
    I1 = imread(imageFileNames1{i});
    I2 = imread(imageFileNames2{i});

    %%% Rectify Images %%%
    [J1, J2, reprojectionMatrix] = rectifyStereoImages(I1, I2, stereoParams,OutputView='valid'); 
    %[J1, J2, reprojectionMatrix] = rectifyStereoImages(I1, I2, stereoParams,OutputView='full'); 
    frameLeftGray  = im2gray(J1);
    frameRightGray = im2gray(J2);
    %%%%%%%%%%%%%%%%%%%%%%%

    %%%%%%%%%%%%% Compute Disparity Map %%%%%%%%%%%%%%%%%%
    if BM_SGBM
        %%%%%%%%%%%%% Block Matching %%%%%%%%%%%%%
        if specs
            disparityMap = disparityBM(frameLeftGray, frameRightGray,'DisparityRange',DisparityRange,...
                'BlockSize',BlockSize,...
                'UniquenessThreshold',UniquenessThreshold,...
                'ContrastThreshold', ContrastThreshold,...
                'DistanceThreshold',DistanceThreshold,...
                'TextureThreshold',TextureThreshold);
        else
            disparityMap = disparityBM(frameLeftGray, frameRightGray); % default block matching
        end
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    else
        %%%%%%%%%%%%% Semi-Global Block Matching %%%%%%%%%%%%%
        if specs
            disparityMap = disparitySGM(frameLeftGray, frameRightGray,'UniquenessThreshold',UniquenessThreshold); 
        else
            disparityMap = disparitySGM(frameLeftGray, frameRightGray); % default semi-global matching
        end
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    end
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    % Extract timestamp and image number from selected file
    [cameraID, timestamp, imageNum] = parse_filename(imageFileNames1{i}(end-24:end));

    % Plotting
    f1 = figure(1);
    imshow(stereoAnaglyph(J1,J2)); % Display rectified images
    filename = [timestamp '_' imageNum '_rect.png'];
    fullFilePath = fullfile(rectifiedImagesDir, filename);
    exportgraphics(f1,fullFilePath,'Resolution',600); % Save rectified images as PNG
    f2 = figure(2); 
    imshow(disparityMap, [0, 64]); % Display disparity map
    colormap jet; colorbar;
    filename = [timestamp '_' imageNum '_disp.png'];
    fullFilePath = fullfile(rectifiedImagesDir, filename);
    exportgraphics(f2,fullFilePath,'Resolution',600); % Save disparity map as PNG

    % Create points3D
    points3D = reconstructScene(disparityMap, reprojectionMatrix); % for single disparity map
    points3D = points3D ./ 1000; % Convert to meters and create a pointCloud object

    % Reshape the point cloud data into an Nx3 matrix
    points3D = reshape(points3D, [], 3);  % Convert to N x 3 format for point cloud
    % Reshape the color information into an Nx3 matrix
    colors = reshape(J1, [], 3);  % Convert to N x 3 format for RGB colors

   % Flip the sign of Y
%     points3D(:,2) = -points3D(:,2);  % Flip the sign of the Y dimension

    % Create point cloud
    ptCloud = pointCloud(points3D, 'Color', colors);
    ptCloud_orig = pointCloud(points3D, 'Color', colors);

    % Send clean flag
    clean = 0;

    if plys 
        filename = [timestamp '_' imageNum];
        fullFilePath = fullfile(ptCloudDir, filename);
        pcwrite(ptCloud_orig, fullFilePath); % Save ptCloud as .ply
    end 

    % Save .mat
    filename = [timestamp '_' imageNum];
    fullFilePath = fullfile(matDir, filename);
    save(fullFilePath,'I1','I2','J1','J2','frameLeftGray',...
        'frameRightGray','reprojectionMatrix','disparityMap', ...
        'calib_path', 'ptCloud_orig','ptCloud', 'points3D','colors','clean');
end
