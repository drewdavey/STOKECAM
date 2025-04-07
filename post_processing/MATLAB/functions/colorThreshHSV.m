% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-11-15

function [points3D, colors] = colorThreshHSV(points3D, colors, colors_orig, ...
                                             topFraction, bottomFraction, Nstd)
% Same usage as colorThreshRGB but uses HSV. The top 25% of 'colors_orig'
% is the background region, and the bottom 50% is the foreground region.
% We convert each region to HSV, compute mean ± 2std, and threshold
% the entire point cloud accordingly.

    % Handle optional inputs with defaults
    if nargin < 4 || isempty(topFraction)
        topFraction = 0.25;
    end
    if nargin < 5 || isempty(bottomFraction)
        bottomFraction = 0.50;
    end
    if nargin < 6 || isempty(Nstd)
        Nstd = 2;
    end

    [imgHeight, ~, ~] = size(colors_orig);
    topRows = round(topFraction * imgHeight);
    bottomRows = round(bottomFraction * imgHeight);
    foreStart  = imgHeight - bottomRows + 1;

    % Background (top)
    backgroundImg = colors_orig(1:topRows, :, :);
    % Foreground (bottom)
    foregroundImg = colors_orig(foreStart:end, :, :);

    % Reshape to Nx3
    bgPixels = reshape(backgroundImg, [], 3);
    fgPixels = reshape(foregroundImg, [], 3);

    % Convert to double
    bgPixels = im2double(bgPixels);
    fgPixels = im2double(fgPixels);

    % Convert from RGB to HSV
    bgHSV = rgb2hsv(bgPixels);
    fgHSV = rgb2hsv(fgPixels);

    % Mean & std in HSV
    bgMean = mean(bgHSV, 'omitnan');
    bgStd  = std(bgHSV,  'omitnan');
    bgThresh = [bgMean - Nstd*bgStd; bgMean + Nstd*bgStd];

    fgMean = mean(fgHSV, 'omitnan');
    fgStd  = std(fgHSV,  'omitnan');
    fgThresh = [fgMean - Nstd*fgStd; fgMean + Nstd*fgStd];

    % Convert all Nx3 "colors" to [0..1], then to HSV
    if max(colors(:)) > 1
        colorsFloat = im2double(colors); % ensures [0..1]
    else
        colorsFloat = double(colors);
    end

    % Nx3 => 1xN x 3 => hsv => Nx3 trick
    hsvVals = rgb2hsv(reshape(colorsFloat, [1, size(colorsFloat,1), 3]));
    hsvVals = reshape(hsvVals, [size(colorsFloat,1), 3]);

    % Build masks
    fgIdx = (hsvVals(:,1) >= fgThresh(1,1) & hsvVals(:,1) <= fgThresh(2,1)) & ...
            (hsvVals(:,2) >= fgThresh(1,2) & hsvVals(:,2) <= fgThresh(2,2)) & ...
            (hsvVals(:,3) >= fgThresh(1,3) & hsvVals(:,3) <= fgThresh(2,3));

    bgIdx = (hsvVals(:,1) >= bgThresh(1,1) & hsvVals(:,1) <= bgThresh(2,1)) & ...
            (hsvVals(:,2) >= bgThresh(1,2) & hsvVals(:,2) <= bgThresh(2,2)) & ...
            (hsvVals(:,3) >= bgThresh(1,3) & hsvVals(:,3) <= bgThresh(2,3));

    % If it's NOT in FG but IS in BG => set to NaN
    outIdx = (~fgIdx & bgIdx);

    points3D(outIdx,:) = NaN;
    colors(outIdx,:)   = 0;

end

