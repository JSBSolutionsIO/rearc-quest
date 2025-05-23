import subprocess
import boto3
from pathlib import Path

DIST_DIR = Path(__file__).resolve().parent.parent / "dist"
CLOUDFORMATION_TEMPLATE = Path(__file__).resolve().parent.parent / "cloudformation/lambdas_only.yaml"
STACK_NAME = "lambda-function-stack"
ZIP_PREFIX = "lambda-zips"

def get_bucket_name():
    sts = boto3.client("sts")
    account_id = sts.get_caller_identity()["Account"]
    region = boto3.session.Session().region_name
    return f"rearc-quest-{account_id}-{region}"

def upload_zip_files(bucket_name):
    s3 = boto3.client("s3")
    for zip_file in DIST_DIR.glob("*.zip"):
        key = f"{ZIP_PREFIX}/{zip_file.name}"
        print(f"Uploading {zip_file} to s3://{bucket_name}/{key}")
        with open(zip_file, "rb") as f:
            s3.upload_fileobj(f, bucket_name, key)
    print("All ZIP files uploaded.")

def deploy_lambda_stack(bucket_name):
    cmd = (
        f"aws cloudformation deploy "
        f"--template-file {CLOUDFORMATION_TEMPLATE} "
        f"--stack-name {STACK_NAME} "
        f"--parameter-overrides BucketName={bucket_name} "
        f"--capabilities CAPABILITY_NAMED_IAM"
    )
    subprocess.run(cmd, shell=True, check=True)
    print("Lambda stack deployed successfully.")

def main():
    bucket_name = get_bucket_name()
    print(f"Using S3 bucket: {bucket_name}")
    upload_zip_files(bucket_name)
    deploy_lambda_stack(bucket_name)

if __name__ == "__main__":
    main()