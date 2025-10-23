"""
Resume Analyzer Lambda Function
Extracts text from resumes using AWS Textract OCR or direct text input
"""
import json
import os
import re
from datetime import datetime
import boto3

AWS_REGION = os.environ.get('AWS_REGION', 'us-west-2')
MOCK_MODE = os.environ.get('MOCK_MODE', 'false').lower() == 'true'

# Initialize clients only if not in mock mode
if not MOCK_MODE:
    textract = boto3.client('textract', region_name=AWS_REGION)
    s3 = boto3.client('s3', region_name=AWS_REGION)
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

BUCKET_NAME = os.environ.get('RESUME_BUCKET', 'interview-coach-resumes')
TABLE_NAME = os.environ.get('SESSIONS_TABLE', 'InterviewSessions')


def lambda_handler(event, context):
    """Main handler for resume analysis"""
    try:
        # Validate event structure
        if not event or 'body' not in event:
            return error_response(400, "Invalid request format")
            
        body = json.loads(event['body']) if isinstance(event.get('body'), str) else event
        
        # Validate required fields
        if not isinstance(body, dict):
            return error_response(400, "Invalid request body")
            
        action = body.get('action', 'analyze')
        
        # Validate action
        valid_actions = ['analyze', 'analyze_text', 'extract_skills']
        if action not in valid_actions:
            return error_response(400, f"Invalid action. Must be one of: {valid_actions}")
        
        if action == 'analyze':
            return analyze_resume(body)
        elif action == 'analyze_text':
            return analyze_resume_text(body)
        elif action == 'extract_skills':
            return extract_skills(body)
            
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {str(e)}")
        return error_response(400, "Invalid JSON format")
    except Exception as e:
        print(f"Error in resume analyzer: {str(e)}")
        return error_response(500, "Internal server error")


def analyze_resume_text(body):
    """Analyze resume from plain text (no OCR needed)"""
    try:
        # Validate inputs
        session_id = body.get('session_id')
        if not session_id or not isinstance(session_id, str):
            return error_response(400, "Valid session_id is required")
        
        resume_text = body.get('resume_text', '')
        if not resume_text or not isinstance(resume_text, str):
            return error_response(400, "Valid resume_text is required")
        
        # Limit text length to prevent abuse
        if len(resume_text) > 50000:  # 50KB limit
            return error_response(400, "Resume text too long (max 50KB)")
        
        # Sanitize text
        resume_text = resume_text.strip()
        
        # Parse resume content
        parsed_resume = parse_resume_content(resume_text)
        
        # Save to DynamoDB (skip in mock mode)
        if not MOCK_MODE:
            table = dynamodb.Table(TABLE_NAME)
            table.update_item(
                Key={'session_id': session_id},
                UpdateExpression='SET resume_text = :text, resume_data = :data, updated_at = :time',
                ExpressionAttributeValues={
                    ':text': resume_text,
                    ':data': parsed_resume,
                    ':time': datetime.utcnow().isoformat()
                }
            )
        
        return success_response({
            'session_id': session_id,
            'resume_text': resume_text,
            'parsed_data': parsed_resume
        })
    except Exception as e:
        print(f"Error analyzing resume text: {str(e)}")
        return error_response(500, "Failed to analyze resume text")


def analyze_resume(body):
    """Analyze resume using Textract OCR"""
    try:
        if MOCK_MODE:
            return error_response(400, "Textract not available in mock mode. Use 'analyze_text' action instead.")
        
        # Validate inputs
        session_id = body.get('session_id')
        if not session_id or not isinstance(session_id, str):
            return error_response(400, "Valid session_id is required")
        
        resume_data = body.get('resume_data')
        if not resume_data or not isinstance(resume_data, str):
            return error_response(400, "Valid resume_data is required")
        
        # Implementation would go here for production
        return error_response(501, "Textract analysis not implemented in this version")
    except Exception as e:
        print(f"Error in analyze_resume: {str(e)}")
        return error_response(500, "Failed to analyze resume")


