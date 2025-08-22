% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2025-04-21

clear; clc; close all;

addpath('functions/');

%% Inputs

squareSize = 45;  % in units of 'millimeters'

focalLength = 6; % mm

pixelSize = 0.00345; % mm

sx = 1440; % x pixels
sy = 1080; % y pixels

cx = sx / 2; % optical center
cy = sy / 2;

fx = focalLength / pixelSize;
fy = focalLength / pixelSize;

s = 0;

InitialK = [fx s cx; 0 fy cy; 0 0 1];

%% Filepath

calib_path = uigetdir('../../../FSR/stereo_cam/DATA','Select path to calibration session'); % load path to calibration session

dir1 = dir([calib_path '/cam0/*.jpg']); 
dir2 = dir([calib_path '/cam1/*.jpg']); 

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
clearvars -except stereoParams calib_path %h1 h2 % comment h1/h2 if you don't want figs to pop up
save([calib_path '/calib.mat']);

%% Convert MATLAB to OpenCV format
% --- Intrinsics (MATLAB IntrinsicMatrix is transposed vs OpenCV) ---
K0 = stereoParams.CameraParameters1.K; % [fx 0 cx; 0 fy cy; 0 0 1]
K1 = stereoParams.CameraParameters2.K;

% --- Distortion to OpenCV order: [k1 k2 p1 p2 k3] ---
rd1 = stereoParams.CameraParameters1.RadialDistortion;     % [k1 k2 (k3)]
td1 = stereoParams.CameraParameters1.TangentialDistortion; % [p1 p2]
k3_1 = 0; if numel(rd1) >= 3, k3_1 = rd1(3); end
D0 = [rd1(1) rd1(2) td1(1) td1(2) k3_1];

rd2 = stereoParams.CameraParameters2.RadialDistortion;
td2 = stereoParams.CameraParameters2.TangentialDistortion;
k3_2 = 0; if numel(rd2) >= 3, k3_2 = rd2(3); end
D1 = [rd2(1) rd2(2) td2(1) td2(2) k3_2];

% --- Extrinsics of cam2 w.r.t. cam1 ---
R = stereoParams.PoseCamera2.Rotation;           % 3x3
T = stereoParams.PoseCamera2.Translation(:);       % 3x1 

% --- Image size as [W H] for OpenCV ---
sz = stereoParams.CameraParameters1.ImageSize; % [H W]
image_size = [sz(2) sz(1)];

% --- Pack and write JSON ---
calib = struct('K0',K0,'D0',D0,'K1',K1,'D1',D1,'R',R,'T',T,'image_size',image_size);
txt   = jsonencode(calib, 'PrettyPrint', true);
outf = fullfile(calib_path, 'calib.json');
fid  = fopen(outf, 'w'); assert(fid>0, 'Cannot open file for write.');
fwrite(fid, txt, 'char'); fclose(fid);
