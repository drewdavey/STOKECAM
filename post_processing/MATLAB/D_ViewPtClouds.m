% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2025-04-21

clear; clc; close all;

addpath('functions/');

%% Inputs

% Animate L2 ptClouds?
animate = 0;

wave = uigetdir('C:\Users\drew\OneDrive - UC San Diego\FSR\stereo_cam\DATA','Select path to wave'); % load path to wave
% wave = '\\wsl.localhost\Ubuntu\home\drew\waveTracking\data\waveTest1';

L1 = 0; L2 = 0; L3 = 0;
answer = questdlg('Select level of post-processing', ...
    'Select level of post-processing', ...
    'L1','L2','L3','L3');
    switch answer
        case 'L1'
            L1 = 1;
        case 'L2'
            L2 = 1;
        case 'L3'
            L3 = 1;
    end

%% View and clean point clouds

viewFlag = 1;
while viewFlag
    % Visualize the point cloud
    if L1
        matFile = uigetfile([wave '/L1/*.mat'],'Select file to L1 ptCloud');
        matPath = [wave '/L1/' matFile]; load(matPath);
        player3D = pcplayer(ptCloud.XLimits, ptCloud.YLimits, ptCloud.ZLimits, VerticalAxis="y", ...
            VerticalAxisDir="down");
        view(player3D, ptCloud);
    elseif L2
        if animate
            load([wave '/imu.mat']);
            matFiles = dir(fullfile(wave, 'L2', '*.mat'));
            if isempty(matFiles)
                disp('No .mat files found in L2 directory.');
                return;
            end
            matPath0 = [wave '/L3ptCloud.mat']; load(matPath0);
            player3D = pcplayer(ptCloud.XLimits, ptCloud.YLimits, ptCloud.ZLimits, VerticalAxis="z", ...
                VerticalAxisDir="up");
            pause(10);
            for k = 1:length(matFiles)
                matPath = fullfile(matFiles(k).folder, matFiles(k).name);
                data = load(matPath);
                if ~isfield(data, 'ptCloud')
                    warning('File %s does not contain ptCloud object.', matFiles(k).name);
                    continue;
                end
                if k == 1
                    cumulativePtCloud = data.ptCloud;
                    pause(10);
                    view(player3D, cumulativePtCloud);
                else
                    cumulativePtCloud = pccat([cumulativePtCloud, data.ptCloud]);
                    view(player3D, cumulativePtCloud);
                end
                pause(1);
                % if k<length(matFiles)
                    % pause(imu.t0(k+1)-imu.t0(k));
                % end
            end
        else
            matFile = uigetfile([wave '/L2/*.mat'],'Select file to L2 ptCloud');
            matPath = [wave '/L2/' matFile]; load(matPath);
            player3D = pcplayer(ptCloud.XLimits, ptCloud.YLimits, ptCloud.ZLimits, VerticalAxis="z", ...
                VerticalAxisDir="up");
            view(player3D, ptCloud);
        end

    elseif L3
        matPath = [wave '/L3ptCloud.mat'];
        if isempty(matPath)
            error('No L3 ptCloud found in wave directory: %s', wave);
        end
        load(matPath);
        player3D = pcplayer(ptCloud.XLimits, ptCloud.YLimits, ptCloud.ZLimits, VerticalAxis="z", ...
            VerticalAxisDir="up");
        view(player3D, ptCloud);
    end

    while isOpen(player3D)
        pause(0.1)
    end

    if L2
        answer = questdlg('Manually clean point cloud?', ...
        'Manually clean point cloud?', ...
        'Yes','No','Yes');
        switch answer
            case 'Yes'
                [points3D, colors] = manualClean(points3D, colors);
                % Remove rows where any of the columns in points3D have NaNs
                validRows = all(~isnan(points3D), 2);  % Find rows where all x, y, z values are non-NaN
                % Keep only the valid rows in points3D and corresponding colors
                points3D = points3D(validRows, :);  % Remove rows with NaNs in points3D
                colors = colors(validRows, :);  % Keep corresponding color rows
                % Write updated point cloud
                ptCloud = pointCloud(points3D, 'Color', colors);
                answer = questdlg('Save changes?', ...
                'Save changes', ...
                'Yes','No','Yes');
                switch answer
                    case 'Yes' % Save updates
                        save(matPath);      % Write updated L2 ptCloud
                end
        end

        answer = questdlg('Export brushedData to transect?', ...
        'Export brushedData to transect?', ...
        'Yes','No','Yes');
        switch answer
            case 'Yes'
                transectDir = fullfile(wave, 'transect');
                if ~exist(transectDir, 'dir')
                    mkdir(transectDir);
                end
                X = brushedData(:,1);
                Y = brushedData(:,2);
                Z = brushedData(:,3);
                tName = matFile(1:end-4);
                save(fullfile(transectDir, tName), 'X', 'Y', 'Z');
        end
    end
    if L1 || L2
        answer = questdlg('View another point cloud?', ...
        'View another point cloud', ...
        'Yes','No','Yes');
        switch answer
            case 'Yes'
                viewFlag = 1; 
            case 'No'
                viewFlag = 0; % Exit
                if L2
                    genL3ptCloud(wave); % Write new L3ptCloud
                end
        end
    else
        viewFlag = 0; % Exit
    end
end