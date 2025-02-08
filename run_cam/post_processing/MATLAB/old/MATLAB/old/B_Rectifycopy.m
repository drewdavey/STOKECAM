% Stereo Reconstruction Code
% Drew Davey
% Last updated: 2024-03-17

clear; clc; close all;

%% Load mat and create dir
calib_path = uigetdir('../../','Select path to calibration session'); % load path to calibration session
load([calib_path '/calib.mat']);

path = uigetdir('../../','Select path to session for reconstruction'); % load path to dir to reconstruct

matDir = [path '/mats'];
if ~exist(matDir, 'dir')
    mkdir(matDir); % mkdir for .mats
end

rectifiedImagesDir = [path '/Rectified_Images']; 
if ~exist(rectifiedImagesDir, 'dir')
    mkdir(rectifiedImagesDir); % mkdir for rectified images
end

dir1 = dir([path '/cam1/*.jpg']);
dir2 = dir([path '/cam0/*.jpg']);

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
    
%     I1 = im2gray(I1);
%     I2 = im2gray(I2);

    %%% Rectify Images %%%
    [J1, J2, reprojectionMatrix] = rectifyStereoImages(I1, I2, stereoParams,OutputView='valid'); 
%     [J1, J2, reprojectionMatrix] = rectifyStereoImages(I1, I2, stereoParams,OutputView='full'); 
    frameLeftGray  = im2gray(J1);
    frameRightGray = im2gray(J2);
    %%%%%%%%%%%%%%%%%%%%%%%

    %%% Compute Disparity Map %%%
%     DisparityRange = [0 64];
%     BlockSize = 25;
%     ContrastThreshold = 0.5;
%     UniquenessThreshold = 15;
%     DistanceThreshold = 20;
%     TextureThreshold = 0.00002;

%     disparityMap = disparityBM(frameLeftGray, frameRightGray); % block matching
%     disparityMap = disparityBM(frameLeftGray, frameRightGray,'DisparityRange',DisparityRange,...
%         'BlockSize',BlockSize,...
%         'UniquenessThreshold',UniquenessThreshold,...
%         'ContrastThreshold', ContrastThreshold,...
%         'DistanceThreshold',DistanceThreshold,...
%         'TextureThreshold',TextureThreshold);
                       % use J1 and J2?

    disparityMap = disparitySGM(frameLeftGray, frameRightGray);
%     disparityMap = disparitySGM(frameLeftGray, frameRightGray,'UniquenessThreshold',UniquenessThreshold); % semi-global matching
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    % Plotting
    f1 = figure(1);
    imshow(stereoAnaglyph(J1,J2)); % Display rectified images
    filename = [imageFileNames1{i}(end-18:end-4) '_rect.png'];
    fullFilePath = fullfile(rectifiedImagesDir, filename);
    exportgraphics(f1,fullFilePath,'Resolution',600); % Save rectified images as PNG
    f2 = figure(2); 
    imshow(disparityMap, [0, 64]); % Display disparity map
    colormap jet; colorbar;
    filename = [imageFileNames1{i}(end-18:end-4) '_disp.png'];
    fullFilePath = fullfile(rectifiedImagesDir, filename);
    exportgraphics(f2,fullFilePath,'Resolution',600); % Save disparity map as PNG

    % Save .mat
    filename = imageFileNames1{i}(end-18:end-4);
    fullFilePath = fullfile(matDir, filename);
    save(fullFilePath,'I1','I2','J1','J2','frameLeftGray', 'frameRightGray','reprojectionMatrix','disparityMap','calib_path');
    
end

%% Write rectified images as a movie
% outputVideo = VideoWriter(fullfile(rectifiedImagesDir, 'rectified_movie'));
% outputVideo.FrameRate = 5;
% open(outputVideo);
% for i = 1:length(imageFileNames1)
%     filename = [imageFileNames1{i}(end-18:end-4) '_rect.png'];
%     fullFilePath = fullfile(rectifiedImagesDir, filename);
%     img = imread(fullFilePath);
%     writeVideo(outputVideo, img);
% end
% close(outputVideo);
% 
% %% Write disparity images as a movie
% outputVideo = VideoWriter(fullfile(rectifiedImagesDir, 'disparity_movie'));
% outputVideo.FrameRate = 5;
% open(outputVideo);
% for i = 1:length(imageFileNames1)
%     filename = [imageFileNames1{i}(end-18:end-4) '_disp.png'];
%     fullFilePath = fullfile(rectifiedImagesDir, filename);
%     img = imread(fullFilePath);
%     writeVideo(outputVideo, img);
% end
% close(outputVideo);

