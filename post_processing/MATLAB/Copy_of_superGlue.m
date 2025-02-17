% STOKECAM Post-Processing - MATLAB Rectification & Disparity Map from SuperGlue Features
% Uses keypoints extracted from Python script but applies known calibration parameters
% SuperGlue sparse keypoints guide disparity computation
% Drew Davey

clear; clc; close all;

addpath('../MATLAB/functions/');

%% Select Calibration Folder
calib_path = uigetdir('../../../FSR/stereo_cam/DATA/calibrations/', 'Select calibration session');
calib_file = fullfile(calib_path, 'calib.mat');
if ~exist(calib_file, 'file')
    error('calib.mat not found in the selected calibration folder.');
end

calib_data = load(calib_file);
if ~isfield(calib_data, 'stereoParams')
    error('stereoParams not found in calibration file. Re-run A_Calibrate.m.');
end
stereoParams = calib_data.stereoParams;

disp('Calibration parameters loaded successfully.');

%% Select Reconstruction Session
session_path = uigetdir('../../../FSR/stereo_cam/DATA/', 'Select session folder containing cam0 and cam1');
features_path = fullfile(session_path, 'features');

if ~exist(features_path, 'dir')
    mkdir(features_path);
    disp('Created features folder. Running SuperGlue for the first time...');
    cmd = sprintf('python "../Python/superGlue.py" "%s" "%s"', calib_path, features_path);
    system(cmd);
    disp('SuperGlue feature extraction completed.');
else
    disp('Features folder already exists. Skipping SuperGlue extraction.');
end

%% Process Extracted Features
mat_files = dir(fullfile(features_path, '*.mat'));
if isempty(mat_files)
    error('No feature .MAT files found in features folder. Run SuperGlue again if needed.');
end

% Load Image Files
imgL_files = dir(fullfile(session_path, 'cam1', '*.jpg'));
imgR_files = dir(fullfile(session_path, 'cam0', '*.jpg'));

if length(imgL_files) ~= length(imgR_files)
    error('Mismatch in number of images between cam0 and cam1.');
end

%% Compute Rectification Transforms from Calibration
imageSize = [1080, 1440];  % Adjust based on actual image resolution
[tform1, tform2] = estimateUncalibratedRectification(...
    stereoParams.FundamentalMatrix, ...
    stereoParams.CameraParameters1.IntrinsicMatrix', ...
    stereoParams.CameraParameters2.IntrinsicMatrix', ...
    imageSize);

disp('Rectification transforms computed using calibration parameters.');

%% Process Each Image Pair
for i = 1:length(mat_files)
    mat_path = fullfile(mat_files(i).folder, mat_files(i).name);
    data = load(mat_path);

    keypointsL = data.keypointsL;
    keypointsR = data.keypointsR;

    % Load Corresponding Images
    imgL_path = fullfile(imgL_files(i).folder, imgL_files(i).name);
    imgR_path = fullfile(imgR_files(i).folder, imgR_files(i).name);
    I1 = imread(imgL_path);
    I2 = imread(imgR_path);

    % Rectify Images Using Known Calibration Parameters
    [J1, J2] = rectifyStereoImages(I1, I2, tform1, tform2);

    % Transform SuperGlue Keypoints to Rectified Coordinates
    keypointsL_rect = transformPointsForward(tform1, keypointsL);
    keypointsR_rect = transformPointsForward(tform2, keypointsR);

    % Compute Sparse Disparity using Rectified Keypoints
    disparitySparse = keypointsL_rect(:,1) - keypointsR_rect(:,1);

    % Create an Interpolated Disparity Map Using Sparse Points
    [gridX, gridY] = meshgrid(1:size(J1,2), 1:size(J1,1));
    disparityInterpolant = scatteredInterpolant(keypointsL_rect(:,1), keypointsL_rect(:,2), disparitySparse, 'natural', 'nearest');
    disparitySparseMap = disparityInterpolant(gridX, gridY);

    % Compute Dense Disparity Map Guided by Sparse Disparity
    disparitySGM_Map = disparitySGM(im2gray(J1), im2gray(J2), 'DisparityRange', [min(disparitySparse(:)) max(disparitySparse(:))]);

    % Blend Sparse and Dense Disparity Maps
    disparityFinal = disparitySGM_Map;
    mask = ~isnan(disparitySparseMap); % Use sparse disparity where available
    disparityFinal(mask) = disparitySparseMap(mask);

    % Save Results
    imwrite(J1, fullfile(features_path, [mat_files(i).name(1:end-4) '_rectL.png']));
    imwrite(J2, fullfile(features_path, [mat_files(i).name(1:end-4) '_rectR.png']));
    imwrite(disparityFinal, fullfile(features_path, [mat_files(i).name(1:end-4) '_disp.png']));

    % Display Results
    figure;
    imshow(stereoAnaglyph(J1, J2));
    title('Rectified Stereo Images');
    figure;
    imshow(disparityFinal, [0, 64]);
    colormap jet; colorbar;
    title('Final Disparity Map with Sparse Guidance');
end

disp('Stereo reconstruction process completed successfully.');
