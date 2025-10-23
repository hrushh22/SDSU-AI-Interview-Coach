"""
Interview Orchestrator Lambda Function
Main coordinator for interview sessions
"""
import json
import boto3
import os
import uuid
from datetime import datetime

# AWS Region Configuration
AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
MOCK_MODE = os.environ.get('MOCK_MODE', 'false').lower() == 'true'

# Initialize AWS clients only if not in mock mode
if not MOCK_MODE:
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    lambda_client = boto3.client('lambda', region_name=AWS_REGION)
else:
    # Mock storage for local testing
    MOCK_SESSIONS = {}

TABLE_NAME = os.environ.get('SESSIONS_TABLE', 'InterviewSessions')

# Common interview questions bank from framework
QUESTION_BANK = {
    'behavioral': [
        {
            'question': 'Tell me about a time when you were asked to do something you had never done before. How did you react? What did you learn?',
            'competency': 'adaptability',
            'expected_duration': '2-3 minutes'
        },
        {
            'question': 'Describe a situation where you needed to persuade someone to see things your way. What steps did you take? What were the results?',
            'competency': 'communication',
            'expected_duration': '2-3 minutes'
        },
        {
            'question': 'Tell me about a time when you had to juggle several projects at the same time. How did you organize your time? What was the result?',
            'competency': 'time_management',
            'expected_duration': '2-3 minutes'
        },
        {
            'question': 'Give an example of when you had to work with someone who was difficult to get along with. How did you handle interactions with that person?',
            'competency': 'conflict_resolution',
            'expected_duration': '2-3 minutes'
        },
        {
            'question': 'Tell me about the last time something significant didn\'t go according to plan at work. What was your role? What was the outcome?',
            'competency': 'problem_solving',
            'expected_duration': '2-3 minutes'
        }
    ],
    'tell_me_about': [
        {
            'question': 'Tell me about yourself.',
            'competency': 'self_presentation',
            'expected_duration': '1-2 minutes'
        }
    ],
    'why_this_job': [
        {
            'question': 'Why do you want this job?',
            'competency': 'motivation',
            'expected_duration': '1-2 minutes'
        },
        {
            'question': 'Why should we hire you?',
            'competency': 'value_proposition',
            'expected_duration': '1-2 minutes'
        }
    ]
}


def lambda_handler(event, context):
    """Main orchestrator handler"""
    try:
        # Validate event structure
        if not event or 'body' not in event:
            return error_response(400, "Invalid request format")
            
        body = json.loads(event['body']) if isinstance(event.get('body'), str) else event
        
        # Validate required fields
        if not isinstance(body, dict) or 'action' not in body:
            return error_response(400, "Missing required field: action")
            
        action = body.get('action')
        
        # Validate action
        valid_actions = ['start_session', 'get_question', 'submit_response', 'end_session', 'get_session']
        if action not in valid_actions:
            return error_response(400, f"Invalid action. Must be one of: {valid_actions}")
        
        if action == 'start_session':
            return start_interview_session(body)
        elif action == 'get_question':
            return get_next_question(body)
        elif action == 'submit_response':
            return process_response(body)
        elif action == 'end_session':
            return end_interview_session(body)
        elif action == 'get_session':
            return get_session_data(body)
            
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {str(e)}")
        return error_response(400, "Invalid JSON format")
    except Exception as e:
        print(f"Error in orchestrator: {str(e)}")
        return error_response(500, "Internal server error")


