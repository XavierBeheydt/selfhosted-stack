"""Hosts file management and generation."""

import os
import requests
from typing import List, Dict, Set


# Hosts file URLs from StevenBlack repository
HOSTS_URL = "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts"
CATEGORIES: Dict[str, str] = {
    "gambling": "https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/fakenews-gambling/hosts",
    "fakenews": "https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/fakenews/hosts",
    "adware": "https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/adware/hosts",
    "social": "https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/social/hosts",
    "porn": "https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/porn/hosts",
}


def download_hosts_file(url: str, output_path: str) -> None:
    """Download a hosts file from a URL.

    Args:
        url: URL to download from
        output_path: Path to save the file

    Raises:
        requests.exceptions.RequestException: If download fails
    """
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(response.text)


def merge_hosts_files(files: List[str], output_path: str) -> None:
    """Merge multiple hosts files into one, removing duplicates.

    Args:
        files: List of file paths to merge
        output_path: Path to save the merged file
    """
    merged_content: Set[str] = set()

    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    stripped_line = line.strip()
                    if stripped_line and not stripped_line.startswith("#"):
                        merged_content.add(line)
        except FileNotFoundError:
            continue

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(merged_content)))


def generate_hosts_for_ip(
    ip: str, categories: List[str], data_dir: str = "/data"
) -> str:
    """Generate a custom hosts file for a specific IP address.

    Args:
        ip: IP address to generate hosts file for
        categories: List of categories to include
        data_dir: Directory to store host files

    Returns:
        Path to the generated hosts file

    Raises:
        ValueError: If no valid categories are provided
    """
    if not categories:
        raise ValueError("At least one category must be specified")

    base_file = os.path.join(data_dir, "hosts_base.txt")
    output_file = os.path.join(data_dir, f"hosts_{ip}.txt")

    # Download base hosts file if it doesn't exist
    if not os.path.exists(base_file):
        download_hosts_file(HOSTS_URL, base_file)

    # Download category files
    category_files: List[str] = []
    for category in categories:
        if category in CATEGORIES:
            category_file = os.path.join(data_dir, f"hosts_{category}.txt")
            download_hosts_file(CATEGORIES[category], category_file)
            category_files.append(category_file)

    # Merge all files
    all_files = [base_file] + category_files
    merge_hosts_files(all_files, output_file)

    return output_file
