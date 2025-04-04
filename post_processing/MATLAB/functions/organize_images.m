% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2025-01-08

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
        
        % Convert the selected timestamp to numeric (nanoseconds)
        targetTimeNs = str2double(timestamp);
        
        % Determine the other camera's file list
        if cameraID == '0'
            otherFiles = cam1Files;
        else
            otherFiles = cam0Files;
        end

        % Find the nearest timestamp match in the other camera's file list
        matchingFile = find_matching_file(otherFiles, targetTimeNs, imageNum);
        
        if isempty(matchingFile)
            warning(['Corresponding file not found for ', selectedFile.name]);
            continue;  % Skip to the next file if no match is found
        end        

        % Copy the files into the wave folder
        if folderIndex == 1
            copyfile(fullfile(cam0Dir, selectedFile.name), fullfile(waveFolder, 'cam0', selectedFile.name));
            copyfile(fullfile(cam1Dir, matchingFile.name), fullfile(waveFolder, 'cam1', matchingFile.name));
        else
            copyfile(fullfile(cam1Dir, selectedFile.name), fullfile(waveFolder, 'cam1', selectedFile.name));
            copyfile(fullfile(cam0Dir, matchingFile.name), fullfile(waveFolder, 'cam0', matchingFile.name));
        end
    end    
    disp(['Files successfully copied to ', waveFolder]);
end


