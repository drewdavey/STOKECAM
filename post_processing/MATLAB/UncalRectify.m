% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-06

clear; clc; close all;

path = uigetdir('../../','Select path to session for reconstruction'); % load path to dir to reconstruct

matDir = [path '/mats'];
if ~exist(matDir, 'dir')
    mkdir(matDir); % mkdir for .mats
end

rectifiedImagesDir = [path '/Unrectified_Images']; 
if ~exist(rectifiedImagesDir, 'dir')
    mkdir(rectifiedImagesDir); % mkdir for rectified images
end

dir1 = dir([path '/cam1/*.jpg']);
dir2 = dir([path '/cam0/*.jpg']);

%% Parse data
 
% Check the number of files in each directory
numFiles = min(length(dir1), length(dir2));

% Initialize arrays to store file paths
imageFileNames1 = cell(numFiles, 1);
imageFileNames2 = cell(numFiles, 1);

% Construct file paths for each directory
for i = 1:numFiles
    imageFileNames1{i} = fullfile(dir1(i).folder, dir1(i).name);
    imageFileNames2{i} = fullfile(dir2(i).folder, dir2(i).name);
end

% Loop through each frame
for i = 1:length(imageFileNames1)
    I1 = imread(imageFileNames1{i});
    I2 = imread(imageFileNames2{i});
    
    I1gray = im2gray(I1);
    I2gray = im2gray(I2);

    f1 = figure(1);
    imshowpair(I1,I2,"montage")
    title("I1 (left); I2 (right)")

    f2 = figure(2);
    imshow(stereoAnaglyph(I1,I2))
    title("Composite Image (Red - Left Image, Cyan - Right Image)")
    blobs1 = detectSURFFeatures(I1gray,MetricThreshold=2000);
    blobs2 = detectSURFFeatures(I2gray,MetricThreshold=2000);

    f3 = figure(3);
    imshow(I1)
    hold on
    plot(selectStrongest(blobs1,30))
    title("Thirty Strongest SURF Features In I1")

    f4 = figure(4);
    imshow(I2)
    hold on
    plot(selectStrongest(blobs2,30))
    title("Thirty Strongest SURF Features In I2")

    [features1,validBlobs1] = extractFeatures(I1gray,blobs1);
    [features2,validBlobs2] = extractFeatures(I2gray,blobs2);
    indexPairs = matchFeatures(features1,features2,Metric="SSD", ...
      MatchThreshold=10, Method='Approximate');
    matchedPoints1 = validBlobs1(indexPairs(:,1),:);
    matchedPoints2 = validBlobs2(indexPairs(:,2),:);

    f5 = figure(5);
    showMatchedFeatures(I1, I2, matchedPoints1, matchedPoints2)
    legend("Matched Points In I1","Matched Points In I2")

    [fMatrix, epipolarInliers, status] = estimateFundamentalMatrix(...
      matchedPoints1,matchedPoints2,Method="MSAC", ...
      NumTrials=10000,DistanceThreshold=10,Confidence=69.99);
      
%     if status ~= 0 || isEpipoleInImage(fMatrix,size(I1)) ...
%       || isEpipoleInImage(fMatrix',size(I2))
%       error(["Not enough matching points were found or "...
%              "the epipoles are inside the images. Inspect "...
%              "and improve the quality of detected features ",...
%              "and images."]);
%     end
    
    inlierPoints1 = matchedPoints1(epipolarInliers, :);
    inlierPoints2 = matchedPoints2(epipolarInliers, :);
    
    f6 = figure(6);
    showMatchedFeatures(I1, I2, inlierPoints1, inlierPoints2)
    legend("Inlier Points In I1","Inlier Points In I2")

    [tform1, tform2] = estimateUncalibratedRectification(fMatrix, ...
      inlierPoints1.Location,inlierPoints2.Location,size(I2));


    [J1, J2] = rectifyStereoImages(I1,I2,tform1,tform2);
    
    frameLeftGray  = im2gray(J1);
    frameRightGray = im2gray(J2);
    
    f7 = figure(7);
    imshow(stereoAnaglyph(J1,J2))
    title("Rectified Stereo Images (Red - Left Image, Cyan - Right Image)")

    %%% Compute Disparity Map %%%
    disparityMap = disparitySGM(frameLeftGray, frameRightGray);
%     disparityMap = disparitySGM(frameLeftGray, frameRightGray,'UniquenessThreshold',UniquenessThreshold); % semi-global matching
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    exportgraphics(f1,fullfile(rectifiedImagesDir, ['f1-' num2str(i) '.png']),'Resolution',600); 
    exportgraphics(f2,fullfile(rectifiedImagesDir, ['f2-' num2str(i) '.png']),'Resolution',600);
    exportgraphics(f3,fullfile(rectifiedImagesDir, ['f3-' num2str(i) '.png']),'Resolution',600);
    exportgraphics(f4,fullfile(rectifiedImagesDir, ['f4-' num2str(i) '.png']),'Resolution',600);
    exportgraphics(f5,fullfile(rectifiedImagesDir, ['f5-' num2str(i) '.png']),'Resolution',600);
    exportgraphics(f6,fullfile(rectifiedImagesDir, ['f6-' num2str(i) '.png']),'Resolution',600);
    exportgraphics(f7,fullfile(rectifiedImagesDir, ['f7-' num2str(i) '.png']),'Resolution',600);

    % Plotting
    f8 = figure(8);
    imshow(stereoAnaglyph(J1,J2)); % Display rectified images
    filename = [imageFileNames1{i}(end-18:end-4) '_rect.png'];
    fullFilePath = fullfile(rectifiedImagesDir, filename);
    exportgraphics(f8,fullFilePath,'Resolution',600); % Save rectified images as PNG
    f9 = figure(9); 
    imshow(disparityMap, [0, 64]); % Display disparity map
    colormap jet; colorbar;
    filename = [imageFileNames1{i}(end-18:end-4) '_disp.png'];
    fullFilePath = fullfile(rectifiedImagesDir, filename);
    exportgraphics(f9,fullFilePath,'Resolution',600); % Save disparity map as PNG

end
