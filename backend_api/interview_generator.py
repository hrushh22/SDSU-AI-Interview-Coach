import json
import boto3
import re
from typing import Dict, Any

bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-west-2')

def generate_interview_questions(resume_data: Dict[str, Any], job_desc_data: Dict[str, Any], model_id: str = 'anthropic.claude-3-5-sonnet-20241022-v2:0') -> Dict[str, Any]:
    """Generate customized interview questions based on resume and job description"""
    input_data = {"resume_data": resume_data, "job_desc_data": job_desc_data}
    
    prompt = f"""You are an expert interviewer for a {job_desc_data.get('title', 'technical')} position.

JOB REQUIREMENTS:
{json.dumps(job_desc_data, indent=2)}

CANDIDATE BACKGROUND:
{json.dumps(resume_data, indent=2)}

Your task: Generate 5 interview questions (2 technical + 3 behavioral) that:

1. FOCUS ON THE JOB DESCRIPTION - Questions must directly relate to the responsibilities and requirements listed in the job posting
2. Are practical and job-relevant (NOT academic or overly scientific)
3. Test real-world experience, not theoretical knowledge
4. Mix technical skills with behavioral/situational scenarios

RULES:
- Technical questions: Focus on tools, technologies, and responsibilities mentioned in the job description
- Behavioral questions: Use STAR method format, focus on teamwork, problem-solving, leadership from the job context
- Make questions conversational and realistic
- Avoid: Generic questions, overly academic questions, questions about research or theory

Return ONLY valid JSON in this exact format:
{{
  "technical_questions": [
    "Question about specific job responsibility 1",
    "Question about specific job requirement 2"
  ],
  "behavioral_questions": [
    "Tell me about a time when [job-relevant scenario]",
    "Describe a situation where [job-relevant challenge]",
    "Give me an example of [job-relevant skill]"
  ],
  "rationale": "Brief explanation"
}}"""
    
    try:
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 1500,
                'temperature': 0.7,
                'messages': [{'role': 'user', 'content': f"You are an expert technical interviewer. Always respond with valid JSON format.\n\n{prompt}"}]
            })
        )
        
        response_body = json.loads(response['body'].read())
        content = response_body['content'][0]['text'].strip()
        
        try:
            result = json.loads(content)
            return result
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"error": "Failed to parse JSON response", "raw_response": content}
    except Exception as e:
        return {"error": f"Bedrock API call failed: {str(e)}"}

def generate_followup_question(question: str, answer: str, job_context: str, model_id: str = 'anthropic.claude-3-5-sonnet-20241022-v2:0') -> str:
    """Generate a follow-up question based on the candidate's answer"""
    prompt = f"""You are an expert interviewer conducting a technical interview.

Original Question: {question}
Candidate's Answer: {answer}
Job Context: {job_context}

Based on the candidate's answer, generate ONE specific follow-up question that:
- Digs deeper into their response
- Probes for technical details or specific examples
- Clarifies any vague points
- Tests their depth of knowledge

Return ONLY the follow-up question text, nothing else."""
    
    try:
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 200,
                'temperature': 0.7,
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text'].strip()
    except Exception as e:
        return f"Can you elaborate more on that aspect?"
