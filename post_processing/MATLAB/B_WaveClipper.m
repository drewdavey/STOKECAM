% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2025-04-21

clear; clc; close all;

addpath('functions/');

%% Clip Waves

clipWaves = 1;
while clipWaves
    
    mainDir = uigetdir('../../../FSR/stereo_cam/DATA/','Select path to session'); % load path to session
    
    WasteMgmtAuto(mainDir); % clean out deleted images from both cam dirs
    
    waveFolder = organize_images(mainDir); % create wave* directory containing 'cam0' and 'cam1' folders

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