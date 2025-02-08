% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-06

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