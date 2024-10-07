% Stereo Camera Code
% Drew Davey
% Last updated: 2024-09-09

clear; clc; close all;

path = uigetdir('../../','Select path to session'); % load path to session

cam0Dir = fullfile(path, 'cam0');
cam1Dir = fullfile(path, 'cam1');

cam0Files = dir(fullfile(cam0Dir, '0_*.jpg'));
cam1Files = dir(fullfile(cam1Dir, '1_*.jpg')); 

cam0Filenames = {cam0Files.name};
cam1Filenames = {cam1Files.name};

% Loop through the cam0 files and find corresponding cam1 files
for i = 1:length(cam0Files)
    
    coreName = cam0Files(i).name(3:end); 

    % Check if the corresponding '1_' prefixed file exists in cam1
    cam1Name = ['1_' coreName];
    
    if ~ismember(cam1Name, cam1Filenames)
        delete(fullfile(cam0Dir, cam0Files(i).name));
        fprintf('Deleted: %s\n', fullfile(cam0Dir, cam0Files(i).name));
    end
end

% Loop through the cam1 files and find corresponding cam0 files
for i = 1:length(cam1Files)

    coreName = cam1Files(i).name(3:end); % Remove '1_' prefix

    % Check if the corresponding '0_' prefixed file exists in cam0
    cam0Name = ['0_' coreName];
    
    if ~ismember(cam0Name, cam0Filenames)
        delete(fullfile(cam1Dir, cam1Files(i).name));
        fprintf('Deleted: %s\n', fullfile(cam1Dir, cam1Files(i).name));
    end
end

disp('Cleanup complete.');






