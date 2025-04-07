% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-11-15

function [points3D, colors] = colorThreshRGB(points3D, colors, colors_orig, ...
                                             topFraction, bottomFraction, Nstd)
% Automatically uses the top 25% of the image (in 'colors_orig') as a
% "background" reference, and the bottom 50% as a "foreground" reference.
% Computes mean & std in the RGB space for each region, then sets out-of-ROI
% points to NaN in 'points3D'.

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

    % Get image size
    [imgHeight, ~, ~] = size(colors_orig);

    % Calculate row indices
    topRows = round(topFraction * imgHeight);       % background region
    bottomRows = round(bottomFraction * imgHeight); % foreground region
    foreStart  = imgHeight - bottomRows + 1;        % start row for foreground

    % Separate background region (top) and foreground region (bottom)
    backgroundImg = colors_orig(1:topRows, :, :);
    foregroundImg = colors_orig(foreStart:end, :, :);

    % Reshape each region into [#pixels x 3]
    bgPixels = reshape(backgroundImg, [], 3);
    fgPixels = reshape(foregroundImg, [], 3);

    % Convert to double
    bgPixels = double(bgPixels);
    fgPixels = double(fgPixels);

    % If your 'colors' are in [0..255], convert them to [0..1] for thresholding
    if max(colors(:)) > 1
        colorsFloat = double(colors) / 255;
    else
        colorsFloat = double(colors);
    end

    % Compute mean & std for background
    bgMean = mean(bgPixels, 'omitnan');
    bgStd  = std(bgPixels,  'omitnan');
    bgThresh = [bgMean - Nstd*bgStd; bgMean + Nstd*bgStd];

    % Compute mean & std for foreground
    fgMean = mean(fgPixels, 'omitnan');
    fgStd  = std(fgPixels,  'omitnan');
    fgThresh = [fgMean - Nstd*fgStd; fgMean + Nstd*fgStd];

    % Is pixel in foreground?
    fgIdx = (colorsFloat(:,1) >= fgThresh(1,1) & colorsFloat(:,1) <= fgThresh(2,1)) & ...
            (colorsFloat(:,2) >= fgThresh(1,2) & colorsFloat(:,2) <= fgThresh(2,2)) & ...
            (colorsFloat(:,3) >= fgThresh(1,3) & colorsFloat(:,3) <= fgThresh(2,3));

    % Is pixel in background?
    bgIdx = (colorsFloat(:,1) >= bgThresh(1,1) & colorsFloat(:,1) <= bgThresh(2,1)) & ...
            (colorsFloat(:,2) >= bgThresh(1,2) & colorsFloat(:,2) <= bgThresh(2,2)) & ...
            (colorsFloat(:,3) >= bgThresh(1,3) & colorsFloat(:,3) <= bgThresh(2,3));

    %   If it is NOT in foreground but IS in background => set to NaN
    %   (Removes background points, keeps foreground).
    outIdx = (~fgIdx & bgIdx);

    points3D(outIdx,:) = NaN;
    colors(outIdx,:)   = 0;   % black them out (could also do NaN)

end
