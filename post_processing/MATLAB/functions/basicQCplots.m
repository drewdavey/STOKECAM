% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2025-04-21

% Function to generate basic QC plots of Vecnav data
function basicQCplots(imu, figDir, res)    

    % If resolution is not passed in or is empty, set default:
    if nargin < 3 || isempty(res)
        res = 600;  % default resolution
    end

    % Relative time
    t = imu.t0;

    %% Plot Cam delay
    % This is cam delay between cam0 and cam1, with hardware trigger, this
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
    ylabel('Yaw (deg)'); ylim([-180 180]);
    title([ '\mu: ' num2str(mean(yaw), '%.3f') ', \sigma: ' num2str(std(yaw), '%.3f')]);
    subplot(3,1,2); hold on; grid on; box on; axis tight;
    plot(t, pitch, 'k', 'LineWidth', 1);
    title([ '\mu: ' num2str(mean(pitch), '%.3f') ', \sigma: ' num2str(std(pitch), '%.3f')]);
    ylabel('Pitch (deg)'); ylim([-90 90]);
    subplot(3,1,3); hold on; grid on; box on; axis tight;
    plot(t, roll, 'k', 'LineWidth', 1);
    title([ '\mu: ' num2str(mean(roll), '%.3f') ', \sigma: ' num2str(std(roll), '%.3f')]);
    ylabel('Roll (deg)'); ylim([-90 90]);
    xlabel('Time (sec)');
    % sgtitle('YPR');
    print(f2, fullfile(figDir, 'ypr.png'), '-dpng', ['-r', num2str(res, '%.3f')]);

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
    title([ '\mu: ' num2str(mean(gyroX), '%.3f') ', \sigma: ' num2str(std(gyroX), '%.3f')]);
    ylabel('GyroX (rad/s)'); ylim([-1 1]);
    subplot(3,1,2); hold on; grid on; box on; axis tight;
    plot(t, gyroY, 'k', 'LineWidth', 1);
    title([ '\mu: ' num2str(mean(gyroY), '%.3f') ', \sigma: ' num2str(std(gyroY), '%.3f')]);
    ylabel('GyroY (rad/s)'); ylim([-1 1]);
    subplot(3,1,3); hold on; grid on; box on; axis tight;
    plot(t, gyroZ, 'k', 'LineWidth', 1);
    title([ '\mu: ' num2str(mean(gyroZ), '%.3f') ', \sigma: ' num2str(std(gyroZ), '%.3f')]);
    ylabel('GyroZ (rad/s)'); ylim([-1 1]);
    xlabel('Time (sec)');
    % sgtitle('Uncompensated Gyro');
    print(f3, fullfile(figDir, 'gyro.png'), '-dpng', ['-r', num2str(res, '%.3f')]);

    %% Plot temp / press
    % Why not
    f4 = figure; hold on; grid on; box on; 
    plot(t, imu.temperature, 'k');
    xlabel('Time (sec)');
    ylabel('Temperature (deg C)');
    % title('');
    print(f4, fullfile(figDir, 'temperature.png'), '-dpng', ['-r', num2str(res, '%.3f')]);
    f5 = figure; hold on; grid on; box on; 
    plot(t, imu.pressure, 'k');
    xlabel('Time (sec)');
    ylabel('Pressure (kPa)');
    % title('');
    print(f5, fullfile(figDir, 'pressure.png'), '-dpng', ['-r', num2str(res, '%.3f')]);

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
    title([ '\mu: ' num2str(mean(magX), '%.3f') ', \sigma: ' num2str(std(magX), '%.3f')]);
    ylabel('MagX (G)'); ylim([0 5]);
    subplot(3,1,2); hold on; grid on; box on; axis tight;
    plot(t, magY, 'k', 'LineWidth', 1);
    title([ '\mu: ' num2str(mean(magY), '%.3f') ', \sigma: ' num2str(std(magY), '%.3f')]);
    ylabel('MagY (G)'); ylim([0 5]);
    subplot(3,1,3); hold on; grid on; box on; axis tight;
    plot(t, magZ, 'k', 'LineWidth', 1);
    title([ '\mu: ' num2str(mean(magZ), '%.3f') ', \sigma: ' num2str(std(magZ), '%.3f')]);
    ylabel('MagZ (G)'); ylim([0 5]);
    xlabel('Time (sec)');
    % sgtitle('Mag');
    print(f6, fullfile(figDir, 'mag.png'), '-dpng', ['-r', num2str(res, '%.3f')]);

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
    title([ '\mu: ' num2str(mean(accelX), '%.3f') ', \sigma: ' num2str(std(accelX), '%.3f')]);
    ylabel('AccelX (m/s^2)'); ylim([-10 10]);
    subplot(3,1,2); hold on; grid on; box on; axis tight;
    plot(t, accelY, 'k', 'LineWidth', 1);
    title([ '\mu: ' num2str(mean(accelY), '%.3f') ', \sigma: ' num2str(std(accelY), '%.3f')]);
    ylabel('AccelY (m/s^2)'); ylim([-10 10]);
    subplot(3,1,3); hold on; grid on; box on; axis tight;
    plot(t, accelZ, 'k', 'LineWidth', 1);
    title([ '\mu: ' num2str(mean(accelZ), '%.3f') ', \sigma: ' num2str(std(accelZ), '%.3f')]);
    ylabel('AccelZ (m/s^2)'); ylim([-20 0]);
    xlabel('Time (sec)');
    % sgtitle('Accel');
    print(f7, fullfile(figDir, 'accel.png'), '-dpng', ['-r', num2str(res, '%.3f')]);

    %% Plot quaternions
    % The estimated attitude describing the body frame with respect to the 
    % local North-East-Down (NED) frame given as the quaternion.
    quatX = imu.quatX;
    quatY = imu.quatY;
    quatZ = imu.quatZ;
    quatW = imu.quatW;
    f8 = figure;
    subplot(4,1,1); hold on; grid on; box on; axis tight;
    plot(t, quatX, 'k', 'LineWidth', 1);
    title([ '\mu: ' num2str(mean(quatX), '%.3f') ', \sigma: ' num2str(std(quatX), '%.3f')]);
    ylabel('QuatX'); ylim([-1 1]);
    subplot(4,1,2); hold on; grid on; box on; axis tight;
    plot(t, quatY, 'k', 'LineWidth', 1);
    title([ '\mu: ' num2str(mean(quatY), '%.3f') ', \sigma: ' num2str(std(quatY), '%.3f')]);
    ylabel('QuatY'); ylim([-1 1]);
    subplot(4,1,3); hold on; grid on; box on; axis tight;
    plot(t, quatZ, 'k', 'LineWidth', 1);
    title([ '\mu: ' num2str(mean(quatZ), '%.3f') ', \sigma: ' num2str(std(quatZ), '%.3f')]);
    ylabel('QuatZ'); ylim([-1 1]);
    subplot(4,1,4); hold on; grid on; box on; axis tight;
    plot(t, quatW, 'k', 'LineWidth', 1);
    title([ '\mu: ' num2str(mean(quatW), '%.3f') ', \sigma: ' num2str(std(quatW), '%.3f')]);
    ylabel('QuatW'); ylim([-1 1]);
    xlabel('Time (sec)');
    % sgtitle('Quaternions');
    print(f8, fullfile(figDir, 'quaternion.png'), '-dpng', ['-r', num2str(res, '%.3f')]);

    %% Plot GNSS position and uncertainty
    % The current GNSS position measurement given as the geodetic latitude, 
    % longitude and altitude above the ellipsoid. The current GNSS position 
    % uncertainty in the North East Down (NED) reference frame.
    lat = imu.lat;
    lon = imu.lon;
    alt = imu.alt;
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
    % sgtitle('INS Position');
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
        h1.LatitudeData = lat(1:i);
        h1.LongitudeData = lon(1:i);
        h2.LatitudeData = lat(i);
        h2.LongitudeData = lon(i);
        frame = getframe(f10);
        writeVideo(video, frame);
    end
    close(video);

end