% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2025-04-21

clear; clc; close all;

addpath('functions/');

%% Inputs

% Process all waves in session?
processAll = 0;

% Input origin [lat, lon]. Defaults to local origin if none specified.
origin = [32.866277163888888, -117.2542791472222]; % SIO

% Rotate wave field?
rotate = 0;
theta_deg = 50; % rotation angle CCW
x_offset = 0;   % translate x
y_offset = 0;   % translate y

% Brighten point colors?
brighten = 0;
brightenFactor = 2;

% Denoise ptClouds?
denoise = 1;

% Downsample ptClouds?
downsample = 0;
randPerc = 0.5; % randomly downsample 50%

% Generate QC figs?
figs = 1;
res = 600; % Figure resolution

g = 9.81;     % gravity

dX = 0.1;     % X step size for plotting (meters)
dY = 0.1;     % Y step size for plotting (meters)
dZ = 0.1;     % Z step size for plotting (meters)

%% Filepath

% Load path to dir to reconstruct
session = uigetdir('../../../FSR/stereo_cam/DATA','Select path to session containing wave subfolders'); 

% Initialize waves array
waves = {};

if processAll
    % Find subfolders that start with "wave"
    waveSubfolders = dir(fullfile(session, 'wave*'));
    waveSubfolders = waveSubfolders([waveSubfolders.isdir]); 
    if isempty(waveSubfolders)
        fprintf('No wave subfolders found in %s\n', session);
        return;
    end
    
    % Loop over each matching entry
    for i = 1:numel(waveSubfolders)
        if waveSubfolders(i).isdir
            % Build full path to subfolder
            wavePath = fullfile(session, waveSubfolders(i).name);
            % Append to the cell array
            waves{end + 1} = wavePath;
        end
    end