def start_interview_session(body):
    """Initialize a new interview session"""
    try:
        # Validate inputs
        job_description = str(body.get('job_description', ''))[:1000]  # Limit length
        job_title = str(body.get('job_title', ''))[:100]  # Limit length
        practice_mode = body.get('practice_mode', 'question_by_question')
        question_types = body.get('question_types', ['behavioral', 'tell_me_about', 'why_this_job'])
        
        # Validate practice mode
        valid_modes = ['question_by_question', 'full_interview']
        if practice_mode not in valid_modes:
            return error_response(400, f"Invalid practice_mode. Must be one of: {valid_modes}")
        
        # Validate question types
        valid_types = ['behavioral', 'tell_me_about', 'why_this_job']
        if not isinstance(question_types, list) or not all(qt in valid_types for qt in question_types):
            return error_response(400, f"Invalid question_types. Must be list of: {valid_types}")
        
        session_id = str(uuid.uuid4())
        current_time = datetime.utcnow().isoformat()
        
        # Pre-compute question list with job context
        question_list = build_question_list(question_types, job_title, job_description)
        
        session_data = {
            'session_id': session_id,
            'job_description': job_description,
            'job_title': job_title,
            'practice_mode': practice_mode,
            'question_types': question_types,
            'question_list': question_list,  # Pre-computed for performance
            'status': 'active',
            'current_question_index': 0,
            'responses': [],
            'created_at': current_time,
            'updated_at': current_time,
            'ttl': int((datetime.utcnow().timestamp() + 86400 * 30))  # 30 days TTL
        }
        
        # Save to DynamoDB or mock storage
        if MOCK_MODE:
            MOCK_SESSIONS[session_id] = session_data
        else:
            table = dynamodb.Table(TABLE_NAME)
            table.put_item(Item=session_data)
        
        return success_response({
            'session_id': session_id,
            'status': 'active',
            'message': 'Interview session started successfully'
        })
    except Exception as e:
        print(f"Error starting session: {str(e)}")
        return error_response(500, "Failed to start interview session")


def get_next_question(body):
    """Get the next interview question for the session"""
    try:
        # Validate session_id
        session_id = body.get('session_id')
        if not session_id or not isinstance(session_id, str):
            return error_response(400, "Valid session_id is required")
        
        # Retrieve session
        if MOCK_MODE:
            if session_id not in MOCK_SESSIONS:
                return error_response(404, "Session not found")
            session = MOCK_SESSIONS[session_id]
        else:
            table = dynamodb.Table(TABLE_NAME)
            response = table.get_item(Key={'session_id': session_id})
            
            if 'Item' not in response:
                return error_response(404, "Session not found")
            
            session = response['Item']
        
        current_index = session.get('current_question_index', 0)
        question_list = session.get('question_list')
        
        # Use pre-computed question list or build if missing
        if not question_list:
            question_types = session.get('question_types', ['behavioral'])
            job_title = session.get('job_title', '')
            job_description = session.get('job_description', '')
            question_list = build_question_list(question_types, job_title, job_description)
            
            # Save the generated question list to session
            session['question_list'] = question_list
            if MOCK_MODE:
                MOCK_SESSIONS[session_id] = session
            else:
                table = dynamodb.Table(TABLE_NAME)
                table.update_item(
                    Key={'session_id': session_id},
                    UpdateExpression='SET question_list = :ql',
                    ExpressionAttributeValues={':ql': question_list}
                )
        
        # Select question from list based on current index
        if current_index < len(question_list):
            question_data = question_list[current_index]
        else:
            question_data = None
        
        if not question_data:
            return success_response({
                'session_id': session_id,
                'completed': True,
                'message': 'All questions completed'
            })
        
        # Update session with current question and increment index
        session['current_question'] = question_data
        session['current_question_index'] = current_index + 1
        session['updated_at'] = datetime.utcnow().isoformat()
        
        if MOCK_MODE:
            MOCK_SESSIONS[session_id] = session
        else:
            table = dynamodb.Table(TABLE_NAME)
            table.update_item(
                Key={'session_id': session_id},
                UpdateExpression='SET current_question = :q, current_question_index = :i, updated_at = :t',
                ExpressionAttributeValues={
                    ':q': question_data,
                    ':i': current_index + 1,
                    ':t': datetime.utcnow().isoformat()
                }
            )
        
        return success_response({
            'session_id': session_id,
            'question': question_data['question'],
            'question_type': question_data['type'],
            'competency': question_data['competency'],
            'expected_duration': question_data['expected_duration'],
            'question_number': current_index + 1,
            'total_questions': len(question_list)
        })
    except Exception as e:
        print(f"Error getting next question: {str(e)}")
        return error_response(500, "Failed to get next question")


