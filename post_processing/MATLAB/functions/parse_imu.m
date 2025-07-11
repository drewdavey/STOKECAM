% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-12-16

function imu = parse_imu(mainDir, waveFolder)

    % Load IMU/GPS
    vn_tmp = dir(fullfile(mainDir, '*.csv'));
    vn = readtable([mainDir '\' vn_tmp.name]);
    % vn = readtable([mainDir '\' vn_tmp.name], 'Variablenamesline',1);

    % Get cam0 and cam1 dirs
    cam0Dir = fullfile(waveFolder, 'cam0');
    cam1Dir = fullfile(waveFolder, 'cam1');
    
    % Select images from cam0 and cam1
    cam0Images = dir(fullfile(cam0Dir, '*.jpg'));
    cam1Images = dir(fullfile(cam1Dir, '*.jpg'));
    
    % Convert filenames into struct arrays
    files0 = struct('name', {cam0Images.name});
    files1 = struct('name', {cam1Images.name});
    
    % Get camera timestamps
    for i = 1:length(files0)
        [~, tstamp0, ~] = parse_filename(files0(i).name);
        tstamps0(i) = str2double(tstamp0);  % Convert to numeric nanoseconds
    end
    for i = 1:length(files1)
        [~, tstamp1, ~] = parse_filename(files1(i).name);
        tstamps1(i) = str2double(tstamp1);  % Convert to numeric nanoseconds
    end

    % Calculate query times for IMU time series
    %%% Avgtimestamp will be same if using hardware trigger %%%
    for i = 1:length(tstamps0)
        % Calculate the time difference in nanoseconds directly
        timeDiffNs(i) = tstamps1(i) - tstamps0(i);  % Difference in nanoseconds

        % Compute the average timestamp in nanoseconds
        avgTimestampNs = (tstamps0(i) + tstamps1(i)) / 2;

        % Interpolate IMU data to these times (apply lag here if necessary)
        queryTime(i) = avgTimestampNs; 
    end

    % Initialize new struct
    imu = struct();

    % Fields to interpolate
    fields = vn.Properties.VariableNames;  % Get all column names of the vn table

    % Loop over each field for interpolation
    for i = 2:numel(fields)

        % Linearly interpolate each column to query points
        interp_values = interp1(vn{:,1}, vn{:,i}, queryTime, 'linear', 'extrap');

        % Store results in struct with same field names
        imu.(fields{i}) = interp_values;
    end

    % Store query times as well
    imu.queryTime = queryTime; % in nanoseconds

    % Create relative time
    imu.t0 = (queryTime - queryTime(1)) * 1e-9; % relative time in seconds

    % Save cam delays
    imu.camDiffs = timeDiffNs * 10^-9;  % cam delay in seconds

end