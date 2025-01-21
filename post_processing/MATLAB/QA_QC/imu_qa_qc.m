% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-10

clear; clc; close all;

addpath('../functions/');

%% Inputs

g = 9.81; % gravity

res = 300;    % resolution for figures (.pngs)

figDir = './figs';

name = 'stairs';

vn = readtable([name '.csv']);

%% RAW IMU

t = (vn.timeStartup - vn.timeStartup(1)) .* 10^-9;

% ECEF
% xm = vn.posEcefX;
% ym = vn.posEcefY;
% zm = vn.posEcefZ;
xm = vn.posEcefX - vn.posEcefX(1);
ym = vn.posEcefY - vn.posEcefY(1);
zm = vn.posEcefZ - vn.posEcefZ(1);

figure;
subplot(3,1,1)
plot(t, xm); ylabel('x');
subplot(3,1,2)
plot(t, ym); ylabel('y');
subplot(3,1,3)
plot(t, zm); ylabel('z');
sgtitle([name ' xyz ECEF']);
xlabel('Time (sec)');
print(gcf, fullfile(figDir, [name ' xyzECEF.png']), '-dpng', ['-r', num2str(res)]);

vLat = var(vn.lat);

figure;
subplot(3,1,1)
plot(t, vn.lat); ylabel('lat');
subplot(3,1,2)
plot(t, vn.lon); ylabel('lon');
subplot(3,1,3)
plot(t, vn.alt); ylabel('alt');
sgtitle([name ' xyz lla']);
xlabel('Time (sec)');
print(gcf, fullfile(figDir, [name ' xyzlla.png']), '-dpng', ['-r', num2str(res)]);

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
sgtitle([name ' accel']);

print(f2, fullfile(figDir, [name ' accel.png']), '-dpng', ['-r', num2str(res)]);

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
sgtitle([name ' mag']);

print(f3, fullfile(figDir, [name ' mag.png']), '-dpng', ['-r', num2str(res)]);

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
sgtitle([name ' YPR']);

print(f4, fullfile(figDir, [name ' ypr.png']), '-dpng', ['-r', num2str(res)]);

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

%% Plot location

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






