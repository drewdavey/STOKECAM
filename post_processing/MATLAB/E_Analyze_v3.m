% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-10

clear; clc; close all;

addpath('functions/');

%% Inputs

g = 9.81; % gravity

res = 300;          % resolution for figures (.pngs)

path = uigetdir('../../../FSR/stereo_cam/DATA/','Select path to session for analysis'); % load path to dir 

load([path '/imu.mat']);

%% Organize dirs
cam0Dir = fullfile(path, 'cam0');
cam1Dir = fullfile(path, 'cam1');
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

%% Parse filenames to extract timestamps
for i = 1:length(selectedFiles0) 
    [cameraID0, tshort0, imageNum0, tlong0] = parse_filename(selectedFiles0(i).name);
    hours0 = tlong0(1:2); minutes0 = tlong0(3:4); seconds0 = tlong0(5:6); microseconds0 = tlong0(7:end);
    fullTimestamp0 = [hours0, ':', minutes0, ':', seconds0, '.', microseconds0];
    tstamps0(i) = datetime(fullTimestamp0, 'InputFormat', 'HH:mm:ss.SSSSSS', 'Format', 'HH:mm:ss.SSSSSS');
end
for i = 1:length(selectedFiles1)
    [cameraID1, tshort1, imageNum1, tlong1] = parse_filename(selectedFiles1(i).name);
    hours1 = tlong1(1:2); minutes1 = tlong1(3:4); seconds1 = tlong1(5:6); microseconds1 = tlong1(7:end); 
    fullTimestamp1 = [hours1, ':', minutes1, ':', seconds1, '.', microseconds1];
    tstamps1(i) = datetime(fullTimestamp1, 'InputFormat', 'HH:mm:ss.SSSSSS', 'Format', 'HH:mm:ss.SSSSSS');
end
timeDiffs = zeros(1, length(tstamps0));  
for i = 1:length(tstamps0)
    % Calculate the difference in time for each image pair (in seconds)
    timeDiffInSeconds = seconds(tstamps1(i) - tstamps0(i));
    % Convert the time difference to microseconds (1 second = 1e6 microseconds)
    timeDiffs(i) = timeDiffInSeconds * 1e6;
end

%% Plot timestamps
f1 = figure; hold on; grid on; box on; 
plot(1:length(timeDiffs), timeDiffs, 'o-', 'LineWidth', 1.5);
yline(0, '--k', 'LineWidth',2);
maxValue = max(abs(timeDiffs));  % Find the max absolute value
% ylim([-maxValue, maxValue]);     % Set y-limits symmetrically
% ylim([0, maxValue]);     % Set y-limits symmetrically
xlabel('Image Pair (Index)');
ylabel('Time Difference (\mus)');
title('Image Delay');
% exportgraphics(f1, fullfile(figDir, 'TimeDifferencePlot.png'), 'Resolution', res);
print(f1, fullfile(figDir, 'TimeDifferencePlot.png'), '-dpng', ['-r', num2str(res)]);
% close(gcf);  % Close the figure after saving

%% Plot accel
ax = vn.accelX/g;
ay = vn.accelY/g;
az = vn.accelZ/g;

f2 = figure; 
subplot(3,1,1); hold on; grid on; box on; axis tight;
plot(1:length(ax), ax, 'r', 'LineWidth', 1);
ylabel('g'); legend('x');
subplot(3,1,2); hold on; grid on; box on; axis tight;
plot(1:length(ay), ay, 'g', 'LineWidth', 1);
ylabel('g'); legend('y');
subplot(3,1,3); hold on; grid on; box on; axis tight;
plot(1:length(az), az, 'b', 'LineWidth', 1);
ylabel('g'); legend('z');
xlabel('idx'); 
sgtitle('XYZ accel');

print(f2, fullfile(figDir, 'accel.png'), '-dpng', ['-r', num2str(res)]);

%% Position
xm = vn.posEcefX - vn.posEcefX(1);
ym = vn.posEcefY - vn.posEcefY(1);
zm = vn.posEcefZ - vn.posEcefZ(1);

%% Plot rotations
video = VideoWriter(fullfile(figDir, '3D_Orientation.mp4'), 'MPEG-4'); 
video.FrameRate = 30; 
open(video); 
numFrames = numel(vn.quatX);
rotationMatrices = zeros(3, 3, numFrames);
for i = 1:numFrames
    qx = vn.quatX(i);
    qy = vn.quatY(i);
    qz = vn.quatZ(i);
    qw = vn.quatW(i);
    % Compute rotation matrix from quaternion
    rotationMatrices(:, :, i) = quat2rotm([qw, qx, qy, qz]);
end

figure('Color', 'w');
% axisLimits = [-1, 1, -1, 1, -1, 1]; % Set axis limits
axisLimits = [min(xm)-1, max(xm)+1, min(ym)-1, max(ym)+1, min(zm)-1, max(zm)+1]; % Set axis limits
xlabel('X'); ylabel('Y'); zlabel('Z');
grid on;
hold on;
for i = 1:numFrames
    cla;
    R = rotationMatrices(:, :, i);
    origin = [0, 0, 0];
    xAxis = R * [1; 0; 0]; 
    yAxis = R * [0; 1; 0]; 
    zAxis = R * [0; 0; 1]; 

    % quiver3(origin(1), origin(2), origin(3), xAxis(1), xAxis(2), xAxis(3), 'r', 'LineWidth', 2);
    % quiver3(origin(1), origin(2), origin(3), yAxis(1), yAxis(2), yAxis(3), 'g', 'LineWidth', 2);
    % quiver3(origin(1), origin(2), origin(3), zAxis(1), zAxis(2), zAxis(3), 'b', 'LineWidth', 2);

    quiver3(xm(i), ym(i), zm(i), xAxis(1), xAxis(2), xAxis(3), 'r', 'LineWidth', 2);
    quiver3(xm(i), ym(i), zm(i), yAxis(1), yAxis(2), yAxis(3), 'g', 'LineWidth', 2);
    quiver3(xm(i), ym(i), zm(i), zAxis(1), zAxis(2), zAxis(3), 'b', 'LineWidth', 2);

    axis equal;
    axis(axisLimits);
    title(['Frame ', num2str(i)]);
    drawnow;
    pause(0.1);
    frame = getframe(gcf);
    writeVideo(video, frame);
