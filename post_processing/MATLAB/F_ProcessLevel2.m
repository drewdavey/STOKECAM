% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2025-04-21

clear; clc; close all;

addpath('functions/');

%% Inputs

% Fig res
res = 600;

g = 9.81;     % gravity

dX = 0.1;     % X step size for plotting (meters)
dY = 0.1;     % Y step size for plotting (meters)
dZ = 0.1;     % Z step size for plotting (meters)

%% Filepath

% Load path to dir to reconstruct
session = uigetdir('../../../FSR/stereo_cam/DATA/testing/dynamic','Select path to session containing wave subfolders'); 

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
    shapesDir = [figDir '/shapes'];
    
    if exist(L1Dir, 'dir')
        % Load L1 mats directory
        matDir = [L1Dir '/mats'];
        matFiles = dir(fullfile(matDir, '*.mat'));
        matFilenames = {matFiles.name};
        % Load IMU data
        load(fullfile(L1Dir, 'imu.mat'));
        % Relative time
        t = imu.t0;
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
    if ~exist(shapesDir, 'dir')
        mkdir(shapesDir);  % Create shapes/ directory if it doesn't exist
    end
    
    %%% Georectification %%%
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
    
    %%% Rotate and translate into local coordinate system
    for i = 1:length(matFilenames)
        matData = load(fullfile(matDir, matFilenames{i}));
        if isfield(matData, 'points3D') && (isfield(matData, 'clean') && matData.clean == true)

            %%%%%%%%%%%%%% Point cloud in camera reference frame %%%%%%%%%%%%%%
            xyz_cam = matData.points3D;

            figure(21); hold on; axis equal; grid on; axis tight;
            title('Camera coordinates');
            % scatter3(xyz_cam(:,1), xyz_cam(:,2), xyz_cam(:,3), 1);
            scatter(xyz_cam(:,1), xyz_cam(:,2), 1, xyz_cam(:,3));
            xlabel('X_{cam} (m)');
            ylabel('Y_{cam} (m)');
            zlabel('Z_{cam} (m)');
            cbar = colorbar; % Add colorbar and set its label
            cbar.Label.String = 'Z_{cam} (m)';  % Label for the colorbar
    
            %%%%%%%%%%%%%% Rotate into IMU coords: XYZ_imu = +Z+X+Y_cam %%%%%%%%%%
            xyz_imu = ([0 0 1; 1 0 0; 0 1 0] * xyz_cam')'; 
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

            figure(22); hold on; axis equal; grid on; axis tight;
            title('imu coord.');
            scatter3(xyz_imu(:,1), xyz_imu(:,2), xyz_imu(:,3), 1);
            % scatter(xyz_imu(:,1), xyz_imu(:,2), 1, xyz_imu(:,3));
            xlabel('X imu');
            ylabel('Y imu');
            zlabel('Z imu');
    
            %%%%%%%%%%%%%%%%%%%%%% Rotation matrix %%%%%%%%%%%%%%%%%%%%%%%%%%%%
            R = rotationMatrices(:, :, i);

            % Rotate and transpose
            xyz_NED = (R * xyz_imu')';
    
            figure(23); hold on; axis equal; grid on; axis tight;
            title('rotated into NED');
            xlabel('Easting (m)'); ylabel('Northing (m)'); zlabel('D world');
            scatter3(xyz_NED(:,2), xyz_NED(:,1), xyz_NED(:,3),...
                1, double(matData.colors) / 255, 'filled');
            % scatter3(xyz_NED(:,2), xyz_NED(:,1), xyz_NED(:,3), 1);
    
            % Origin
            cam_origin = [N(i), E(i), U(1)]; % NED
            % cam_origin = [ySIO(i), xSIO(i), U(1)]; % XY_SIO and Up 
    
            %%%%%%%%%%%%%%%%%% Translate to world coord %%%%%%%%%%%%%%%%%%%%%%%
            xyz_world = cam_origin - xyz_NED;
            
            figure(24); hold on; axis equal; grid on; axis tight;
            title('World coordinates');
            scatter3(xyz_world(:,2), xyz_world(:,1), xyz_world(:,3),...
                1, double(matData.colors) / 255, 'filled');
            % xlabel('Easting (m)'); ylabel('Northing (m)'); zlabel('D world');
            % scatter3(xyz_world(:,2), xyz_world(:,1), xyz_world(:,3), 1);
            xlabel('X_{SIO} (m)', 'FontSize', 12);
            ylabel('Y_{SIO} (m)', 'FontSize', 12);
            zlabel('Z_{NAVD88} (m)', 'FontSize', 12);
    
            % view(-64,16);
            % view(-164,10);
            
            % % Save the figure in the shapes/ directory
            % print(gcf, fullfile(shapesDir, [matFiles(i).name(end-8:end-4)]),...
            %     '-dpng', ['-r', num2str(res)]);

            % Save transformed points3D, colors, and ptCloud
            points3D = xyz_world;
            colors = matData.colors;
            ptCloud = pointCloud(points3D, 'Color', colors);

            % Save .mat
            filename = [timestamp '_' imageNum];
            fullFilePath = fullfile(matDir, filename);
            save(fullFilePath, 'points3D', 'colors', ...
            'ptCloud', 'clean');

        end
    end

    % close all; % close figs before next wave
end

f1 = figure;
set(gcf,'position',[260 9 691 613]);
subplot(3,1,1); hold on; grid on; box on; axis tight;
plot(t, xSIO, 'LineWidth', 1); hold on;
plot(t, E, 'LineWidth', 1);
legend('SIO','NED');
ylabel('x-pos');
subplot(3,1,2); hold on; grid on; box on; axis tight;
plot(t, ySIO, 'LineWidth', 1); hold on;
plot(t, N, 'LineWidth', 1);
legend('SIO','NED');
ylabel('y-pos');
subplot(3,1,3); hold on; grid on; box on; axis tight;
plot(t, U, 'LineWidth', 1); hold on;
plot(t, D, 'LineWidth', 1);
legend('SIO','NED');
ylabel('elevation');
xlabel('Time (min)');
print(f1, fullfile(figDir, 'sio_NED.png'), '-dpng', ['-r', num2str(res, '%.3f')]);