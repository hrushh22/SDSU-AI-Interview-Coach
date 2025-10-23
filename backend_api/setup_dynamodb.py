import boto3

def setup_dynamodb():
    """Create DynamoDB table for interview sessions"""
    dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
    
    try:
        table = dynamodb.create_table(
            TableName='InterviewSessions',
            KeySchema=[
                {'AttributeName': 'session_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'session_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        print("Creating table...")
        table.wait_until_exists()
        print("✅ DynamoDB table 'InterviewSessions' created successfully!")
        
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        print("✅ Table 'InterviewSessions' already exists")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    setup_dynamodb()
