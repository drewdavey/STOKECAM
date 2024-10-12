% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-10

clear; clc; close all;

addpath('functions/');

%% Inputs

res = 300;          % resolution for figures (.pngs)

dX = 0.001;     % X step size for plotting (meters)
dY = 0.01;     % Y step size for plotting (meters)
dZ = 1;       % Z step size for plotting (meters)

path = uigetdir('../../','Select path to session for analysis'); % load path to dir 

choice = questdlg('Select a subset of images?', ...
    'Subset Selection', ...
    'Yes', 'No', 'No');
switch choice
    case 'Yes'
        subset = 1;  % Select subset of images
    case 'No'
        subset = 0;  % Do not select subset
end

%% Organize dirs
cam0Dir = fullfile(path, 'cam0');
cam1Dir = fullfile(path, 'cam1');
cam0Files = dir(fullfile(cam0Dir, '0_*.jpg'));
cam1Files = dir(fullfile(cam1Dir, '1_*.jpg'));
matDir = fullfile(path, 'mats');
ptCloudDir = fullfile(path, 'ptClouds');
rectifiedImagesDir = fullfile(path, 'Rectified_Images');
figDir = fullfile(path, 'figs');
if ~exist(figDir, 'dir')
    mkdir(figDir);  % Create the 'figs/' folder if it doesn't exist
end
% Set loadMats if mat and rectified dirs exist
if exist(matDir, 'dir') && exist(rectifiedImagesDir, 'dir')
    loadMats = 1; % Enable loading mats based on rectified images
    matFiles = dir(fullfile(matDir, '*.mat'));
else
    loadMats = 0; % Skip loading mats
end

%% Select images from cam0 and cam1
if subset == 1
    % Select subset of images from either cam0 or cam1
    [selectedFiles, folderIndex] = select_files(cam0Dir, cam1Dir); 
    % Automatically find the corresponding files from the other camera
    if folderIndex == 1
        % Selected files are from cam0, find corresponding files in cam1
        selectedFiles0 = selectedFiles;  % cam0 selected
        selectedFiles1 = [];
        selectedMatFiles = [];
        for i = 1:length(selectedFiles0)
            [cameraID0, tshort0, imageNum0, ~] = parse_filename(selectedFiles0(i).name);
            cam0Filename = selectedFiles0(i).name;
            % Find the corresponding cam1 file using the helper function
            correspondingFile = find_corresponding_file(cameraID0, tshort0, imageNum0, cam0Files, cam1Files);
            selectedFiles1(i).name = correspondingFile.name;
            if loadMats
                matIndex = find(contains({matFiles.name}, tshort0) & contains({matFiles.name}, imageNum0));
                if ~isempty(matIndex)
                    % Add the corresponding .mat file to the selected list
                    selectedMatFiles = [selectedMatFiles, matFiles(matIndex)];
                end
            end
        end
        if loadMats
            matFilenames = {selectedMatFiles.name};
        else
            matFilenames = [];
            disp('No mats/ to analyze.');
        end
    else
        % Selected files are from cam1, find corresponding files in cam0
        selectedFiles1 = selectedFiles;  % cam1 selected
        selectedFiles0 = [];
        selectedMatFiles = [];
        for i = 1:length(selectedFiles1)
            [cameraID1, tshort1, imageNum1, ~] = parse_filename(selectedFiles1(i).name);
            cam1Filename = selectedFiles1(i).name;
            % Find the corresponding cam0 file using the helper function
            correspondingFile = find_corresponding_file(cameraID1, tshort1, imageNum1, cam0Files, cam1Files);
            selectedFiles0(i).name = correspondingFile.name;
            if loadMats
                matIndex = find(contains({matFiles.name}, tshort1) & contains({matFiles.name}, imageNum1));
                if ~isempty(matIndex)
                    % Add the corresponding .mat file to the selected list
                    selectedMatFiles = [selectedMatFiles, matFiles(matIndex)];
                end
            end
        end
        if loadMats
            matFilenames = {selectedMatFiles.name};
        else
            matFilenames = [];
            disp('No mats/ to analyze.');
        end
    end
else
    % Select all images automatically
    cam0Images = dir(fullfile(cam0Dir, '*.jpg'));
    cam1Images = dir(fullfile(cam1Dir, '*.jpg'));
    % Convert filenames into struct arrays same as select_files output
    selectedFiles0 = struct('name', {cam0Images.name});
    selectedFiles1 = struct('name', {cam1Images.name});
    % Select all mats automatically
    if loadMats
        matFiles = dir(fullfile(matDir, '*.mat'));
        matFilenames = {matFiles.name};
    else
        matFilenames = [];
        disp('No mats/ to analyze.');
    end
