% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-06

function mask = create_mask(img)
    % SEGMENT_IMAGE_GUI Launch the Image Segmenter app for interactive segmentation.
    % Input: img - The RGB image to be segmented.
    % Output: mask - Binary mask for the segmented region.
    
    % Open the image segmenter app with the provided image
    imageSegmenter(img);
    
    % Wait for user input
    disp('Use the Image Segmenter to select foreground and background.');
    uiwait(msgbox('Press OK after exporting BW and close the Image Segmenter.'));

    % Export the segmentation mask
    mask = evalin('base', 'BW');  

end
