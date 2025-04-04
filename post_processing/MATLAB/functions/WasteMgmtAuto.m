% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-11-17

function WasteMgmtAuto(path)
    % Identify camera directories
    cam0Dir = fullfile(path, 'cam0');
    cam1Dir = fullfile(path, 'cam1');

    % Gather files
    cam0Files = dir(fullfile(cam0Dir, '0_*.jpg'));
    cam1Files = dir(fullfile(cam1Dir, '1_*.jpg'));

    % For each file in cam0, see if there's a match in cam1. If none, delete it.
    for i = 1:numel(cam0Files)
        % Parse filename
        [~, ts0, imgNum0] = parse_filename(cam0Files(i).name);
        timeNs0 = str2double(ts0);

        % Use your "find_matching_file" to look in cam1's file list
        matchingFile = find_matching_file(cam1Files, timeNs0, imgNum0);

        % If there's no matching file, delete the cam0 file
        if isempty(matchingFile)
            delete(fullfile(cam0Dir, cam0Files(i).name));
            fprintf('Deleted cam0 file: %s\n', cam0Files(i).name);
        end
    end

    % For each file in cam1, see if there's a match in cam0. If none, delete it.
    for i = 1:numel(cam1Files)
        % Parse filename
        [~, ts1, imgNum1] = parse_filename(cam1Files(i).name);
        timeNs1 = str2double(ts1);

        % Look for a match in cam0
        matchingFile = find_matching_file(cam0Files, timeNs1, imgNum1);

        % If there's no matching file, delete the cam1 file
        if isempty(matchingFile)
            delete(fullfile(cam1Dir, cam1Files(i).name));
            fprintf('Deleted cam1 file: %s\n', cam1Files(i).name);
        end
    end

    [~, lastDir] = fileparts(path);
    disp([lastDir ' cleanup complete.']);
end