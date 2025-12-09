function convertPointCloudsToPLYorLAS()
    % Create a GUI for selecting the folder containing .mat files
    folderName = uigetdir(pwd, 'Select Folder Containing .mat Point Clouds');
    if folderName == 0
        disp('No folder selected. Exiting.');
        return;
    end
    
    % Get a list of all .mat files in the selected folder
    matFiles = dir(fullfile(folderName, '*.mat'));
    
    % Check if there are any .mat files in the folder
    if isempty(matFiles)
        disp('No .mat files found in the selected folder. Exiting.');
        return;
    end
    
    % Loop through each .mat file and convert to .ply or .las
    for k = 1:length(matFiles)
        % Load the .mat file
        matFilePath = fullfile(folderName, matFiles(k).name);
        data = load(matFilePath);
        
        % Assuming the point cloud data is stored in a variable named 'ptCloud'
        if isfield(data, 'ptCloud')
            ptCloud = data.ptCloud;
        else
            disp(['Variable ptCloud not found in ', matFiles(k).name]);
            continue;
        end
        
        % Define the output file name and format
        [~, name, ~] = fileparts(matFiles(k).name);
        outputPLY = fullfile(folderName, [name, '.ply']);
        outputLAS = fullfile(folderName, [name, '.las']);
        
        % Convert and save to .ply format
        pcwrite(ptCloud, outputPLY, 'Encoding', 'ascii');
        disp(['Saved ', outputPLY]);
        
        % Optionally, convert and save to .las format 
        % pcwrite(ptCloud, outputLAS, 'Encoding', 'las');
        % disp(['Saved ', outputLAS]);
    end
    
    disp('Conversion completed.');
end