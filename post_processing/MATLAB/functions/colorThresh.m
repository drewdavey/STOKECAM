% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-11-13

function [points3D, colors] = colorThresh(points3D, colors, colors_tmp)


        % Load image
        figure; imshow(colors_tmp); 
        hold on;
        
        % Arrays to store all pixel values from foreground and background ROIs
        foregroundPixels = [];
        backgroundPixels = [];
        
        for i = 1:6
            if i <= 3
                title('Select Foreground ROI');
                color = 'g';  % Green for foreground
            else
                title('Select Background ROI');
                color = 'r';  % Red for background
            end
            
            h = drawrectangle('Color', color); % Draw rectangle
            position = h.Position; % [x, y, width, height]
    
            % Convert position to integer indices
            x1 = round(position(1));
            y1 = round(position(2));
            x2 = x1 + round(position(3)) - 1;
            y2 = y1 + round(position(4)) - 1;
            centerX = x1 + (x2 - x1) / 2;
            centerY = y1 + (y2 - y1) / 2;
    
            % Extract the region of interest
            roi = colors_tmp(y1:y2, x1:x2, :);
    
            % Accumulate all pixel values from the selected regions
            if i <= 3
                foregroundPixels = [foregroundPixels; reshape(roi, [], 3)];
            else
                backgroundPixels = [backgroundPixels; reshape(roi, [], 3)];
            end
    
            % Plot shaded rectangle
            fill([x1 x2 x2 x1], [y1 y1 y2 y2], color, 'FaceAlpha', 0.3, 'EdgeColor', color);
            text(centerX, centerY, sprintf('ROI %d', i), 'Color', color, 'FontSize', 10);
    
            pause(1); % Pause to view rectangle
        end
        
        % Calculate mean and standard deviation for each color channel
        foregroundMeanRGB = mean(foregroundPixels);
        foregroundStdRGB = std(double(foregroundPixels));
        backgroundMeanRGB = mean(backgroundPixels);
        backgroundStdRGB = std(double(backgroundPixels));
        N = 2; % Multiplier (N std from mean)
        
        % Define thresholds based on the combined foreground and background regions
        foregroundThresholds = [foregroundMeanRGB - N * foregroundStdRGB; foregroundMeanRGB + N * foregroundStdRGB];
        backgroundThresholds = [backgroundMeanRGB - N * backgroundStdRGB; backgroundMeanRGB + N * backgroundStdRGB];
        
        % Apply thresholding
        fgIdx = (colors(:,1) >= foregroundThresholds(1,1) & colors(:,1) <= foregroundThresholds(2,1)) & ...
                (colors(:,2) >= foregroundThresholds(1,2) & colors(:,2) <= foregroundThresholds(2,2)) & ...
                (colors(:,3) >= foregroundThresholds(1,3) & colors(:,3) <= foregroundThresholds(2,3));
    
        bgIdx = (colors(:,1) >= backgroundThresholds(1,1) & colors(:,1) <= backgroundThresholds(2,1)) & ...
                (colors(:,2) >= backgroundThresholds(1,2) & colors(:,2) <= backgroundThresholds(2,2)) & ...
                (colors(:,3) >= backgroundThresholds(1,3) & colors(:,3) <= backgroundThresholds(2,3));
    
        % % Filter out background points and keep foreground points
        % colors = colors(fgIdx & ~bgIdx, :);
        % points3D = points3D(fgIdx & ~bgIdx, :);
        colors(~fgIdx & bgIdx, :) = NaN;
        points3D(~fgIdx & bgIdx, :) = NaN;
    
        close(gcf);
end