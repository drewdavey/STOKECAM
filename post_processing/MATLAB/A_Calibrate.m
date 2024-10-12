% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-10

clear; clc; close all;

addpath('functions/');

%% Inputs

squareSize = 45;  % in units of 'millimeters'

calib_path = uigetdir('../../','Select path to calibration session'); % load path to calibration session

dir1 = dir([calib_path '/cam1/*.jpg']); % THESE ARE FLIPPED
dir2 = dir([calib_path '/cam0/*.jpg']); % THESE ARE FLIPPED

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

%% Detect calibration pattern in images
detector = vision.calibration.stereo.CheckerboardDetector();
[imagePoints, imagesUsed] = detectPatternPoints(detector, imageFileNames1, imageFileNames2);

% Generate world coordinates for the planar patten keypoints
worldPoints = generateWorldPoints(detector, 'SquareSize', squareSize);

% Read one of the images from the first stereo pair
I1 = imread(imageFileNames1{1});
[mrows, ncols, ~] = size(I1);

% Calibrate the camera
[stereoParams, pairsUsed, estimationErrors] = estimateCameraParameters(imagePoints, worldPoints, ...
    'EstimateSkew', true, 'EstimateTangentialDistortion', true, ...
    'NumRadialDistortionCoefficients', 3, 'WorldUnits', 'millimeters', ...
    'InitialIntrinsicMatrix', [], 'InitialRadialDistortion', [], ...
    'ImageSize', [mrows, ncols]);

% View reprojection errors
h1=figure; showReprojectionErrors(stereoParams);

% Visualize pattern locations
h2=figure; showExtrinsics(stereoParams, 'CameraCentric');

% Display parameter estimation errors
displayErrors(estimationErrors, stereoParams);

%% Save mat
save([calib_path '/full_calibration.mat']);
clearvars -except stereoParams calib_path h1 h2
save([calib_path '/calib.mat']);
