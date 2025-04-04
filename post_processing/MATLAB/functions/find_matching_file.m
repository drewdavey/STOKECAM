% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2025-01-08

% Find the matching file in other set
function matchingFile = find_matching_file(files, targetTimeNs, targetImageNum)
    matchingFile = [];
    matchingImageNum = '';    % Predefine as empty string
    minTimeDiff = 1e6;        % 1 ms timediff cutoff in ns

    % Find the file that is closest in timestamp
    for i = 1:numel(files)
        [~, ts, imageNum] = parse_filename(files(i).name);
        fileTimeNs = str2double(ts);

        timeDiff = abs(fileTimeNs - targetTimeNs);
        if timeDiff < minTimeDiff
            minTimeDiff = timeDiff;
            matchingFile = files(i);
            matchingImageNum = imageNum;
        end
    end

    % Check image number, if it doesn't match, throw a warning and skip
    if ~isempty(matchingFile) && ~strcmp(matchingImageNum, targetImageNum)
        warning(['Nearest timestamp %s, is greater than ' num2str(minTimeDiff*1e-6) 'ms from %s. Skipping this file.'], ...
                matchingImageNum, targetImageNum);
        matchingFile = [];
    end
end

