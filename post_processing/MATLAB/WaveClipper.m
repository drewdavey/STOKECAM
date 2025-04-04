% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-10

clear; clc; close all;

addpath('functions/');

%% Inputs

segment = 0;        % Segment images?

%% Clip Waves

clipWaves = 1;
while clipWaves
    
    mainDir = uigetdir('../../../FSR/stereo_cam/DATA/','Select path to session'); % load path to session
    
    WasteMgmtAuto(mainDir); % clean out deleted images from both cam dirs
    
    waveFolder = organize_images(mainDir); % create wave* directory containing 'cam0' and 'cam1' folders

    %%%%%%%% MAKE L1.MAT HOLD ORIGINAL CROPPED PTCLOUD DATA AND IMU STRUCT
    %%%%%%%% L2.MAT WILL BE DOWNSIZED / SMOOTHED PTCLOUD AND CROSS SECTIONS

    if segment
        cam0Dir = fullfile(waveFolder, 'cam0');
        cam1Dir = fullfile(waveFolder, 'cam1');
    
        % Get all jpg files in cam0 and cam1
        cam0Files = dir(fullfile(cam0Dir, '*.jpg'));
        cam1Files = dir(fullfile(cam1Dir, '*.jpg'));

        % Loop through each frame
        for i = 1:length(cam0Files)
            % Get the full path of each image file
            cam0File = fullfile(cam0Dir, cam0Files(i).name);
            cam1File = fullfile(cam1Dir, cam1Files(i).name);
    
            % Read the images
            I1 = imread(cam0File);
            I2 = imread(cam1File);
    
            % Segment the air and water in I1 (using GUI)
            mask = create_mask(I1);
    
            % Apply the mask to both cam0 and cam1 images
            maskedI1 = I1;
            maskedI1(repmat(~mask,[1 1 3])) = 0;  % Apply mask to cam0 image
    
            maskedI2 = I2;
            maskedI2(repmat(~mask,[1 1 3])) = 0;  % Apply the same mask to cam1 image
    
            % Display the segmented image
            figure;
            title(['Segmented Images ', num2str(i)]);
            subplot(1, 2, 1), imshow(maskedI1), title('Cam0');
            subplot(1, 2, 2), imshow(maskedI2), title('Cam1');
    
            % Write segmented images
            imwrite(maskedI1,cam0File);
            imwrite(maskedI2,cam1File);

            clearvars BW
            % close all
        end
    end
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