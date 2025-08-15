% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-11-15

clear; clc; close all;

addpath('functions/');

%% Inputs

default_calib = 'C:\Users\drew\OneDrive - UC San Diego\FSR\stereo_cam\DATA\calibrations\calib6_SIO';

def_calib = 0;   % default calib (0) or select calib (1)
BM_SGBM = 0;     % default semi-global block matching? (0) use block matching? (1)
specs = 0;       % default specs (0) or input specs (1)
plys = 0;        % save .plys seperate in a 'ptCloud' directory?

% Applied to BM & SGBM
UniquenessThreshold = 5;       % only applied if specs

% Applied to BM only
DisparityRange = [0 64];       % only applied if specs
BlockSize = 15;                % only applied if specs
ContrastThreshold = 0.25;      % only applied if specs
DistanceThreshold = 20;        % only applied if specs
TextureThreshold = 0.00002;    % only applied if specs

%% Filepath

% Initialize paths array
paths = {};

path = uigetdir('../../../FSR/stereo_cam/DATA/','Select path to session for reconstruction'); % load path to dir to reconstruct
paths{end + 1} = path;  % Add selected session to paths array

% Queue up additional sessions?
while true
    answer = questdlg('Queue another session?', ...
    'Queue another session?', ...
    'Yes','No','Yes');
    switch answer
        case 'Yes'
            path = uigetdir([path '/../'],'Select path to session for reconstruction');
        case 'No' 
            break;
    end
    paths{end + 1} = path;  % Add selected directory to paths array
end

% Process each selected path
for m = 1:length(paths)
    path = paths{m};

    % WasteMgmtAuto(path); % Run WasteMgmt on path

    dir1 = dir([path '/cam0/*.jpg']); 
    dir2 = dir([path '/cam1/*.jpg']); 
    % dir1 = dir([path '/cam1/*.jpg']); % THESE ARE FLIPPED
    % dir2 = dir([path '/cam0/*.jpg']); % THESE ARE FLIPPED
    
    %% Load calibration and create dirs
    
    if def_calib
        calib_path = uigetdir('../../../FSR/stereo_cam/DATA/calibrations/', 'Select path to calibration session'); % load path to calibration session
    else
        calib_path = default_calib;
    end
    
    load([calib_path '/calib.mat']);
    pause(2); close(gcf); pause(2); close(gcf);
    % uiwait(gcf); uiwait(gcf); 
    
    matDir = [path '/mats'];
    rectifiedImagesDir = [path '/Rectified_Images']; 
    % rectifiedImagesDir = [path '/Rectified_Images_histMatch']; 
    ptCloudDir = [path '/ptClouds'];
    
    if ~exist(rectifiedImagesDir, 'dir')
        mkdir(rectifiedImagesDir); % mkdir for rectified images
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

        % Extract timestamp and image number from selected file
        [cameraID, timestamp, imageNum] = parse_filename(imageFileNames1{i}(end-24:end));
        % 
        % %%% Histogram matching %%%
        % % Plot hist matching
        % f1 = figure(1);
        % subplot(2,1,1);
        % montage({I1,I2});
        % title('cam0 (Left) vs cam1 (Right)');
        % I1 = imhistmatch(I1,I2,256,'method','polynomial'); % use polynomial matched I1
        % % K = imhistmatch(I1,I2,'method','uniform');
        % subplot(2,1,2);
        % montage({I1,I2});
        % title('Histogram-Matched cam0 (Left) vs cam1 (Right)');
        % filename = [timestamp '_' imageNum '_hist.png'];
        % fullFilePath = fullfile(rectifiedImagesDir, filename);
        % % exportgraphics(f1,fullFilePath,'Resolution',600); % Save rectified images as PNG
    
        %%% Rectify Images %%%
        [J1, J2, reprojectionMatrix] = rectifyStereoImages(I1, I2, stereoParams, OutputView='valid'); 
        %[J1, J2, reprojectionMatrix] = rectifyStereoImages(I1, I2, stereoParams, OutputView='full'); 
        frameLeftGray  = im2gray(J1);
        frameRightGray = im2gray(J2);
        %%%%%%%%%%%%%%%%%%%%%%%
    
        %%%%%%%%%%%%% Compute Disparity Map %%%%%%%%%%%%%%%%%%
        if BM_SGBM
            %%%%%%%%%%%%% Block Matching %%%%%%%%%%%%%
            if specs
                disparityMap = disparityBM(frameLeftGray, frameRightGray,'DisparityRange', DisparityRange,...
                    'BlockSize', BlockSize,...
                    'UniquenessThreshold', UniquenessThreshold,...
                    'ContrastThreshold', ContrastThreshold,...
                    'DistanceThreshold', DistanceThreshold,...
                    'TextureThreshold', TextureThreshold);
            else
                disparityMap = disparityBM(frameLeftGray, frameRightGray); % default block matching
            end
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        else
            %%%%%%%%%%%%% Semi-Global Block Matching %%%%%%%%%%%%%
            if specs
                disparityMap = disparitySGM(frameLeftGray, frameRightGray, 'UniquenessThreshold', UniquenessThreshold, 'DisparityRange', DisparityRange); 
            else
                disparityMap = disparitySGM(frameLeftGray, frameRightGray, 'DisparityRange', DisparityRange); % default semi-global matching
            end
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
        end
        %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
        % Plotting
        f2 = figure(2); 
        imshow(disparityMap, [0, 64]); % Display disparity map
        colormap jet; colorbar;
        filename = [timestamp '_' imageNum '_disp.png'];
        fullFilePath = fullfile(rectifiedImagesDir, filename);
        exportgraphics(f2,fullFilePath,'Resolution',600); % Save disparity map as PNG
    end
end