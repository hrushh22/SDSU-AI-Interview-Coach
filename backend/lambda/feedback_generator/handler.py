"""
Feedback Generator Lambda Function
Uses AWS Bedrock (Claude) to generate personalized interview feedback
Based on Professor Henry's Interview Framework
"""
import json
import boto3
import os
from datetime import datetime

# AWS Region Configuration
AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
MOCK_MODE = os.environ.get('MOCK_MODE', 'false').lower() == 'true'

# Initialize AWS clients
if not MOCK_MODE:
    bedrock = boto3.client('bedrock-runtime', region_name=AWS_REGION)
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
else:
    bedrock = None
    dynamodb = None

TABLE_NAME = os.environ.get('SESSIONS_TABLE', 'InterviewSessions')
MODEL_ID = 'anthropic.claude-3-5-sonnet-20241022-v2:0'  # Latest Claude model


def lambda_handler(event, context):
    """Generate feedback for interview responses"""
    try:
        # Validate event structure
        if not event or 'body' not in event:
            return error_response(400, "Invalid request format")
            
        body = json.loads(event['body']) if isinstance(event.get('body'), str) else event
        
        # Validate required fields
        if not isinstance(body, dict):
            return error_response(400, "Invalid request body")
            
        action = body.get('action', 'analyze_response')
        
        # Validate action
        valid_actions = ['analyze_response', 'generate_question', 'overall_feedback']
        if action not in valid_actions:
            return error_response(400, f"Invalid action. Must be one of: {valid_actions}")
        
        if action == 'analyze_response':
            return analyze_response(body)
        elif action == 'generate_question':
            return generate_interview_question(body)
        elif action == 'overall_feedback':
            return generate_overall_feedback(body)
            
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {str(e)}")
        return error_response(400, "Invalid JSON format")
    except Exception as e:
        print(f"Error in feedback generator: {str(e)}")
        return error_response(500, "Internal server error")


def analyze_response(body):
    """
    Analyze interview response and generate feedback
    Based on STAR framework and interview best practices
    """
    try:
        # Validate required fields
        session_id = body.get('session_id')
        if not session_id or not isinstance(session_id, str):
            return error_response(400, "Valid session_id is required")
        
        question = body.get('question', '')
        response_text = body.get('response_text', '')
        
        if not question or not response_text:
            return error_response(400, "Question and response_text are required")
        
        # Sanitize and validate inputs
        question_type = body.get('question_type', 'behavioral')
        valid_types = ['behavioral', 'tell_me_about', 'why_this_job']
        if question_type not in valid_types:
            question_type = 'behavioral'
        
        response_metrics = body.get('metrics', {})
        if not isinstance(response_metrics, dict):
            response_metrics = {}
        
        # Limit input lengths to prevent abuse
        job_description = str(body.get('job_description', ''))[:2000]
        resume_text = str(body.get('resume_text', ''))[:2000]
        question = str(question)[:1000]
        response_text = str(response_text)[:5000]
        
        # Build prompt based on question type
        prompt = build_analysis_prompt(
            question=question,
            question_type=question_type,
            response_text=response_text,
            metrics=response_metrics,
            job_description=job_description,
            resume_text=resume_text
        )
        
        # Call Claude via Bedrock or return mock feedback
        if MOCK_MODE:
            feedback = "Mock feedback: Good response structure. Consider adding more specific examples and metrics."
        else:
            feedback = call_claude(prompt)
            
            if not feedback or "Error generating feedback" in feedback:
                return error_response(500, "Failed to generate feedback")
        
        # Save feedback to DynamoDB (skip in mock mode)
        if not MOCK_MODE:
            save_feedback(session_id, question, response_text, feedback, response_metrics)
        
        return success_response({
            'session_id': session_id,
            'feedback': feedback,
            'metrics': response_metrics
        })
    except Exception as e:
        print(f"Error analyzing response: {str(e)}")
        return error_response(500, "Failed to analyze response")


