% Quaternion Demo

close all; clear; clc;

% quaternions 
quaternions = [
    1     0     0     0;      % Identity quaternion
    0.707 0     0     0.707;  % 90 deg about Z
    0.707 0     0.707 0;      % 90 deg about Y
];

% rotation matrices
R_mats(:,:,1) = [ 1  0  0; 0  1  0; 0  0  1];  % Identity
R_mats(:,:,2) = [0 -1  0; 1  0  0; 0  0  1];  % 90 deg about Z
R_mats(:,:,3) = [ 0  0  1; 0  1  0; -1 0  0]; % 90 deg about Y

figure;
title('Quaternions and Rotation Matrices');
hold on; grid on; axis equal; view(3);
xlabel('X'); ylabel('Y'); zlabel('Z');
title('Quaternions and Rotation Matrices');

scale = 0.5;  
origin = [0 0 0];

% original axes in black
quiver3(origin(1), origin(2), origin(3), scale, 0, 0, ...
         '-r', 'LineWidth', 2,'DisplayName', 'Original X');
quiver3(origin(1), origin(2), origin(3), 0, scale, 0, ...
         '-g', 'LineWidth', 2, 'DisplayName', 'Original Y');
quiver3(origin(1), origin(2), origin(3), 0, 0, scale, ...
        '-b', 'LineWidth', 2, 'DisplayName', 'Original Z');

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Current rotation matrix

R0 = R_mats(:,:,3);  

R = quat2rotm(quaternions(3,:));

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

translated_origin = origin;
% translated_origin = [1 1 1];

xAxis = R(:,1) * scale;
yAxis = R(:,2) * scale;
zAxis = R(:,3) * scale;

quiver3(translated_origin(1), translated_origin(2), translated_origin(3),...
    xAxis(1), xAxis(2), xAxis(3), '--r', 'LineWidth', 1, 'DisplayName', 'X');
quiver3(translated_origin(1), translated_origin(2), translated_origin(3),...
    yAxis(1), yAxis(2), yAxis(3), '--g', 'LineWidth', 1,'DisplayName', 'Y');
quiver3(translated_origin(1), translated_origin(2), translated_origin(3),...
    zAxis(1), zAxis(2), zAxis(3), '--b', 'LineWidth', 1, 'DisplayName', 'Z');

legend show;

