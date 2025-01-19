% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-10

clear; clc; close all;

addpath('functions/');

%% Inputs

g = 9.81; % gravity

res = 300;    % resolution for figures (.pngs)

dX = 0.1;     % X step size for plotting (meters)
dY = 0.1;     % Y step size for plotting (meters)
dZ = 0.1;     % Z step size for plotting (meters)

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
% Initialize arrays to store timestamps in nanoseconds
tstamps0 = zeros(1, length(selectedFiles0));
tstamps1 = zeros(1, length(selectedFiles1));

% Parse filenames to extract timestamps in nanoseconds
for i = 1:length(selectedFiles0)
    [~, tstamp0, ~] = parse_filename(selectedFiles0(i).name);  % Get timestamp in nanoseconds as a string
    tstamps0(i) = str2double(tstamp0);  % Convert to numeric nanoseconds
end

for i = 1:length(selectedFiles1)
    [~, tstamp1, ~] = parse_filename(selectedFiles1(i).name);  % Get timestamp in nanoseconds as a string
    tstamps1(i) = str2double(tstamp1);  % Convert to numeric nanoseconds
end

% Calculate the difference in time between image pairs in nanoseconds
timeDiffs = zeros(1, length(tstamps0));

t = zeros(1, length(tstamps0)); % Create avg tstamps for plotting

for i = 1:length(tstamps0)
    t(i) = ((tstamps0(i) + tstamps1(i)) / 2) * 10^-9; % Average tstamp in sec
    timeDiffNs = tstamps1(i) - tstamps0(i);  % Difference in nanoseconds
    timeDiffs(i) = timeDiffNs * 10^-3;  % Difference in microseconds
end

t = t - t(1); % make time relative

%% Plot timestamps
f1 = figure; hold on; grid on; box on; 
plot(t, timeDiffs, 'o-', 'LineWidth', 1.5);
yline(0, '--k', 'LineWidth',2);
maxValue = max(abs(timeDiffs));  % Find the max absolute value
% ylim([-maxValue, maxValue]);     % Set y-limits symmetrically
% ylim([0, maxValue]);     % Set y-limits symmetrically
xlabel('Time (sec)');
ylabel('Time Difference (\mus)');
title('Image Delay');
% exportgraphics(f1, fullfile(figDir, 'TimeDifferencePlot.png'), 'Resolution', res);
print(f1, fullfile(figDir, 'TimeDifferencePlot.png'), '-dpng', ['-r', num2str(res)]);
% close(gcf);  % Close the figure after saving

%% Plot accel
ax = vn.accelX/g;
ay = vn.accelY/g;
az = vn.accelZ/g;
at = sqrt(ax.^2 + ay.^2 + az.^2);

f2 = figure; 
subplot(4,1,1); hold on; grid on; box on; axis tight;
plot(t, ax, 'r', 'LineWidth', 1);
ylabel('g'); legend('x');
subplot(4,1,2); hold on; grid on; box on; axis tight;
plot(t, ay, 'g', 'LineWidth', 1);
ylabel('g'); legend('y');
subplot(4,1,3); hold on; grid on; box on; axis tight;
plot(t, az, 'b', 'LineWidth', 1);
ylabel('g'); legend('z');
subplot(4,1,4); hold on; grid on; box on; axis tight;
plot(t, at, 'm', 'LineWidth', 1);
ylabel('g'); legend('total');
xlabel('Time (sec)'); 
sgtitle('XYZ accel');

print(f2, fullfile(figDir, 'accel.png'), '-dpng', ['-r', num2str(res)]);

%% Plot mag
mx = vn.magX;
my = vn.magY;
mz = vn.magZ;

f3 = figure; 
subplot(3,1,1); hold on; grid on; box on; axis tight;
plot(t, mx, 'r', 'LineWidth', 1);
ylabel('mag'); legend('x');
subplot(3,1,2); hold on; grid on; box on; axis tight;
plot(t, my, 'g', 'LineWidth', 1);
ylabel('mag'); legend('y');
subplot(3,1,3); hold on; grid on; box on; axis tight;
plot(t, mz, 'b', 'LineWidth', 1);
ylabel('mag'); legend('z');
xlabel('Time (sec)'); 
sgtitle('XYZ mag');

print(f3, fullfile(figDir, 'mag.png'), '-dpng', ['-r', num2str(res)]);

%% Plot YPR
yaw = vn.yaw;
pitch = vn.pitch;
roll = vn.roll;

f4 = figure;
subplot(3,1,1); hold on; grid on; box on; axis tight;
plot(t, yaw, 'r', 'LineWidth', 1);
ylabel('yaw');
subplot(3,1,2); hold on; grid on; box on; axis tight;
plot(t, pitch, 'g', 'LineWidth', 1);
ylabel('pitch');
subplot(3,1,3); hold on; grid on; box on; axis tight;
plot(t, roll, 'b', 'LineWidth', 1);
ylabel('roll');
xlabel('Time (sec)');
sgtitle('YPR');

