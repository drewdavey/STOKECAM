% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-06

clear; clc; close all;

%% Inputs 

path = uigetdir('../../','Select path to session'); % load path to session

%% Cleanup dirs

cam0Dir = fullfile(path, 'cam0');
cam1Dir = fullfile(path, 'cam1');

cam0Files = dir(fullfile(cam0Dir, '0_*.jpg'));
cam1Files = dir(fullfile(cam1Dir, '1_*.jpg'));

cam0Filenames = {cam0Files.name};
cam1Filenames = {cam1Files.name};

% Loop through the cam0 files and find corresponding cam1 files
for i = 1:length(cam0Files)
    
    [cameraID0, timestamp0, imageNum0] = parse_filename(cam0Files(i).name);
    
    % Find the corresponding cam1 file
    correspondingFile = find_corresponding_file(cameraID0, timestamp0, imageNum0, cam1Files);
    
    % If no corresponding file is found, delete the cam0 file
    if isempty(correspondingFile)
        delete(fullfile(cam0Dir, cam0Files(i).name));
        fprintf('Deleted: %s\n', fullfile(cam0Dir, cam0Files(i).name));
    end
end

% Loop through the cam1 files and find corresponding cam0 files
for i = 1:length(cam1Files)

    [cameraID1, timestamp1, imageNum1] = parse_filename(cam1Files(i).name);

    % Find the corresponding cam0 file
    correspondingFile = find_corresponding_file(cameraID1, timestamp1, imageNum1, cam0Files);
    
    % If no corresponding file is found, delete the cam1 file
    if isempty(correspondingFile)
        delete(fullfile(cam1Dir, cam1Files(i).name));
        fprintf('Deleted: %s\n', fullfile(cam1Dir, cam1Files(i).name));
    end
end

disp('Cleanup complete.');

%% Functions

% Parse the filename into cameraID, timestamp (up to seconds), and imageNum
function [cameraID, timestamp, imageNum] = parse_filename(filename)
    parts = split(filename, '_');
    cameraID = parts{1}; % '0' or '1'
    timestamp = parts{2}(1:6); % Ignore milliseconds, keep only HHMMSS
    imageNum = parts{3}(1:end-4); % Remove '.jpg' extension
end

% Function to find the corresponding file in the other camera folder
function correspondingFile = find_corresponding_file(cameraID, timestamp, imageNum, files)
    correspondingFile = [];
    
    for i = 1:numel(files)
        [~, ts, imgNum] = parse_filename(files(i).name);
        
        % Compare timestamp up to seconds and image number
        if strcmp(ts, timestamp) && strcmp(imgNum, imageNum)
            correspondingFile = files(i);
            return;
        end
    end
end
