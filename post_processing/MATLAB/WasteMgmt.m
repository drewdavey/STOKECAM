% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-10

clear; clc; close all;

addpath('functions/');

%% Filepath

% Initialize paths array
paths = {};

path = uigetdir('../../../FSR/stereo_cam/DATA/','Select path to session'); % load path to session
paths{end + 1} = path;  % Add selected session to paths array

% Queue up additional sessions?
while true
    answer = questdlg('Queue another session?', ...
    'Queue another session?', ...
    'Yes','No','Yes');
    switch answer
        case 'Yes'
            path = uigetdir([path '/../'],'Select path to session for reconstruction');
        case 'No' 
            break;
    end
    paths{end + 1} = path;  % Add selected directory to paths array
end

% Process each selected path
for m = 1:length(paths)
    path = paths{m};

    matDir = fullfile(path, 'mats');
    rectifiedImagesDir = fullfile(path, 'Rectified_Images');
    
    cam0Dir = fullfile(path, 'cam0');
    cam1Dir = fullfile(path, 'cam1');
    
    % Set cleanAll if mat and rectified dirs exist
    if exist(matDir, 'dir') && exist(rectifiedImagesDir, 'dir')
        cleanAll = 1; % Enable cleaning mats based on rectified images
    else
        cleanAll = 0; % Skip cleaning mats
    end
    
    %% Cleanup dirs
    
    matFiles = dir(fullfile(matDir, '*.mat'));
    rectFiles = dir(fullfile(rectifiedImagesDir, '*.png'));
    cam0Files = dir(fullfile(cam0Dir, '0_*.jpg'));
    cam1Files = dir(fullfile(cam1Dir, '1_*.jpg'));
    
    matFilenames = {matFiles.name};
    rectFilenames = {rectFiles.name};
    cam0Filenames = {cam0Files.name};
    cam1Filenames = {cam1Files.name};
    
    % Loop through the cam0 files and find corresponding cam1 files
    for i = 1:length(cam0Files)
        
        [cameraID0, timestamp0, imageNum0] = parse_filename(cam0Files(i).name);
        
        % Find the corresponding cam1 file
        correspondingFile = find_corresponding_file(cameraID0, timestamp0, imageNum0, cam0Files, cam1Files);
        
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
        correspondingFile = find_corresponding_file(cameraID1, timestamp1, imageNum1, cam0Files, cam1Files);
        
        % If no corresponding file is found, delete the cam1 file
        if isempty(correspondingFile)
            delete(fullfile(cam1Dir, cam1Files(i).name));
            fprintf('Deleted: %s\n', fullfile(cam1Dir, cam1Files(i).name));
        end
    end
    
    if cleanAll
    
        % Loop through mat files and check if corresponding files exist
        for i = 1:length(rectFiles)
            % Parse timestamp and image number from rect file (no microseconds in mats)
            tokens = regexp(rectFiles(i).name, '(\d{6})_(\d+)', 'tokens', 'once');
            if isempty(tokens)
                continue; % Skip if the filename doesn't match the expected format
            end
            timestamp = tokens{1};
            imageNum = tokens{2};
            
            % Check if the corresponding _rect or _disp file exists
            rectFileExists = exist(fullfile(rectifiedImagesDir, sprintf('%s_%s_rect.png', timestamp, imageNum)), 'file');
            dispFileExists = exist(fullfile(rectifiedImagesDir, sprintf('%s_%s_disp.png', timestamp, imageNum)), 'file');
         
            % If rect file is missing, delete the disp file
            if ~rectFileExists && dispFileExists
                dispFilePath = fullfile(rectifiedImagesDir, sprintf('%s_%s_disp.png', timestamp, imageNum));
                delete(dispFilePath);
                fprintf('Deleted disp file: %s\n', dispFilePath);
            end
            % If disp file is missing, delete the rect file
            if ~dispFileExists && rectFileExists
                rectFilePath = fullfile(rectifiedImagesDir, sprintf('%s_%s_rect.png', timestamp, imageNum));
                delete(rectFilePath);
                fprintf('Deleted rect file: %s\n', rectFilePath);  
            end
        end
    
        % Loop through mat files and check if corresponding files exist
        for i = 1:length(matFiles)
            % Parse timestamp and image number from rect file (no microseconds in mats)
            tokens = regexp(matFiles(i).name, '(\d{6})_(\d+)', 'tokens', 'once');
            if isempty(tokens)
                continue; % Skip if the filename doesn't match the expected format
            end
            timestamp = tokens{1};
            imageNum = tokens{2};
            
            % Check if the corresponding _rect or _disp file exists
            rectFileExists = exist(fullfile(rectifiedImagesDir, sprintf('%s_%s_rect.png', timestamp, imageNum)), 'file');
            dispFileExists = exist(fullfile(rectifiedImagesDir, sprintf('%s_%s_disp.png', timestamp, imageNum)), 'file');
            
            % If either rect or disp is missing, delete corresponding files
            if ~rectFileExists || ~dispFileExists
                matFilePath = fullfile(matDir, sprintf('%s_%s.mat', timestamp, imageNum));
                if exist(matFilePath, 'file')
                    delete(matFilePath);
                    fprintf('Deleted mat file: %s\n', matFilePath);
                end
                
                % Find the corresponding cam1 file
                cam1File = find_corresponding_file('0', timestamp, imageNum, cam0Files, cam1Files);
                cam1FilePath = fullfile(cam1File.folder, cam1File.name);
                if exist(cam1FilePath, 'file')
                    delete(cam1FilePath); 
                    fprintf('Deleted cam1 file: %s\n', cam1FilePath);
                end
                
                % Find the corresponding cam1 file
                cam0File = find_corresponding_file('1', timestamp, imageNum, cam0Files, cam1Files);
                cam0FilePath = fullfile(cam0File.folder, cam0File.name);
                if exist(cam0FilePath, 'file')
                    delete(cam0FilePath); 
                    fprintf('Deleted cam0 file: %s\n', cam0FilePath); 
                end
            end
        end
    end
    [~, lastDir] = fileparts(path);
    disp([lastDir ' cleanup complete.']);
end