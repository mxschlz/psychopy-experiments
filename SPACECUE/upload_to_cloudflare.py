import os
import boto3
from concurrent.futures import ThreadPoolExecutor

# =========================================================================
# CONFIGURATION
# 1. Fill in these 4 variables with your Cloudflare R2 credentials.
#    You can generate an API Token in the Cloudflare Dashboard under R2 -> Manage R2 API Tokens.
# =========================================================================

ACCOUNT_ID = "6d8e0be23f9278f65f2bc87c5ad5c482"       # Find this on the right side of the R2 dashboard
ACCESS_KEY = "0f89535d8d420905b5d971e1704d83e9"            # Access Key ID from token
SECRET_KEY = "c1b059d6b1f653186f3c840a51a0f9b4064a830de664b915b0f7b648ed19f496"        # Secret Access Key from token
BUCKET_NAME = "spacecue-stimuli"                # The exact name of the bucket you created

# =========================================================================

s3 = boto3.client(
    "s3",
    endpoint_url=f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name="auto",
)

def upload_file(local_path, s3_key):
    print(f"Uploading {s3_key}...")
    try:
        content_type = "audio/wav" if local_path.endswith(".wav") else "text/csv"
        s3.upload_file(local_path, BUCKET_NAME, s3_key, ExtraArgs={"ContentType": content_type})
    except Exception as e:
        print(f"Failed to upload {local_path}: {e}")

def main():
    folders_to_upload = ["sequences", "screening_stimuli", "stimuli/targets_low_30_Hz", "stimuli/digits_all_250ms"]
    files_to_upload = []
    
    for folder in folders_to_upload:
        if not os.path.exists(folder):
            print(f"Warning: Folder '{folder}' not found.")
            continue
            
        for root, _, files in os.walk(folder):
            for file in files:
                local_path = os.path.join(root, file)
                # Ensure forward slashes for URL paths on Cloudflare
                s3_key = local_path.replace(os.sep, "/")
                files_to_upload.append((local_path, s3_key))
                
    print(f"Found {len(files_to_upload)} files to upload to bucket '{BUCKET_NAME}'.")
    print("Starting concurrent upload...")
    
    # Upload concurrently with 30 threads for maximum speed
    with ThreadPoolExecutor(max_workers=30) as executor:
        for local_path, s3_key in files_to_upload:
            executor.submit(upload_file, local_path, s3_key)
            
    print("Upload complete!")

if __name__ == "__main__":
    main()
