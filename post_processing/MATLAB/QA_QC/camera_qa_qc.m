% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-10

clear; clc; close all;

addpath('functions/');

%% Inputs

res = 300;    % resolution for figures (.pngs)

% path = 'C:\Users\drew\OneDrive - UC San Diego\FSR\stereo_cam\DATA\testing\20250112\000447_session_auto\wave3';
path = 'C:\Users\drew\OneDrive - UC San Diego\FSR\stereo_cam\DATA\testing\20250119\000216_session_auto\wave1';
load([path '/imu.mat']);

%% Organize dirs
cam0Dir = fullfile(path, 'cam0');
cam1Dir = fullfile(path, 'cam1');
matDir = fullfile(path, 'mats');
rectifiedImagesDir = fullfile(path, 'Rectified_Images');
figDir = fullfile(path, 'figs');
if ~exist(figDir, 'dir')
    mkdir(figDir);  % Create the 'figs/' folder if it doesn't exist
end
matFiles = dir(fullfile(matDir, '*.mat'));
cam0Images = dir(fullfile(cam0Dir, '*.jpg'));
cam1Images = dir(fullfile(cam1Dir, '*.jpg'));
% Convert filenames into struct arrays same as select_files output
selectedFiles0 = struct('name', {cam0Images.name});
selectedFiles1 = struct('name', {cam1Images.name});
matFiles = dir(fullfile(matDir, '*.mat'));
matFilenames = {matFiles.name};
% Parse filenames to extract timestamps
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
t = zeros(1, length(tstamps0)); % Create avg tstamps for plotting
for i = 1:length(tstamps0)
    t(i) = ((tstamps0(i) + tstamps1(i)) / 2) * 10^-9; % Average tstamp in sec
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
% 
xm = xm - xm(1);
ym = ym - ym(1);
zm = zm - zm(1);

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

%% points
for i = 1:length(matFilenames)-4
    matData = load(fullfile(matDir, matFilenames{i}));
    matData = matData.data;
    % if isfield(matData, 'points3D') && (isfield(matData, 'clean') && matData.clean == true)
    if isfield(matData, 'points3D')

        % Point cloud in camera reference frame
        xyz_cam = matData.points3D;

        figure;
        set(gcf,'position',[124 173 1039 302]);
        subplot(1,3,1)
        histogram(xyz_cam(:,1), 'Normalization', 'probability');
        title('X');
        subplot(1,3,2)
        histogram(xyz_cam(:,2), 'Normalization', 'probability');
        title('Y');
        subplot(1,3,3)
        histogram(xyz_cam(:,3), 'Normalization', 'probability');
        title('Z');
        sgtitle([matFiles(i).name(end-8:end-4) ' cam']);
        print(gcf, fullfile(figDir, [matFiles(i).name(end-8:end-4) ' cam']),...
            '-dpng', ['-r', num2str(res)]);

        % Reorder to X, Z, Y for NED convention
        % xyz_imu = xyz_cam * [0 0 1; 1 0 0; 0 -1 0]; % Swap Y and Z and flip Y
        xyz_imu = xyz_cam * [0 1 0; 0 0 -1; 1 0 0]; %

        figure;
        set(gcf,'position',[124 173 1039 302]);
        subplot(1,3,1)
        histogram(xyz_imu(:,1), 'Normalization', 'probability');
        title('X');
        subplot(1,3,2)
        histogram(xyz_imu(:,2), 'Normalization', 'probability');
        title('Y');
        subplot(1,3,3)
        histogram(xyz_imu(:,3), 'Normalization', 'probability');
        title('Z');
        sgtitle([matFiles(i).name(end-8:end-4) ' imu']);
        print(gcf, fullfile(figDir, [matFiles(i).name(end-8:end-4) ' imu']),...
            '-dpng', ['-r', num2str(res)]);

        % Rotation matrix
        R = rotationMatrices(:, :, i);

        % Origin
        % imu_origin = [xm(i), ym(i), zm(i)];
        cam_origin = [xm(i), ym(i), zm(i)];

        % Rotate, transpose, and translate
        xyz_world = (R * xyz_imu')' + cam_origin;

        figure;
        set(gcf,'position',[124 173 1039 302]);
        subplot(1,3,1)
        histogram(xyz_world(:,1), 'Normalization', 'probability');
        title('X');
        subplot(1,3,2)
        histogram(xyz_world(:,2), 'Normalization', 'probability');
        title('Y');
        subplot(1,3,3)
        histogram(xyz_world(:,3), 'Normalization', 'probability');
        title('Z');
        sgtitle([matFiles(i).name(end-8:end-4) ' world']);
        print(gcf, fullfile(figDir, [matFiles(i).name(end-8:end-4) ' world']),...
            '-dpng', ['-r', num2str(res)]);
    end
end

% 
% figure;
% 
% for i = 1:length(points3D)
%     dist = sqrt()
% end