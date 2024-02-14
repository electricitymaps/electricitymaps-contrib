import os

import yaml

import yaml


def restructure_yaml(file_path):
    with open(file_path, "r") as file:
        data = yaml.safe_load(file)

    # Check if the file needs restructuring
    needs_restructuring = False
    for key, value in data.get("capacity", {}).items():
        if isinstance(value, dict):
            needs_restructuring = True
            break

    # Skip files that don't need restructuring
    if not needs_restructuring:
        return

    # Restructure the file
    for key, value in data["capacity"].items():
        if isinstance(value, dict):
            data["capacity"][key] = [value]

    with open(file_path, "w") as file:
        yaml.dump(data, file, default_flow_style=False, sort_keys=False)


if __name__ == "__main__":
    directory = "./"  # Replace 'your_directory' with the path to your directory

    for filename in os.listdir(directory):
        if filename.endswith(".yaml"):
            file_path = os.path.join(directory, filename)
            restructure_yaml(file_path)
