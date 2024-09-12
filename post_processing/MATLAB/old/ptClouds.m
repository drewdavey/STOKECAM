% Generate Point Clouds
% Drew Davey
% Last updated: 2024-03-17 

clear; clc; close all;

%% Inputs

path = uigetdir('../../','Select path to session for point cloud generation/analysis'); % load path to dir

answer = questdlg('What you wanna do?', ...
	'Task', ...
	'Generate point clouds','View point clouds','Both','Both');
switch answer
    case 'Generate point clouds'
        disp([answer 'aye aye'])
        genFlag = 1; viewFlag = 0; 
    case 'View point clouds'
        disp([answer 'aye aye'])
        genFlag = 0; viewFlag = 1; 
    case 'Both'
        disp('aye aye')
        genFlag = 1; viewFlag = 1;
end

%% File management

if genFlag
    ptCloudDir = [path '/ptClouds'];
    if ~exist(ptCloudDir, 'dir')
        mkdir(ptCloudDir); % mkdir for ptClouds
    end
end

matDir = [path '/mats'];
dir = dir([matDir '/*.mat']);

% Check the number of files in directory
numFiles = length(dir);

% Initialize arrays to store file paths
matFileNames = cell(numFiles, 1);

% Construct file paths for each directory
for i = 1:numFiles
    matFileNames{i} = fullfile(dir(i).folder, dir(i).name);
end

%% Generate point clouds

if genFlag
    for i = 1:length(matFileNames)
    
        load(matFileNames{i});
    
        % Create point cloud
        points3D = reconstructScene(disparityMap, reprojectionMatrix); % for single disparity map
        points3D = points3D ./ 1000; % Convert to meters and create a pointCloud object
        ptCloud = pointCloud(points3D, Color=J1);
    
        % Append ptCloud to mat
        save(matFileNames{i},'ptCloud','-append');
    
        % Save ptCloud as .ply
        filename = matFileNames{i}(end-18:end-4);
        fullFilePath = fullfile(ptCloudDir, filename);
        pcwrite(ptCloud, fullFilePath);
        
    end
end

%% View point clouds

if viewFlag
   
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

end

