% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-12-16

function data2 = parse_data(mainDir, waveFolder)

    % Load IMU/GPS
    vn_tmp = dir(fullfile(mainDir, '*.csv'));
    vn = readtable([mainDir '\' vn_tmp.name]);

    % Get cam0 and cam1 dirs
    cam0Dir = fullfile(waveFolder, 'cam0');
    cam1Dir = fullfile(waveFolder, 'cam1');
    
    % Select images from cam0 and cam1
    cam0Images = dir(fullfile(cam0Dir, '*.jpg'));
    cam1Images = dir(fullfile(cam1Dir, '*.jpg'));
    
    % Convert filenames into struct arrays same as select_files output
    selectedFiles0 = struct('name', {cam0Images.name});
    selectedFiles1 = struct('name', {cam1Images.name});
    
    % Get camera timestamps
    for i = 1:length(selectedFiles0) 
        [cameraID0, tstamp0, imageNum0] = parse_filename(selectedFiles0(i).name);
        tstamps0(i) = str2double(tstamp0);  % Convert to numeric nanoseconds
    end
    for i = 1:length(selectedFiles1)
        [cameraID1, tstamp1, imageNum1] = parse_filename(selectedFiles1(i).name);
        tstamps1(i) = str2double(tstamp1);  % Convert to numeric nanoseconds
    end

    % Calculate query times for IMU time series
    for i = 1:length(tstamps0)
        % Calculate the time difference in nanoseconds directly
        timeDiffNs(i) = tstamps1(i) - tstamps0(i);  % Difference in nanoseconds

        % Compute the average timestamp in nanoseconds
        avgTimestampNs = (tstamps0(i) + tstamps1(i)) / 2;

        % Interpolate IMU data to these times (apply lag here if necessary)
        queryTime(i) = avgTimestampNs; 
    end

    % Initialize new struct
    data2 = struct();

    % Fields to interpolate
    fields = vn.Properties.VariableNames;  % Get all column names of the vn table

    % Loop over each field for interpolation
    for i = 2:numel(fields)

        % Linearly interpolate each column to query points
        interp_values = interp1(vn{:,1}, vn{:,i}, queryTime, 'linear', 'extrap');

        % Store results in struct with same field names
        data2.(fields{i}) = interp_values;
    end

    % Store query times as well
    data2.queryTime = queryTime; % in nanoseconds

    % Create relative time
    data2.t0 = (queryTime - queryTime(1)) * 1e-9; % relative time in seconds

    % Save cam delays
    data2.camDiffs = timeDiffNs * 10^-9;  % cam delay in seconds

end