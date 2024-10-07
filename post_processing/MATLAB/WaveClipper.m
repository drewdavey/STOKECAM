% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-06

clear; clc; close all;

%% Inputs

clipWaves = 1;      % Repetition flag
segment = 1;        % Segment images?

while clipWaves
    mainDir = uigetdir('../../','Select path to session'); % load path to session
    waveFolder = organize_images(mainDir);
    if segment
        segment_images(waveFolder);
    end
    answer = questdlg('Another?', ...
    'Clip another wave?', ...
    'Yes','No','Yes');
    switch answer
        case 'Yes'
            clipWaves = 1; 
        case 'No'
            clipWaves = 0; 
    end
end

%% Image Segmentation Functions

function segment_images(waveFolder)

    % Input: wave* directory containing 'cam0' and 'cam1' folders
    cam0Dir = fullfile(waveFolder, 'cam0');
    cam1Dir = fullfile(waveFolder, 'cam1');

    % Get all jpg files in cam0 and cam1
    cam0Files = dir(fullfile(cam0Dir, '*.jpg'));
    cam1Files = dir(fullfile(cam1Dir, '*.jpg'));

    % Loop through each frame
    for i = 1:length(cam0Files)
        % Get the full path of each image file
        cam0File = fullfile(cam0Dir, cam0Files(i).name);
        cam1File = fullfile(cam1Dir, cam1Files(i).name);

        % Read the images
        I1 = imread(cam0File);
        I2 = imread(cam1File);

        % Segment the air and water 
        segmentedI1 = segment_water(I1);
        segmentedI2 = segment_water(I2);

        % Display the segmented image
        figure;
        title(['Segmented Images ', num2str(i)]);
        subplot(1, 2, 1), imshow(segmentedI1), title('Cam0');
        subplot(1, 2, 2), imshow(segmentedI2), title('Cam1');

        % Write segmented images
        imwrite(segmentedI1,cam0File);
        imwrite(segmentedI2,cam1File);
    end
end

function seg_I = segment_water(img)

    level = multithresh(img);
    seg_I = imquantize(img,level);
%     imshow(seg_I,[])

end

%% Organization Functions

function waveFolder = organize_images(mainDir)
    % Input: main directory containing 'cam0' and 'cam1' folders
    % mainDir is the path to the directory containing cam0/ and cam1/ folders
    cam0Dir = fullfile(mainDir, 'cam0');
    cam1Dir = fullfile(mainDir, 'cam1');
    % Get all jpg files in cam0 and cam1
    cam0Files = dir(fullfile(cam0Dir, '*.jpg'));
    cam1Files = dir(fullfile(cam1Dir, '*.jpg'));
    % Select files from either cam0 or cam1 
    [selectedFiles, folderIndex] = select_files(cam0Dir, cam1Dir);
    % Get number of 'wave' folders already present and increment
    waveFolder = get_wave_folder(mainDir);
    % Process selected files and find corresponding ones in the other camera folder
    for i = 1:numel(selectedFiles)
        selectedFile = selectedFiles(i);        
        % Extract timestamp and image number from selected file
        [cameraID, timestamp, imageNum] = parse_filename(selectedFile.name);        
        % Find the corresponding file in the other folder
        correspondingFile = find_corresponding_file(cameraID, timestamp, imageNum, cam0Files, cam1Files);        
        if isempty(correspondingFile)
            warning(['Corresponding file not found for ', selectedFile.name]);
            continue;  % Skip to the next file if no match is found
        end        
        if folderIndex == 1
            % Copy selected file to wavei/cam0/
            copyfile(fullfile(cam0Dir, selectedFile.name), fullfile(waveFolder, 'cam0', selectedFile.name));
            % Copy corresponding file to wavei/cam1/
            copyfile(fullfile(cam1Dir, correspondingFile.name), fullfile(waveFolder, 'cam1', correspondingFile.name));
        else
            % Copy selected file to wavei/cam1/
            copyfile(fullfile(cam1Dir, selectedFile.name), fullfile(waveFolder, 'cam1', selectedFile.name));
            % Copy corresponding file to wavei/cam0/
            copyfile(fullfile(cam0Dir, correspondingFile.name), fullfile(waveFolder, 'cam0', correspondingFile.name));
        end
    end    
    disp(['Files successfully copied to ', waveFolder]);
