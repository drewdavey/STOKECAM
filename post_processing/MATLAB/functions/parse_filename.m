% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-06

% Parse the filename into cameraID, timestamp, and imageNum
function [cameraID, timestamp, imageNum] = parse_filename(filename)
    parts = split(filename, '_');
    cameraID = parts{1}; % '0' or '1'
    timestamp = parts{2}(1:6); % Ignore microseconds, keep only HHMMSS
    imageNum = parts{3}(1:end-4); % Remove '.jpg' extension
end