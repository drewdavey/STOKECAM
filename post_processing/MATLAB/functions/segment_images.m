% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-06

function segment_images(waveFolder)

    % Input: wave* directory containing 'cam0' and 'cam1' folders
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

        % Segment the air and water 
        segmentedI1 = segment_water(I1);
        segmentedI2 = segment_water(I2);

        % Display the segmented image
        figure;
        title(['Segmented Images ', num2str(i)]);
        subplot(1, 2, 1), imshow(segmentedI1), title('Cam0');
        subplot(1, 2, 2), imshow(segmentedI2), title('Cam1');

        % Write segmented images
        imwrite(segmentedI1,cam0File);
        imwrite(segmentedI2,cam1File);
    end
end