end

% Function to select multiple files using Finder/Explorer
function [selectedFiles, folderIndex] = select_files(cam0Dir, cam1Dir)
    folderIndex = menu('Select the folder to choose images from', 'cam0', 'cam1');    
    if folderIndex == 1
        % Selects files from cam0 
        [fileNames, ~] = uigetfile(fullfile(cam0Dir, '*.jpg'), 'Select images from cam0', 'MultiSelect', 'on');
    else
        % Selects files from cam1
        [fileNames, ~] = uigetfile(fullfile(cam1Dir, '*.jpg'), 'Select images from cam1', 'MultiSelect', 'on');
    end
    % Ensure fileNames is a cell array (in case only one file is selected)
    if ischar(fileNames)
        fileNames = {fileNames};
    end
    % Create a struct array for the selected files
    selectedFiles = struct('name', fileNames);
end

% Parse the filename into cameraID, timestamp, and imageNum
function [cameraID, timestamp, imageNum] = parse_filename(filename)
    parts = split(filename, '_');
    cameraID = parts{1}; % '0' or '1'
    timestamp = parts{2}(1:6); % Ignore microseconds, keep only HHMMSS
    imageNum = parts{3}(1:end-4); % Remove '.jpg' extension
end

% Function to find the corresponding file in the other camera folder
function correspondingFile = find_corresponding_file(cameraID, timestamp, imageNum, cam0Files, cam1Files)
    if cameraID == '0'
        % Look for matching timestamp and image number in cam1Files
        correspondingFile = find_matching_file(cam1Files, timestamp, imageNum);
    else
        % Look for matching timestamp and image number in cam0Files
        correspondingFile = find_matching_file(cam0Files, timestamp, imageNum);
    end
end

% Function to find a matching file by timestamp (ignoring milliseconds) and image number
function matchingFile = find_matching_file(files, timestamp, imageNum)
    matchingFile = [];
    for i = 1:numel(files)
        [~, ts, imgNum] = parse_filename(files(i).name);
        % Compare only the timestamp up to seconds and the image number
        if strcmp(ts, timestamp) && strcmp(imgNum, imageNum)
            matchingFile = files(i);
            return;
        end
    end
end

% Function to get the next wave folder index
function newWaveFolder = get_wave_folder(mainDir)
    % Get a list of all wave* folders in the main directory
    folderList = dir(fullfile(mainDir, 'wave*')); 
    % Initialize maxWaveNumber to 0
    maxWaveNumber = 0;    
    % Loop through each folder and extract the number
    for i = 1:length(folderList)
        folderName = folderList(i).name;
        % Check if the folder name starts with 'wave'
        if startsWith(folderName, 'wave')
            % Extract the number from the folder name
            waveNumber = sscanf(folderName, 'wave%d');
            % Update the maxWaveNumber if the current waveNumber is larger
            if ~isempty(waveNumber) && waveNumber > maxWaveNumber
                maxWaveNumber = waveNumber;
            end
        end
    end    
    % Create the new wave folder with incremented number
    newWaveNumber = maxWaveNumber + 1;
    newWaveFolder = fullfile(mainDir, sprintf('wave%d', newWaveNumber));
    % Create the new directories
    mkdir(newWaveFolder);
    mkdir(fullfile(newWaveFolder,'cam0/'));
    mkdir(fullfile(newWaveFolder,'cam1/'));
    disp(['Created new wave folder: ', newWaveFolder]);
end
