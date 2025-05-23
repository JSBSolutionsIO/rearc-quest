import json
import boto3
from io import BytesIO

# S3 config
BUCKET_NAME = "rearc-quest-brandon"
PREFIX = "bls-files/"
FILES_PREFIX = PREFIX + "files/"
METADATA_KEY = PREFIX + "metadata.json"

s3 = boto3.client("s3")

# Load existing metadata from S3
try:
    response = s3.get_object(Bucket=BUCKET_NAME, Key=METADATA_KEY)
    data = json.load(response["Body"])
except s3.exceptions.NoSuchKey:
    data = []

# 1. Add a fake new file
fake_filename = "pr.fake.new"
data.append({
    "file_name": fake_filename,
    "url": f"https://download.bls.gov/pub/time.series/pr/{fake_filename}",
    "last_updated_date": "5/23/2025",
    "last_updated_time": "1:00 PM",
    "last_updated_timestamp": "2025-05-23T13:00:00",
    "file_size_bytes": 1234
})
s3.put_object(
    Bucket=BUCKET_NAME,
    Key=FILES_PREFIX + fake_filename,
    Body=b"fake data"
)

# 2. Change timestamp on existing file
for item in data:
    if item["file_name"] == "pr.class":
        item["last_updated_timestamp"] = "2000-01-01T00:00:00"

# 3. Remove a valid file entry
data = [d for d in data if d["file_name"] != "pr.series"]
try:
    s3.delete_object(Bucket=BUCKET_NAME, Key=FILES_PREFIX + "pr.series")
except s3.exceptions.ClientError:
    pass  # Ignore if already deleted

# Save updated metadata to S3
s3.put_object(
    Bucket=BUCKET_NAME,
    Key=METADATA_KEY,
    Body=json.dumps(data, indent=2).encode("utf-8")
)

print("Simulated add (pr.fake.new), update (pr.class), and removal (pr.series) in S3.")