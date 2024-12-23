import json
import os
import subprocess
from pathlib import Path
from typing import Any


# Function to run Git commands and retrieve tags and branches
def get_git_versions():
    versions_file = "../versions"

    # Check if the versions file exists
    if not os.path.exists(versions_file):
        raise FileNotFoundError(f"Versions file '{versions_file}' not found.")

    # Read versions (tags) from the file
    with open(versions_file, "r") as f:
        tags = [line.strip() for line in f if line.strip()]

    # Optionally, include branches
    # Get Git branches if needed
    branches = (
        subprocess.check_output(
            ["git", "branch", "--format", "%(refname:short)"], text=True
        )
        .strip()
        .split("\n")
    )

    return tags, branches


# Generate version information for the JSON
def generate_version_data():
    tags, branches = get_git_versions()

    # List to store JSON version data
    versions: list[dict[str, Any]] = []

    # Add development version (main branch)
    if "main" in branches:
        versions.append(
            {
                "name": "dev",
                "version": "dev",
                "url": "https://soichiroyamane.github.io/gsplot/dev/",
            }
        )

    # Add tag versions
    for tag in sorted(tags, reverse=True):  # Sort tags in descending order
        if tag == tags[-1]:
            version_info = {
                "name": f"{tag} (stable)",  # Mark the latest tag as stable
                "version": f"{tag}",
                "url": f"https://soichiroyamane.github.io/gsplot/stable/",
                "preferred": True,
            }
        else:
            version_info = {
                "name": f"{tag}",
                "version": f"{tag}",
                "url": f"https://soichiroyamane.github.io/gsplot/{tag}/",
            }
        version_info = {
            key: str(value) if not isinstance(value, bool) else value
            for key, value in version_info.items()
        }
        versions.append(version_info)

    return versions


# Define the output directory and file name
output_dir = Path(".")
output_file = output_dir / "switcher.json"


# Create the JSON file
def write_version_switcher():
    versions = generate_version_data()

    # Ensure the output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write version data to the JSON file
    with open(output_file, "w") as f:
        json.dump(versions, f, indent=2)


# Generate the version switcher JSON file
write_version_switcher()
