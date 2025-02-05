% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2025-01-08

% Find the file in other set with the nearest timestamp 
function nearestFile = find_nearest_file(files, targetTimeNs)
    nearestFile = [];
    minTimeDiff = Inf;  % Initialize with a large value

    for i = 1:numel(files)
        [~, ts, ~] = parse_filename(files(i).name);  % Extract timestamp
        fileTimeNs = str2double(ts);  % Convert to numeric

        % Compute the absolute time difference
        timeDiff = abs(fileTimeNs - targetTimeNs);

        % Update if this file is closer
        if timeDiff < minTimeDiff
            minTimeDiff = timeDiff;
            nearestFile = files(i);
        end
    end
end