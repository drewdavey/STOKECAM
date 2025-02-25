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

% path = uigetdir('../../../FSR/stereo_cam/DATA/','Select path to session for analysis'); % load path to dir 
% path = 'C:\Users\drew\OneDrive - UC San Diego\FSR\stereo_cam\DATA\testing\20250119\000216_session_auto\wave1';
% path = 'C:\Users\drew\OneDrive - UC San Diego\FSR\stereo_cam\DATA\testing\20250112\000447_session_auto\wave3';
path = 'C:\Users\drew\OneDrive - UC San Diego\FSR\stereo_cam\DATA\testing\20250202\234540_session_auto\wave1';

load([path '/imu.mat']);

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

%% Select images from cam0 and cam1
cam0Images = dir(fullfile(cam0Dir, '*.jpg'));
cam1Images = dir(fullfile(cam1Dir, '*.jpg'));
% Convert filenames into struct arrays same as select_files output
selectedFiles0 = struct('name', {cam0Images.name});
selectedFiles1 = struct('name', {cam1Images.name});
% Select all mats automatically
if loadMats
    matFiles = dir(fullfile(matDir, '*.mat'));
    matFilenames = {matFiles.name};
else
    matFilenames = [];
    disp('No mats/ to analyze.');
end

%% Parse filenames to extract timestamps
% Initialize arrays to store timestamps in nanoseconds
tstamps0 = zeros(1, length(selectedFiles0));
tstamps1 = zeros(1, length(selectedFiles1));

% Parse filenames to extract timestamps in nanoseconds
for i = 1:length(selectedFiles0)
    [~, tstamp0, ~] = parse_filename(selectedFiles0(i).name);  % Get timestamp in nanoseconds as a string
    tstamps0(i) = str2double(tstamp0);  % Convert to numeric nanoseconds
end

for i = 1:length(selectedFiles1)
    [~, tstamp1, ~] = parse_filename(selectedFiles1(i).name);  % Get timestamp in nanoseconds as a string
    tstamps1(i) = str2double(tstamp1);  % Convert to numeric nanoseconds
end

% Calculate the difference in time between image pairs in nanoseconds
timeDiffs = zeros(1, length(tstamps0));
for i = 1:length(tstamps0)
    t(i) = ((tstamps0(i) + tstamps1(i)) / 2) * 10^-9; % Average tstamp in sec
    % Calculate the time difference in nanoseconds directly
    timeDiffNs = tstamps1(i) - tstamps0(i);  % Difference in nanoseconds
    timeDiffs(i) = timeDiffNs * 10^-3;  % Difference in microseconds
end

t = t - t(1); % make time relative

%% Position

% Convert geodetic to UTM
[xm, ym, zone] = deg2utm(vn.lat, vn.lon);
% Geoid height correction 
geoidHeight = geoidheight(vn.lat(1), vn.lon(1), 'EGM96'); 
zm = vn.alt - geoidHeight;

E = xm - xm(1);
N = ym - ym(1);
U = zm - zm(1);

% LL to XY SIO
[xSIO, ySIO] = lltoxy_siopier(vn.lat, vn.lon);

% % ECEF
% xm = vn.posEcefX;
% ym = vn.posEcefY;
% zm = vn.posEcefZ;
% xm = vn.posEcefX - vn.posEcefX(1);
% ym = vn.posEcefY - vn.posEcefY(1);
% zm = vn.posEcefZ - vn.posEcefZ(1);

% %  Direction cosine matrix (ECEF to NED)
% % Define the angles mu (latitude) and l (longitude)
% mu = deg2rad(vn.lat); % Convert latitude to radians
% l = deg2rad(vn.lon);  % Convert longitude to radians
% 
% % Initialize arrays for transformed coordinates
% ox2 = zeros(size(xm));
% oy2 = zeros(size(ym));
% oz2 = zeros(size(zm));
% 
% % Loop through each data point to calculate the rotated coordinates
% for i = 1:length(xm)
%     % Define the initial vector for the current point
%     v0 = [xm(i); ym(i); zm(i)];
% 
%     % Define the rotation matrices for the current mu and l
%     R1 = [-sin(mu(i)), 0, cos(mu(i));
%             0,         1,      0;
%           -cos(mu(i)), 0, -sin(mu(i))];
% 
%     R2 = [cos(l(i)),  sin(l(i)), 0;
%          -sin(l(i)),  cos(l(i)), 0;
%                0,         0,     1];
% 
%     % Combine the rotations
%     R = R1 * R2;
% 
%     % Apply the combined rotation to the initial vector
%     v2 = R * v0;
% 
%     % Store the rotated coordinates
%     ox2(i) = v2(1);
%     oy2(i) = v2(2);
%     oz2(i) = v2(3);
% end