def build_analysis_prompt(question, question_type, response_text, metrics, job_description, resume_text):
    """Build detailed prompt for Claude based on interview framework"""
    
    framework_context = """
You are an expert interview coach following Professor Henry's Interview Framework. Your role is to provide constructive, specific feedback on interview responses.

KEY EVALUATION CRITERIA:
1. Content Quality (50%)
   - Specific examples with concrete details
   - Quantifiable metrics and results
   - Relevance to job requirements
   - Work experience prioritized over classroom examples

2. Delivery Quality (30%)
   - Clarity and confidence
   - Appropriate pace (120-160 WPM is ideal)
   - Minimal filler words (um, uh, like)
   - Concise and structured

3. Framework Adherence (20%)
   - STAR method for behavioral questions
   - Present-Past-Future for "Tell me about yourself"
   - Company research + skills match for "Why this job"

RED FLAGS TO WATCH FOR:
❌ Vague generalizations without specific examples
❌ Negativity about past employers/colleagues
❌ Personal life details (unless explicitly asked)
❌ Wrong motivations (money, work-life balance)
❌ Missing metrics or quantifiable results
❌ No connection to job requirements
"""

    if question_type == 'behavioral':
        framework_guide = """
STAR METHOD EVALUATION:
- Situation: Context/background described?
- Task: Specific responsibility explained?
- Action: Specific actions THEY took (not team)?
- Result: Outcomes shared? Quantifiable?
- Length: Should be 1.5-3 minutes
"""
    elif question_type == 'tell_me_about':
        framework_guide = """
"TELL ME ABOUT YOURSELF" STRUCTURE:
- Present: Major, certifications, leadership relevant to job
- Past: Key experiences and skills relevant to job
- Future: Why excited for THIS specific job
- Length: Should be 1-2 minutes
- Must NOT include: personal life, hobbies, where you grew up
"""
    elif question_type == 'why_this_job':
        framework_guide = """
"WHY THIS JOB" EVALUATION:
- Shows genuine interest in company/job/industry?
- Demonstrates research on position?
- Connects skills/values to company?
- Addresses longevity (won't leave soon)?
- Avoids wrong motivations (money, work-life balance)?
"""
    else:
        framework_guide = "Evaluate based on clarity, relevance, and specificity."

    metrics_context = ""
    if metrics:
        metrics_context = f"""
DELIVERY METRICS:
- Speaking pace: {metrics.get('pace_wpm', 'N/A')} WPM ({metrics.get('pace_assessment', 'N/A')})
- Filler words: {metrics.get('filler_count', 0)} total ({metrics.get('filler_rate', 0)}%)
- Clarity score: {metrics.get('clarity_score', 0)}%
- Long pauses (>2s): {metrics.get('long_pauses', 0)}
- Total words: {metrics.get('total_words', 0)}
- Duration: {metrics.get('duration_seconds', 0)} seconds
"""

    job_context = ""
    if job_description:
        job_context = f"\nJOB DESCRIPTION:\n{job_description[:1000]}\n"

    resume_context = ""
    if resume_text:
        resume_context = f"\nCANDIDATE'S RESUME:\n{resume_text[:1000]}\n"

    prompt = f"""{framework_context}

{framework_guide}

{metrics_context}

{job_context}

{resume_context}

INTERVIEW QUESTION:
{question}

CANDIDATE'S RESPONSE:
{response_text}

TASK:
Provide specific, actionable feedback following this structure:

1. **Overall Assessment** (1-2 sentences)
   - Brief summary of response quality

2. **Content Strengths** (2-3 bullet points)
   - What they did well
   - Specific examples from their response

3. **Content Areas for Improvement** (2-3 bullet points)
   - What's missing or weak
   - Specific suggestions with examples

4. **Delivery Feedback**
   - Comments on pace, clarity, filler words
   - Based on the metrics provided

5. **Revised Answer Suggestion**
   - Provide a brief example of how they could improve 1-2 key parts

6. **Score** (1-5 scale)
   - Content: X/5
   - Delivery: X/5
   - Overall: X/5

Be constructive, specific, and encouraging. Focus on actionable improvements."""

    return prompt


def call_claude(prompt):
    """Call Claude via AWS Bedrock"""
    
    if MOCK_MODE:
        return "Mock Claude response: This is a simulated feedback response for testing purposes."
    
    try:
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "temperature": 0.7,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = bedrock.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        feedback_text = response_body['content'][0]['text']
        
        return feedback_text
        
    except Exception as e:
        print(f"Error calling Bedrock: {str(e)}")
        return f"Error generating feedback: {str(e)}"


