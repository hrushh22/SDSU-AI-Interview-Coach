import json
import boto3
import re
from typing import Dict, Any

bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-west-2')

def parse_resume(resume_text: str, model_id: str = 'anthropic.claude-3-5-sonnet-20241022-v2:0') -> Dict[str, Any]:
    """Parse resume text into structured data"""
    prompt = f"""Extract structured information from this resume and return as JSON:

Resume:
{resume_text}

Return a JSON object with these keys:
{{
  "name": "candidate name",
  "skills": ["list of technical skills"],
  "soft_skills": ["list of soft skills"],
  "experience": [
    {{"company": "name", "position": "title", "duration": "time", "responsibilities": ["list"]}}
  ],
  "projects": [
    {{"name": "project name", "technologies": ["tech used"], "description": "brief desc"}}
  ],
  "education": [
    {{"degree": "degree name", "institution": "school", "year": "year"}}
  ]
}}"""
    
    try:
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 1500,
                'temperature': 0.3,
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        response_body = json.loads(response['body'].read())
        content = response_body['content'][0]['text'].strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"error": "Failed to parse resume"}
    except Exception as e:
        return {"error": f"Resume parsing failed: {str(e)}"}

def parse_job_description(job_desc: str, job_title: str, model_id: str = 'anthropic.claude-3-5-sonnet-20241022-v2:0') -> Dict[str, Any]:
    """Parse job description into structured data"""
    prompt = f"""Extract structured information from this job description and return as JSON:

Job Title: {job_title}
Job Description:
{job_desc}

Return a JSON object with these keys:
{{
  "title": "job title",
  "required_skills": ["must-have skills"],
  "preferred_skills": ["nice-to-have skills"],
  "responsibilities": ["key responsibilities"],
  "company_values": ["company values or culture"],
  "experience_level": "junior/mid/senior"
}}"""
    
    try:
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 1000,
                'temperature': 0.3,
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        response_body = json.loads(response['body'].read())
        content = response_body['content'][0]['text'].strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"error": "Failed to parse job description"}
    except Exception as e:
        return {"error": f"Job description parsing failed: {str(e)}"}
