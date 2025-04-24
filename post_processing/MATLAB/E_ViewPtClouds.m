% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2025-04-21

clear; clc; close all;

addpath('functions/');

%% Inputs

% Bounds for viewing ptCloud [xmin xmax ymin ymax zmin zmax] (meters)
bounds = [-10 10 -10 10 0 30];  
% bounds = [-50 50 -50 50 0 50]; 

session = uigetdir('../../../FSR/stereo_cam/DATA/','Select path to session'); % load path to session
wave = uigetdir(session,'Select path to wave'); % load path to wave

RAW = 0; L1 = 0; L2 = 0; L3 = 0;

answer = questdlg('Select level of post-processing', ...
    'Select level of post-processing', ...
    'RAW','L1','L2','L3','L3');
    switch answer
        case 'RAW'
            RAW = 1; 
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
    if RAW
        player3D = pcplayer(xbounds, ybounds, depth, VerticalAxis="y", ...
            VerticalAxisDir="down");
        matFile = uigetfile([wave '/L1/*.mat'],'Select file to RAW ptCloud');
        load(matFile);
        view(player3D, original.ptCloud);
    elseif L1
        player3D = pcplayer(xbounds, ybounds, depth, VerticalAxis="y", ...
            VerticalAxisDir="down");
        matFile = uigetfile([wave '/L1/*.mat'],'Select file to L1 ptCloud');
        load(matFile);
        view(player3D, ptCloud);
    elseif L2
        player3D = pcplayer(xbounds, ybounds, depth, VerticalAxis="z", ...
            VerticalAxisDir="down");
        matFile = uigetfile([wave '/L2/*.mat'],'Select file to L2 ptCloud');
        load(matFile);
        view(player3D, ptCloud);
    elseif L3
        player3D = pcplayer(xbounds, ybounds, depth, VerticalAxis="z", ...
            VerticalAxisDir="down");
        matFile = [wave '/L3ptCloud.mat'];
        load(matFile);
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
                        if L2
                            % Re align updated L2 ptclouds and write wave dir merged
                            % ptcloud
                        end
                        clean = 1;
                        save(matFile); 
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
            viewFlag = 0; 
    end
end
