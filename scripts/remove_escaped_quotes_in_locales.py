# To check if there are any escaped quotes in the JSON files, run the script:
# python remove_escaped_quotes_in_locales.py --detect
# To fix the escaped quotes, run the script without the --detect flag:
# python remove_escaped_quotes_in_locales.py

import os
import sys


def process_json_file(file_path, detect_only=False):
    with open(file_path, encoding="utf-8") as file:
        content = file.read()

    # Check if there are any \" in the content
    if '\\"' in content:
        if detect_only:
            return True
        else:
            # Replace \" with '
            updated_content = content.replace('\\"', "'")
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(updated_content)
            print(f"Processed: {file_path}")
    return False


def main():
    detect_mode = "--detect" in sys.argv
    script_dir = os.path.dirname(os.path.abspath(__file__))
    directory = os.path.normpath(
        os.path.join(script_dir, "..", "web", "src", "locales")
    )
    escaped_quotes_found = False

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                if process_json_file(file_path, detect_mode):
                    escaped_quotes_found = True
                    if detect_mode:
                        print(f"Escaped quotes found in: {file_path}")

    if detect_mode and escaped_quotes_found:
        print(
            "Error: Escaped quotes detected in JSON files. Run the script remove_escaped_quotes_in_locales.py without --detect to fix."
        )
        sys.exit(1)
    elif not detect_mode:
        print("All JSON files have been processed.")


if __name__ == "__main__":
    main()
