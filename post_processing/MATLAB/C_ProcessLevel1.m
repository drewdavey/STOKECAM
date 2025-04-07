% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-11-15

clear; clc; close all;

addpath('functions/');

%% Inputs

% Define calibration path
calib_path = 'C:\Users\drew\OneDrive - UC San Diego\FSR\stereo_cam\DATA\calibrations\calib4_SIO';
load([calib_path '/calib.mat']); 

% Feature matching
BM_SGBM = 0;     % default semi-global block matching? (0) use block matching? (1)
specs = 0;       % default specs (0) or input specs (1)

% Applied to BM & SGBM
UniquenessThreshold = 0;       % only applied if specs

% Applied to BM only
DisparityRange = [0 64];       % only applied if specs
BlockSize = 25;                % only applied if specs
ContrastThreshold = 0.25;       % only applied if specs
DistanceThreshold = 20;        % only applied if specs
TextureThreshold = 0.00002;    % only applied if specs

% Bounds for trimBounds (meters)
bounds = [-10 10 -10 10 0 30];   % [xmin xmax ymin ymax zmin zmax] 

% Default resolution for figures
res = 600; % dpng

% Image regions for RGB and HSV thresholding
topFraction = 0.25;
bottomFraction = 0.5;
Nstd = 2; % std from RGB or HSV values

% Nstd from centroid for refinedTrim
Nstd2 = 3;

%% Filepath

% Load path to dir to reconstruct
session = uigetdir('../../../FSR/stereo_cam/DATA/','Select path to session containing wave subfolders'); 

% Find subfolders that start with "wave"
waveSubfolders = dir(fullfile(session, 'wave*'));

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

    % WasteMgmtAuto(wave); % Run WasteMgmt on wave

    dir1 = dir([wave '/cam0/*.jpg']); 
    dir2 = dir([wave '/cam1/*.jpg']); 
    % dir1 = dir([wave '/cam1/*.jpg']); % THESE ARE FLIPPED
    % dir2 = dir([wave '/cam0/*.jpg']); % THESE ARE FLIPPED
    
    %% Create dirs

    %%%%% THIS WILL OVERWRITE PREVIOUS L1 DATA IF IT EXISTS %%%%%
    L1Dir = [wave '/L1'];
    figDir = [wave '/figs'];
    matDir = [L1Dir '/mats'];
    rectifiedImagesDir = [figDir '/Rectified_Images']; 
    
    if ~exist(L1Dir, 'dir')
        mkdir(L1Dir); % mkdir for L1
    end

    if ~exist(rectifiedImagesDir, 'dir')
        mkdir(rectifiedImagesDir); % mkdir for rectified images
    end

    if ~exist(matDir, 'dir')
        mkdir(matDir); % mkdir for mats
    end

    if ~exist(figDir, 'dir')
        mkdir(figDir); % mkdir for figs
    end

    %% Parse Vectornav data

    imu = parse_imu(session, wave); % Parse imu data into struct

    basicQCplots(imu, figDir, res); % Plot basic QC figs

    save(fullfile(L1Dir, 'imu.mat'), 'imu'); % Save VN-200 data to L1

    close all; % Close QC figs

    %% Rectify images
     
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
        %[J1, J2, reprojectionMatrix] = rectifyStereoImages(I1, I2, stereoParams, OutputView='full'); 
        frameLeftGray  = im2gray(J1);
        frameRightGray = im2gray(J2);
    
        % Compute Disparity Map
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
        else

            %%%%%%%%%%%%% Semi-Global Block Matching %%%%%%%%%%%%%
            if specs
                disparityMap = disparitySGM(frameLeftGray, frameRightGray, 'UniquenessThreshold', UniquenessThreshold); 
            else
                disparityMap = disparitySGM(frameLeftGray, frameRightGray); % default semi-global matching
            end
    
        end
    
        % Extract timestamp and image number from selected file
        [cameraID, timestamp, imageNum] = parse_filename(imageFileNames1{i}(end-24:end));
    
        % Plotting
        % f1 = figure(1);
        % imshow(stereoAnaglyph(J1,J2)); % Display rectified images
        % filename = [timestamp '_' imageNum '_rect.png'];
        % fullFilePath = fullfile(rectifiedImagesDir, filename);
        % exportgraphics(f1,fullFilePath,'Resolution',600); % Save rectified images as PNG
        figure; 
        imshow(disparityMap, [0, 64]); % Display disparity map
        colormap jet; colorbar;
        filename = [timestamp '_' imageNum '_disp.png'];
        fullFilePath = fullfile(rectifiedImagesDir, filename);
        exportgraphics(gcf,fullFilePath,'Resolution',res); % Save disparity map as PNG
    
        % Create points3D
        points3D = reconstructScene(disparityMap, reprojectionMatrix);
        points3D = points3D ./ 1000; % Convert to meters
        
        % Use J1 as color matrix
        colors = J1;
    
        % Create point cloud
        ptCloud = pointCloud(points3D, 'Color', colors);

        % Duplicate originals
        original.points3D = points3D;
        original.colors = colors;
        original.ptCloud = ptCloud;

        % Reshape points3D into an Nx3 matrix
        points3D = reshape(points3D, [], 3);  
        
        % Reshape colors into an Nx3 matrix
        colors = reshape(colors, [], 3);  
    
        %% L1 cleaning of point clouds

        [points3D, colors] = trimBounds(points3D, colors, bounds);

        [points3D, colors] = colorThreshHSV(points3D, colors, J1, ...
                                      topFraction, bottomFraction, Nstd);

        [points3D, colors] = colorThreshRGB(points3D, colors, J1, ...
                                      topFraction, bottomFraction, Nstd);

        [points3D, colors] = refinedTrim(points3D, colors, Nstd2);

        % Remove rows where any of the columns in points3D have NaNs
        validRows = all(~isnan(points3D), 2);  % Find rows where all x, y, z values are non-NaN
        
        % Keep only the valid rows in points3D and corresponding colors
        points3D = points3D(validRows, :);  % Remove rows with NaNs in points3D
        colors = colors(validRows, :);  % Keep corresponding color rows
        
        % Write updated point cloud
        ptCloud = pointCloud(points3D, 'Color', colors);
        
        % MATLAB denoise ptCloud
        ptCloud = pcdenoise(ptCloud);

        % Send clean flag
        clean = 1; 
   
        % Save .mat
        filename = [timestamp '_' imageNum];
        fullFilePath = fullfile(matDir, filename);
        save(fullFilePath,'I1','I2','J1','J2','frameLeftGray',...
            'frameRightGray','reprojectionMatrix','disparityMap', ...
            'calib_path', 'original', 'points3D', 'colors', ...
            'ptCloud', 'clean');
    end

end