% Clean Point Clouds
% Drew Davey
% Last updated: 2024-03-17 

clear; clc; close all;

%% Inputs

cleanFlag = 0;
saveFlag = 0;

depth = [0, 30];

xbounds = [-5, 5];
ybounds = [-5, 5];

path = uigetdir('../../','Select path to session for point cloud cleaning'); % load path to dir

matDir = [path '/mats'];
dir = dir([path '/mats/*.mat']);

% Check the number of files in directory
numFiles = length(dir);

% Initialize arrays to store file paths
matFileNames = cell(numFiles, 1);

% Construct file paths for each directory
for i = 1:numFiles
    matFileNames{i} = fullfile(dir(i).folder, dir(i).name);
end

%% QA/QC

for i = 1:length(matFileNames)

    load(matFileNames{i});

    points3D = points3D ./ 1000; % Convert to meters and create a pointCloud object
    ptCloud = pointCloud(points3D, Color=J1);

    
    % Trim ptcloud
    
    % Cubically filter out >3std from mean
    
    % Specify z-step distance and output X/Y points at Z depths
    % Save these cross sections, label in order, fit curves?

    % Append ptCloud to mat
    save(matFileNames{i},'ptCloud','points3D','-append');
    
end



%% Manually clean point clouds

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

%     answer = questdlg('Save Changes?', ...
%     'Save Point Cloud', ...
%     'Yes','No','Yes');
%     switch answer
%         case 'Yes'
%             saveFlag = 1; 
%         case 'No'
%             saveFlag = 0; 
%     end
% 
%     if saveFlag
%         save([matDir '/' file '.mat'],'ptCloud'); % Save mat
%     end

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
