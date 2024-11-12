% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-10

clear; clc; close all;

addpath('functions/');

%% Inputs

viewPtCloud_orig = 0; % display original ptCloud? helps determine where to cut off background

depth = [0, 30];
xbounds = [-10, 10];
ybounds = [-10, 10];

%% Filepath

path = uigetdir('../../../FSR/stereo_cam/DATA/','Select path to session for point cloud viewing'); % load path to dir
matDir = [path '/mats'];

%% View point clouds

viewFlag = 1;
while viewFlag
    % Choose point cloud
    file = uigetfile([path '/Rectified_Images/*.png'],'Select file to view point cloud');
    file = file(1:end-9);
    % Load mat
    load([matDir '/' file '.mat']);

    % Create a streaming point cloud viewer
    player3D = pcplayer(xbounds, ybounds, depth, VerticalAxis="y", ...
        VerticalAxisDir="down");

    % Visualize the point cloud
    if viewPtCloud_orig
        view(player3D, data.ptCloud_orig);
    else
        view(player3D, data.ptCloud);
    end

    while isOpen(player3D)
        pause(0.1)
    end

    answer = questdlg('View another point cloud?', ...
    'View another point cloud', ...
    'Yes','No','Yes');
    switch answer
        case 'Yes'
            viewFlag = 1; 
        case 'No'
            viewFlag = 0; 
    end
end