def build_question_list(question_types, job_title="", job_description=""):
    """Build dynamic question list using LLM generation"""
    question_list = []
    
    # Use LLM to generate contextual questions if job info provided
    if job_title and not MOCK_MODE:
        try:
            # Generate questions using feedback generator
            for qtype in question_types:
                if qtype == 'behavioral':
                    competencies = ['problem_solving', 'leadership', 'teamwork', 'communication', 'adaptability']
                    for comp in competencies[:2]:  # Limit to 2 per type
                        question_result = invoke_lambda('feedback_generator', {
                            'action': 'generate_question',
                            'job_description': job_description,
                            'job_title': job_title,
                            'question_type': qtype,
                            'competency': comp
                        })
                        
                        if question_result.get('statusCode') == 200:
                            try:
                                question_body = json.loads(question_result['body'])
                                question_list.append({
                                    'question': question_body.get('question', f"Tell me about a time when you demonstrated {comp} in your work."),
                                    'type': qtype,
                                    'competency': comp,
                                    'expected_duration': '2-3 minutes'
                                })
                            except (json.JSONDecodeError, KeyError):
                                # Fallback to default question
                                question_list.append({
                                    'question': f"Tell me about a time when you demonstrated {comp} in your work.",
                                    'type': qtype,
                                    'competency': comp,
                                    'expected_duration': '2-3 minutes'
                                })
                elif qtype == 'tell_me_about':
                    question_list.append({
                        'question': f"Tell me about yourself and why you're interested in this {job_title} position.",
                        'type': qtype,
                        'competency': 'self_presentation',
                        'expected_duration': '1-2 minutes'
                    })
                elif qtype == 'why_this_job':
                    question_list.append({
                        'question': f"Why do you want to work as a {job_title} at our company?",
                        'type': qtype,
                        'competency': 'motivation',
                        'expected_duration': '1-2 minutes'
                    })
        except Exception as e:
            print(f"Error generating dynamic questions: {str(e)}")
            # Fall back to static questions
            pass
    
    # Fallback to static questions if dynamic generation fails or no job info
    if not question_list:
        for qtype in question_types:
            if qtype in QUESTION_BANK:
                for q in QUESTION_BANK[qtype]:
                    question_list.append({
                        'question': q['question'],
                        'type': qtype,
                        'competency': q['competency'],
                        'expected_duration': q['expected_duration']
                    })
    
    return question_list


def process_response(body):
    """Process candidate's response and generate feedback"""
    try:
        # Validate inputs
        session_id = body.get('session_id')
        if not session_id or not isinstance(session_id, str):
            return error_response(400, "Valid session_id is required")
        
        audio_data = body.get('audio_data')
        if not MOCK_MODE and (not audio_data or not isinstance(audio_data, str)):
            return error_response(400, "Valid audio_data is required")
        
        # Retrieve session data
        if MOCK_MODE:
            if session_id not in MOCK_SESSIONS:
                return error_response(404, "Session not found")
            session = MOCK_SESSIONS[session_id]
        else:
            table = dynamodb.Table(TABLE_NAME)
            response = table.get_item(Key={'session_id': session_id})
            
            if 'Item' not in response:
                return error_response(404, "Session not found")
            
            session = response['Item']
        
        current_question = session.get('current_question', {})
        job_description = session.get('job_description', '')
        resume_text = session.get('resume_text', '')
        
        if MOCK_MODE:
            # Mock response for testing
            return success_response({
                'session_id': session_id,
                'transcript': 'Mock transcript of the response',
                'metrics': {
                    'pace_wpm': 145,
                    'filler_count': 2,
                    'pace_assessment': 'good'
                },
                'feedback': {
                    'strengths': ['Clear communication', 'Good structure'],
                    'improvements': ['Add more specific examples'],
                    'score': 8
                },
                'processed': True
            })
        
        # Step 1: Transcribe audio
        audio_result = invoke_lambda('audio_processor', {
            'action': 'transcribe',
            'audio_data': audio_data,
            'session_id': session_id
        })
        
        if audio_result.get('statusCode') != 200:
            return error_response(500, "Audio transcription failed")
        
        try:
            audio_body = json.loads(audio_result['body'])
            transcript = audio_body.get('transcript', '')
            metrics = audio_body.get('metrics', {})
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            print(f"Error parsing audio processor response: {str(e)}")
            return error_response(500, "Invalid response from audio processor")
        
        # Step 2: Generate feedback
        feedback_result = invoke_lambda('feedback_generator', {
            'action': 'analyze_response',
            'session_id': session_id,
            'question': current_question.get('question', ''),
            'question_type': current_question.get('type', 'behavioral'),
            'response_text': transcript,
            'metrics': metrics,
            'job_description': job_description,
            'resume_text': resume_text
        })
        
        if feedback_result.get('statusCode') != 200:
            return error_response(500, "Feedback generation failed")
        
        try:
            feedback_body = json.loads(feedback_result['body'])
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            print(f"Error parsing feedback generator response: {str(e)}")
            return error_response(500, "Invalid response from feedback generator")
        
        return success_response({
            'session_id': session_id,
            'transcript': transcript,
            'metrics': metrics,
            'feedback': feedback_body.get('feedback', ''),
            'processed': True
        })
    except Exception as e:
        print(f"Error processing response: {str(e)}")
        return error_response(500, "Failed to process response")


