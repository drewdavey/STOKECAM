% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-06

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