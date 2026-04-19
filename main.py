# filename: main.py

"""
The Main Python File.
Entry Point for CLI for rotuer simulation
"""

import logging
import sys
import json


def run_simulation():
    pass
    
    # TODO: Implement all the Functionailiyt to Run the Simulation

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s"
    )

    
    config_path = ""

    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        print("No configuration file provided.")
        config_path = input("Please enter the path to your config file: ").strip()

    if not config_path:
        print("Error: No config path provided. Exiting.")
        return

    try:
        with open(config_path, "r") as f:
            config_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find file '{config_path}'")
        return
    except json.JSONDecodeError:
        print(f"Error: '{config_path}' is not a valid JSON file.")
        return

if __name__ == "__main__":
    main()