end

%% Parse filenames to extract timestamps
tstamps0 = datetime.empty;
tstamps1 = datetime.empty;

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

timeDiffs = zeros(1, length(tstamps0));  
for i = 1:length(tstamps0)
    % Calculate the difference in time for each image pair (in seconds)
    timeDiffInSeconds = seconds(tstamps0(i) - tstamps1(i));
    % Convert the time difference to microseconds (1 second = 1e6 microseconds)
    timeDiffs(i) = timeDiffInSeconds * 1e6;
end

%% Plot timestamps
f1 = figure; hold on; grid on; box on; 
plot(1:length(timeDiffs), timeDiffs, 'o-');
yline(0, '--k', 'LineWidth',2);
maxValue = max(abs(timeDiffs));  % Find the max absolute value
ylim([-maxValue, maxValue]);     % Set y-limits symmetrically
xlabel('Image Pair (Index)');
ylabel('Time Difference (Microseconds)');
title('Time Difference Between cam0 and cam1 (Microseconds)');
exportgraphics(f1, fullfile(figDir, 'TimeDifferencePlot.png'), 'Resolution', res);
close(gcf);  % Close the figure after saving

%% Plot X-Y cross sections
shapesDir = fullfile(figDir, 'shapes');
if ~exist(shapesDir, 'dir') && loadMats
    mkdir(shapesDir);  % Create shapes/ directory if it doesn't exist
end

for k = 1:length(matFilenames)
    matData = load(fullfile(matDir, matFilenames{k}));
    if isfield(matData, 'points3D') && (isfield(matData, 'clean') && matData.clean == true)
        points3D = matData.points3D;
        
        % Get the x-values, y-values (flip y-values), and z-values (depth)
        xValues = points3D(:,1);
        yValues = -points3D(:,2);  % Flip the Y values by multiplying by -1
        zValues = points3D(:,3);
        
        % Get the minimum and maximum Z, X, Y values
        minX = min(xValues);
        maxX = max(xValues);
        minY = min(yValues);
        maxY = max(yValues);
        minZ = min(zValues);
        maxZ = max(zValues);
        
        figure; hold on; axis equal; grid on;
        blueToRed = [linspace(0, 1, 256)', zeros(256, 1), linspace(1, 0, 256)'];
        colormap(blueToRed);
        
        for z = minZ:dZ:maxZ
            % Find points within the current z bin
            zIndices = find(zValues >= z & zValues < z + dZ);
            % For each X bin within the Z slice
            X = []; Y = [];
            for x = minX:dX:maxX
                % Find points within the current x bin
                xIndices = find(xValues(zIndices) >= x & xValues(zIndices) < x + dX);
       
                % Extract the corresponding Y points within the X bin
                yInBin = yValues(zIndices(xIndices));
                
                % Find the Y location corresponding to this X bin and average
                if ~isempty(yInBin)
                    avgY = nanmean(yInBin);  % Average Y points in the bin
                else
                    avgY = NaN;  % Handle case where no points exist in the bin
                end
                
                % Plot the cross section for this Z value
                colorValue = (z - minZ) / (maxZ - minZ);  % Normalize color based on Z depth
                color = [colorValue, 0, 1 - colorValue];  % Blue-red gradient
                
                % Add to the X-Y cross section
                if ~isnan(avgY)
                    X = [X x];
                    Y = [Y avgY];
                end
            end

            %%%%%%%%%%%%%%%% Plot X-Y %%%%%%%%%%%%%%%%%%
%             plot(X, Y, 'Color', color, 'LineWidth', 1.5);
            plot(X, Y, 'o', 'Color', color, 'MarkerFaceColor', color,'MarkerSize', 5);
%             plot(X, Y, '-o', 'Color', color, 'MarkerFaceColor', color, 'LineWidth', 1.5);
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        end
     
        title(sprintf('Cross Sections for %s', matFiles(k).name), 'Interpreter', 'none');
        xlabel('X (m)');
        ylabel('Y (m)');
        yline(minY, '--k', 'LineWidth',2); % lowest water level (trough)
        c = colorbar;
        c.Label.String = 'Z (m)';
        caxis([minZ maxZ]);  % Set the colorbar limits to match the Z range
        
        % Save the figure in the shapes/ directory
        exportgraphics(gcf, fullfile(shapesDir, sprintf('CrossSection_Plot_%s.png', matFiles(k).name(1:end-4))), 'Resolution', res);
        close(gcf); 
    else
        disp(['points3D not found in ', matFiles(k).name, ' or ', matFiles(k).name, ' not yet cleaned.']);
    end
end








