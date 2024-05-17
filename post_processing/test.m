
clear; clc; close all;

%% Load mat and create dir

load('C:\Users\drew\SIO\testing_drew\calibration\20240517\191625_calib\calib.mat');

%%
% I1 = imread('C:\Users\drew\SIO\testing_drew\calibration\20240517\225526_burst\cam0\0_225622156_00008.jpg');
% I2 = imread('C:\Users\drew\SIO\testing_drew\calibration\20240517\225526_burst\cam1\1_225622156_00008.jpg');
% I1 = imread(uigetfile());
% I2 = imread(uigetfile());
% I1 = imread('C:\Users\drew\SIO\testing_drew\calibration\20240517\225526_burst\cam0\0_225617253_00008.jpg');
% I2 = imread('C:\Users\drew\SIO\testing_drew\calibration\20240517\225526_burst\cam1\1_225617253_00008.jpg');
I1 = imread('C:\Users\drew\SIO\testing_drew\calibration\20240517\191625_calib\cam0\0_191751062_00028.jpg');
I2 = imread('C:\Users\drew\SIO\testing_drew\calibration\20240517\191625_calib\cam1\1_191751062_00028.jpg');

[J1, J2, reprojectionMatrix] = rectifyStereoImages(I1, I2, stereoParams); %rectify

frameLeftGray  = im2gray(J1);
frameRightGray = im2gray(J2);

disparityMap = disparitySGM(frameLeftGray, frameRightGray);

% Display rectified images
f1 = figure(1);
imshow(stereoAnaglyph(J1,J2));

% Display disparity map
f2 = figure(2);
imshow(disparityMap, [0, 64]);
colormap jet; colorbar;

% Create point cloud
points3D = reconstructScene(disparityMap, reprojectionMatrix); % for single disparity map
% Convert to meters and create a pointCloud object
points3D = points3D ./ 1000;
ptCloud = pointCloud(points3D, Color=J1);

% Create a streaming point cloud viewer
player3D = pcplayer([-3, 3], [-3, 3], [0, 8], VerticalAxis="y", ...
    VerticalAxisDir="down");
% Visualize the point cloud
view(player3D, ptCloud);



