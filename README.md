# Evangadi-S3-Tasks
# 1. Delete the stuck IAM Role using the AWS CLI
aws iam delete-role-policy --role-name S3ReplicationExecutionRole-evangadi-s3-practice-v2 --policy-name S3ReplicationPolicy
aws iam delete-role --role-name S3ReplicationExecutionRole-evangadi-s3-practice-v2

# 2. Delete the source bucket (from us-east-1)
aws s3 rb s3://task5-source-bucket-evangadi-s3-practice-v2 --force

# 3. Delete the replica destination bucket (from us-east-2)
aws s3 rb s3://task5-replica-bucket-evangadi-s3-practice-v2 --force --region us-east-2

        # 🌟 FIXED: Moved DeleteMarkerReplication to its proper location at the Rule level
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


# 1. Create a quick verification file
echo "Testing Cross-Region Replication Live!" > replication-test.txt

# 2. Upload it to the SOURCE bucket
aws s3 cp replication-test.txt s3://task5-source-bucket-evangadi-s3-practice-v2/replication-test.txt
aws s3 ls s3://task5-replica-bucket-evangadi-s3-practice-v2 --region us-east-2
aws s3api get-bucket-replication --bucket task5-source-bucket-evangadi-s3-practice-v2

        }

