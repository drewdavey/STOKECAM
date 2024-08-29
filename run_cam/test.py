import yaml


camera_settings='settings.yaml'

config = {'config': {}}

with open(camera_settings, 'r') as file:
    settings = yaml.safe_load(file)

for key, value in settings['config'].items():
    # if isinstance(value, list):
    #     if len(value) == 2:  # Assuming tuples are used for size and white balance settings
    #         value = tuple(value)
    print(f"{key} = {value}")
    print( value)
# Iterate over the items in the YAML file
# for key, value in settings['config'].items():
#     # Handle tuple conversion for lists
#     if isinstance(value, list):
#         if len(value) == 2:  # Assuming tuples are used for size and white balance settings
#             value = tuple(value)
#     # Add the setting to the config dictionary
#     config['config'][key] = value

# # Example of how you might use these settings
# for key, value in config['config'].items():
#     print(f"config['config']['{key}'] = {value}  # {key} setting")