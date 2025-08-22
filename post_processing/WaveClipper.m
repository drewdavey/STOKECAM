% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2025-04-21

clear; clc; close all;

addpath('MATLAB/functions/');

%% Clip Waves

clipWaves = 1;
while clipWaves
    
    session = uigetdir('../../FSR/stereo_cam/DATA/','Select path to session'); % load path to session
    
    % WasteMgmtAuto(session); % clean out deleted images from both cam dirs
    
    wave = organize_images(session); % create wave* directory containing 'cam0' and 'cam1' folders

    imu = parse_imu(session, wave); % Parse VN-200 data into struct
    save(fullfile(wave, 'imu.mat'), 'imu'); % Save VN-200 struct to wave dir

    answer = questdlg('Clip another wave?', ...
    'Clip another wave?', ...
    'Yes','No','Yes');
    switch answer
        case 'Yes'
            clipWaves = 1; 
        case 'No'
            clipWaves = 0; 
    end
end