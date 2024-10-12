% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-10

clear; clc; close all;

addpath('functions/');

%% Inputs
           
vers_control = 1;            % timestamp and save current ptCloud?
manualFlag = 1;              % Set to 1 for manual point cloud editing, or 0 for only automatic cleaning
bounds = [-10 10 -10 10 0 20];   % [xmin xmax ymin ymax zmin zmax] for trimming points (meters)
binSize = 1;                 % size of the cubic bin for stepping through points (meters)

path = uigetdir('../../','Select path to session to clean ptClouds'); % load path to dir to clean ptClouds
%%%%               ^^^^^^^^^^^^ Queue up multiple dirs ^^^^^^^^^^^

matDir = [path '/mats'];
if ~exist(matDir, 'dir')
    disp('No mats/ directory in this session.');
    return;
end

%% Process ptClouds

cleanFlag = 1; 
while cleanFlag
    % Choose point cloud
    file = uigetfile([path '/Rectified_Images/*.png'],'Select file to view point cloud');
    file = file(1:end-9);
    
    % Load mat
    matFile = [matDir '/' file '.mat'];
    fprintf('Processing file: %s\n', matFile);
    load(matFile);

    % Save previous versions with timestamp before applying changes
    timestamp = datestr(now, 'yyyymmdd_HHMMSS');
    
    % Create new variable names with timestamps
    eval(['points3D_', timestamp, ' = points3D;']);
    eval(['colors_', timestamp, ' = colors;']);

    if vers_control
        % Save timestamped variables to the mat file
        save(matFile, ['points3D_', timestamp], ['colors_', timestamp], '-append');
    end

    %%%%%%%%%%%%%%%%%%%%%%%%%%% Apply QA/QC %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    % Remove rows where any of the columns in points3D have NaNs
    validRows = all(~isnan(points3D), 2);  % Find rows where all x, y, z values are non-NaN
    
    % Keep only the valid rows in points3D and corresponding colors
    points3D = points3D(validRows, :);  % Remove rows with NaNs in points3D
    colors = colors(validRows, :);  % Keep corresponding color rows

    [points3D, colors] = trimBounds(points3D, colors, bounds); % Update points3D after QA/QC

    ptCloud = pointCloud(points3D, 'Color', colors);
    ptCloud = pcdenoise(ptCloud);
  
    % Change clean flag
    clean = 1;

    % Save updated points3D and ptCloud
    save(matFile, 'points3D', 'colors', 'ptCloud', 'clean', '-append');

    % If manualFlag is set, manually edit the point cloud using the brush tool
    if manualFlag
        
        % Create a 3D scatter plot with the points and colors
        f = figure;
        p = scatter3(points3D(:,1), points3D(:,2), points3D(:,3), 1, double(colors) / 255, 'filled');
        xlabel('X'); ylabel('Y'); zlabel('Z');
        title('Brush Data to Delete Points');

        % Initialize a logical array to keep track of all brushed points
        brushedIdx = false(size(points3D, 1), 1);

        % Enable data brushing for the figure
        brush on;

        while ishandle(f)
            newBrushedIdx = find(p.BrushData);  % Get the indices of brushed points
            brushedIdx(newBrushedIdx) = true;
            pause(0.1)
        end

        % Delete the brushed points
        points3D = points3D(~brushedIdx, :);
        colors = colors(~brushedIdx, :);
        
        % Write updated ptCloud
        ptCloud = pointCloud(points3D, 'Color', colors);

        % Save the updated points3D, ptCloud and colors
        save(matFile, 'points3D', 'colors', 'ptCloud', '-append');

    end
    answer = questdlg('Clean another point cloud?', ...
    'Clean another point cloud', ...
    'Yes','No','Yes');
    switch answer
        case 'Yes'
            cleanFlag = 1; 
        case 'No'
            cleanFlag = 0; 
    end
end
