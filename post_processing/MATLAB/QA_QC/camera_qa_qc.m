% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-10

clear; clc; close all;

addpath('functions/');

%% Inputs

res = 300;    % resolution for figures (.pngs)

% path = 'C:\Users\drew\OneDrive - UC San Diego\FSR\stereo_cam\DATA\testing\20250112\000447_session_auto\wave3';
path = 'C:\Users\drew\OneDrive - UC San Diego\FSR\stereo_cam\DATA\testing\20250119\000216_session_auto\wave1';

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

%% points
for k = 1:length(matFilenames)
    matData = load(fullfile(matDir, matFilenames{k}));
    matData = matData.data;
    % if isfield(matData, 'points3D') && (isfield(matData, 'clean') && matData.clean == true)
    if isfield(matData, 'points3D')

        % Point cloud in camera reference frame
        points3D = matData.points3D;
        
        % % Reorder to X, Z, Y for NED convention
        % points3D = points3D(:, [1, 3, 2]); % Swap Y and Z

        % Get the x-values, y-values, and z-values (depth)
        xValues = points3D(:,1);
        yValues = points3D(:,2);
        zValues = points3D(:,3);
        
        % % Get the minimum and maximum X, Y, Z values
        % minX = min(xValues);
        % maxX = max(xValues);
        % minY = min(yValues);
        % maxY = max(yValues);
        % minZ = min(zValues);
        % maxZ = max(zValues);

        figure;
        set(gcf,'position',[124 173 1039 302]);
        subplot(1,3,1)
        histogram(xValues, 'Normalization', 'probability');
        title('X');
        subplot(1,3,2)
        histogram(yValues, 'Normalization', 'probability');
        title('Y');
        subplot(1,3,3)
        histogram(zValues, 'Normalization', 'probability');
        title('Z');
        
        sgtitle([matFiles(k).name(end-8:end-4)]);
        print(gcf, fullfile(figDir, [matFiles(k).name(end-8:end-4)]),...
            '-dpng', ['-r', num2str(res)]);

        % scatter3(xValues, yValues, zValues,...
        %     1, double(matData.colors) / 255, 'filled');

        % scatter3(xValues, zValues, yValues, 1);
    end
end

% 
% figure;
% 
% for i = 1:length(points3D)
%     dist = sqrt()
% end