def generate_interview_question(body):
    """Generate interview question based on job description and question type"""
    
    job_description = body.get('job_description', '')
    question_type = body.get('question_type', 'behavioral')
    competency = body.get('competency', 'problem-solving')
    
    prompt = f"""You are an expert interviewer. Generate a relevant interview question.

JOB DESCRIPTION:
{job_description[:500]}

QUESTION TYPE: {question_type}
COMPETENCY TO ASSESS: {competency}

Generate ONE interview question that:
1. Is relevant to this specific job
2. Follows the {question_type} format
3. Assesses {competency} competency
4. Is clear and professional

Return only the question text, nothing else."""

    question = call_claude(prompt)
    
    return success_response({
        'question': question.strip(),
        'question_type': question_type,
        'competency': competency
    })


def generate_overall_feedback(body):
    """Generate overall interview performance feedback"""
    try:
        # Validate session_id
        session_id = body.get('session_id')
        if not session_id or not isinstance(session_id, str):
            return error_response(400, "Valid session_id is required")
        
        if MOCK_MODE:
            return success_response({
                'session_id': session_id,
                'overall_feedback': 'Mock overall feedback for testing',
                'total_questions': 3
            })
        
        # Retrieve session data from DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        response = table.get_item(Key={'session_id': session_id})
        
        if 'Item' not in response:
            return error_response(404, "Session not found")
        
        session_data = response['Item']
        responses = session_data.get('responses', [])
        
        # Build summary prompt
        prompt = f"""Provide an overall interview performance summary for a candidate who completed a mock interview.

NUMBER OF QUESTIONS ANSWERED: {len(responses)}

RESPONSES AND FEEDBACK:
"""
        
        for i, resp in enumerate(responses, 1):
            prompt += f"\nQuestion {i}: {resp.get('question', 'N/A')}\n"
            prompt += f"Response: {resp.get('response_text', 'N/A')[:200]}...\n"
            prompt += f"Metrics: {resp.get('metrics', {})}\n"
            prompt += "---\n"
        
        prompt += """
Provide a comprehensive performance summary with:

1. **Overall Performance** (2-3 sentences)
2. **Key Strengths** (3-4 points)
3. **Areas for Improvement** (3-4 points)
4. **Delivery Patterns** (pace, filler words, clarity trends)
5. **Top 3 Action Items** for next practice session
6. **Overall Scores**:
   - Content Quality: X/5
   - Delivery Quality: X/5
   - Job Fit: X/5
   - Overall Readiness: X/5

Be encouraging but honest."""

        overall_feedback = call_claude(prompt)
        
        # Update session with overall feedback
        table.update_item(
            Key={'session_id': session_id},
            UpdateExpression='SET overall_feedback = :feedback, completed_at = :time',
            ExpressionAttributeValues={
                ':feedback': overall_feedback,
                ':time': datetime.utcnow().isoformat()
            }
        )
        
        return success_response({
            'session_id': session_id,
            'overall_feedback': overall_feedback,
            'total_questions': len(responses)
        })
    except Exception as e:
        print(f"Error generating overall feedback: {str(e)}")
        return error_response(500, "Failed to generate overall feedback")


def save_feedback(session_id, question, response_text, feedback, metrics):
    """Save feedback to DynamoDB"""
    if MOCK_MODE:
        return  # Skip saving in mock mode
        
    try:
        # Validate inputs
        if not session_id or not isinstance(session_id, str):
            raise ValueError("Invalid session_id")
            
        table = dynamodb.Table(TABLE_NAME)
        
        # Sanitize data before saving
        response_data = {
            'question': str(question)[:1000],
            'response_text': str(response_text)[:5000],
            'feedback': str(feedback)[:10000],
            'metrics': metrics if isinstance(metrics, dict) else {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Append to responses array
        table.update_item(
            Key={'session_id': session_id},
            UpdateExpression='SET responses = list_append(if_not_exists(responses, :empty_list), :new_response)',
            ExpressionAttributeValues={
                ':new_response': [response_data],
                ':empty_list': []
            }
        )
    except Exception as e:
        print(f"Error saving feedback: {str(e)}")
        raise e


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