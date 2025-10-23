"""
Fixed Test Script for AI Interview Coach
Tests all components with proper error handling
"""
import os
import sys
import json
import requests
from datetime import datetime

# Set environment variables for testing
os.environ['MOCK_MODE'] = 'true'
os.environ['AWS_REGION'] = 'us-west-2'

def test_lambda_function(handler_module, test_event):
    """Test a Lambda function with proper error handling"""
    try:
        result = handler_module.lambda_handler(test_event, {})
        return result
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def test_interview_orchestrator():
    """Test interview orchestrator"""
    print("🧪 Testing Interview Orchestrator...")
    
    try:
        sys.path.append('backend/lambda/interview_orchestrator')
        import handler as orchestrator
        
        # Test start session
        event = {
            'body': json.dumps({
                'action': 'start_session',
                'job_title': 'Software Engineer',
                'job_description': 'Python developer role'
            })
        }
        
        result = test_lambda_function(orchestrator, event)
        
        if result['statusCode'] == 200:
            print("  ✅ Start session: PASSED")
            body = json.loads(result['body'])
            session_id = body.get('session_id')
            
            # Test get question
            event = {
                'body': json.dumps({
                    'action': 'get_question',
                    'session_id': session_id
                })
            }
            
            result = test_lambda_function(orchestrator, event)
            if result['statusCode'] == 200:
                print("  ✅ Get question: PASSED")
            else:
                print(f"  ❌ Get question: FAILED - {result}")
        else:
            print(f"  ❌ Start session: FAILED - {result}")
            
    except Exception as e:
        print(f"  ❌ Import error: {str(e)}")

def test_feedback_generator():
    """Test feedback generator"""
    print("🧪 Testing Feedback Generator...")
    
    try:
        sys.path.append('backend/lambda/feedback_generator')
        import handler as feedback
        
        event = {
            'body': json.dumps({
                'action': 'analyze_response',
                'session_id': 'test-123',
                'question': 'Tell me about a time you solved a problem',
                'question_type': 'behavioral',
                'response_text': 'I solved a database performance issue by optimizing queries',
                'metrics': {'pace_wpm': 145, 'filler_count': 2}
            })
        }
        
        result = test_lambda_function(feedback, event)
        
        if result['statusCode'] == 200:
            print("  ✅ Analyze response: PASSED")
        else:
            print(f"  ❌ Analyze response: FAILED - {result}")
            
    except Exception as e:
        print(f"  ❌ Import error: {str(e)}")

def test_resume_analyzer():
    """Test resume analyzer"""
    print("🧪 Testing Resume Analyzer...")
    
    try:
        sys.path.append('backend/lambda/resume_analyzer')
        import handler as resume
        
        event = {
            'body': json.dumps({
                'action': 'analyze_text',
                'session_id': 'test-123',
                'resume_text': 'John Doe\nSoftware Engineer\nPython, AWS, React\nExperience: 5 years'
            })
        }
        
        result = test_lambda_function(resume, event)
        
        if result['statusCode'] == 200:
            print("  ✅ Analyze text: PASSED")
        else:
            print(f"  ❌ Analyze text: FAILED - {result}")
            
    except Exception as e:
        print(f"  ❌ Import error: {str(e)}")

def test_audio_processor():
    """Test audio processor"""
    print("🧪 Testing Audio Processor...")
    
    try:
        sys.path.append('backend/lambda/audio_processor')
        import handler as audio
        
        event = {
            'body': json.dumps({
                'action': 'analyze_speech',
                'transcript': 'This is a test response with some filler words like um and uh',
                'duration': 10.5
            })
        }
        
        result = test_lambda_function(audio, event)
        
        if result['statusCode'] == 200:
            print("  ✅ Analyze speech: PASSED")
        else:
            print(f"  ❌ Analyze speech: FAILED - {result}")
            
    except Exception as e:
        print(f"  ❌ Import error: {str(e)}")

def test_api_endpoint():
    """Test API endpoint if available"""
    print("🧪 Testing API Endpoint...")
    
    try:
        from config import API_ENDPOINT
        
        if API_ENDPOINT and API_ENDPOINT != 'YOUR_API_GATEWAY_URL':
            response = requests.post(
                f"{API_ENDPOINT}/interview",
                json={
                    'action': 'start_session',
                    'job_title': 'Test Engineer'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print("  ✅ API endpoint: PASSED")
            else:
                print(f"  ❌ API endpoint: FAILED - {response.status_code}")
        else:
            print("  ⏭️ API endpoint: SKIPPED (not configured)")
            
    except ImportError:
        print("  ⏭️ API endpoint: SKIPPED (config not found)")
    except Exception as e:
        print(f"  ❌ API endpoint: FAILED - {str(e)}")

def main():
    """Run all tests"""
    print("🚀 AI Interview Coach - Test Suite")
    print("=" * 50)
    print(f"📅 Test run: {datetime.now().isoformat()}")
    print(f"🔧 Mock mode: {os.environ.get('MOCK_MODE', 'false')}")
    print()
    
    # Run tests
    test_interview_orchestrator()
    print()
    test_feedback_generator()
    print()
    test_resume_analyzer()
    print()
    test_audio_processor()
    print()
    test_api_endpoint()
    
    print()
    print("=" * 50)
    print("✅ Test suite completed!")
    print()
    print("📝 Next steps:")
    print("1. Fix any failed tests")
    print("2. Deploy to AWS using deploy.bat")
    print("3. Update API_ENDPOINT in config.py")
    print("4. Run: streamlit run streamlit_app.py")

if __name__ == "__main__":
    main()