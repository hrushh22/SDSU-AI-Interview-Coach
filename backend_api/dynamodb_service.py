import boto3
from datetime import datetime
from typing import Dict, Any, List
import uuid

dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
TABLE_NAME = 'InterviewSessions'

def create_table_if_not_exists():
    """Create DynamoDB table if it doesn't exist"""
    try:
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'session_id', 'KeyType': 'HASH'},
            ],
            AttributeDefinitions=[
                {'AttributeName': 'session_id', 'AttributeType': 'S'},
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        table.wait_until_exists()
        return True
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        return True
    except Exception as e:
        print(f"Error creating table: {e}")
        return False

def create_session(job_title: str, job_description: str, resume_text: str) -> str:
    """Create a new interview session"""
    table = dynamodb.Table(TABLE_NAME)
    session_id = str(uuid.uuid4())
    
    table.put_item(Item={
        'session_id': session_id,
        'job_title': job_title,
        'job_description': job_description,
        'resume_text': resume_text,
        'conversations': [],
        'created_at': datetime.utcnow().isoformat(),
        'status': 'active'
    })
    
    return session_id

def add_conversation(session_id: str, question: str, answer: str, feedback: str, metrics: Dict[str, Any]):
    """Add a conversation turn to the session"""
    try:
        table = dynamodb.Table(TABLE_NAME)
        
        conversation = {
            'timestamp': datetime.utcnow().isoformat(),
            'question': question,
            'answer': answer,
            'feedback': feedback,
            'metrics': metrics
        }
        
        response = table.get_item(Key={'session_id': session_id})
        item = response.get('Item', {})
        
        if not item:
            print(f"Warning: Session {session_id} not found, creating minimal session")
            # Create minimal session if it doesn't exist
            table.put_item(Item={
                'session_id': session_id,
                'conversations': [conversation],
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'status': 'active'
            })
            return
        
        conversations = item.get('conversations', [])
        conversations.append(conversation)
        
        table.update_item(
            Key={'session_id': session_id},
            UpdateExpression='SET conversations = :c, updated_at = :u',
            ExpressionAttributeValues={
                ':c': conversations,
                ':u': datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        print(f"Error adding conversation: {e}")
        raise

def get_session(session_id: str) -> Dict[str, Any]:
    """Retrieve a session by ID"""
    table = dynamodb.Table(TABLE_NAME)
    response = table.get_item(Key={'session_id': session_id})
    return response.get('Item', {})

def complete_session(session_id: str):
    """Mark session as complete"""
    table = dynamodb.Table(TABLE_NAME)
    table.update_item(
        Key={'session_id': session_id},
        UpdateExpression='SET #status = :s, completed_at = :c',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':s': 'completed',
            ':c': datetime.utcnow().isoformat()
        }
    )

def get_conversation_history(session_id: str) -> List[Dict[str, Any]]:
    """Get all conversations for a session"""
    session = get_session(session_id)
    return session.get('conversations', [])
