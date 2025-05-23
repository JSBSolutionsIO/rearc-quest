import json
import os

folder = "bls_data"
files_folder = os.path.join(folder, "files")
meta_file = os.path.join(folder, "metadata.json")

with open(meta_file, "r") as f:
    data = json.load(f)

# 1. Add a fake new file
data.append({
    "file_name": "pr.fake.new",
    "url": "https://download.bls.gov/pub/time.series/pr/pr.fake.new",
    "last_updated_date": "5/23/2025",
    "last_updated_time": "1:00 PM",
    "last_updated_timestamp": "2025-05-23T13:00:00",
    "file_size_bytes": 1234
})
with open(os.path.join(files_folder, "pr.fake.new"), "w") as f:
    f.write("fake data")

# 2. Change timestamp on existing file
for item in data:
    if item["file_name"] == "pr.class":
        item["last_updated_timestamp"] = "2000-01-01T00:00:00"

# 3. Remove a valid file entry
data = [d for d in data if d["file_name"] != "pr.series"]
series_path = os.path.join(files_folder, "pr.series")
if os.path.exists(series_path):
    os.remove(series_path)

# Save changes
with open(meta_file, "w") as f:
    json.dump(data, f, indent=2)

print("Simulated add (pr.fake.new), update (pr.class), and removal (pr.series).")