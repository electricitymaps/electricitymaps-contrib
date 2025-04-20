import os
import subprocess


def run_aggregate_france_script():
    """Run the aggregate_france_territories.py script to generate aggregated data."""
    script_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "scripts",
        "aggregate_france_territories.py",
    )
    try:
        subprocess.run(["python3", script_path], check=True)
        print("Aggregated France data script executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error while running the script: {e}")


# Call the function to ensure the script runs when the backend starts
run_aggregate_france_script()
