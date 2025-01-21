import yaml
import sys

def read_config():
    if len(sys.argv) > 1:
        print(f"Reading config from {sys.argv[1]}")
        with open(sys.argv[1], "r") as f:
            config = yaml.safe_load(f)
    else:
        with open("config.yml", "r") as f:
            config = yaml.safe_load(f)
    return config