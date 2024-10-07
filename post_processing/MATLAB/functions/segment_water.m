% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-06

function seg_I = segment_water(img)

    level = multithresh(img);
    seg_I = imquantize(img,level);
%     imshow(seg_I,[])

end