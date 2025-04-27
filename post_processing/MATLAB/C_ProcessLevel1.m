% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2025-04-21

clear; clc; close all;

addpath('functions/');

%% Inputs

% Manually clean ptClouds
% else: auto clean ptClouds (RGB and HSV thresholding + refinedTrim)
manual_clean = 1;

% Bounds for trimBounds [xmin xmax ymin ymax zmin zmax] (meters)
bounds = [-10 10 -10 10 0 30];

% Image regions for RGB and HSV thresholding
topFraction = 0.25;
bottomFraction = 0.5;
Nstd = 2; % std from RGB or HSV values

% Nstd from centroid for refinedTrim
Nstd2 = 5;

% Default resolution for figures
res = 600; % dpng

% Define calibration path
calib_path = 'C:\Users\drew\OneDrive - UC San Diego\FSR\stereo_cam\DATA\calibrations\calib4_SIO';
load([calib_path '/calib.mat']); 

%% Process Level 1

% Load path to dir to reconstruct
session = uigetdir('../../../FSR/stereo_cam/DATA/','Select path to session containing wave subfolders'); 

% %%% Session QC figs %%%
% figDir = [session '/figs'];
% if ~exist(figDir, 'dir')
%     mkdir(figDir);                     % mkdir for figs
%     imu = parse_imu(session, session); % Parse imu data into struct
%     basicQCplots(imu, figDir, res);    % Plot basic QC figs
% end

% Find subfolders that start with "wave"
waveSubfolders = dir(fullfile(session, 'wave*'));
waveSubfolders = waveSubfolders([waveSubfolders.isdir]); 
if isempty(waveSubfolders)
    fprintf('No wave subfolders found in %s\n', session);
    return;
end

% Initialize waves array
waves = {};

% Loop over each matching entry
for i = 1:numel(waveSubfolders)
    if waveSubfolders(i).isdir
        % Build full path to subfolder
        wavePath = fullfile(session, waveSubfolders(i).name);
        % Append to the cell array
        waves{end + 1} = wavePath;
    end
end

% Process each selected path
for m = 1:length(waves)
    wave = waves{m};

    dir1 = dir([wave '/cam0/*.jpg']); 
    dir2 = dir([wave '/cam1/*.jpg']); 
    % dir1 = dir([wave '/cam1/*.jpg']); 
    % dir2 = dir([wave '/cam0/*.jpg']); 

    %%% Create dirs %%%
    L1Dir = [wave '/L1'];
    figDir = [wave '/figs'];
    dispDir = [figDir '/disparityMaps']; 
    
    if ~exist(L1Dir, 'dir')
        mkdir(L1Dir); % mkdir for L1
    end
    if ~exist(dispDir, 'dir')
        mkdir(dispDir); % mkdir for rectified images
    end
    if ~exist(figDir, 'dir')
        mkdir(figDir); % mkdir for figs
    end

    %%% Parse Vectornav data %%%
    imu = parse_imu(session, wave); % Parse imu data into struct
    % basicQCplots(imu, figDir, res); % Plot basic QC figs
    save(fullfile(wave, 'imu.mat'), 'imu'); % Save VN-200 data to L1
    close all; % Close QC figs

    %%% Rectify images %%%
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
    
        % Rectify Images
        [J1, J2, reprojectionMatrix] = rectifyStereoImages(I1, I2, stereoParams, OutputView='valid'); 
        frameLeftGray  = im2gray(J1);
        frameRightGray = im2gray(J2);

        %%%%%%%%%%%%% Semi-Global Block Matching %%%%%%%%%%%%%
        disparityMap = disparitySGM(frameLeftGray, frameRightGray); 
    
        % Extract timestamp and image number from selected file
        [cameraID, timestamp, imageNum] = parse_filename(imageFileNames1{i}(end-24:end));
    
        % Plotting
        f1 = figure(1); 
        imshow(disparityMap, [0, 64]); % Display disparity map
        colormap jet; colorbar;
        filename = [timestamp '_' imageNum '.png'];
        fullFilePath = fullfile(dispDir, filename);
        exportgraphics(f1,fullFilePath,'Resolution',res); % Save disparity map as PNG

        % Create points3D
        points3D = reconstructScene(disparityMap, reprojectionMatrix);
        points3D = points3D ./ 1000; % Convert to meters
        
        % Use J1 as color matrix
        colors = J1;
    
        % Create point cloud
        ptCloud = pointCloud(points3D, 'Color', colors);

        % Duplicate originals
        raw.points3D = points3D;
        raw.colors = colors;
        raw.ptCloud = ptCloud;

        % Reshape points3D into an Nx3 matrix
        points3D = reshape(points3D, [], 3);  
        
        % Reshape colors into an Nx3 matrix
        colors = reshape(colors, [], 3);  
    
        %%% L1 cleaning of point clouds %%%
        % Trim to bounding box
        [points3D, colors] = trimBounds(points3D, colors, bounds);

        % Manually clean ptClouds
        if manual_clean
            % Trim to polygon
            [points3D, colors] = refinedTrimPolygon(points3D, colors, J1);
            % Brush points
            [points3D, colors] = manualClean(points3D, colors);
        else
            % Threshold foreground/background by HSV
            [points3D, colors] = colorThreshHSV(points3D, colors, J1, ...
                                          topFraction, bottomFraction, Nstd);
            % Threshold foreground/background by RGB
            [points3D, colors] = colorThreshRGB(points3D, colors, J1, ...
                                          topFraction, bottomFraction, Nstd);
            % Trim points >= Nstd from centroid
            [points3D, colors] = refinedTrim(points3D, colors, Nstd2);
        end

        % Remove rows where any of the columns in points3D have NaNs
        validRows = all(~isnan(points3D), 2);  % Find rows where all x, y, z values are non-NaN
        
        % Keep only the valid rows in points3D and corresponding colors
        points3D = points3D(validRows, :);  % Remove rows with NaNs in points3D
        colors = colors(validRows, :);      % Keep corresponding color rows
        
        % Write updated point cloud
        ptCloud = pointCloud(points3D, 'Color', colors);

        % Send clean flag
        clean = 1; 
   
        % Save L1 .mat
        filename = [timestamp '_' imageNum];
        fullFilePath = fullfile(L1Dir, filename);
        save(fullFilePath,'I1','I2','J1','J2','frameLeftGray',...
            'frameRightGray','reprojectionMatrix','disparityMap', ...
            'calib_path', 'raw', 'points3D', 'colors', ...
            'ptCloud', 'clean');
    end
end

close all; % Close disparity map