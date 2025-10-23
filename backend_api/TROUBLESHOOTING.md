# Troubleshooting Guide

## Common Errors and Solutions

### Error: "Error getting feedback"

**Possible Causes:**
1. Session ID not being passed correctly
2. DynamoDB table doesn't exist
3. AWS credentials issue
4. Bedrock API error

**Solutions:**

#### 1. Check if DynamoDB table exists
```bash
aws dynamodb describe-table --table-name InterviewSessions --region us-west-2
```

If not found, create it:
```bash
cd backend_api
python setup_dynamodb.py
```

#### 2. Check AWS credentials
```bash
aws sts get-caller-identity
```

Should return your AWS account info. If not, set credentials:
```bash
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_DEFAULT_REGION="us-west-2"
```

#### 3. Check backend logs
Look for error messages in the terminal where you ran `uvicorn main:app --reload`

#### 4. Test without DynamoDB (temporary fix)

If you want to test without DynamoDB, modify the frontend to not require session_id:

**frontend/app/page.tsx** - Make session_id optional:
```typescript
// Change this line:
session_id: sessionId,

// To:
session_id: sessionId || "test-session",
```

---

### Error: "Table not found"

**Solution:**
```bash
cd backend_api
python setup_dynamodb.py
```

---

### Error: "Access Denied" on Bedrock

**Solution:**
1. Go to AWS Console → Bedrock → Model access
2. Click "Manage model access"
3. Enable "Claude 3.5 Sonnet"
4. Wait for approval (usually instant)

---

### Error: "Questions are generic/hardcoded"

**Causes:**
- Resume or job description too short
- Parsing failed
- Bedrock API error

**Solutions:**
1. Provide detailed job description (100+ words)
2. Provide complete resume with skills and experience
3. Check backend logs for parsing errors

---

### Error: "Interview won't start"

**Check:**
1. All three fields filled (job title, description, resume)
2. Backend running on port 8000
3. No CORS errors in browser console

**Test backend directly:**
```bash
curl -X POST http://localhost:8000/start-interview \
  -H "Content-Type: application/json" \
  -d '{
    "job_title": "Software Engineer",
    "job_description": "Looking for Python developer with AWS experience",
    "resume_text": "John Doe. Skills: Python, AWS. Experience: 5 years"
  }'
```

---

### Error: "Transcription failed"

**Causes:**
- S3 bucket doesn't exist
- Wrong audio format
- Transcribe service issue

**Solutions:**
1. Create S3 bucket:
```bash
aws s3 mb s3://ai-interview-audio-temp --region us-west-2
```

2. Check audio format (should be WAV)

3. Check Transcribe limits (100 concurrent jobs max)

---

## Quick Fixes

### Reset Everything
```bash
# Stop backend (Ctrl+C)
# Stop frontend (Ctrl+C)

# Recreate DynamoDB table
aws dynamodb delete-table --table-name InterviewSessions --region us-west-2
cd backend_api
python setup_dynamodb.py

# Restart backend
uvicorn main:app --reload --port 8000

# Restart frontend (new terminal)
cd frontend
npm run dev
```

### Test Without Dynamic Questions

If you want to test with hardcoded questions temporarily, modify `backend_api/main.py`:

```python
@app.post("/start-interview")
def start_interview(req: InterviewRequest):
    # Skip parsing and generation
    all_questions = [
        f"Tell me about your experience relevant to this {req.job_title} position.",
        "Describe a challenging technical problem you've solved.",
        "How do you approach learning new technologies?",
        "Tell me about a time you worked in a team.",
        "Where do you see yourself growing?"
    ]
    
    session_id = create_session(req.job_title, req.job_description, req.resume_text)
    
    return {
        "session_id": session_id,
        "question": all_questions[0],
        "total_questions": len(all_questions),
        "question_type": "behavioral"
    }
```

---

## Debug Mode

### Enable Detailed Logging

**backend_api/main.py** - Add at the top:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check What's Being Sent

**Browser Console (F12):**
- Network tab
- Look for failed requests
- Check request payload
- Check response

---

## Still Having Issues?

1. **Check all prerequisites:**
   - [ ] Python 3.9+
   - [ ] Node.js 18+
   - [ ] AWS credentials configured
   - [ ] Bedrock access enabled
   - [ ] DynamoDB table exists
   - [ ] S3 bucket exists

2. **Run integration tests:**
```bash
cd backend_api
python test_integration.py
```

3. **Check specific service:**
```bash
# Test DynamoDB
aws dynamodb scan --table-name InterviewSessions --region us-west-2

# Test S3
aws s3 ls s3://ai-interview-audio-temp

# Test Bedrock
aws bedrock list-foundation-models --region us-west-2
```

4. **Simplify and test incrementally:**
   - Start with hardcoded questions
   - Add parsing
   - Add DynamoDB
   - Add follow-ups

---

## Contact Points

- Check backend terminal for error logs
- Check browser console (F12) for frontend errors
- Check AWS CloudWatch for service errors
- Review INTEGRATION_GUIDE.md for detailed setup
