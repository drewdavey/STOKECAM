% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2025-01-14

clear; clc; close all;

addpath('functions/');

%% Inputs

g = 9.81; % gravity

res = 300;    % resolution for figures (.pngs)

dX = 0.1;     % X step size for plotting (meters)
dY = 0.1;     % Y step size for plotting (meters)
dZ = 0.1;     % Z step size for plotting (meters)

path = uigetdir('../../../FSR/stereo_cam/DATA/','Select path to session for analysis'); % load path to dir 
[~, last_folder] = fileparts(path);  % Extract the last folder name

load(fullfile(path, [last_folder '.mat']));

% Relative time
t = data2.t0;

%% Organize dirs
cam0Dir = fullfile(path, 'cam0');
cam1Dir = fullfile(path, 'cam1');
matDir = fullfile(path, 'mats');
ptCloudDir = fullfile(path, 'ptClouds');
rectifiedImagesDir = fullfile(path, 'Rectified_Images');
figDir = fullfile(path, 'figs');
if ~exist(figDir, 'dir')
    mkdir(figDir);  % Create the 'figs/' folder if it doesn't exist
end
% Set loadMats if mat and rectified dirs exist
if exist(matDir, 'dir') && exist(rectifiedImagesDir, 'dir')
    loadMats = 1; % Enable loading mats based on rectified images
    matFiles = dir(fullfile(matDir, '*.mat'));
else
    loadMats = 0; % Skip loading mats
end

%% Plot cam delays
f1 = figure; hold on; grid on; box on; 
plot(t, data2.camDiffs * 1e6, 'o-', 'LineWidth', 1.5);
yline(0, '--k', 'LineWidth',2);
xlabel('Time (sec)');
ylabel('Time Difference (\mus)');
title('Image Delay');
print(f1, fullfile(figDir, 'TimeDifferencePlot.png'), '-dpng', ['-r', num2str(res)]);

%% Plot YPR
yaw = data2.yaw;
pitch = data2.pitch;
roll = data2.roll;

f2 = figure;
subplot(3,1,1); hold on; grid on; box on; axis tight;
plot(t, yaw, 'r', 'LineWidth', 1);
ylabel('yaw');
subplot(3,1,2); hold on; grid on; box on; axis tight;
plot(t, pitch, 'g', 'LineWidth', 1);
ylabel('pitch');
subplot(3,1,3); hold on; grid on; box on; axis tight;
plot(t, roll, 'b', 'LineWidth', 1);
ylabel('roll');
xlabel('Time (sec)');
sgtitle('YPR');

print(f2, fullfile(figDir, 'ypr.png'), '-dpng', ['-r', num2str(res)]);

%% Plot location

lat = data2.gnss1PosLat;
lon = data2.gnss1PosLon;
alt = data2.gnss1PosAlt;

buffer = 0.0001;
figure; ax = geoaxes; 
geobasemap(ax, 'satellite'); hold on;
geolimits([min(lat)-buffer max(lat)+buffer], [min(lon)-buffer max(lon)+buffer]);
video = VideoWriter(fullfile(figDir, 'gps.mp4'), 'MPEG-4');
video.FrameRate = 30; 
open(video);
h1 = geoplot(NaN, NaN, '-b', 'LineWidth', 1, 'DisplayName', 'Path'); hold on;
h2 = geoscatter(NaN, NaN, 20, 'r','filled', 'DisplayName', 'VN-200'); 
legend show;
for i = 1:length(lat)
    title(['Frame ', num2str(i)]);
    % geoscatter(lat(i), lon(i), 10, 'r','filled'); hold on;
    h1.LatitudeData = lat(1:i);
    h1.LongitudeData = lon(1:i);
    h2.LatitudeData = lat(i);
    h2.LongitudeData = lon(i);
    % pause(0.00001);
    frame = getframe(gcf);
    writeVideo(video, frame);
end
close(video);

%% Position

% Convert geodetic to UTM
[xm, ym, zone] = deg2utm(data2.lat, data2.lon);
% Geoid height correction 
geoidHeight = geoidheight(data2.lat(1), data2.lon(1), 'EGM96'); 
zm = data2.alt - geoidHeight;

E = xm - xm(1);
N = ym - ym(1);
U = zm - zm(1);

% LL to XY SIO
[xSIO, ySIO] = lltoxy_siopier(data2.lat, data2.lon);

% % ECEF
% xm = data2.posEcefX;
% ym = data2.posEcefY;
% zm = data2.posEcefZ;
% xm = data2.posEcefX - data2.posEcefX(1);
% ym = data2.posEcefY - data2.posEcefY(1);
% zm = data2.posEcefZ - data2.posEcefZ(1);


