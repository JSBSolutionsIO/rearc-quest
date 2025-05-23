import os
import requests
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime

# Configuration
BASE_URL = "https://download.bls.gov/pub/time.series/pr/"
LOCAL_FOLDER = "bls_data"
FILES_SUBDIR = "files"
FILES_FOLDER = os.path.join(LOCAL_FOLDER, FILES_SUBDIR)
METADATA_FILE = "metadata.json"
CONTACT_INFO = "Brandon Young (brandon@jsbsolutions.io)"
USER_AGENT = f"DataSyncBot/1.0 ({CONTACT_INFO})"
HEADERS = {"User-Agent": USER_AGENT}

# Ensure folders exist
os.makedirs(LOCAL_FOLDER, exist_ok=True)
os.makedirs(FILES_FOLDER, exist_ok=True)

# Load existing metadata
metadata_path = os.path.join(LOCAL_FOLDER, METADATA_FILE)
if os.path.exists(metadata_path):
    with open(metadata_path, "r") as f:
        old_metadata = {item["file_name"]: item for item in json.load(f)}
else:
    old_metadata = {}

# Scrape live directory
response = requests.get(BASE_URL, headers=HEADERS)
response.raise_for_status()
soup = BeautifulSoup(response.text, "html.parser")
pre_block = soup.find("pre")
if not pre_block:
    raise RuntimeError("No <pre> block found on the page.")

# Parse current metadata
new_metadata = {}
for a_tag in pre_block.find_all("a"):
    href = a_tag.get("href")
    if not href or "Parent Directory" in href or href.endswith("/"):
        continue

    file_name = os.path.basename(href)
    if not file_name.strip():
        continue

    file_url = BASE_URL + file_name
    file_path = os.path.join(FILES_FOLDER, file_name)

    # Parse date, time, and size from sibling text
    sibling = a_tag.find_next_sibling(string=True)
    date_str, time_str, file_size, timestamp = "", "", None, None
    if sibling:
        match = re.search(r"(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}:\d{2}\s+[AP]M)\s+([\d,]+)", sibling.strip())
        if match:
            date_str, time_str, size_str = match.groups()
            file_size = int(size_str.replace(",", ""))
            dt = datetime.strptime(f"{date_str} {time_str}", "%m/%d/%Y %I:%M %p")
            timestamp = dt.isoformat()

    # Determine if the file should be downloaded
    existing = old_metadata.get(file_name)
    should_download = (
        existing is None or
        existing.get("last_updated_timestamp") != timestamp or
        not os.path.exists(file_path)
    )

    if should_download:
        print(f"Downloading: {file_name}")
        file_response = requests.get(file_url, headers=HEADERS)
        if file_response.status_code == 200:
            with open(file_path, "wb") as f:
                f.write(file_response.content)
        else:
            print(f"Failed to download {file_name}")
            continue

    new_metadata[file_name] = {
        "file_name": file_name,
        "url": file_url,
        "last_updated_date": date_str,
        "last_updated_time": time_str,
        "last_updated_timestamp": timestamp,
        "file_size_bytes": file_size
    }

# Remove deleted files from disk
deleted_files = set(old_metadata) - set(new_metadata)
for file_name in deleted_files:
    local_path = os.path.join(FILES_FOLDER, file_name)
    if os.path.exists(local_path):
        print(f"Removing deleted file: {file_name}")
        os.remove(local_path)

# Save updated metadata
with open(metadata_path, "w") as f:
    json.dump(list(new_metadata.values()), f, indent=2)

print(f"Sync complete. {len(new_metadata)} files current.")