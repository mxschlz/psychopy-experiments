import boto3

ACCOUNT_ID = "YOUR_CLOUDFLARE_ACCOUNT_ID"       # Find this on the right side of the R2 dashboard
ACCESS_KEY = "YOUR_R2_ACCESS_KEY_ID"            # Access Key ID from token
SECRET_KEY = "YOUR_R2_SECRET_ACCESS_KEY"        # Secret Access Key from token
BUCKET_NAME = "spacecue-stimuli"                # The exact name of the bucket you created

s3 = boto3.client(
    "s3",
    endpoint_url=f"https://{ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name="auto",
)

cors_configuration = {
    'CORSRules': [{
        'AllowedHeaders': ['*'],
        'AllowedMethods': ['GET', 'HEAD'],
        'AllowedOrigins': ['*'],
        'ExposeHeaders': []
    }]
}

try:
    s3.put_bucket_cors(Bucket=BUCKET_NAME, CORSConfiguration=cors_configuration)
    print("Successfully updated CORS policy for bucket!")
except Exception as e:
    print(f"Failed to update CORS: {e}")
