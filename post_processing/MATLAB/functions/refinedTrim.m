% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2025-04-07

function [points3D, colors] = refinedTrim(points3D, colors, Nstd)
% Computes the centroid of the (valid) 3D point set, then removes any points
% that lie farther than N standard deviations from that centroid in Euclidean
% distance by setting those points to NaN.

    % Handle optional argument
    if nargin < 3 || isempty(Nstd)
        Nstd = 3;  % default
    end

    % Find all valid (non-NaN) rows in points3D
    validIdx = ~any(isnan(points3D), 2);  % row is valid if no component is NaN
    if ~any(validIdx)
        % If no valid points left, nothing to do
        return;
    end
    validPoints = points3D(validIdx, :);

    % Compute centroid of the valid points
    centroid = mean(validPoints, 1, 'omitnan');

    % Compute distance from each point to the centroid
    %    (points that are already NaN will get distance=NaN)
    diffs = points3D - centroid;           % Nx3
    dist2centroid = sqrt(sum(diffs.^2, 2)); % Nx1 Euclidean distance

    % Compute standard deviation of distances (ignoring NaN)
    stdDist = std(dist2centroid(validIdx), 'omitnan');

    % Mark as outliers any points with dist > 3*stdDist
    outlierIdx = dist2centroid > (Nstd * stdDist);

    % If stdDist = 0 (e.g., all points identical), no outliers
    % but handle the degenerate case:
    if stdDist == 0
        outlierIdx(:) = false;
    end

    % Set outliers to NaN in both points3D and colors
    points3D(outlierIdx, :) = NaN;
    colors(outlierIdx, :)   = NaN;

end
