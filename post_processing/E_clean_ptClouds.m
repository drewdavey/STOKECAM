% Clean Point Clouds
% Drew Davey
% Last updated: 2024-03-17 

clear; clc; close all;

%% Inputs

path = uigetdir('../../','Select path to session for point cloud generation'); % load path to dir
matDir = [path '/mats'];

cleanFlag = 1;

%% Clean point clouds

while cleanFlag
    % Choose point cloud
    file = uigetfile([path '/Rectified_Images/*.png'],'Select file to clean point cloud');
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

    % answer = overwrite? ADD PROMPT
    % Save mat
    save([matDir '/' file '.mat'],'ptCloud');

    answer = questdlg('Another?', ...
    'Clean another point cloud', ...
    'Yes','No','Yes');
    switch answer
        case 'Yes'
            cleanFlag = 1; 
        case 'No'
            cleanFlag = 0; 
    end
end
