% STOKECAM Post-Processing
% Drew Davey
% Simplified cleanup script to remove unmatched files from cam0, cam1, mats, and Rectified_Images

clear; clc; close all;

% Directories
path = uigetdir('../../','Select path to session'); % load path to session
cam0Dir = fullfile(path, 'cam0');
cam1Dir = fullfile(path, 'cam1');
matDir = fullfile(path, 'mats');
rectifiedDir = fullfile(path, 'Rectified_Images');

% Get file lists from each directory
cam0Files = dir(fullfile(cam0Dir, '0_*.jpg'));
cam1Files = dir(fullfile(cam1Dir, '1_*.jpg'));
matFiles = dir(fullfile(matDir, '*.mat'));
rectifiedFiles = dir(fullfile(rectifiedDir, '*_rect.jpg')); % only _rect to start, check _disp later

% Store parsed filenames (timestamp and image number) in a map to track presence across directories
fileMap = containers.Map();

% Process cam0 files
for i = 1:length(cam0Files)
    [timestamp, imageNum] = parse_filename(cam0Files(i).name, true); % Pass true for cam files
    key = strcat(timestamp, '_', imageNum);
    fileMap(key) = struct('cam0', true, 'cam1', false, 'mat', false, 'rect', false, 'disp', false);
end

% Process cam1 files
for i = 1:length(cam1Files)
    [timestamp, imageNum] = parse_filename(cam1Files(i).name, true); % Pass true for cam files
    key = strcat(timestamp, '_', imageNum);
    if isKey(fileMap, key)
        entry = fileMap(key);   % Retrieve the structure
        entry.cam1 = true;      % Update the field
        fileMap(key) = entry;   % Store it back in the map
    else
        fileMap(key) = struct('cam0', false, 'cam1', true, 'mat', false, 'rect', false, 'disp', false);
    end
end

% Process mat files
for i = 1:length(matFiles)
    [timestamp, imageNum] = parse_filename(matFiles(i).name, false); % Pass false for mat files
    key = strcat(timestamp, '_', imageNum);
    if isKey(fileMap, key)
        entry = fileMap(key);   % Retrieve the structure
        entry.mat = true;       % Update the field
        fileMap(key) = entry;   % Store it back in the map
    else
        fileMap(key) = struct('cam0', false, 'cam1', false, 'mat', true, 'rect', false, 'disp', false);
    end
end

% Process rectified images (_rect and _disp)
for i = 1:length(rectifiedFiles)
    [timestamp, imageNum] = parse_filename(rectifiedFiles(i).name, false); % Pass false for rectified files
    key = strcat(timestamp, '_', imageNum);
    % Check for both _rect and _disp
    if contains(rectifiedFiles(i).name, '_rect')
        if isKey(fileMap, key)
            entry = fileMap(key);   % Retrieve the structure
            entry.rect = true;      % Update the field
            fileMap(key) = entry;   % Store it back in the map
        else
            fileMap(key) = struct('cam0', false, 'cam1', false, 'mat', false, 'rect', true, 'disp', false);
        end
    elseif contains(rectifiedFiles(i).name, '_disp')
        if isKey(fileMap, key)
            entry = fileMap(key);   % Retrieve the structure
            entry.disp = true;      % Update the field
            fileMap(key) = entry;   % Store it back in the map
        else
            fileMap(key) = struct('cam0', false, 'cam1', false, 'mat', false, 'rect', false, 'disp', true);
        end
    end
end

% Loop over the map and delete any entries where a file is missing in any directory
keys = fileMap.keys;
for i = 1:length(keys)
    key = keys{i};
    fileEntry = fileMap(key);
    
    % If any file is missing, delete all related files
    if ~fileEntry.cam0 || ~fileEntry.cam1 || ~fileEntry.mat || ~fileEntry.rect || ~fileEntry.disp
        delete_files(key, cam0Dir, cam1Dir, matDir, rectifiedDir, fileMap);
    end
end

disp('Cleanup complete.');

% --- HELPER FUNCTIONS BELOW --- %

% Helper function to parse filenames and return timestamp and image number
function [timestamp, imageNum] = parse_filename(filename, camFile)
    if camFile
        % For cam files, extract timestamp and ignore microseconds (only first 6 digits HHMMSS)
        tokens = regexp(filename, '(\d{6})\d*_(\d+)', 'tokens', 'once'); % Microseconds ignored
    else
        % For mat and rectified files, just extract timestamp and image number
        tokens = regexp(filename, '(\d{6})_(\d+)', 'tokens', 'once');
    end
    if isempty(tokens)
        error('Filename does not match expected format: %s', filename);
    end
    timestamp = tokens{1};
    imageNum = tokens{2};
end

% Helper function to delete corresponding files from all directories
function delete_files(key, cam0Dir, cam1Dir, matDir, rectifiedDir, fileMap)
    [timestamp, imageNum] = strtok(key, '_');
    imageNum = strrep(imageNum, '_', '');
    
    fileEntry = fileMap(key);
    
    fprintf('Deleting files with timestamp: %s and image number: %s\n', timestamp, imageNum);
    
    % Delete from cam0
    if fileEntry.cam0
        delete(fullfile(cam0Dir, sprintf('0_%s_%s.jpg', timestamp, imageNum)));
        fprintf('Deleted cam0 file: 0_%s_%s.jpg\n', timestamp, imageNum);
    end
    % Delete from cam1
    if fileEntry.cam1
        delete(fullfile(cam1Dir, sprintf('1_%s_%s.jpg', timestamp, imageNum)));
        fprintf('Deleted cam1 file: 1_%s_%s.jpg\n', timestamp, imageNum);
    end
    % Delete from mats
    if fileEntry.mat
        delete(fullfile(matDir, sprintf('%s_%s.mat', timestamp, imageNum)));
        fprintf('Deleted mat file: %s_%s.mat\n', timestamp, imageNum);
    end
    % Delete from Rectified_Images (_rect and _disp)
    if fileEntry.rect
        delete(fullfile(rectifiedDir, sprintf('%s_%s_rect.jpg', timestamp, imageNum)));
        fprintf('Deleted _rect file: %s_%s_rect.jpg\n', timestamp, imageNum);
    end
    if fileEntry.disp
        delete(fullfile(rectifiedDir, sprintf('%s_%s_disp.jpg', timestamp, imageNum)));
        fprintf('Deleted _disp file: %s_%s_disp.jpg\n', timestamp, imageNum);
    end
end
