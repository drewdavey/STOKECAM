% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-11-13

function [points3D, colors] = refinedTrim(points3D, colors, colors_tmp)
    % Get image dimensions
    [imgHeight, imgWidth, ~] = size(colors_tmp);    

    % Display the image
    figure; imshow(colors_tmp);
    hold on;
    title('Select points to define the polygon (double-click to finish)');

    % Let user select multiple points to define the polygon
    h = drawpolygon('Color', 'b', 'LineWidth', 1.5); % Draws the polygon interactively
    polygonVertices = h.Position; % Get polygon vertices after user finishes

    % Draw the completed polygon with shaded area
    fill(polygonVertices(:, 1), polygonVertices(:, 2), 'y', 'FaceAlpha', 0.3, 'EdgeColor', 'b');

    % Generate a grid of pixel coordinates
    [X, Y] = meshgrid(1:imgWidth, 1:imgHeight);
    X = X(:); % Flatten to match reshaped image data
    Y = Y(:);

    % Determine which pixels are inside the polygon
    inPolygon = inpolygon(X, Y, polygonVertices(:, 1), polygonVertices(:, 2));

    % Filter points3D and colors based on the polygon mask
    points3D = points3D(inPolygon, :);
    colors = colors(inPolygon, :);

    % Close the figure
    close(gcf);
end