% % Using built in func (ECEF to NED)
% wgs84 = wgs84Ellipsoid;
% [ox2, oy2, oz2] = ecef2ned(xm, ym, zm, vn.lat, vn.lon, vn.alt, wgs84);

%% Compute rotation matrix from quaternion
numFrames = numel(vn.quatX);
rotationMatrices = zeros(3, 3, numFrames);
for i = 1:numFrames
    qx = vn.quatX(i);
    qy = vn.quatY(i);
    qz = vn.quatZ(i);
    qw = vn.quatW(i);
    rotationMatrices(:, :, i) = quat2rotm([qw, qx, qy, qz]);
end

% %% Compute rotation matrix from Yaw-Pitch-Roll (3-2-1 sequence)
% numFrames = numel(vn.yaw);
% rotationMatrices = zeros(3, 3, numFrames);
% 
% for i = 1:numFrames
%     yaw = deg2rad(vn.yaw(i));   % Yaw (rotation around Z-axis)
%     pitch = deg2rad(vn.pitch(i));  % Pitch (rotation around Y-axis)
%     roll = deg2rad(vn.roll(i));    % Roll (rotation around X-axis)
% 
%     % Compute rotation matrix using 3-2-1 (Z-Y-X) Euler sequence
%     Rz = [cos(yaw), -sin(yaw), 0;
%           sin(yaw),  cos(yaw), 0;
%                 0,        0,  1];  % Yaw (Z-axis)
% 
%     Ry = [ cos(pitch), 0, sin(pitch);
%                    0, 1,          0;
%           -sin(pitch), 0, cos(pitch)];  % Pitch (Y-axis)
% 
%     Rx = [1,        0,         0;
%           0, cos(roll), -sin(roll);
%           0, sin(roll),  cos(roll)];  % Roll (X-axis)
% 
%     % Final rotation matrix (Z-Y-X sequence)
%     rotationMatrices(:, :, i) = Rz * Ry * Rx;
% end

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

        % % This is what works
        xyz_imu = xyz_cam * [0 1 0; 0 0 -1; -1 0 0]; % XYZ_imu = +Y-Z+X_cam

        % % This should be right
        % xyz_imu = xyz_cam * [0 0 1; 1 0 0; 0 1 0]; % XYZ_imu = +Z+X+Y_cam

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
        % scatter3(xyz_world(:,1), xyz_world(:,2), -xyz_world(:,3),...
        %     1, double(matData.colors) / 255, 'filled');
        % xlabel('N world'); ylabel('E world'); zlabel('D world');
        % xlabel('X_S_I_O'); ylabel('Y_S_I_O'); zlabel('D world');

        % title([matFiles(i).name(end-8:end-4)]);
        % legend show;
        % 
        % % Save the figure in the shapes/ directory
        % print(gcf, fullfile(shapesDir, [matFiles(i).name(end-8:end-4)]),...
        %     '-dpng', ['-r', num2str(res)]); 
    end
end


% %% Calculate distances from origin for each set of points
% dist_cam = sqrt(sum(xyz_cam.^2, 2));
% dist_imu = sqrt(sum(xyz_imu.^2, 2));
% dist_world = sqrt(sum((xyz_world - cam_origin).^2, 2));
% 
% figure; hold on; grid on;
% title('Distance from Origin');
% plot(dist_cam, 'LineWidth', 2);
% plot(dist_imu, 'LineWidth', 1);
% plot(dist_world, 'LineWidth', 0.5);
% ylabel('Distance');
% legend('Cam','IMU','World');

