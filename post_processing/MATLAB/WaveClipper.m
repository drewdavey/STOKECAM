% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-10

clear; clc; close all;

addpath('functions/');

%% Inputs

segment = 0;        % Segment images?

%% Clip Waves

clipWaves = 1;
while clipWaves
    mainDir = uigetdir('../../../FSR/stereo_cam/DATA/','Select path to session'); % load path to session
    waveFolder = organize_images(mainDir); % wave* directory containing 'cam0' and 'cam1' folders
    % vn = parse_imu(mainDir, waveFolder);
    % 

    % Load IMU/GPS
    vn_tmp = dir(fullfile(mainDir, '*.csv'));
    tstamps_tmp = dir(fullfile(mainDir, '*.txt'));
    vn = readtable([mainDir '\' vn_tmp.name]);
    tstamps = readtable([mainDir '\' tstamps_tmp.name]);

    % GPS epoch (January 6, 1980)
    gpsEpoch = datetime(1980, 1, 6, 0, 0, 0, 'Format', 'HH:mm:ss.SSS');
    
    % Convert timeGps from nanoseconds to seconds
    timeGps1 = vn.timeGps / 1e9;
    % Convert timeGps from microseconds to seconds
    timeGps2 = tstamps.VN_timeGps / 1e6;
    
    % GPS-UTC offset (leap seconds)
    leapSeconds = 18; % Current offset 
    
    % Convert GPS time to UTC time
    % vn.utcTimes = gpsEpoch + seconds(timeGps1 - leapSeconds);
    tstamps.VN_Gps2Utc = gpsEpoch + seconds(timeGps2 - leapSeconds);
    
    % % OR, just use UTC fields to make VN datetime vector
    % vn.utcTimes = datetime(vn.utcYear, vn.utcMonth, vn.utcDay, ...
    %                    vn.utcHour, vn.utcMinute, vn.utcSecond + vn.utcFracsec / 1000, ...
    %                    'Format', 'HH:mm:ss.SSS');
    % vn.utcTimes = datetime(vn.utcHour, vn.utcMinute, vn.utcSecond + vn.utcFracsec / 1000, 'InputFormat', 'HH:mm:ss.SSSSSS',...
    %                    'Format', 'HH:mm:ss.SSS');
    vn.utcTimes = datetime(0,0,0, vn.utcHour, vn.utcMinute, vn.utcSecond + vn.utcFracsec / 1000, ...
                       'Format', 'HH:mm:ss.SSS', 'InputFormat', 'HH:mm:ss.SSS');
    
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
        [cameraID0, tshort0, imageNum0, tlong0] = parse_filename(selectedFiles0(i).name);
        hours0 = tlong0(1:2);
        minutes0 = tlong0(3:4);
        seconds0 = tlong0(5:6);
        microseconds0 = tlong0(7:end);
        fullTimestamp0 = [hours0, ':', minutes0, ':', seconds0, '.', microseconds0];
        tstamps0(i) = datetime(fullTimestamp0, 'InputFormat', 'HH:mm:ss.SSSSSS', 'Format', 'HH:mm:ss.SSSSSS');
    end
    for i = 1:length(selectedFiles1)
        [cameraID1, tshort1, imageNum1, tlong1] = parse_filename(selectedFiles1(i).name);
        hours1 = tlong1(1:2);
        minutes1 = tlong1(3:4);
        seconds1 = tlong1(5:6);
        microseconds1 = tlong1(7:end); 
        fullTimestamp1 = [hours1, ':', minutes1, ':', seconds1, '.', microseconds1];
        tstamps1(i) = datetime(fullTimestamp1, 'InputFormat', 'HH:mm:ss.SSSSSS', 'Format', 'HH:mm:ss.SSSSSS');
    end

    % Find corresponding start times 
    start_indices = strcmp(tstamps.burst, 'start');
    start = tstamps(start_indices,:);
    for i = 1:height(start)
        tmp1 = num2str(start.RP_time(i), '%012.0f'); % Ensure 12-digit zero-padded string
        hours1 = tmp1(1:2); minutes1 = tmp1(3:4); seconds1 = tmp1(5:6); microseconds1 = tmp1(7:12); 
        fullTimestamp1 = [hours1, ':', minutes1, ':', seconds1, '.', microseconds1];
        RP_time(i) = datetime(fullTimestamp1, 'InputFormat', 'HH:mm:ss.SSSSSS', 'Format', 'HH:mm:ss.SSSSSS');
        
        VN_time(i) = start.VN_Gps2Utc(i);

        % tmp2 = num2str(start.VN_timeUtc(i), '%09.0f'); % Ensure 9-digit zero-padded string 
        % hours2 = tmp2(1:2); minutes2 = tmp2(3:4); seconds2 = tmp2(5:6); milliseconds2 = tmp2(7:9); 
        % fullTimestamp2 = [hours2, ':', minutes2, ':', seconds2, '.', milliseconds2];
        % VN_time(i) = datetime(fullTimestamp2, 'InputFormat', 'HH:mm:ss.SSS', 'Format', 'HH:mm:ss.SSSSSS');
    end

    % % Find diff from RP to VN
    % diffs = RP_time - VN_time; % RP to VN
    % diffs = milliseconds(diffs); % Convert duration to milliseconds
    lag = 0.052428; % seconds
    
    % Find start time associated with first image. 
    % [~, idx] = min(abs(RP_time - (tstamps0(1) + diffs(1))));
    % [~, idx] = min(abs(RP_time - (tstamps0(1) + diffs(1))));
    
    % Apply corresponding diff to sequence
    % diff = diffs(idx);
    % searchTime = tstamps0 - milliseconds(diff);

    searchTime = tstamps0 + seconds(lag);

    % Extract idx from VN-200 struct
    for i = 1:length(searchTime)
        [~, idx] = min(abs(vn.utcTimes - searchTime(i))); % Find the closest match
        closest_idx(i) = idx; % Store the index
    end

    % Create new downsampled VN-200 struct
    imu = vn(closest_idx,:);

    vn=imu;
    % Save parsed VN-200 data to waveDir
    save(fullfile(waveFolder, 'imu.mat'), 'vn');











    if segment
        cam0Dir = fullfile(waveFolder, 'cam0');
        cam1Dir = fullfile(waveFolder, 'cam1');
    
        % Get all jpg files in cam0 and cam1
        cam0Files = dir(fullfile(cam0Dir, '*.jpg'));
        cam1Files = dir(fullfile(cam1Dir, '*.jpg'));

        % Loop through each frame
        for i = 1:length(cam0Files)
            % Get the full path of each image file
            cam0File = fullfile(cam0Dir, cam0Files(i).name);
            cam1File = fullfile(cam1Dir, cam1Files(i).name);
    
            % Read the images
            I1 = imread(cam0File);
            I2 = imread(cam1File);
    
            % Segment the air and water in I1 (using GUI)
            mask = create_mask(I1);
    
            % Apply the mask to both cam0 and cam1 images
            maskedI1 = I1;
            maskedI1(repmat(~mask,[1 1 3])) = 0;  % Apply mask to cam0 image
    
            maskedI2 = I2;
            maskedI2(repmat(~mask,[1 1 3])) = 0;  % Apply the same mask to cam1 image
    
            % Display the segmented image
            figure;
            title(['Segmented Images ', num2str(i)]);
            subplot(1, 2, 1), imshow(maskedI1), title('Cam0');
            subplot(1, 2, 2), imshow(maskedI2), title('Cam1');
    
            % Write segmented images
            imwrite(maskedI1,cam0File);
            imwrite(maskedI2,cam1File);

            clearvars BW
            % close all
        end
    end
    answer = questdlg('Clip another wave?', ...
    'Clip another wave?', ...
    'Yes','No','Yes');
    switch answer
        case 'Yes'
            clipWaves = 1; 
        case 'No'
            clipWaves = 0; 
    end
end