import argparse
import json
import os
import time
import boto3
from botocore.exceptions import ClientError
from git import Repo

# ----------------------------------------------------
# CONFIGURATION & GLOBAL INITIALIZATION
# ----------------------------------------------------
UNIQUE_ID = "evangadi-s3-practice"

s3_client = boto3.client('s3', region_name='us-east-1')
iam_client = boto3.client('iam')

def create_us_east_1_bucket(bucket_name):
    try:
        s3_client.create_bucket(Bucket=bucket_name)
        print(f"✅ Created bucket: {bucket_name}")
    except ClientError as e:
        print(f"❌ Error creating bucket {bucket_name}: {e}")

# ----------------------------------------------------
# INDIVIDUAL TASK FUNCTIONS
# ----------------------------------------------------
def run_task_1():
    print("\n--- Task 1: Uploading a Photo to an Isolated Bucket ---")
    t1_bucket = f"task1-photo-bucket-{UNIQUE_ID}"
    create_us_east_1_bucket(t1_bucket)

    local_photo_path = "sample_photo.jpg"
    with open(local_photo_path, "wb") as f:
        f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00')

    try:
        s3_client.upload_file(local_photo_path, t1_bucket, "vacation_photo.jpg", ExtraArgs={'ContentType': 'image/jpeg'})
        print(f"✅ Successfully uploaded '{local_photo_path}' as 'vacation_photo.jpg' to {t1_bucket}")
    except ClientError as e:
        print(f"❌ Photo upload failed: {e}")

def run_task_2():
    print("\n--- Task 2: Testing Encryption Restrictions on a Dedicated Bucket ---")
    t2_bucket = f"task2-encryption-bucket-{UNIQUE_ID}"
    create_us_east_1_bucket(t2_bucket)

    encryption_policy = {
       "Version": "2012-10-17",
       "Statement": [
          {
             "Sid": "DenyUnencryptedUploads",
             "Effect": "Deny",
             "Principal": "*",
             "Action": "s3:PutObject",
             "Resource": f"arn:aws:s3:::{t2_bucket}/*",
             "Condition": {
                "StringNotEquals": {
                   "s3:x-amz-server-side-encryption": "AES256"
                }
             }
          }
       ]
    }

    s3_client.put_bucket_policy(Bucket=t2_bucket, Policy=json.dumps(encryption_policy))
    print("Attached strict encryption policy.")

    try:
        s3_client.put_object(Bucket=t2_bucket, Key="plain.txt", Body="This should be blocked.")
        print("❌ Test Failed: Unencrypted upload unexpectedly went through!")
    except ClientError:
        print("✅ Test Passed: Unencrypted upload was blocked (AccessDenied).")

    try:
        s3_client.put_object(Bucket=t2_bucket, Key="secure.txt", Body="Secured data.", ServerSideEncryption="AES256")
        print("✅ Test Passed: Encrypted upload (AES256) succeeded.")
    except ClientError as e:
        print(f"❌ Test Failed: Encrypted upload was blocked: {e}")   

