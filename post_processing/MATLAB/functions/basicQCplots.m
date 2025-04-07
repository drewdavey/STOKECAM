% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2025-04-07

% Function to generate basic QC plots of Vecnav data
function basicQCplots(imu, figDir, res)    

    % If resolution is not passed in or is empty, set default:
    if nargin < 3 || isempty(res)
        res = 600;  % default resolution
    end

    % Relative time
    t = imu.t0;

    %% Plot Cam delay
    % This is camd elay between cam0 and cam1, with hardware trigger, this
    % is now zero. Keep here for QC if not using hardware trigger.
    f1 = figure; hold on; grid on; box on; 
    plot(t, imu.camDiffs * 1e6, 'o-', 'LineWidth', 1.5);
    yline(0, '--k', 'LineWidth',2);
    xlabel('Time (sec)');
    ylabel('Time Difference (\mus)');
    title('Image Delay');
    print(f1, fullfile(figDir, 'TimeDifferencePlot.png'), '-dpng', ['-r', num2str(res)]);
    
    %% Plot YPR
    % Attitude solution as yaw, pitch, and roll in degrees. 
    % The yaw, pitch, and roll is given as a 3,2,1 Euler angle rotation 
    % sequence describing the orientation of the sensor with respect to the 
    % inertial North East Down (NED) frame.
    yaw = imu.yaw;
    pitch = imu.pitch;
    roll = imu.roll;
    f2 = figure;
    subplot(3,1,1); hold on; grid on; box on; axis tight;
    plot(t, yaw, 'k', 'LineWidth', 1);
    ylabel('Yaw (deg)');
    subplot(3,1,2); hold on; grid on; box on; axis tight;
    plot(t, pitch, 'k', 'LineWidth', 1);
    ylabel('Pitch (deg)');
    subplot(3,1,3); hold on; grid on; box on; axis tight;
    plot(t, roll, 'k', 'LineWidth', 1);
    ylabel('Roll (deg)');
    xlabel('Time (sec)');
    % sgtitle('YPR');
    print(f2, fullfile(figDir, 'ypr.png'), '-dpng', ['-r', num2str(res)]);

    %% Plot gyro
    % The IMU angular rate given in the body-frame. 
    % This measurement is compensated by the static calibration (individual factory calibration stored in flash), 
    % however it is not compensated by any bias compensation from the onboard Kalman filter.
    gyroX = imu.uncompGyroX;
    gyroY = imu.uncompGyroY;
    gyroZ = imu.uncompGyroZ;
    f3 = figure;
    subplot(3,1,1); hold on; grid on; box on; axis tight;
    plot(t, gyroX, 'k', 'LineWidth', 1);
    ylabel('GyroX (deg/s)');
    subplot(3,1,2); hold on; grid on; box on; axis tight;
    plot(t, gyroY, 'k', 'LineWidth', 1);
    ylabel('GyroY (deg/s)');
    subplot(3,1,3); hold on; grid on; box on; axis tight;
    plot(t, gyroZ, 'k', 'LineWidth', 1);
    ylabel('GyroZ (deg/s)');
    xlabel('Time (sec)');
    % sgtitle('Uncompensated Gyro');
    print(f3, fullfile(figDir, 'gyro.png'), '-dpng', ['-r', num2str(res)]);

    %% Plot temp / press
    % Why not
    f4 = figure; hold on; grid on; box on; 
    plot(t, imu.temperature, 'k');
    xlabel('Time (sec)');
    ylabel('Temperature (deg C)');
    % title('');
    print(f4, fullfile(figDir, 'temperature.png'), '-dpng', ['-r', num2str(res)]);
    f5 = figure; hold on; grid on; box on; 
    plot(t, imu.pressure, 'k');
    xlabel('Time (sec)');
    ylabel('Pressure (kPa)');
    % title('');
    print(f5, fullfile(figDir, 'pressure.png'), '-dpng', ['-r', num2str(res)]);

    %% Plot magnetometer
    % The IMU compensated magnetic field given in the body-frame. 
    % This measurement is compensated by the static calibration 
    % (individual factory calibration stored in flash), the user compensation, 
    % and the dynamic calibration from the onboard Hard/Soft Iron estimator.
    magX = imu.magX;
    magY = imu.magY;
    magZ = imu.magZ;
    f6 = figure;
    subplot(3,1,1); hold on; grid on; box on; axis tight;
    plot(t, magX, 'k', 'LineWidth', 1);
    ylabel('MagX (deg/s)');
    subplot(3,1,2); hold on; grid on; box on; axis tight;
    plot(t, magY, 'k', 'LineWidth', 1);
    ylabel('MagY (deg/s)');
    subplot(3,1,3); hold on; grid on; box on; axis tight;
    plot(t, magZ, 'k', 'LineWidth', 1);
    ylabel('MagZ (deg/s)');
    xlabel('Time (sec)');
    % sgtitle('Mag');
    print(f6, fullfile(figDir, 'mag.png'), '-dpng', ['-r', num2str(res)]);

    %% Plot accelerometer
    % The bias-compensated acceleration measured in the body-frame. 
    % This measurement is compensated by the static calibration 
    % (individual factory calibration stored in flash), the user compensation,
    % and the dynamic bias compensation from the onboard Kalman filter (if applicable).
    accelX = imu.accelX;
    accelY = imu.accelY;
    accelZ = imu.accelZ;
    f7 = figure;
    subplot(3,1,1); hold on; grid on; box on; axis tight;
    plot(t, accelX, 'k', 'LineWidth', 1);
    ylabel('AccelX (m/s^2)');
    subplot(3,1,2); hold on; grid on; box on; axis tight;
    plot(t, accelY, 'k', 'LineWidth', 1);
    ylabel('AccelY (m/s^2)');
    subplot(3,1,3); hold on; grid on; box on; axis tight;
    plot(t, accelZ, 'k', 'LineWidth', 1);
    ylabel('AccelZ (m/s^2)');
    xlabel('Time (sec)');
    % sgtitle('Accel');
    print(f7, fullfile(figDir, 'accel.png'), '-dpng', ['-r', num2str(res)]);

    %% Plot quaternions
    % The estimated attitude describing the body frame with respect to the 
    % local North-East-Down (NED) frame given as the quaternion.
    quatX = imu.quatX;
    quatY = imu.quatY;
    quatZ = imu.quatZ;
    f8 = figure;
    subplot(3,1,1); hold on; grid on; box on; axis tight;
    plot(t, quatX, 'k', 'LineWidth', 1);
    ylabel('QuatX');
    subplot(3,1,2); hold on; grid on; box on; axis tight;
    plot(t, quatY, 'k', 'LineWidth', 1);
    ylabel('QuatY');
    subplot(3,1,3); hold on; grid on; box on; axis tight;
    plot(t, quatZ, 'k', 'LineWidth', 1);
    ylabel('QuatZ');
    xlabel('Time (sec)');
    % sgtitle('Accel');
    print(f8, fullfile(figDir, 'quaternion.png'), '-dpng', ['-r', num2str(res)]);

    %% Plot GNSS position and uncertainty
    % The current GNSS position measurement given as the geodetic latitude, 
    % longitude and altitude above the ellipsoid. The current GNSS position 
    % uncertainty in the North East Down (NED) reference frame.
    lat = imu.gnss1PosLat;
    lon = imu.gnss1PosLon;
    alt = imu.gnss1PosAlt;
    unc = imu.posU;

    f9 = figure;
    set(gcf,'position',[260 9 691 613]);
    subplot(4,1,1); hold on; grid on; box on; axis tight;
    plot(t, lat, 'k', 'LineWidth', 1);
    ylabel('Latitude (deg)');
    subplot(4,1,2); hold on; grid on; box on; axis tight;
    plot(t, lon, 'k', 'LineWidth', 1);
    ylabel('Longitude (deg)');
    subplot(4,1,3); hold on; grid on; box on; axis tight;
    plot(t, alt, 'k', 'LineWidth', 1);
    ylabel('Altitude (m, WGS84)');
    subplot(4,1,4); hold on; grid on; box on; axis tight;
    plot(t, unc, 'k', 'LineWidth', 1);
    ylabel('Uncertainty (%)');
    xlabel('Time (sec)');
    % sgtitle('Accel');
    print(f9, fullfile(figDir, 'position.png'), '-dpng', ['-r', num2str(res)]);
    
    % Video
    buffer = 0.0001;
    f10 = figure; ax = geoaxes; 
    geobasemap(ax, 'satellite'); hold on;
    geolimits([min(lat)-buffer max(lat)+buffer], [min(lon)-buffer max(lon)+buffer]);
    video = VideoWriter(fullfile(figDir, 'position.mp4'), 'MPEG-4');
    video.FrameRate = 30; 
    open(video);
    h1 = geoplot(NaN, NaN, '-b', 'LineWidth', 1, 'DisplayName', 'Path'); hold on;
    h2 = geoscatter(NaN, NaN, 20, 'r','filled', 'DisplayName', 'VN-200'); 
    legend show;
    for i = 1:length(lat)
        title(['Frame ', num2str(i)]);
        % geoscatter(lat(i), lon(i), 10, 'r','filled'); hold on;
        h1.LatitudeData = lat(1:i);
        h1.LongitudeData = lon(1:i);
        h2.LatitudeData = lat(i);
        h2.LongitudeData = lon(i);
        % pause(0.00001);
        frame = getframe(f10);
        writeVideo(video, frame);
    end
    close(video);

end