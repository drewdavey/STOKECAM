% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-06

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