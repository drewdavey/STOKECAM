% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-10

clear; clc; close all;

addpath('functions/');

%% Clip Waves

clipWaves = 1;
while clipWaves
    
    mainDir = uigetdir('../../../FSR/stereo_cam/DATA/','Select path to session'); % load path to session
    
    WasteMgmtAuto(mainDir); % clean out deleted images from both cam dirs
    
    waveFolder = organize_images(mainDir); % create wave* directory containing 'cam0' and 'cam1' folders

    %%%%%%%% MAKE L1.MAT HOLD ORIGINAL CROPPED PTCLOUD DATA AND IMU STRUCT
    %%%%%%%% L2.MAT WILL BE DOWNSIZED / SMOOTHED PTCLOUD AND CROSS SECTIONS

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