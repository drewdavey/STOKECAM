% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-12-16

function imu = parse_imu(mainDir, waveFolder)

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

    % Find corresponding IMU times
    for i = 1:length(tstamps0)
        % Compute the average timestamp in nanoseconds
        avgTimestampNs = (tstamps0(i) + tstamps1(i)) / 2;
    
        % Find the VN system timestamp closest to the average timestamp
        [~, idx] = min(abs(vn.systemTimeStamp - avgTimestampNs));  % Find the index of the nearest VN timestamp
        closest_idx(i) = idx;  % Store the index
    end

    % Create new downsampled VN-200 struct
    imu = vn(closest_idx,:);

end