def parse_resume_content(text):
    """Parse resume content into structured data"""
    try:
        if not text or not isinstance(text, str):
            return {'education': [], 'experience': [], 'skills': [], 'contact': {}}
        
        sections = {
            'education': [],
            'experience': [],
            'skills': [],
            'contact': {}
        }
        
        lines = text.split('\n')
        current_section = None
        
        # Keywords for section detection
        education_keywords = ['education', 'academic', 'degree', 'university', 'college', 'school']
        experience_keywords = ['experience', 'employment', 'work history', 'professional', 'career']
        skills_keywords = ['skills', 'technical skills', 'competencies', 'expertise', 'technologies']
        
        for line in lines:
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            
            if not line_stripped:
                continue
            
            # Detect sections (look for section headers)
            if any(keyword in line_lower for keyword in education_keywords) and len(line_stripped) < 50:
                current_section = 'education'
                continue
            elif any(keyword in line_lower for keyword in experience_keywords) and len(line_stripped) < 50:
                current_section = 'experience'
                continue
            elif any(keyword in line_lower for keyword in skills_keywords) and len(line_stripped) < 50:
                current_section = 'skills'
                continue
            
            # Add content to current section
            if current_section and line_stripped:
                sections[current_section].append(line_stripped)
            
            # Extract email using regex
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            email_match = re.search(email_pattern, line)
            if email_match:
                sections['contact']['email'] = email_match.group()
            
            # Extract phone using regex (various formats)
            phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
            phone_match = re.search(phone_pattern, line)
            if phone_match:
                sections['contact']['phone'] = phone_match.group()
        
        return sections
    except Exception as e:
        print(f"Error parsing resume content: {str(e)}")
        return {'education': [], 'experience': [], 'skills': [], 'contact': {}}


def extract_skills(body):
    """Extract skills from resume text using keyword matching"""
    try:
        # Validate input
        text = body.get('resume_text', '')
        
        if not text or not isinstance(text, str):
            return error_response(400, "Valid resume_text is required")
        
        # Limit text length
        if len(text) > 50000:
            return error_response(400, "Resume text too long (max 50KB)")
        
        # Comprehensive technical skills list
        tech_skills = {
            'Programming Languages': [
                'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'Go', 'Rust',
                'Ruby', 'PHP', 'Swift', 'Kotlin', 'Scala', 'R', 'MATLAB', 'SQL'
            ],
            'Web Technologies': [
                'React', 'Angular', 'Vue.js', 'Node.js', 'Express', 'Django', 'Flask',
                'Spring Boot', 'HTML', 'CSS', 'REST API', 'GraphQL', 'WebSockets'
            ],
            'Cloud & DevOps': [
                'AWS', 'Azure', 'Google Cloud', 'Docker', 'Kubernetes', 'Jenkins',
                'GitLab CI', 'GitHub Actions', 'Terraform', 'Ansible', 'CircleCI'
            ],
            'Databases': [
                'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'DynamoDB', 'Cassandra',
                'Oracle', 'SQL Server', 'Elasticsearch', 'Neo4j'
            ],
            'Data & ML': [
                'Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch', 'Scikit-learn',
                'Pandas', 'NumPy', 'Data Analysis', 'Data Science', 'NLP', 'Computer Vision'
            ],
            'Soft Skills': [
                'Leadership', 'Project Management', 'Communication', 'Team Collaboration',
                'Problem Solving', 'Critical Thinking', 'Agile', 'Scrum'
            ]
        }
        
        found_skills = {}
        text_lower = text.lower()
        
        for category, skills in tech_skills.items():
            category_skills = []
            for skill in skills:
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(skill.lower()) + r'\b'
                if re.search(pattern, text_lower):
                    category_skills.append(skill)
            
            if category_skills:
                found_skills[category] = category_skills
        
        return success_response({
            'skills_by_category': found_skills,
            'total_skills_found': sum(len(skills) for skills in found_skills.values())
        })
    except Exception as e:
        print(f"Error extracting skills: {str(e)}")
        return error_response(500, "Failed to extract skills")


def success_response(data):
    """Return successful response"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
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
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps({'error': message})
    }