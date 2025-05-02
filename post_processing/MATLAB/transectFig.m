
clear; clc; close all;

%% Inputs
% wave = uigetdir('../../../FSR/stereo_cam/DATA','Select path to wave with transect'); 
% tDir = [wave '/transect'];

%% Full transect
wave = 'C:\Users\drew\OneDrive - UC San Diego\FSR\stereo_cam\DATA\20250429\003014_session_auto\wave6_rotated3';
tDir = 'C:\Users\drew\OneDrive - UC San Diego\FSR\stereo_cam\DATA\20250429\003014_session_auto\wave6_rotated3\transect';
tFiles = dir(fullfile(tDir, '*.mat'));
tFilenames = {tFiles.name};
load([wave '/imu.mat']);
t = imu.t0;
f1 = figure(1); hold on; axis equal; grid on;
f2 = figure(2); hold on; axis equal; grid on;
cmap = jet(length(t)); 
for i = 1:length(tFilenames)
    load(fullfile(tDir, tFilenames{i}));
    % 3D scatter colored by elapsed time
    figure(f1);
    scatter3(X, Y, Z, 5, repmat(t(i), size(X)), 'filled');
    % 2D scatter colored by elapsed time
    figure(f2);
    scatter(X, Z, 5, repmat(t(i), size(X)), 'filled');
end
figure(f1);
colormap(icecream);
cb1 = colorbar;
cb1.Label.String = 'Elapsed Time (s)';
xlabel('X_{SIO} (m)'); ylabel('Y_{SIO} (m)'); zlabel('Z_{NAVD88} (m)');
% set(gca, 'XDir', 'reverse');
figure(f2);
colormap(icecream);
cb2 = colorbar;
cb2.Label.String = 'Elapsed Time (s)';
xlabel('X_{SIO} (m)'); ylabel('Z_{NAVD88} (m)');
% set(gca, 'XDir', 'reverse');
axis tight;


% %% Thin slice
% targetY = 5.9;
% dy = 0.01;  % Half-thickness of the Y-slice
% X_slice = [];
% Z_slice = [];
% for i = 1:length(tFilenames)
%     load(fullfile(tDir, tFilenames{i}));
%     % Select points in Y-slice
%     idx = abs(Y - targetY) <= dy;
%     X_slice = [X_slice; X(idx)];
%     Z_slice = [Z_slice; Z(idx)];
% end
% figure; hold on; axis equal; grid on;
% scatter(X_slice, Z_slice, 10, 'b', 'filled');
% xlabel('X_{SIO} (m)');
% ylabel('Z_{NAVD88} (m)');


%% Animated slice

v = VideoWriter([wave '/transect/animated_slice.mp4'], 'MPEG-4');
v.FrameRate = 10; 
open(v); 

targetYs = linspace(10, 5, 50); % Range of Y-slice values
dy = 0.05;                      % Thickness of each slice

f = figure('Position', [100 100 800 700]);
tiledlayout(2,1);

load([wave '/imu.mat']);
t = imu.t0;

X_all = []; Y_all = []; Z_all = []; T_all = [];

for i = 1:length(tFilenames)
    load(fullfile(tDir, tFilenames{i})); % Loads X, Y, Z
    n = numel(X);
    X_all = [X_all; X(:)];
    Y_all = [Y_all; Y(:)];
    Z_all = [Z_all; Z(:)];
    T_all = [T_all; repmat(t(i), n, 1)];
end

for j = 1:length(targetYs)
    targetY = targetYs(j);

    % Select slice points within ±dy
    idx = abs(Y_all - targetY) <= dy;
    X_slice = X_all(idx);
    Z_slice = Z_all(idx);
    % horizontal line
    nexttile(1); cla;
    set(gcf,'position',[318 93 560 420]);
    scatter3(X_all, Y_all, Z_all, 4, T_all, 'filled');
    colormap(icecream);            
    clim([min(t), max(t)]);   
    cb = colorbar;                     % Create the colorbar
    cb.Label.String = 'Elapsed Time (s)';  % Set the label

    hold on;
    yline(targetY - dy, 'k--','LineWidth',1);
    yline(targetY + dy, 'k--','LineWidth',1);
    % view(0, 90); 
    xlabel('X_{SIO} (m)'); ylabel('Y_{SIO} (m)'); zlabel('Z_{NAVD88} (m)');
    % title(sprintf('Aerial view: Slice at Y = %.3f ± %.3f', targetY, dy));
    axis equal; grid on; caxis([min(t) max(t)]);
    set(gca, 'XDir', 'reverse');
    set(gca, 'YDir', 'reverse');

    % XZ slice
    nexttile(2); cla;
    scatter(X_slice, Z_slice, 2, 'k', 'filled');
    xlabel('X_{SIO} (m)'); ylabel('Z_{NAVD88} (m)');
    title(sprintf('XZ Slice at Y = %.3f ± %.3f', targetY, dy));
    axis equal; grid on;
    xlim([min(X_all), max(X_all)]);
    ylim([min(Z_all), max(Z_all)]);
    set(gca, 'XDir', 'reverse');

    drawnow;
    frame = getframe(gcf); 
    writeVideo(v, frame); 
end

close(v);





%% Fit curves
% tFiles = dir(fullfile(tDir, '*.mat'));
% tFilenames = {tFiles.name};
% load([wave '/imu.mat']);
% t = imu.t0;
% f2 = figure(2); hold on; axis equal; grid on;
% colormap(icecream);
% cmap = colormap;
% clim([min(t) max(t)]);
% 
% for i = 1:length(tFilenames)
% 
%     load(fullfile(tDir, tFilenames{i}), 'X', 'Z');
% 
%     % Plot original data points
%     scatter(X, Z, 5, repmat(t(i), size(X)), 'filled');
% 
%     % Fit a line to each transect 
%     p = polyfit(X, Z, 9); % cubic fit
% 
%     % Create fitted line for plotting
%     Xfit = linspace(min(X), max(X), 100);
%     Zfit = polyval(p, Xfit);
% 
%     % Choose line color matching scatter points
%     [~, colIdx] = min(abs(linspace(min(t),max(t),size(cmap,1))-t(i)));
%     lineColor = cmap(colIdx, :);
% 
%     plot(Xfit, Zfit, '-k', 'LineWidth', 2);
%     % plot(Xfit, Zfit, '-', 'LineWidth', 2, 'Color', lineColor);
% 
% end
% 
% xlabel('X_{SIO} (m)');
% ylabel('Z_{NAVD88} (m)');
% cb = colorbar;
% cb.Label.String = 'Elapsed Time (s)';
% axis tight;


