% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-06

function [points3D_cleaned, colors_cleaned] = trimBounds(points3D, colors, bounds)
    
    % Get the min and max values of the points3D for safety
    xMinPts = min(points3D(:,1));
    xMaxPts = max(points3D(:,1));
    yMinPts = min(points3D(:,2));
    yMaxPts = max(points3D(:,2));
    zMinPts = min(points3D(:,3));
    zMaxPts = max(points3D(:,3));
    
    % Ensure the bounds are within the actual limits of the point cloud
    bounds(1) = max(bounds(1), xMinPts); % xmin
    bounds(2) = min(bounds(2), xMaxPts); % xmax
    bounds(3) = max(bounds(3), yMinPts); % ymin
    bounds(4) = min(bounds(4), yMaxPts); % ymax
    bounds(5) = max(bounds(5), zMinPts); % zmin
    bounds(6) = min(bounds(6), zMaxPts); % zmax
    
    % Trim points to the specified bounds
    x = points3D(:,1);
    y = points3D(:,2);
    z = points3D(:,3);
    
    % Apply bounds to keep only the points within specified ranges
    withinBounds = (x >= bounds(1) & x <= bounds(2)) & ...
                   (y >= bounds(3) & y <= bounds(4)) & ...
                   (z >= bounds(5) & z <= bounds(6));
    
    points3D_cleaned = points3D(withinBounds, :);
    colors_cleaned = colors(withinBounds, :);

end