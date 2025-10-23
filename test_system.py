#!/usr/bin/env python3
"""
Test script to verify AI Interview Coach system functionality
"""
import requests
import json
import time

API_ENDPOINT = 'https://vejsi9djoh.execute-api.us-west-2.amazonaws.com/dev'

def test_api_endpoint(endpoint, payload):
    """Test API endpoint"""
    try:
        url = f"{API_ENDPOINT}/{endpoint}"
        print(f"Testing: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {json.dumps(result, indent=2)}")
            return result
        else:
            print(f"Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"Exception: {str(e)}")
        return None

def main():
    """Run system tests"""
    print("AI Interview Coach - System Test")
    print("=" * 50)
    
    # Test 1: Start Interview Session
    print("\n1. Testing: Start Interview Session")
    session_data = test_api_endpoint('interview', {
        "action": "start_session",
        "job_title": "Software Engineer",
        "job_description": "Python developer role with AWS experience",
        "practice_mode": "question_by_question",
        "question_types": ["behavioral", "tell_me_about"]
    })
    
    if not session_data:
        print("Failed to start session. Exiting.")
        return
    
    session_id = session_data.get('session_id')
    print(f"Session ID: {session_id}")
    
    # Test 2: Get First Question
    print("\n2. Testing: Get Question")
    question_data = test_api_endpoint('interview', {
        "action": "get_question",
        "session_id": session_id
    })
    
    if not question_data:
        print("Failed to get question. Exiting.")
        return
    
    print(f"Question: {question_data.get('question')}")
    
    # Test 3: Submit Response and Get Feedback
    print("\n3. Testing: Submit Response & Get Feedback")
    feedback_data = test_api_endpoint('feedback', {
        "action": "analyze_response",
        "session_id": session_id,
        "question": question_data.get('question', ''),
        "question_type": question_data.get('question_type', 'behavioral'),
        "response_text": "At my previous company, I was tasked with migrating our legacy database to AWS RDS. I analyzed the current system, created a migration plan, and executed it over two weeks. The result was a 40% improvement in query performance and $50,000 annual cost savings.",
        "metrics": {
            "word_count": 45,
            "duration": 30,
            "pace_wpm": 90,
            "pace_assessment": "slow",
            "filler_count": 0,
            "filler_rate": 0
        },
        "job_description": "Python developer role with AWS experience",
        "resume_text": "Software Engineer with 3 years Python and AWS experience"
    })
    
    if feedback_data:
        print(f"Feedback: {feedback_data.get('feedback', 'No feedback')}")
    
    # Test 4: Get Next Question
    print("\n4. Testing: Get Next Question")
    next_question = test_api_endpoint('interview', {
        "action": "get_question",
        "session_id": session_id
    })
    
    if next_question:
        print(f"Next Question: {next_question.get('question', 'No question')}")
        print(f"Question Number: {next_question.get('question_number', 'N/A')}")
    
    # Test 5: Get Third Question
    print("\n5. Testing: Get Third Question")
    third_question = test_api_endpoint('interview', {
        "action": "get_question",
        "session_id": session_id
    })
    
    if third_question:
        print(f"Third Question: {third_question.get('question', 'No question')}")
        print(f"Question Number: {third_question.get('question_number', 'N/A')}")
    
    print("\nSystem test completed!")
    print("If all tests passed, the system is working correctly.")

if __name__ == "__main__":
    main()