print(f4, fullfile(figDir, 'ypr.png'), '-dpng', ['-r', num2str(res)]);

%% Position

% % UTM
% xm = vn.posEcefX;
% ym = vn.posEcefY;
% zm = vn.posEcefZ;

% UTM (local)
xm = vn.posEcefX - vn.posEcefX(1);
ym = vn.posEcefY - vn.posEcefY(1);
zm = vn.posEcefZ - vn.posEcefZ(1);

%% Compute rotation matrix from quaternion
numFrames = numel(vn.quatX);
rotationMatrices = zeros(3, 3, numFrames);
for i = 1:numFrames
    qx = vn.quatX(i);
    qy = vn.quatY(i);
    qz = vn.quatZ(i);
    qw = vn.quatW(i);
    
    rotationMatrices(:, :, i) = quat2rotm([qw, qx, qy, qz]);
end

% %% Plot location
% 
% lat = vn.gnss1PosLat;
% lon = vn.gnss1PosLon;
% alt = vn.gnss1PosAlt;
% 
% buffer = 0.0001;
% figure; ax = geoaxes; 
% geobasemap(ax, 'satellite'); hold on;
% geolimits([min(lat)-buffer max(lat)+buffer], [min(lon)-buffer max(lon)+buffer]);
% video = VideoWriter(fullfile(figDir, 'gps.mp4'), 'MPEG-4');
% video.FrameRate = 30; 
% open(video);
% h1 = geoplot(NaN, NaN, '-b', 'LineWidth', 1, 'DisplayName', 'Path'); hold on;
% h2 = geoscatter(NaN, NaN, 20, 'r','filled', 'DisplayName', 'VN-200'); 
% legend show;
% for i = 1:length(lat)
%     % title(string(vn.timeGps(i)));
%     title(['Frame ', num2str(i)]);
%     % geoscatter(lat(i), lon(i), 10, 'r','filled'); hold on;
%     h1.LatitudeData = lat(1:i);
%     h1.LongitudeData = lon(1:i);
%     h2.LatitudeData = lat(i);
%     h2.LongitudeData = lon(i);
%     pause(0.1);
%     frame = getframe(gcf);
%     writeVideo(video, frame);
% end
% close(video);

%% Plot rotations/translations

% Create points

depth = 2;

pointColors = {'r', 'g', 'b', 'm'}; % Corner colors 

points = [depth, depth, depth, depth;  % X-coordinates 
          0.5, -0.5, -0.5,  0.5;       % Y-coordinates
          0.5,  0.5, -0.5, -0.5];      % Z-coordinates

% Plot
video = VideoWriter(fullfile(figDir, '3D_Orientation_with_Plane.mp4'), 'MPEG-4');
video.FrameRate = 10;
open(video);

figure;
xlabel('X'); ylabel('Y'); zlabel('Z');
grid on;
hold on;

% Set axis limits
range = depth*1.5;
% axisLimits = [-1, 1, -1, 1, -1, 1];
axisLimits = [min(xm)-range, max(xm)+range, min(ym)-range, max(ym)+range, min(zm)-range, max(zm)+range];

for i = 1:numFrames
    cla;
    R = rotationMatrices(:, :, i);

    % Rotate the points
    rotated = R * points;
    
    % Translate the points 
    translated = rotated + [xm(i); ym(i); zm(i)];
    
    % Plot the camera axes 
    xAxis = R * [1; 0; 0];
    yAxis = R * [0; 1; 0];
    zAxis = R * [0; 0; 1];
    
    quiver3(xm(i), ym(i), zm(i), xAxis(1), xAxis(2), xAxis(3), 'r', 'LineWidth', 2);
    quiver3(xm(i), ym(i), zm(i), yAxis(1), yAxis(2), yAxis(3), 'g', 'LineWidth', 2);
    quiver3(xm(i), ym(i), zm(i), zAxis(1), zAxis(2), zAxis(3), 'b', 'LineWidth', 2);
    
    % origin = [0, 0, 0];
    % quiver3(origin(1), origin(2), origin(3), xAxis(1), xAxis(2), xAxis(3), 'r', 'LineWidth', 2);
    % quiver3(origin(1), origin(2), origin(3), yAxis(1), yAxis(2), yAxis(3), 'g', 'LineWidth', 2);
    % quiver3(origin(1), origin(2), origin(3), zAxis(1), zAxis(2), zAxis(3), 'b', 'LineWidth', 2);
    
    % Shade the plane
    fill3(translated(1, :), translated(2, :), translated(3, :), ...
          'k', 'FaceAlpha', 0.5, 'EdgeColor', 'none');

    for j = 1:4
        scatter3(translated(1, j), translated(2, j), translated(3, j), ...
                 10, pointColors{j}, 'filled');
    end
    
    axis equal;
    axis(axisLimits);
    title(['Frame ', num2str(i)]);
    drawnow;
    % pause(0.01);

    % Write frame to video
    frame = getframe(gcf);
    writeVideo(video, frame);