def end_interview_session(body):
    """End interview session and generate overall feedback"""
    try:
        # Validate inputs
        session_id = body.get('session_id')
        if not session_id or not isinstance(session_id, str):
            return error_response(400, "Valid session_id is required")
        
        if MOCK_MODE:
            # Mock response
            if session_id not in MOCK_SESSIONS:
                return error_response(404, "Session not found")
            
            MOCK_SESSIONS[session_id]['status'] = 'completed'
            MOCK_SESSIONS[session_id]['completed_at'] = datetime.utcnow().isoformat()
            
            return success_response({
                'session_id': session_id,
                'status': 'completed',
                'overall_feedback': 'Mock overall feedback',
                'total_questions': 3
            })
        
        # Generate overall feedback
        feedback_result = invoke_lambda('feedback_generator', {
            'action': 'overall_feedback',
            'session_id': session_id
        })
        
        if feedback_result.get('statusCode') != 200:
            return error_response(500, "Overall feedback generation failed")
        
        try:
            feedback_body = json.loads(feedback_result['body'])
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            print(f"Error parsing feedback response: {str(e)}")
            return error_response(500, "Invalid response from feedback generator")
        
        # Update session status
        table = dynamodb.Table(TABLE_NAME)
        table.update_item(
            Key={'session_id': session_id},
            UpdateExpression='SET #status = :status, completed_at = :time',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'completed',
                ':time': datetime.utcnow().isoformat()
            }
        )
        
        return success_response({
            'session_id': session_id,
            'status': 'completed',
            'overall_feedback': feedback_body.get('overall_feedback', ''),
            'total_questions': feedback_body.get('total_questions', 0)
        })
    except Exception as e:
        print(f"Error ending session: {str(e)}")
        return error_response(500, "Failed to end interview session")


def get_session_data(body):
    """Retrieve session data"""
    try:
        # Validate inputs
        session_id = body.get('session_id')
        if not session_id or not isinstance(session_id, str):
            return error_response(400, "Valid session_id is required")
        
        if MOCK_MODE:
            if session_id not in MOCK_SESSIONS:
                return error_response(404, "Session not found")
            
            return success_response({
                'session': MOCK_SESSIONS[session_id]
            })
        
        table = dynamodb.Table(TABLE_NAME)
        response = table.get_item(Key={'session_id': session_id})
        
        if 'Item' not in response:
            return error_response(404, "Session not found")
        
        return success_response({
            'session': response['Item']
        })
    except Exception as e:
        print(f"Error getting session data: {str(e)}")
        return error_response(500, "Failed to retrieve session data")


def invoke_lambda(function_name, payload):
    """Invoke another Lambda function"""
    
    if MOCK_MODE:
        return {'statusCode': 500, 'body': json.dumps({'error': 'Lambda invocation not available in mock mode'})}
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        return json.loads(response['Payload'].read())
    except Exception as e:
        print(f"Error invoking {function_name}: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}


def success_response(data):
    """Return success response"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps(data)
    }


def error_response(status_code, message):
    """Return error response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps({
            'error': message
        })
    }