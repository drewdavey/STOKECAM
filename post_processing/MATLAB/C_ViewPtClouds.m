% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-06

clear; clc; close all;

%% Inputs

path = uigetdir('../../','Select path to session for point cloud viewing'); % load path to dir
matDir = [path '/mats'];

viewFlag = 1;

depth = [0, 30];
xbounds = [-5, 5];
ybounds = [-5, 5];

%% View point clouds

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
    view(player3D, ptCloud);
    while isOpen(player3D)
        pause(0.1)
    end
    answer = questdlg('Another?', ...
    'View another point cloud', ...
    'Yes','No','Yes');
    switch answer
        case 'Yes'
            viewFlag = 1; 
        case 'No'
            viewFlag = 0; 
    end
end
