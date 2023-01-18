import os

zone_files = os.listdir("config/zones")
exchange_files = os.listdir("config/exchanges")
zone_error: bool = False
exchange_error: bool = False
print("Checking config files...")
print("Checking if zone files are valid...")
"""Check if zone files are valid. Zone files must be uppercase."""
for file in zone_files:
    if file.endswith(".yaml") or file.endswith(".yml"):
        file = file.replace(".yaml", "") or file.replace(".yml", "")
        if file != file.upper():
            zone_error = True
            print(f"ERROR: {file} is not uppercase")
if zone_error == False:
    print("All zone filenames are valid!")
elif zone_error == True:
    print("There are errors in the above zone filenames!")

"""Check if exchange files are valid. Exchange files must be sorted and uppercase."""
for file in exchange_files:
    if file.endswith(".yaml") or file.endswith(".yml"):
        file = file.replace(".yaml", "") or file.replace(".yml", "")
        exchange_keys = file.split("_")
        sorted_exchange_keys = sorted(exchange_keys)
        if file != file.upper():
            exchange_error = True
            print(f"ERROR: {file} is not uppercase")
        if exchange_keys != sorted_exchange_keys:
            exchange_error = True
            print(f"ERROR: {file} is not sorted")
if exchange_error == False:
    print("All exchange filenames are valid!")
elif exchange_error == True:
    print("There are errors in the above exchange filenames!")


if zone_error or exchange_error:
    exit(1)
