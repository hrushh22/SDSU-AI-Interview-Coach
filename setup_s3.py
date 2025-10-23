import boto3

# Create S3 bucket for audio storage
s3 = boto3.client('s3', region_name='us-west-2')

bucket_name = 'ai-interview-audio-temp'

try:
    s3.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={'LocationConstraint': 'us-west-2'}
    )
    print(f"✅ Created S3 bucket: {bucket_name}")
    
    # Set lifecycle policy to delete files after 1 day
    s3.put_bucket_lifecycle_configuration(
        Bucket=bucket_name,
        LifecycleConfiguration={
            'Rules': [{
                'Id': 'DeleteAfter1Day',
                'Status': 'Enabled',
                'Prefix': 'audio/',
                'Expiration': {'Days': 1}
            }]
        }
    )
    print("✅ Set lifecycle policy to auto-delete after 1 day")
    
except Exception as e:
    print(f"❌ Error: {e}")
