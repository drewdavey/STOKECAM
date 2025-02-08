% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-06

% % Function to find a matching file by timestamp (ignoring milliseconds) and image number
% function matchingFile = find_matching_file(files, timestamp, imageNum)
%     matchingFile = [];
%     for i = 1:numel(files)
%         [~, ts, imgNum] = parse_filename(files(i).name);
%         % Compare only the timestamp up to seconds and the image number
%         if strcmp(ts, timestamp) && strcmp(imgNum, imageNum)
%             matchingFile = files(i);
%             return;
%         end
%     end
% end

% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-10

% Function to find a matching file by timestamp (ignoring milliseconds) and image number
% Also checks mats and Rectified_Images directories
function matchingFile = find_matching_file(files, timestamp, imageNum, matFiles, rectifiedFiles)

    matchingFile = [];
    
    % First, check if there is a matching file in cam0 or cam1
    for i = 1:numel(files)
        [~, ts, imgNum] = parse_filename(files(i).name);
        % Compare only the timestamp up to seconds and the image number
        if strcmp(ts, timestamp) && strcmp(imgNum, imageNum)
            matchingFile = files(i);
            break;
        end
    end
    
    % If no matching file was found in cam0/cam1, return empty
    if isempty(matchingFile)
        return;
    end
    
    % Check mats directory for corresponding file by timestamp and image number
    matFileExists = find_matching_mats(matFiles, timestamp, imageNum);
    
    % Check Rectified_Images directory for both _rect and _disp files
    rectFileExists = find_matching_rectified(rectifiedFiles, timestamp, imageNum, '_rect');
    dispFileExists = find_matching_rectified(rectifiedFiles, timestamp, imageNum, '_disp');
    
    % If any file is missing, mark the match as invalid
    if isempty(matFileExists) || isempty(rectFileExists) || isempty(dispFileExists)
        matchingFile = []; % Mark it as missing since one or more files are absent
    end
    
end

% Helper function to find a match in mats directory
function matchingMatFile = find_matching_mats(matFiles, timestamp, imageNum)
    matchingMatFile = [];
    for i = 1:numel(matFiles)
        [~, ts, imgNum] = parse_filename(matFiles(i).name);
        % Compare timestamp and image number (ignoring microseconds)
        if strcmp(ts, timestamp) && strcmp(imgNum, imageNum)
            matchingMatFile = matFiles(i);
            return;
        end
    end
end

% Helper function to find a match in Rectified_Images directory (either _rect or _disp)
function matchingRectFile = find_matching_rectified(rectifiedFiles, timestamp, imageNum, suffix)
    matchingRectFile = [];
    for i = 1:numel(rectifiedFiles)
        [~, ts, imgNum] = parse_filename(rectifiedFiles(i).name);
        % Compare timestamp, image number, and the suffix (_rect or _disp)
        if strcmp(ts, timestamp) && strcmp(imgNum, imageNum) && contains(rectifiedFiles(i).name, suffix)
            matchingRectFile = rectifiedFiles(i);
            return;
        end
    end
end
