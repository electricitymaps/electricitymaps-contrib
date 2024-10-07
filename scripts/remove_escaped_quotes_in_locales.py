import os


def process_json_file(file_path):
    with open(file_path, encoding="utf-8") as file:
        content = file.read()

    # Replace \" with '
    updated_content = content.replace('\\"', "'")

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(updated_content)

    print(f"Processed: {file_path}")


def main():
    directory = "../web/src/locales"

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                process_json_file(file_path)


if __name__ == "__main__":
    main()
    print("All JSON files have been processed.")
