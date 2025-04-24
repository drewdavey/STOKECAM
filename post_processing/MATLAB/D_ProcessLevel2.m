% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2025-04-21

clear; clc; close all;

addpath('functions/');

%% Inputs

% Select NED origin
origin = 'local';
% origin = 'SIO';

% Fig res
res = 600;

g = 9.81;     % gravity

dX = 0.1;     % X step size for plotting (meters)
dY = 0.1;     % Y step size for plotting (meters)
dZ = 0.1;     % Z step size for plotting (meters)

%% Filepath

% Load path to dir to reconstruct
session = uigetdir('../../../FSR/stereo_cam/DATA','Select path to session containing wave subfolders'); 

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

%% Process Level 2
for m = 1:length(waves)
    wave = waves{m};
    dir1 = dir([wave '/cam0/*.jpg']); 
    dir2 = dir([wave '/cam1/*.jpg']); 

    %%% Create dirs and load L1 data %%%
    L1Dir = [wave '/L1'];
    L2Dir = [wave '/L2'];
    figDir = [wave '/figs'];
    
    if exist(L1Dir, 'dir')
        % Load L1 mats
        L1matFiles = dir(fullfile(L1Dir, '*.mat'));
        L1matFilenames = {L1matFiles.name};
    else
        disp('No L1 directory for this wave.');
        return;
    end
    if ~exist(L2Dir, 'dir')
        mkdir(L2Dir); % mkdir for L2
    end
    if ~exist(figDir, 'dir')
        mkdir(figDir); % mkdir for figs
    end
    
    %%% Georectification %%%
    load(fullfile(wave, 'imu.mat')); % Load IMU data

    t = imu.t0; % Relative time

    % Convert geodetic to UTM
    % [E, N, zone] = deg2utm(imu.lat, imu.lon); % Easting, Northing
    % [N, E, UTMZone] = lltoUTM(imu.lat, imu.lon);

    % Convert LLA to NED
    lla = [imu.lat; imu.lon; imu.alt]';
    % lla0 = [mean(imu.lat); mean(imu.lon); mean(imu.alt)]';
    lla0 = [(32 + 51/60. + 58.59779/3600.); -1*(117 + 15/60. + 15.40493/3600.); -20]';
    NED = lla2ned(lla, lla0, 'ellipsoid');
    N = NED(:,1); E = NED(:,2); D = NED(:,3);

    % LL to XY SIO
    [xSIO, ySIO] = lltoxy_siopier(imu.lat, imu.lon);
    
    % Geoid height correction 
    geoidHeight = geoidheight(imu.lat(1), imu.lon(1), 'EGM96'); 
    U = imu.alt - geoidHeight; % Up
    
    %%% Compute rotation matrix from quaternion %%%
    numFrames = numel(imu.quatX);
    rotationMatrices = zeros(3, 3, numFrames);
    for i = 1:numFrames
        qx = imu.quatX(i);
        qy = imu.quatY(i);
        qz = imu.quatZ(i);
        qw = imu.quatW(i);
        rotationMatrices(:, :, i) = quat2rotm([qw, qx, qy, qz]);
    end
    
    %%% Rotate and translate into NED coordinate system
    for i = 1:length(L1matFilenames)

        L1matData = load(fullfile(L1Dir, L1matFilenames{i}));

        %%%%%%%%%%%%%% Point cloud in camera reference frame %%%%%%%%%%%%%%
        xyz_cam = L1matData.points3D;

        f1 = figure(1); hold on; axis equal; grid on; axis tight;
        title('Camera reference frame');
        % scatter3(xyz_cam(:,1), xyz_cam(:,2), xyz_cam(:,3), 1);
        scatter(xyz_cam(:,1), xyz_cam(:,2), 1, xyz_cam(:,3));
        xlabel('X_{cam} (m)');
        ylabel('Y_{cam} (m)');
        zlabel('Z_{cam} (m)');
        cbar = colorbar; % Add colorbar and set its label
        cbar.Label.String = 'Z_{cam} (m)';  % Label for the colorbar
        % print(f1, fullfile(figDir, [L1matFilenames{i} '_camCoord.png']), '-dpng', ['-r', num2str(res)]);

        %%%%%%%%%%%%%% Rotate into IMU coords: XYZ_imu = +Z+X+Y_cam %%%%%%%%%%
        xyz_imu = ([0 0 1; 1 0 0; 0 1 0] * xyz_cam')'; 

        f2 = figure(2); hold on; axis equal; grid on; axis tight;
        title('IMU reference frame');
        scatter3(xyz_imu(:,1), xyz_imu(:,2), xyz_imu(:,3), 1);
        % scatter(xyz_imu(:,1), xyz_imu(:,2), 1, xyz_imu(:,3));
        xlabel('X imu'); ylabel('Y imu'); zlabel('Z imu');
        % print(f2, fullfile(figDir, [L1matFilenames{i} '_imuCoord.png']), '-dpng', ['-r', num2str(res)]);

        %%%%%%%%%%%%%%%%%%%%%% Rotation matrix %%%%%%%%%%%%%%%%%%%%%%%%%%%%
        R = rotationMatrices(:, :, i);

        xyz_NED = (R * xyz_imu')'; % Rotate and transpose

        f3 = figure(3); hold on; axis equal; grid on; axis tight;
        title('Local NED reference frame');
        xlabel('Easting (m)'); ylabel('Northing (m)'); zlabel('D world');
        scatter3(xyz_NED(:,2), xyz_NED(:,1), xyz_NED(:,3),...
            1, double(L1matData.colors) / 255, 'filled');
        % scatter3(xyz_NED(:,2), xyz_NED(:,1), xyz_NED(:,3), 1);
        % print(f3, fullfile(figDir, [L1matFilenames{i} '_NEDlocal.png']), '-dpng', ['-r', num2str(res)]);

        cam_origin = [N(i), E(i), U(1)]; % NED Origin

        %%%%%%%%%%%%%%%%%% Translate to world coord %%%%%%%%%%%%%%%%%%%%%%%
        xyz_world = cam_origin - xyz_NED;
        
        f4 = figure(4); hold on; axis equal; grid on; axis tight;
        title('World NED reference frame');
        scatter3(xyz_world(:,2), xyz_world(:,1), xyz_world(:,3),...
            1, double(L1matData.colors) / 255, 'filled');
        % scatter3(xyz_world(:,2), xyz_world(:,1), xyz_world(:,3), 1);
        % xlabel('Easting (m)'); ylabel('Northing (m)'); zlabel('D world');
        xlabel('X_{SIO} (m)', 'FontSize', 12);
        ylabel('Y_{SIO} (m)', 'FontSize', 12);
        zlabel('Z_{NAVD88} (m)', 'FontSize', 12);
        % print(f4, fullfile(figDir, [L1matFilenames{i} '_NEDworld.png']), '-dpng', ['-r', num2str(res)]);

        % Save transformed points3D, colors, and ptCloud
        points3D = xyz_world;
        colors = L1matData.colors;
        ptCloud = pointCloud(points3D, 'Color', colors);
        
        %%% Extract cross sections %%%


        % Save L2 .mat
        filename = L1matFilenames{i};
        fullFilePath = fullfile(L2Dir, filename);
        save(fullFilePath, 'points3D', 'colors', ...
        'ptCloud', 'R', 'cam_origin');
    end

    % Save figures in figDir
    print(f1, fullfile(figDir, 'camCoord.png'), '-dpng', ['-r', num2str(res)]);
    print(f2, fullfile(figDir, 'imuCoord.png'), '-dpng', ['-r', num2str(res)]);
    print(f3, fullfile(figDir, 'NEDlocal.png'), '-dpng', ['-r', num2str(res)]);
    print(f4, fullfile(figDir, 'NEDworld.png'), '-dpng', ['-r', num2str(res)]);

    % Generate L3 concatenated ptCloud from all L2 ptClouds
    genL3ptCloud(wave);

    close all; % close figs before next wave

end








