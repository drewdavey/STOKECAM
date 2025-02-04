%% Load IMU Data
% Specify the CSV file path
filePath = 'FA_3E_0073_0331_0279_0006_0207.csv';
imuData = readtable(filePath);

% Extract quaternions and position data
quats = table2array(imuData(:, {'quatW', 'quatX', 'quatY', 'quatZ'}));
positions = table2array(imuData(:, {'posEcefX', 'posEcefY', 'posEcefZ'}));

% Example point cloud 
pointCloud = [1, 0, 0; 0, 1, 0; 0, 0, 1; -1, 0, 0; 0, -1, 0; 0, 0, -1];

%% Process and Plot
figure;
hold on;
grid on;
axis equal;
xlabel('X (m)'); ylabel('Y (m)'); zlabel('Z (m)');
title('IMU Rotation and Translation of Point Cloud');

for i = 1:size(quats, 1)
    % Extract quaternion
    q = quats(i, :);

    % Convert quaternion to rotation matrix
    R = quat2rotm(q);

    % Apply rotation and translation to the point cloud
    transformedCloud = (R * pointCloud')' + positions(i, :);

    % Plot the transformed point cloud
    scatter3(transformedCloud(:, 1), transformedCloud(:, 2), transformedCloud(:, 3), 'filled');

    % Plot IMU position
    plot3(positions(i, 1), positions(i, 2), positions(i, 3), 'ro', 'MarkerSize', 8);

    pause(0.1); % Pause for visualization
end

hold off;