end

close(video);

% %% Plot points3D rectified
% 
% video = VideoWriter(fullfile(figDir, '3D_Orientation_points3D.mp4'), 'MPEG-4');
% video.FrameRate = 10;
% open(video);
% 
% figure;
% xlabel('X'); ylabel('Y'); zlabel('Z');
% grid on;
% hold on;
% 
% % Set axis limits
% range = depth*1.5;
% % axisLimits = [-1, 1, -1, 1, -1, 1];
% axisLimits = [min(xm)-range, max(xm)+range, min(ym)-range, max(ym)+range, min(zm)-range, max(zm)+range];
% 
% for i = 1:numFrames
%     R = rotationMatrices(:, :, i);
% 
%     % Load points3D
%     load(fullfile(matDir,matFiles(i).name));
%     points = data.points3D';
% 
%     % Rotate the points
%     rotated = R * points;
% 
%     % Translate the points 
%     translated = rotated + [xm(i); ym(i); zm(i)];
% 
%     % Plot the camera axes 
%     xAxis = R * [1; 0; 0];
%     yAxis = R * [0; 1; 0];
%     zAxis = R * [0; 0; 1];
% 
%     % quiver3(xm(i), ym(i), zm(i), xAxis(1), xAxis(2), xAxis(3), 'r', 'LineWidth', 2);
%     % quiver3(xm(i), ym(i), zm(i), yAxis(1), yAxis(2), yAxis(3), 'g', 'LineWidth', 2);
%     % quiver3(xm(i), ym(i), zm(i), zAxis(1), zAxis(2), zAxis(3), 'b', 'LineWidth', 2);
% 
%     for j = 1:1000:length(points)
%         scatter3(translated(1, j), translated(2, j), translated(3, j), ...
%                  10, pointColors{i}, 'filled'); hold on;
%     end
% 
%     axis equal;
%     axis(axisLimits);
%     title(['Frame ', num2str(i)]);
%     drawnow;
%     % pause(0.01);
% 
%     % Write frame to video
%     frame = getframe(gcf);
%     writeVideo(video, frame);
% end
% 
% close(video);

%% Plot X-Y cross sections
shapesDir = fullfile(figDir, 'shapes');
if ~exist(shapesDir, 'dir') && loadMats
    mkdir(shapesDir);  % Create shapes/ directory if it doesn't exist
end

for k = 1:length(matFilenames)
    matData = load(fullfile(matDir, matFilenames{k}));
    matData = matData.data;
    if isfield(matData, 'points3D') && (isfield(matData, 'clean') && matData.clean == true)

        R = rotationMatrices(:, :, i);

        points3D = matData.points3D;
        
        % Rotate the points
        points3D = R * points3D';

        % points3D = points3D';

        % Translate the points 
        points3D = points3D' + [xm(i); ym(i); zm(i)]';

        % Get the x-values, y-values (flip y-values), and z-values (depth)
        xValues = points3D(:,1);
        yValues = points3D(:,2);  % Flip the Y values by multiplying by -1
        zValues = points3D(:,3);
        
        % Get the minimum and maximum Z, X, Y values
        minX = min(xValues);
        maxX = max(xValues);
        minY = min(yValues);
        maxY = max(yValues);
        minZ = min(zValues);
        maxZ = max(zValues);

        figure; hold on; axis equal; grid on; axis tight;
        blueToRed = [linspace(0, 1, 256)', zeros(256, 1), linspace(1, 0, 256)'];
        colormap(blueToRed);

        scatter3(points3D(:,1),points3D(:,2),points3D(:,3),'.k')

        title(sprintf('Cross Sections for %s', matFiles(k).name), 'Interpreter', 'none');
        xlabel('X (m)');
        ylabel('Y (m)');
        yline(minY, '--k', 'LineWidth',2); % lowest water level (trough)
        c = colorbar;
        c.Label.String = 'Z (m)';
        clim([minZ maxZ]);  % Set the colorbar limits to match the Z range

        % Save the figure in the shapes/ directory
        % exportgraphics(gcf, fullfile(shapesDir, sprintf('CrossSection_Plot_%s.png', matFiles(k).name(1:end-4))),...
        %     'Resolution', res);
        print(gcf, fullfile(shapesDir, sprintf('CrossSection_Plot_%s.png', matFiles(k).name(1:end-4))),...
            '-dpng', ['-r', num2str(res)]); 
    else
        disp(['points3D not found in ', matFiles(k).name, ' or ', matFiles(k).name, ' not yet cleaned.']);
    end
end