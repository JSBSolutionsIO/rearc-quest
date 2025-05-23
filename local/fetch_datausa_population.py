import requests
import boto3
import json
import botocore.exceptions

# Config
API_URL = "https://datausa.io/api/data?drilldowns=Nation&measures=Population"
BUCKET_NAME = "rearc-quest-brandon"
S3_KEY = "datausa/population.json"

s3 = boto3.client("s3")

try:
    # Fetch data
    response = requests.get(API_URL, timeout=10)
    response.raise_for_status()
    json_data = response.json()

    # Upload to S3
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=S3_KEY,
        Body=json.dumps(json_data, indent=2).encode("utf-8"),
        ContentType="application/json"
    )
    print(f"Success: Saved population data to s3://{BUCKET_NAME}/{S3_KEY}")

except requests.exceptions.RequestException as e:
    print(f"Error fetching data from API: {e}")

except botocore.exceptions.ClientError as e:
    print(f"Error uploading to S3: {e}")

except Exception as e:
    print(f"Unexpected error: {e}")