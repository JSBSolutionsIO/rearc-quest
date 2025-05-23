import os
import subprocess
import shutil
import zipfile
import boto3
import stat

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LAMBDA_DIR = os.path.join(BASE_DIR, "lambda")
DIST_DIR = os.path.join(BASE_DIR, "dist")
BUILD_DIR = os.path.join(BASE_DIR, ".lambda_build")

# S3 prefix for Lambda deployment zips
ZIP_PREFIX = "lambda-zips/"

# Get AWS account ID and region for dynamic bucket name
sts = boto3.client("sts")
account_id = sts.get_caller_identity()["Account"]
region = boto3.session.Session().region_name

BUCKET_NAME = f"rearc-quest-{account_id}-{region}"
print(f"Using bucket: {BUCKET_NAME}")

def force_remove_readonly(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def package_lambda_function(lambda_name):
    print(f"\nPackaging: {lambda_name}")
    source_dir = os.path.join(LAMBDA_DIR, lambda_name)
    requirements_file = os.path.join(source_dir, "requirements.txt")
    output_zip = os.path.join(DIST_DIR, f"{lambda_name}.zip")

    # Clean existing ZIP
    if os.path.exists(output_zip):
        os.remove(output_zip)

    build_dir = os.path.join(BUILD_DIR, lambda_name)
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir, onerror=force_remove_readonly)
    os.makedirs(build_dir)

    # Install dependencies
    if os.path.exists(requirements_file):
        subprocess.check_call([
            "pip", "install", "-r", requirements_file,
            "--target", build_dir
        ])

    # Copy source files
    for file in os.listdir(source_dir):
        if file.endswith(".py"):
            shutil.copy(os.path.join(source_dir, file), build_dir)

    # Create ZIP
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(build_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, build_dir)
                z.write(file_path, arcname)

    print(f"Created ZIP: {output_zip}")
    return output_zip, f"{ZIP_PREFIX}{lambda_name}.zip"

def upload_to_s3(zip_path, bucket, key):
    print(f"Uploading to s3://{bucket}/{key}")
    s3 = boto3.client("s3")
    with open(zip_path, "rb") as f:
        s3.upload_fileobj(f, bucket, key)
    print("Upload complete.")

def main():
    os.makedirs(DIST_DIR, exist_ok=True)
    os.makedirs(BUILD_DIR, exist_ok=True)

    # Only package combined_sync for now
    functions = [name for name in os.listdir(LAMBDA_DIR)
                 if os.path.isdir(os.path.join(LAMBDA_DIR, name))]

    for fn in functions:
        zip_path, s3_key = package_lambda_function(fn)
        upload_to_s3(zip_path, BUCKET_NAME, s3_key)

if __name__ == "__main__":
    main()