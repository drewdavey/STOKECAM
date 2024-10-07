% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-06

function points3D_cleaned = trimBounds(points3D, bounds, binSize)
    
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
    
    points3D = points3D(withinBounds, :);
    
    % Now step through the points cubically in bins of size binSize
    xMin = bounds(1); xMax = bounds(2);
    yMin = bounds(3); yMax = bounds(4);
    zMin = bounds(5); zMax = bounds(6);
    
    points3D_cleaned = [];
    
    for xStart = xMin:binSize:xMax
        for yStart = yMin:binSize:yMax
            for zStart = zMin:binSize:zMax
                % Define the current bin
                xEnd = xStart + binSize;
                yEnd = yStart + binSize;
                zEnd = zStart + binSize;
                
                % Find points within this bin
                inBin = (points3D(:,1) >= xStart & points3D(:,1) < xEnd) & ...
                        (points3D(:,2) >= yStart & points3D(:,2) < yEnd) & ...
                        (points3D(:,3) >= zStart & points3D(:,3) < zEnd);
                
                binPoints = points3D(inBin, :);
                
                if ~isempty(binPoints)
                    % Compute the mean and standard deviation for each dimension
                    binMean = mean(binPoints, 1);
                    binStd = std(binPoints, 1);
                    
                    % Find points within 3 standard deviations of the mean
                    deviationFromMean = abs(binPoints - binMean);
                    within3Std = all(deviationFromMean <= 3 * binStd, 2);
                    
                    % Add the cleaned points for this bin to the final output
                    points3D_cleaned = [points3D_cleaned; binPoints(within3Std, :)]; %#ok<AGROW>
                end
            end
        end
    end
end