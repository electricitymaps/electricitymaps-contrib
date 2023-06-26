import yaml

from electricitymap.contrib.config import CONFIG_DIR
from electricitymap.contrib.config.reading import read_zones_config


def remove_flag_name():
    for zone_key in read_zones_config(config_dir=CONFIG_DIR):
        with open(CONFIG_DIR.joinpath(f"zones/{zone_key}.yaml"), "r") as reader:
            file: dict = yaml.safe_load(reader)
            if "flag_file_name" in file:
                file.pop("flag_file_name")
                with open(
                    CONFIG_DIR.joinpath(f"zones/{zone_key}.yaml"), "w", encoding="utf-8"
                ) as f:
                    f.write(yaml.dump(file, default_flow_style=False))
                print(f"🧹 Removed flag_file_name from {zone_key}.yaml")

    print("🎉 Done!")


if __name__ == "__main__":
    remove_flag_name()
