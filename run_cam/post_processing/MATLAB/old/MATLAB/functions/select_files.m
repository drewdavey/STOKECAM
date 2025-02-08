% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-06

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