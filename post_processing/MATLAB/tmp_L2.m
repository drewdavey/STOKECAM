% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2025-04-21

clear; clc; close all;

addpath('functions/');

%% Inputs

% Process all waves?
all = 0;

% Rotate wave field?
rotate = 0;
theta_deg = -10; % CCW

% Brighten point colors?
brighten = 1;
brightenFactor = 1.25;

% Denoise ptClouds?
denoise = 1;

% Downsample ptClouds?
downsample = 0;
randPerc = 0.5; % randomly downsample 50%

%% Filepath

% Load path to dir to reconstruct
session = uigetdir('../../../FSR/stereo_cam/DATA','Select path to session containing wave subfolders'); 

% Just process one wave
wave = uigetdir(session, 'Select a wave subfolder');


%% Reprocess Level 2

L2Dir = [wave '/L2'];
figDir = [wave '/figs'];

if exist(L2Dir, 'dir') % Load L1 mats
    L2matFiles = dir(fullfile(L2Dir, '*.mat'));
    L2matFilenames = {L2matFiles.name};
else
    disp('No L1 directory for this wave.');
    return;
end


%%% Rotate and translate into NED coordinate system
for i = 1:length(L2matFilenames)

    load(fullfile(L2Dir, L2matFilenames{i}));

    points3D = [points3D(:,1), points3D(:,2), points3D(:,3)+136];

    if rotate
            theta_rad = deg2rad(theta_deg); % Convert degrees to radians
            % Rotate around z-axis
            R = [cos(theta_rad) -sin(theta_rad); 
                 sin(theta_rad)  cos(theta_rad)];
            % Apply to x-y part (East, North)
            xy = points3D(:,1:2);       % Extract East-North
            xy_rot = (R * xy')';       % Rotate (transpose -> rotate -> transpose back)
            % Reassemble rotated xyz
            points3D = [xy_rot points3D(:,3)];  % Keep Up (z) unchanged
    end

    if brighten
        colors = min(colors * brightenFactor, 255);
        colors = uint8(colors);
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
    filename = L2matFilenames{i};
    fullFilePath = fullfile(L2Dir, filename);
    save(fullFilePath, 'points3D', 'colors', ...
    'ptCloud', 'R', 'cam_origin');
end

% Generate L3 concatenated ptCloud from all L2 ptClouds
genL3ptCloud(wave);