else
    % Just process one wave
    waves{1} = uigetdir(session, 'Select a wave subfolder');
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
    
    if exist(L1Dir, 'dir') % Load L1 mats
        L1matFiles = dir(fullfile(L1Dir, '*.mat'));
        L1matFilenames = {L1matFiles.name};
    else
        disp('No L1 directory for this wave.');
        return;
    end
    if ~exist(L2Dir, 'dir')
        mkdir(L2Dir);  % mkdir for L2
    end
    if ~exist(figDir, 'dir')
        mkdir(figDir); % mkdir for figs
    end
    
    %%%%%%%%%%%%%%%%%%%%%%%%% Georectification %%%%%%%%%%%%%%%%%%%%%%%%%%%%
    load(fullfile(wave, 'imu.mat')); % Load IMU data

    t = imu.t0; % Relative time

    % Check if origin was specified
    if ~exist('origin', 'var')
        % If no origin, set to cam origin
        origin = [mean(imu.lat), mean(imu.lon)];
    end

    % Geoid height correction 
    geoidHeight = geoidheight(origin(1), origin(2), 'EGM96');

    % Define LLA origin
    lla0 = [origin(1); origin(2); geoidHeight]';

    % Convert LLA to NED
    lla = [imu.lat; imu.lon; imu.alt]';
    NED = lla2ned(lla, lla0, 'ellipsoid');
    N = NED(:,1); E = NED(:,2); D = NED(:,3);
    
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

        if figs
            f1 = figure(1); hold on; axis equal; grid on; axis tight;
            title('Camera reference frame');
            % scatter3(xyz_cam(:,1), xyz_cam(:,2), xyz_cam(:,3), 1);
            scatter3(xyz_cam(:,1), xyz_cam(:,2), xyz_cam(:,3),...
                    1, double(L1matData.colors) / 255, 'filled');
            xlabel('X_{cam} (m)'); ylabel('Y_{cam} (m)'); zlabel('Z_{cam} (m)');
        end
        %%%%%%%%%%%% Rotate into IMU coords: XYZ_imu = +Z+X+Y_cam %%%%%%%%%
        xyz_imu = ([0 0 1; 1 0 0; 0 1 0] * xyz_cam')'; 

        if figs
            f2 = figure(2); hold on; axis equal; grid on; axis tight;
            title('IMU reference frame');
            % scatter3(xyz_imu(:,1), xyz_imu(:,2), xyz_imu(:,3), 1);
            scatter3(xyz_imu(:,1), xyz_imu(:,2), xyz_imu(:,3),...
                    1, double(L1matData.colors) / 255, 'filled');
            xlabel('X_{IMU} (m)'); ylabel('Y_{IMU} (m)'); zlabel('Z_{IMU} (m)');
        end
        %%%%%%%%%%%%%%%%%%%%%% Rotation matrix %%%%%%%%%%%%%%%%%%%%%%%%%%%%
        R = rotationMatrices(:, :, i);

        xyz_NED = (R * xyz_imu')'; % Rotate and transpose

        if figs
            f3 = figure(3); hold on; axis equal; grid on; axis tight;
            title('Local NED reference frame');
            % scatter3(xyz_NED(:,2), xyz_NED(:,1), xyz_NED(:,3), 1);
            scatter3(xyz_NED(:,2), xyz_NED(:,1), xyz_NED(:,3),...
                    1, double(L1matData.colors) / 255, 'filled');
            xlabel('Easting (m)'); ylabel('Northing (m)'); zlabel('Down (m)');
        end
        %%%%%%%%%%%%%%%%%% Translate to world coord %%%%%%%%%%%%%%%%%%%%%%%
        % cam_origin = [N(i), E(i), D(1)]; % NED Origin (uses first elev)
        cam_origin = [N(i), E(i), D(i)]; % NED Origin (uses each elev)
        % cam_origin = [mean(N), mean(E), mean(D)]; % NED Origin (uses mean NED)

        % Need to invert E, N to account for ptCloud-->cam displacement
        xyz_NED = [-xyz_NED(:,1), -xyz_NED(:,2), xyz_NED(:,3)] + cam_origin;
        % xyz_NED = xyz_NED + cam_origin;

        %%%%%%%%%%%%% Rotate NED to ENU: XYZ_ENU = +Y+X-Z_NED %%%%%%%%%%%%%
        xyz_ENU = ([0 1 0; 1 0 0; 0 0 -1] * xyz_NED')'; 
        
        if figs
            f4 = figure(4); hold on; axis equal; grid on; axis tight;
            title('World ENU reference frame');
            % scatter3(xyz_ENU(:,1), xyz_ENU(:,2), xyz_ENU(:,3), 1);
            scatter3(xyz_ENU(:,1), xyz_ENU(:,2), xyz_ENU(:,3),...
                    1, double(L1matData.colors) / 255, 'filled');
            % xlabel('Easting (m)'); ylabel('Northing (m)'); zlabel('Z_{NAVD88} (m)');
            xlabel('X_{SIO} (m)'); ylabel('Y_{SIO} (m)'); zlabel('Z_{NAVD88} (m)');
        end

        % Save transformed (rotate optional) points3D, colors, and ptCloud
        if rotate
            theta_rad = deg2rad(theta_deg); % Convert degrees to radians
            % Rotate around z-axis
            R = [cos(theta_rad) -sin(theta_rad); 
                 sin(theta_rad)  cos(theta_rad)];
            % Apply to x-y part (East, North)
            xy = xyz_ENU(:,1:2);       % Extract East-North
            xy_rot = (R * xy')';       % Rotate (transpose -> rotate -> transpose back)
            % Reassemble rotated xyz
            xy_rot(:,1) = xy_rot(:,1) + x_offset;
            xy_rot(:,2) = xy_rot(:,2) + y_offset;
            points3D = [xy_rot xyz_ENU(:,3)];  % Keep Up (z) unchanged
        else
            points3D = xyz_ENU;
        end

        if brighten
            colors = min(L1matData.colors * brightenFactor, 255);
            colors = uint8(colors);
        else
            colors = L1matData.colors;
        end
        ptCloud = pointCloud(points3D, 'Color', colors);

        % Denoise ptCloud
        if denoise
            ptCloud = pcdenoise(ptCloud);
        end

        % Downsample ptCloud
        if downsample
            ptCloud = pcdownsample(ptCloud, random=randPerc);
        end

        % Save L2 .mat
        filename = L1matFilenames{i};
        fullFilePath = fullfile(L2Dir, filename);
        save(fullFilePath, 'points3D', 'colors', ...
        'ptCloud', 'R', 'cam_origin');
    end

    if figs
        % Save figures in figDir
        print(f1, fullfile(figDir, 'camCoord.png'), '-dpng', ['-r', num2str(res)]);
        print(f2, fullfile(figDir, 'imuCoord.png'), '-dpng', ['-r', num2str(res)]);
        print(f3, fullfile(figDir, 'NEDlocal.png'), '-dpng', ['-r', num2str(res)]);
        print(f4, fullfile(figDir, 'ENUworld.png'), '-dpng', ['-r', num2str(res)]);
        % savefig(f1, fullfile(figDir, 'camCoord.fig'));
        % savefig(f2, fullfile(figDir, 'imuCoord.fig'));
        % savefig(f3, fullfile(figDir, 'NEDlocal.fig'));
        % savefig(f4, fullfile(figDir, 'ENUworld.fig'));
        % close all; % close figs before next wave
    end

    % Generate L3 concatenated ptCloud from all L2 ptClouds
    genL3ptCloud(wave);

end