end
close(video);

%% Plot location

lat = vn.gnss1PosLat;
lon = vn.gnss1PosLon;
alt = vn.gnss1PosAlt;

buffer = 0.0001;
figure; ax = geoaxes; 
geobasemap(ax, 'satellite'); hold on;
geolimits([min(lat)-buffer max(lat)+buffer], [min(lon)-buffer max(lon)+buffer]);
video = VideoWriter(fullfile(figDir, 'gps.mp4'), 'MPEG-4');
video.FrameRate = 30; 
open(video);
h1 = geoplot(NaN, NaN, '-b', 'LineWidth', 1, 'DisplayName', 'Path'); hold on;
h2 = geoscatter(NaN, NaN, 20, 'r','filled', 'DisplayName', 'VN-200'); 
legend show;
for i = 1:length(lat)
    % title(string(vn.timeGps(i)));
    title(['Frame ', num2str(i)]);
    % geoscatter(lat(i), lon(i), 10, 'r','filled'); hold on;
    h1.LatitudeData = lat(1:i);
    h1.LongitudeData = lon(1:i);
    h2.LatitudeData = lat(i);
    h2.LongitudeData = lon(i);
    pause(0.1);
    frame = getframe(gcf);
    writeVideo(video, frame);
end
close(video);































% %% Plot X-Y cross sections
% shapesDir = fullfile(figDir, 'shapes');
% if ~exist(shapesDir, 'dir') && loadMats
%     mkdir(shapesDir);  % Create shapes/ directory if it doesn't exist
% end
% 
% for k = 1:length(matFilenames)
%     matData = load(fullfile(matDir, matFilenames{k}));
%     matData = matData.data;
%     if isfield(matData, 'points3D') && (isfield(matData, 'clean') && matData.clean == true)
%         points3D = matData.points3D;
% 
%         % Get the x-values, y-values (flip y-values), and z-values (depth)
%         xValues = points3D(:,1);
%         yValues = -points3D(:,2);  % Flip the Y values by multiplying by -1
%         zValues = points3D(:,3);
% 
%         % Get the minimum and maximum Z, X, Y values
%         minX = min(xValues);
%         maxX = max(xValues);
%         minY = min(yValues);
%         maxY = max(yValues);
%         minZ = min(zValues);
%         maxZ = max(zValues);
% 
%         figure; hold on; axis equal; grid on;
%         blueToRed = [linspace(0, 1, 256)', zeros(256, 1), linspace(1, 0, 256)'];
%         colormap(blueToRed);
% 
%         for z = minZ:dZ:maxZ
%             % Find points within the current z bin
%             zIndices = find(zValues >= z & zValues < z + dZ);
%             % For each X bin within the Z slice
%             X = []; Y = [];
%             for x = minX:dX:maxX
%                 % Find points within the current x bin
%                 xIndices = find(xValues(zIndices) >= x & xValues(zIndices) < x + dX);
% 
%                 % Extract the corresponding Y points within the X bin
%                 yInBin = yValues(zIndices(xIndices));
% 
%                 % Find the Y location corresponding to this X bin and average
%                 if ~isempty(yInBin)
%                     avgY = nanmean(yInBin);  % Average Y points in the bin
%                 else
%                     avgY = NaN;  % Handle case where no points exist in the bin
%                 end
% 
%                 % Plot the cross section for this Z value
%                 colorValue = (z - minZ) / (maxZ - minZ);  % Normalize color based on Z depth
%                 color = [colorValue, 0, 1 - colorValue];  % Blue-red gradient
% 
%                 % Add to the X-Y cross section
%                 if ~isnan(avgY)
%                     X = [X x];
%                     Y = [Y avgY];
%                 end
%             end
% 
%             %%%%%%%%%%%%%%%% Plot X-Y %%%%%%%%%%%%%%%%%%
%             % plot(X, Y, 'Color', color, 'LineWidth', 1.5);
%             plot(X, Y, 'o', 'Color', color, 'MarkerFaceColor', color,'MarkerSize', 5);
%             % plot(X, Y, '-o', 'Color', color, 'MarkerFaceColor', color, 'LineWidth', 1.5);
%             %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%         end
% 
%         title(sprintf('Cross Sections for %s', matFiles(k).name), 'Interpreter', 'none');
%         xlabel('X (m)');
%         ylabel('Y (m)');
%         yline(minY, '--k', 'LineWidth',2); % lowest water level (trough)
%         c = colorbar;
%         c.Label.String = 'Z (m)';
%         clim([minZ maxZ]);  % Set the colorbar limits to match the Z range
% 
%         % Save the figure in the shapes/ directory
%         % exportgraphics(gcf, fullfile(shapesDir, sprintf('CrossSection_Plot_%s.png', matFiles(k).name(1:end-4))),...
%         %     'Resolution', res);
%         print(gcf, fullfile(shapesDir, sprintf('CrossSection_Plot_%s.png', matFiles(k).name(1:end-4))),...
%             '-dpng', ['-r', num2str(res)]);
%         close(gcf); 
%     else
%         disp(['points3D not found in ', matFiles(k).name, ' or ', matFiles(k).name, ' not yet cleaned.']);
%     end
% end