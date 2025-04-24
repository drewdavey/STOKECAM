% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2025-04-21

clear; clc; close all;

addpath('functions/');

%% Inputs

session = uigetdir('../../../FSR/stereo_cam/DATA/','Select path to session'); % load path to session
wave = uigetdir(session,'Select a wave'); % load path to wave

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
        matFile = uigetfile([wave '/L2/*.mat'],'Select file to L2 ptCloud');
        matPath = [wave '/L2/' matFile]; load(matPath);
        player3D = pcplayer(ptCloud.XLimits, ptCloud.YLimits, ptCloud.ZLimits, VerticalAxis="z", ...
            VerticalAxisDir="down");
        view(player3D, ptCloud);
    elseif L3
        matPath = [wave '/L3ptCloud.mat'];
        if isempty(matPath)
            error('No L3 ptCloud found in wave directory: %s', wave);
        end
        load(matPath);
        player3D = pcplayer(ptCloud.XLimits, ptCloud.YLimits, ptCloud.ZLimits, VerticalAxis="z", ...
            VerticalAxisDir="down");
        view(player3D, ptCloud);
    end

    while isOpen(player3D)
        pause(0.1)
    end

    if L1 || L2
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
                        clean = 1;
                        save(matPath); 
                end
        end
    end
    answer = questdlg('View another point cloud?', ...
    'View another point cloud', ...
    'Yes','No','Yes');
    switch answer
        case 'Yes'
            viewFlag = 1; 
        case 'No'
            if L2
                answer = questdlg('Generate L3 ptCloud?', ...
                'Generate L3 ptCloud?', ...
                'Yes','No','Yes');
                switch answer
                    case 'Yes' % Write new L3ptCloud with L2 edits
                        genL3ptCloud(wave);
                end
            end
            viewFlag = 0; % Exit
    end
end