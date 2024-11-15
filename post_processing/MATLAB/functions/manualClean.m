% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-11-13

function [points3D, colors] = manualClean(points3D, colors)

        % Create a 3D scatter plot with the points and colors
        f = figure; axis equal;
        p = scatter3(points3D(:,1), points3D(:,2), points3D(:,3), 1, double(colors) / 255, 'filled');
        xlabel('X'); ylabel('Y'); zlabel('Z');
        title('Brush Data to Delete Points');

        % Initialize a logical array to keep track of all brushed points
        brushedIdx = false(size(points3D, 1), 1);

        % Enable data brushing for the figure
        brush on;

        while ishandle(f)
            newBrushedIdx = find(p.BrushData);  % Get the indices of brushed points
            brushedIdx(newBrushedIdx) = true;
            pause(0.1)
        end

        % Delete the brushed points
        points3D = points3D(~brushedIdx, :);
        colors = colors(~brushedIdx, :);

end