%% Compute rotation matrix from quaternion
numFrames = numel(data2.quatX);
rotationMatrices = zeros(3, 3, numFrames);
for i = 1:numFrames
    qx = data2.quatX(i);
    qy = data2.quatY(i);
    qz = data2.quatZ(i);
    qw = data2.quatW(i);
    rotationMatrices(:, :, i) = quat2rotm([qw, qx, qy, qz]);
end

%% Plot X-Y cross sections
shapesDir = fullfile(figDir, 'shapes');
if ~exist(shapesDir, 'dir') && loadMats
    mkdir(shapesDir);  % Create shapes/ directory if it doesn't exist
end

% for i = 1
for i = 1:length(matFilenames)
    matData = load(fullfile(matDir, matFilenames{i}));
    matData = matData.data;
    % if isfield(matData, 'points3D') && (isfield(matData, 'clean') && matData.clean == true)
    if isfield(matData, 'points3D')

        %%%%%%%%%%%%%% Point cloud in camera reference frame %%%%%%%%%%%%%%
        xyz_cam = matData.points3D;
        
        figure(1); hold on; axis equal; grid on; axis tight;
        title('camera coord.');
        % scatter3(xyz_cam(:,1), xyz_cam(:,2), xyz_cam(:,3), 1);
        scatter(xyz_cam(:,1), -xyz_cam(:,2), 1, xyz_cam(:,3));
        xlabel('X cam');
        ylabel('Y cam');
        zlabel('Z cam');
        colorbar;

        %%%%%%%%%%%%%% Reorder to X, Z, Y for NED convention %%%%%%%%%%%%%%
        % xyz_imu = xyz_cam * [0 0 1; 1 0 0; 0 -1 0]; % Swap Y and Z and flip Y

        % % % This is what works
        % xyz_imu = xyz_cam * [0 1 0; 0 0 -1; -1 0 0]; % XYZ_imu = +Y-Z+X_cam

        % This should be right
        xyz_imu = xyz_cam * [0 0 1; 1 0 0; 0 1 0]; % XYZ_imu = +Z+X+Y_cam

        figure(2); hold on; axis equal; grid on; axis tight;
        title('imu coord.');
        % scatter3(xyz_imu(:,1), xyz_imu(:,2), xyz_imu(:,3), 1);
        scatter(xyz_imu(:,1), xyz_imu(:,2), 1, xyz_imu(:,3));
        xlabel('X imu');
        ylabel('Y imu');
        zlabel('Z imu');

        %%%%%%%%%%%%%%%%%%%%%% Rotation matrix %%%%%%%%%%%%%%%%%%%%%%%%%%%%
        R = rotationMatrices(:, :, i);

        % Rotate and transpose
        xyz_NED = (R * xyz_imu')';

        figure(3); hold on; axis equal; grid on; axis tight;
        title('rotated into NED');
        xlabel('N world'); ylabel('E world'); zlabel('D world');
        % scatter3(xyz_NED(:,2), xyz_NED(:,1), xyz_NED(:,3),...
        %     1, double(matData.colors) / 255, 'filled');
        scatter3(xyz_NED(:,2), xyz_NED(:,1), xyz_NED(:,3),1);

        % Origin
        % imu_origin = [xm(i), ym(i), zm(i)];
        % cam_origin = [E(i), N(i), U(i)]; % ENU?
        % cam_origin = [N(i), E(i), -U(i)]; % NED?
        cam_origin = [ySIO(i), xSIO(i), U(i)]; % XY_SIO and Up 

        %%%%%%%%%%%%%%%%%% Translate to world coord %%%%%%%%%%%%%%%%%%%%%%%
        xyz_world = xyz_NED + cam_origin;

        figure(4); hold on; axis equal; grid on; axis tight;
        title('world coord.');

        scatter3(xyz_world(:,1), xyz_world(:,2), xyz_world(:,3), 1);
        
        % scatter3(xyz_world(:,2), xyz_world(:,1), xyz_world(:,3),...
        %     1, double(matData.colors) / 255, 'filled');
        % xlabel('N world'); ylabel('E world'); zlabel('D world');
        xlabel('X_S_I_O'); ylabel('Y_S_I_O'); zlabel('D world');

        % 
        % % Save the figure in the shapes/ directory
        % print(gcf, fullfile(shapesDir, [matFiles(i).name(end-8:end-4)]),...
        %     '-dpng', ['-r', num2str(res)]); 
    end
end

