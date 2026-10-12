import boto3
import json
import os
import datetime

# Initialize clients
region = os.environ['AWS_REGION']
ec2_client = boto3.client('ec2', region_name=region)
cloudwatch_client = boto3.client('cloudwatch', region_name=region)
sns_client = boto3.client('sns', region_name=region)

# SNS Topic ARN (Replace with your actual SNS topic ARN)
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']

def get_metric_data(metric_name, volume_id, instance_id):
    """ Fetch CloudWatch metric data for the given EBS volume """
    end_time = datetime.datetime.utcnow()
    start_time = end_time - datetime.timedelta(minutes=2)  # Look at last 2 minutes

    response = cloudwatch_client.get_metric_data(
        MetricDataQueries=[
            {
                'Id': 'metric_query',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/EBS',
                        'MetricName': metric_name,
                        'Dimensions': [
                            {'Name': 'InstanceId', 'Value': instance_id},
                            {'Name': 'VolumeId', 'Value': volume_id}
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Maximum'
                },
                'ReturnData': True
            }
        ],
        StartTime=start_time,
        EndTime=end_time
    )

    data_points = response.get("MetricDataResults", [])[0].get("Values", [])
    return data_points[0] if data_points else None  # Return latest value

def modify_volume_throughput(volume_id, current_throughput):
    """ Double the throughput of the EBS volume """
    new_throughput = current_throughput * 2
    ec2_client.modify_volume(
        VolumeId=volume_id,
        Throughput=new_throughput
    )
    print(f"Throughput for volume {volume_id} doubled to {new_throughput} MB/s")
    return new_throughput

def modify_volume_iops(volume_id, current_iops):
    """ Add 3000 IOPS to the EBS volume """
    new_iops = current_iops + 3000
    ec2_client.modify_volume(
        VolumeId=volume_id,
        Iops=new_iops
    )
    print(f"IOPS for volume {volume_id} increased by 3000 to {new_iops}")
    return new_iops

def send_sns_alert(message):
    """ Send an SNS alert with the given message """
    sns_client.publish(
        TopicArn=SNS_TOPIC_ARN,
        Message=message,
        Subject="EBS Volume Adjustment Alert"
    )
    print(f"SNS alert sent: {message}")

def lambda_handler(event, context):
    print("Event received:", json.dumps(event, indent=4))  # Log the event

    try:
        # Extract instance ID and volume ID from the event
        alarm_data = event.get('alarmData', {})
        metrics = alarm_data.get('configuration', {}).get('metrics', [])
        
        if not metrics:
            print("No metrics found in alarm data.")
            return {'statusCode': 400, 'body': 'Invalid event structure'}
        
        dimensions = metrics[0].get('metricStat', {}).get('metric', {}).get('dimensions', {})
        instance_id = dimensions.get('InstanceId')
        volume_id = dimensions.get('VolumeId')
        
        if not instance_id or not volume_id:
            print("Instance ID or Volume ID not found in the event.")
            return {'statusCode': 400, 'body': 'Missing Instance ID or Volume ID'}
        
        print(f"Instance ID: {instance_id}, Volume ID: {volume_id}")

        # Fetch individual metric values
        m1_value = get_metric_data("VolumeThroughputExceededCheck", volume_id, instance_id)
        m2_value = get_metric_data("VolumeIOPSExceededCheck", volume_id, instance_id)

        # Print results
        print(f"Latest VolumeThroughputExceededCheck (m1): {m1_value}")
        print(f"Latest VolumeIOPSExceededCheck (m2): {m2_value}")

        # Fetch current volume configuration
        volume_info = ec2_client.describe_volumes(VolumeIds=[volume_id])
        current_throughput = volume_info['Volumes'][0].get('Throughput', 0)
        current_iops = volume_info['Volumes'][0]['Iops']

        # Modify volume based on metric values
        if m1_value == 1 and m2_value == 0:
            new_throughput = modify_volume_throughput(volume_id, current_throughput)
            message = f"EC2 Instance {instance_id} - EBS Volume {volume_id} throughput doubled to {new_throughput} MB/s."
            send_sns_alert(message)
        elif m1_value == 0 and m2_value == 1:
            new_iops = modify_volume_iops(volume_id, current_iops)
            message = f"EC2 Instance {instance_id} - EBS Volume {volume_id} IOPS increased by 3000 to {new_iops}."
            send_sns_alert(message)
        else:
            print("No action required. Both metrics are within limits.")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "VolumeThroughputExceededCheck": m1_value,
                "VolumeIOPSExceededCheck": m2_value,
                "CurrentThroughput": current_throughput,
                "CurrentIOPS": current_iops
            })
        }
    
    except Exception as e:
        print(f"Error: {e}")
        return {'statusCode': 500, 'body': str(e)}