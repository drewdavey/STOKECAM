% STOKECAM Post-Processing
% Drew Davey
% Last updated: 2024-10-06

% Function to get the next wave folder index
function newWaveFolder = get_wave_folder(mainDir)
    % Get a list of all wave* folders in the main directory
    folderList = dir(fullfile(mainDir, 'wave*')); 
    % Initialize maxWaveNumber to 0
    maxWaveNumber = 0;    
    % Loop through each folder and extract the number
    for i = 1:length(folderList)
        folderName = folderList(i).name;
        % Check if the folder name starts with 'wave'
        if startsWith(folderName, 'wave')
            % Extract the number from the folder name
            waveNumber = sscanf(folderName, 'wave%d');
            % Update the maxWaveNumber if the current waveNumber is larger
            if ~isempty(waveNumber) && waveNumber > maxWaveNumber
                maxWaveNumber = waveNumber;
            end
        end
    end    
    % Create the new wave folder with incremented number
    newWaveNumber = maxWaveNumber + 1;
    newWaveFolder = fullfile(mainDir, sprintf('wave%d', newWaveNumber));
    % Create the new directories
    mkdir(newWaveFolder);
    mkdir(fullfile(newWaveFolder,'cam0/'));
    mkdir(fullfile(newWaveFolder,'cam1/'));
    disp(['Created new wave folder: ', newWaveFolder]);
end