% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-06

% Parse the filename into cameraID, timestamp, and imageNum
function [cameraID, tstamp, imageNum] = parse_filename(filename)
    parts = split(filename, '_');
    cameraID = parts{1}; % '0' or '1'
    tstamp = parts{2}; % Monotonic time in nanoseconds
    imageNum = parts{3}(1:end-4); % Remove '.jpg' extension
end