def run_task_3():
    print("\n--- Task 3: Deploying Full Web Layout Directly From GitHub ---")
    
    # CONFIGURATION: GitHub repository URL!
    GITHUB_REPO_URL = "https://github.com/RuthZinabu/Evangadi-S3-Tasks.git"
    
    t3_bucket = f"task3-website-bucket-{UNIQUE_ID}"
    create_us_east_1_bucket(t3_bucket)

    # Disable Block Public Access
    s3_client.put_public_access_block(
        Bucket=t3_bucket,
        PublicAccessBlockConfiguration={
            'BlockPublicAcls': False, 'IgnorePublicAcls': False,
            'BlockPublicPolicy': False, 'RestrictPublicBuckets': False
        }
    )

    # Apply Public Read Policy
    public_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": f"arn:aws:s3:::{t3_bucket}/*"
        }]
    }
    s3_client.put_bucket_policy(Bucket=t3_bucket, Policy=json.dumps(public_policy))

    # 🌟 NEW CODE: Clone the repository locally
    web_folder = "cloned_github_website"
    
    # Clean up the folder if it already exists from a previous run
    if os.path.exists(web_folder):
        import shutil
        shutil.rmtree(web_folder, ignore_errors=True)
        
    print(f"Cloning codebase from {GITHUB_REPO_URL}...")
    try:
        Repo.clone_from(GITHUB_REPO_URL, web_folder)
        print("Cloning complete.")
    except Exception as e:
        print(f"❌ Failed to clone repository: {e}")
        return

    # Walk the downloaded repo folder and upload all assets to S3
    content_types = {
        '.html': 'text/html', 
        '.css': 'text/css', 
        '.js': 'application/javascript',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.svg': 'image/svg+xml'
    }
    
    for root, dirs, files in os.walk(web_folder):
        # Skip git internal tracking files so they don't get uploaded to your website
        if '.git' in root:
            continue
            
        for file in files:
            local_file_path = os.path.join(root, file)
            # Determine the S3 key structure path relative to the root clone path
            s3_key = os.path.relpath(local_file_path, web_folder).replace("\\", "/")
            _, ext = os.path.splitext(file)
            mime_type = content_types.get(ext.lower(), 'binary/octet-stream')
            
            s3_client.upload_file(local_file_path, t3_bucket, s3_key, ExtraArgs={'ContentType': mime_type})
            print(f"Uploaded asset: {s3_key} ({mime_type})")

    # Set S3 website entry point configuration
    s3_client.put_bucket_website(Bucket=t3_bucket, WebsiteConfiguration={'IndexDocument': {'Suffix': 'index.html'}})
    print(f"✅ GitHub Site is now Live! URL: http://{t3_bucket}.s3-website-us-east-1.amazonaws.com")

def run_task_4():
    print("\n--- Task 4: Testing Versioning Lifecycle Followed by Immediate Destruction ---")
    t4_bucket = f"task4-ephemeral-bucket-{UNIQUE_ID}"
    create_us_east_1_bucket(t4_bucket)

    s3_client.put_bucket_versioning(Bucket=t4_bucket, VersioningConfiguration={'Status': 'Enabled'})
    s3_client.put_object(Bucket=t4_bucket, Key="lifecycle.txt", Body="Version A")
    s3_client.put_object(Bucket=t4_bucket, Key="lifecycle.txt", Body="Version B")
    print("Enabled versioning and uploaded multiple object revisions.")

    # print(f"Cleaning out version history logs inside {t4_bucket}...")
    # v_response = s3_client.list_object_versions(Bucket=t4_bucket)
    # if 'Versions' in v_response:
    #     for item in v_response['Versions']:
    #         s3_client.delete_object(Bucket=t4_bucket, Key=item['Key'], VersionId=item['VersionId'])
    # if 'DeleteMarkers' in v_response:
    #     for marker in v_response['DeleteMarkers']:
    #         s3_client.delete_object(Bucket=t4_bucket, Key=marker['Key'], VersionId=marker['VersionId'])

    # s3_client.delete_bucket(Bucket=t4_bucket)
    # print(f"✅ Safely removed task 4 bucket: {t4_bucket}")

def run_task_5():
    print("\n--- Task 5: Dynamic Provisioning of CRR Rules & Associated IAM Security Roles ---")
    t5_src_bucket = f"task5-source-bucket-{UNIQUE_ID}"
    t5_dst_bucket = f"task5-replica-bucket-{UNIQUE_ID}"

    create_us_east_1_bucket(t5_src_bucket)
    s3_west_client = boto3.client('s3', region_name='us-east-2')
    try:
        s3_west_client.create_bucket(Bucket=t5_dst_bucket, CreateBucketConfiguration={'LocationConstraint': 'us-east-2'})
        print(f"✅ Created replica bucket: {t5_dst_bucket} (us-east-2)")
    except ClientError as e:
        print(f"❌ Error creating destination bucket: {e}")

    s3_client.put_bucket_versioning(Bucket=t5_src_bucket, VersioningConfiguration={'Status': 'Enabled'})
    s3_west_client.put_bucket_versioning(Bucket=t5_dst_bucket, VersioningConfiguration={'Status': 'Enabled'})

    role_name = f"S3ReplicationExecutionRole-{UNIQUE_ID}"
    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "s3.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }

    replication_permissions = {
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Allow", "Action": ["s3:GetReplicationConfiguration", "s3:ListBucket"], "Resource": f"arn:aws:s3:::{t5_src_bucket}"},
            {"Effect": "Allow", "Action": ["s3:GetObjectVersionForReplication", "s3:GetObjectVersionAcl", "s3:GetObjectVersionTagging"], "Resource": f"arn:aws:s3:::{t5_src_bucket}/*"},
            {"Effect": "Allow", "Action": ["s3:ReplicateObject", "s3:ReplicateDelete", "s3:ReplicateTags"], "Resource": f"arn:aws:s3:::{t5_dst_bucket}/*"}
        ]
    }

    try:
        role_arn = iam_client.create_role(RoleName=role_name, AssumeRolePolicyDocument=json.dumps(assume_role_policy))['Role']['Arn']
        iam_client.put_role_policy(RoleName=role_name, PolicyName="S3ReplicationPolicy", PolicyDocument=json.dumps(replication_permissions))
        print(f"✅ Synthesized IAM Execution Role dynamically: {role_arn}")
        print("Waiting 10s for IAM propagation consistency...")
        time.sleep(10)
        
         replication_config = {
            'Role': role_arn,
            'Rules': [{
                'ID': 'CrossRegionReplicationRule', 
                'Status': 'Enabled', 
                'Priority': 1,
                'Filter': {'Prefix': ''},
                'DeleteMarkerReplication': {
                    'Status': 'Disabled'
                },
                'Destination': {
                    'Bucket': f'arn:aws:s3:::{t5_dst_bucket}'
                }
            }]
        }
        s3_client.put_bucket_replication(Bucket=t5_src_bucket, ReplicationConfiguration=replication_config)
        print("✅ Cross-Region Replication initialized successfully between source and target components.")
    except ClientError as e:
        print(f"❌ IAM or Replication binding sequence interrupted: {e}")

def run_task_6():
    print("\n--- Task 6: Custom Storage Tier Profiles & Final Public Broadcast Layout ---")
    t6_bucket = f"task6-storage-bucket-{UNIQUE_ID}"
    create_us_east_1_bucket(t6_bucket)

    s3_client.put_object(Bucket=t6_bucket, Key="archive_candidate.dat", Body="Cold metadata archive.", StorageClass="STANDARD_IA")
    print("Targeted entry committed straight onto STANDARD_IA layer.")

    lifecycle_rules = {
        'Rules': [{
            'ID': 'DeepArchiveTransition', 'Status': 'Enabled', 'Filter': {'Prefix': ''},
            'Transitions': [{'Days': 30, 'StorageClass': 'GLACIER'}]
        }]
    }
    s3_client.put_bucket_lifecycle_configuration(Bucket=t6_bucket, LifecycleConfiguration=lifecycle_rules)
    print("Configured lifecycle rotation matrix to GLACIER tier (30 Day execution threshold).")

    s3_client.put_public_access_block(Bucket=t6_bucket,PublicAccessBlockConfiguration={'BlockPublicAcls': False, 'IgnorePublicAcls': False,'BlockPublicPolicy': False, 'RestrictPublicBuckets': False})
    s3_client.put_bucket_policy(Bucket=t6_bucket, Policy=json.dumps({"Version": "2012-10-17","Statement": [{"Sid": "MakeAllObjectsPubliclyReadable", "Effect": "Allow", "Principal": "","Action": "s3:GetObject", "Resource": f"arn:aws:s3:::{t6_bucket}/"}]}))
    print("✅ Universal read permission successfully applied across the whole storage block scope.")

# 🌟 ADDED ENTRYPOINT EXECUTOR (This fixes the missing output!)
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run specific S3 Practice Labs.")
    parser.add_argument(
        '--task',
        type=str,
        required=True,
        choices=['1', '2', '3', '4', '5', '6', 'all'],
        help="Task ID to execute (1-6) or 'all'."
    )
    args = parser.parse_args()

    if args.task == '1' or args.task == 'all':
        run_task_1()
    if args.task == '2' or args.task == 'all':
        run_task_2()
    if args.task == '3' or args.task == 'all':
        run_task_3()
    if args.task == '4' or args.task == 'all':
        run_task_4()
    if args.task == '5' or args.task == 'all':
        run_task_5()
    if args.task == '6' or args.task == 'all':
        run_task_6()
