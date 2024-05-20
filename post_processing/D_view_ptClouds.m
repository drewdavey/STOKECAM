% View Point Clouds
% Drew Davey
% Last updated: 2024-03-17 

clear; clc; close all;

%% Inputs

path = uigetdir('../../','Select path to session for point cloud viewing'); % load path to dir
matDir = [path '/mats'];

viewFlag = 1;

%% View point clouds

while viewFlag
    % Choose point cloud
    file = uigetfile([path '/Rectified_Images/*.png'],'Select file to view point cloud');
    file = file(end-23:end-9);
    % Load mat
    load([matDir '/' file '.mat']);
    % Create a streaming point cloud viewer
    player3D = pcplayer([-3, 3], [-3, 3], [0, 8], VerticalAxis="y", ...
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
