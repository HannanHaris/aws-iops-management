import boto3
import os
import datetime
import json

# Get environment variables
TAG_KEY = os.environ.get('TAG_KEY', 'env')
TAG_VALUE = os.environ.get('TAG_VALUE', 'k8s')
REGIONS = os.environ.get('REGIONS', 'us-east-2').split(',')  # Split comma-separated regions
TARGET_LAMBDA_NAME = "Modify_Volume_When_Triggered"

def get_k8s_instances(region):
    """Fetch all running EC2 instances with the specified tag in a region."""
    ec2_client = boto3.client("ec2", region_name=region)
    instances = []
    response = ec2_client.describe_instances(Filters=[
        {"Name": f"tag:{TAG_KEY}", "Values": [TAG_VALUE]},
        {"Name": "instance-state-name", "Values": ["running"]}
    ])
    
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            instances.append(instance["InstanceId"])
    
    return instances

def get_instance_volumes(region, instance_id):
    """Fetch all volume IDs attached to a given instance in a region."""
    ec2_client = boto3.client("ec2", region_name=region)
    volumes = []
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            for block_device in instance.get("BlockDeviceMappings", []):
                volumes.append(block_device["Ebs"]["VolumeId"])
    
    return volumes

def create_combined_cloudwatch_alarm(region, instance_id, volume_id):
    """Create a single CloudWatch alarm monitoring both metrics in a given region."""
    cloudwatch_client = boto3.client("cloudwatch", region_name=region)
    sts_client = boto3.client("sts", region_name=region)
    account_id = sts_client.get_caller_identity()["Account"]
    
    alarm_name = f"Volume-Metrics-Alarm-{instance_id}-{volume_id}"
    target_lambda_arn = f"arn:aws:lambda:{region}:{account_id}:function:{TARGET_LAMBDA_NAME}"
    
    cloudwatch_client.put_metric_alarm(
        AlarmName=alarm_name,
        EvaluationPeriods=1,
        Threshold=1.0,
        ComparisonOperator="GreaterThanOrEqualToThreshold",
        AlarmActions=[target_lambda_arn],
        TreatMissingData="notBreaching",
        Metrics=[
            {
                "Id": "m1",
                "MetricStat": {
                    "Metric": {
                        "Namespace": "AWS/EBS",
                        "MetricName": "VolumeThroughputExceededCheck",
                        "Dimensions": [
                            {"Name": "InstanceId", "Value": instance_id},
                            {"Name": "VolumeId", "Value": volume_id}
                        ]
                    },
                    "Period": 60,
                    "Stat": "Maximum"
                },
                "ReturnData": False
            },
            {
                "Id": "m2",
                "MetricStat": {
                    "Metric": {
                        "Namespace": "AWS/EBS",
                        "MetricName": "VolumeIOPSExceededCheck",
                        "Dimensions": [
                            {"Name": "InstanceId", "Value": instance_id},
                            {"Name": "VolumeId", "Value": volume_id}
                        ]
                    },
                    "Period": 60,
                    "Stat": "Maximum"
                },
                "ReturnData": False
            },
            {
                "Id": "e1",
                "Expression": "m1 + m2",
                "ReturnData": True
            }
        ]
    )
    print(f"Created combined alarm in {region}: {alarm_name} with target Lambda ARN: {target_lambda_arn}")

def get_terminated_instances(region, last_hours=2):
    """Fetch instances terminated in the last specified hours with the specified tag."""
    cloudtrail_client = boto3.client("cloudtrail", region_name=region)
    end_time = datetime.datetime.utcnow()
    start_time = end_time - datetime.timedelta(hours=last_hours)

    terminated_instances = []
    response = cloudtrail_client.lookup_events(
        LookupAttributes=[
            {"AttributeKey": "EventName", "AttributeValue": "TerminateInstances"}
        ],
        StartTime=start_time,
        EndTime=end_time,
        MaxResults=100
    )

    for event in response["Events"]:
        try:
            resources = event.get("Resources", [])
            for resource in resources:
                if resource["ResourceType"] == "AWS::EC2::Instance":
                    instance_id = resource["ResourceName"]
                    ec2_client = boto3.client("ec2", region_name=region)
                    try:
                        tags_response = ec2_client.describe_tags(
                            Filters=[
                                {"Name": "resource-id", "Values": [instance_id]},
                                {"Name": "key", "Values": [TAG_KEY]},
                                {"Name": "value", "Values": [TAG_VALUE]}
                            ]
                        )
                        if tags_response["Tags"]:
                            terminated_instances.append(instance_id)
                    except ec2_client.exceptions.ClientError as e:
                        print(f"Error checking tags for {instance_id} in {region}: {e}")
        except Exception as e:
            print(f"Error processing event in {region}: {e}")

    return list(set(terminated_instances))

def delete_alarms_for_instance(region, instance_id):
    """Delete CloudWatch alarms associated with the terminated instance in a region."""
    cloudwatch_client = boto3.client("cloudwatch", region_name=region)
    alarms = cloudwatch_client.describe_alarms(
        AlarmNamePrefix=f"Volume-Metrics-Alarm-{instance_id}-"
    )
    
    alarm_names = [alarm["AlarmName"] for alarm in alarms["MetricAlarms"]]
    if alarm_names:
        cloudwatch_client.delete_alarms(AlarmNames=alarm_names)
        print(f"Deleted alarms in {region} for instance {instance_id}: {alarm_names}")
    else:
        print(f"No alarms found in {region} for instance {instance_id}")

def lambda_handler(event, context):
    """AWS Lambda main handler to manage alarms across all regions."""
    print(f"Using tag filter: {TAG_KEY}={TAG_VALUE}")
    print(f"Managing regions: {REGIONS}")
    
    for region in REGIONS:
        print(f"Processing region: {region}")
        
        # Step 1: Set up alarms for running instances
        instances = get_k8s_instances(region)
        for instance in instances:
            volumes = get_instance_volumes(region, instance)
            for volume in volumes:
                create_combined_cloudwatch_alarm(region, instance, volume)
        
        # Step 2: Check for terminated instances and clean up alarms
        terminated_instances = get_terminated_instances(region, last_hours=2)
        for instance_id in terminated_instances:
            print(f"Found terminated instance in {region} with tag {TAG_KEY}:{TAG_VALUE}: {instance_id}")
            delete_alarms_for_instance(region, instance_id)

    return {
        "status": "CloudWatch alarms managed successfully across all regions",
        "terminated_instances": {region: get_terminated_instances(region) for region in REGIONS},
        "tag_key": TAG_KEY,
        "tag_value": TAG_VALUE,
        "regions": REGIONS
    }