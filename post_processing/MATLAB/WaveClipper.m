% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-06

clear; clc; close all;

addpath('functions/');

%% Inputs

clipWaves = 1;      % Repetition flag
segment = 1;        % Segment images?


while clipWaves
    mainDir = uigetdir('../../','Select path to session'); % load path to session
    waveFolder = organize_images(mainDir);
    if segment
        segment_images(waveFolder);
    end
    answer = questdlg('Another?', ...
    'Clip another wave?', ...
    'Yes','No','Yes');
    switch answer
        case 'Yes'
            clipWaves = 1; 
        case 'No'
            clipWaves = 0; 
    end
end