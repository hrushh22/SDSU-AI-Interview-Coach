"""
AI Interview Coach - Complete Streamlit Frontend
Real-time voice interaction with AWS integration
"""
import streamlit as st
import requests
import json
import base64
import os
import time
from io import BytesIO
import tempfile

# Page configuration
st.set_page_config(
    page_title="AI Interview Coach",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load configuration - FORCE CORRECT URL
API_ENDPOINT = 'https://vejsi9djoh.execute-api.us-west-2.amazonaws.com/dev'
AWS_REGION = 'us-west-2'



USE_LOCAL = os.environ.get('USE_LOCAL', 'false').lower() == 'true'

# Session state initialization
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'current_question' not in st.session_state:
    st.session_state.current_question = None
if 'question_number' not in st.session_state:
    st.session_state.question_number = 0
if 'total_questions' not in st.session_state:
    st.session_state.total_questions = 0
if 'responses' not in st.session_state:
    st.session_state.responses = []
if 'job_title' not in st.session_state:
    st.session_state.job_title = "Software Engineer"
if 'job_description' not in st.session_state:
    st.session_state.job_description = ""
if 'resume_text' not in st.session_state:
    st.session_state.resume_text = ""
if 'feedback_ready' not in st.session_state:
    st.session_state.feedback_ready = False
if 'current_feedback' not in st.session_state:
    st.session_state.current_feedback = None
if 'voice_transcript' not in st.session_state:
    st.session_state.voice_transcript = None

if 'client_question_index' not in st.session_state:
    st.session_state.client_question_index = 0


# Removed caching to prevent issues
# @st.cache_data(ttl=300)
# def call_api_cached(endpoint, payload_str):
#     """Cached API calls for better performance"""
#     payload = json.loads(payload_str)
#     return call_api(endpoint, payload)

def call_api(endpoint, payload):
    """Call API Gateway endpoint"""
    if API_ENDPOINT == 'YOUR_API_GATEWAY_URL' or 'your-api-id.execute-api' in API_ENDPOINT:
        st.error("❌ API endpoint not configured. Please set API_ENDPOINT environment variable.")
        return None
        
    try:
        url = f"{API_ENDPOINT}/{endpoint}"
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timed out. Please try again.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ API Error: {str(e)}")
        return None
    except json.JSONDecodeError:
        st.error("❌ Invalid response from server")
        return None


def extract_text_from_pdf(pdf_file):
    """Extract text from PDF"""
    try:
        from PyPDF2 import PdfReader
        
        pdf_reader = PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    except ImportError:
        st.error("📦 PyPDF2 not installed. Run: pip install PyPDF2")
        return None
    except Exception as e:
        st.error(f"❌ Error reading PDF: {str(e)}")
        return None


def play_audio_from_base64(audio_base64):
    """Play audio from base64 string"""
    try:
        audio_bytes = base64.b64decode(audio_base64)
        st.audio(audio_bytes, format='audio/mp3', start_time=0)
        return True
    except Exception as e:
        st.error(f"❌ Error playing audio: {str(e)}")
        return False





def start_interview_session():
    """Start new interview session"""
    
    if not st.session_state.job_title.strip():
        st.error("❌ Please enter a job title")
        return False
    
    with st.spinner("🔄 Starting interview session..."):
        try:
            # Start session
            data = call_api('interview', {
                "action": "start_session",
                "job_title": st.session_state.job_title,
                "job_description": st.session_state.job_description,
                "practice_mode": "question_by_question",
                "question_types": ["behavioral", "tell_me_about", "why_this_job"]
            })
            
            if not data:
                return False
            
            st.session_state.session_id = data.get('session_id')
            st.session_state.total_questions = data.get('total_questions', 0)
            
            # Upload resume if provided
            if st.session_state.resume_text.strip():
                resume_data = call_api('resume', {
                    "action": "analyze_text",
                    "session_id": st.session_state.session_id,
                    "resume_text": st.session_state.resume_text
                })
                
                if resume_data:
                    st.success("✅ Resume processed successfully!")
            
            st.success("✅ Interview session started!")
            time.sleep(1)
            return True
            
        except Exception as e:
            st.error(f"❌ Error starting session: {str(e)}")
            return False


def load_next_question():
    """Load next question with client-side cycling"""
    
    # Client-side question bank for reliable cycling
    question_bank = [
        {
            'question': f"Tell me about yourself and why you're interested in this {st.session_state.job_title} position.",
            'question_type': 'tell_me_about',
            'competency': 'self_presentation',
            'expected_duration': '1-2 minutes'
        },
        {
            'question': 'Tell me about a time when you faced a challenging problem at work.',
            'question_type': 'behavioral', 
            'competency': 'problem_solving',
            'expected_duration': '2-3 minutes'
        },
        {
            'question': 'Describe a situation where you had to work with a difficult team member.',
            'question_type': 'behavioral',
            'competency': 'teamwork', 
            'expected_duration': '2-3 minutes'
        },
        {
            'question': f"Why do you want to work as a {st.session_state.job_title}?",
            'question_type': 'why_this_job',
            'competency': 'motivation',
            'expected_duration': '1-2 minutes'
        },
        {
            'question': 'Tell me about a time when you had to learn something new quickly.',
            'question_type': 'behavioral',
            'competency': 'adaptability',
            'expected_duration': '2-3 minutes'
        }
    ]
    
    with st.spinner("📥 Loading question..."):
        try:
            # Use client-side question cycling
            if st.session_state.client_question_index >= len(question_bank):
                st.session_state.interview_complete = True
                return True
            
            question_data = question_bank[st.session_state.client_question_index]
            
            # Format the question data
            st.session_state.current_question = {
                'question': question_data['question'],
                'question_type': question_data['question_type'],
                'competency': question_data['competency'],
                'expected_duration': question_data['expected_duration'],
                'question_number': st.session_state.client_question_index + 1
            }
            
            st.session_state.question_number = st.session_state.client_question_index + 1
            st.session_state.total_questions = len(question_bank)
            st.session_state.feedback_ready = False
            st.session_state.current_feedback = None
            
            return True
            
        except Exception as e:
            st.error(f"❌ Error loading question: {str(e)}")
            return False


def submit_response(response_text):
    """Submit user response and get real AI feedback"""
    
    with st.spinner("🤖 Getting AI feedback..."):
        try:
            # Calculate metrics
            words = response_text.split()
            word_count = len(words)
            
            # Only calculate pace for voice responses
            is_voice = getattr(st.session_state, 'is_voice_response', False)
            
            if is_voice:
                estimated_duration = max((word_count / 145) * 60, 30)
                filler_words = ['um', 'uh', 'like', 'you know', 'so', 'actually', 'basically']
                filler_count = sum(response_text.lower().count(filler) for filler in filler_words)
                filler_rate = (filler_count / word_count * 100) if word_count > 0 else 0
                pace_wpm = int((word_count / estimated_duration) * 60) if estimated_duration > 0 else 0
                pace_assessment = 'good' if 120 <= pace_wpm <= 160 else 'slow' if pace_wpm < 120 else 'fast'
            else:
                estimated_duration = 0
                filler_count = 0
                filler_rate = 0
                pace_wpm = 0
                pace_assessment = 'text_input'
            
            metrics = {
                'word_count': word_count,
                'duration': estimated_duration,
                'pace_wpm': pace_wpm,
                'pace_assessment': pace_assessment,
                'filler_count': filler_count,
                'filler_rate': filler_rate,
                'is_voice_response': is_voice
            }
            
            # Get real AI feedback
            question = st.session_state.current_question.get('question', '')
            question_type = st.session_state.current_question.get('question_type', 'behavioral')
            feedback = get_ai_feedback(question, response_text, question_type, metrics)
            
            # Store response data
            st.session_state.responses.append({
                'question': question,
                'response': response_text,
                'metrics': metrics,
                'feedback': feedback
            })
            
            st.session_state.current_feedback = {
                'text': response_text,
                'metrics': metrics,
                'feedback': feedback
            }
            st.session_state.feedback_ready = True
            
            return True
            
        except Exception as e:
            st.error(f"❌ Error processing response: {str(e)}")
            return False


def get_ai_feedback(question, response, question_type, metrics):
    """Get real AI feedback using AWS Bedrock"""
    try:
        import boto3
        import json
        
        # Initialize Bedrock client with Streamlit secrets
        bedrock = boto3.client(
            'bedrock-runtime',
            region_name='us-west-2',
            aws_access_key_id=st.secrets["aws"]["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=st.secrets["aws"]["AWS_SECRET_ACCESS_KEY"],
            aws_session_token=st.secrets["aws"]["AWS_SESSION_TOKEN"]
        )
        
        prompt = f"""You are an expert interview coach. Analyze this interview response and provide specific, actionable feedback.

Question: {question}
Question Type: {question_type}
Candidate's Response: {response}

Delivery Metrics:
- Words: {metrics.get('word_count', 0)}
- Pace: {metrics.get('pace_wpm', 0)} WPM
- Filler words: {metrics.get('filler_count', 0)} ({metrics.get('filler_rate', 0):.1f}%)

Provide feedback in this format:

**Content Analysis:**
[Analyze the content quality, relevance, and structure]

**Delivery Assessment:**
[Comment on pace, clarity, and speaking style]

**Strengths:**
[2-3 specific things they did well]

**Areas for Improvement:**
[2-3 specific suggestions with examples]

**Score: X/10**

Be constructive, specific, and encouraging. Focus on actionable improvements."""
        
        # Call Claude via Bedrock
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "temperature": 0.7,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
        
    except Exception as e:
        # Generate intelligent fallback feedback
        word_count = len(response.split())
        has_examples = 'example' in response.lower() or 'time when' in response.lower()
        has_numbers = any(char.isdigit() for char in response)
        
        # Proper scoring for short responses
        if word_count < 10:
            score = 2
            content_msg = f"Response is too brief ({word_count} words). This appears to be incomplete."
        elif word_count < 30:
            score = 3
            content_msg = f"Response is very short ({word_count} words). Expand with specific examples."
        elif word_count < 50:
            score = 4
            content_msg = f"Response is short ({word_count} words). Add more detail and examples."
        elif 50 <= word_count <= 200:
            score = 7 + (1 if has_examples else 0) + (1 if has_numbers else 0)
            content_msg = f"Good response length ({word_count} words)."
        else:
            score = 6
            content_msg = f"Response is lengthy ({word_count} words). Consider being more concise."
        
        feedback = f"""**Content Analysis:**
{content_msg}

**Strengths:**
{'• Includes specific examples' if has_examples else '• Response addresses the question'}
{'• Contains quantifiable data' if has_numbers else '• Clear communication style'}

**Areas for Improvement:**
{'• Expand with specific examples and details' if word_count < 50 else '• Consider adding more specific examples' if not has_examples else '• Practice confident delivery'}
{'• Include numbers/metrics to strengthen impact' if not has_numbers else '• Ensure STAR method structure'}

**Score: {min(max(score, 1), 10)}/10**

*Note: Enhanced AI feedback temporarily unavailable. Please check AWS credentials.*"""
        return feedback


def generate_speech_aws(text):
    """Generate speech using AWS Polly"""
    try:
        import boto3
        
        polly = boto3.client(
            'polly',
            region_name='us-west-2',
            aws_access_key_id=st.secrets["aws"]["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=st.secrets["aws"]["AWS_SECRET_ACCESS_KEY"],
            aws_session_token=st.secrets["aws"]["AWS_SESSION_TOKEN"]
        )
        
        response = polly.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId='Joanna',
            Engine='neural'
        )
        
        return response['AudioStream'].read()
        
    except Exception as e:
        st.error(f"AWS Polly error: {str(e)}")
        return None


def transcribe_audio_aws(audio_file):
    """Transcribe audio using AWS Transcribe (simplified)"""
    try:
        import boto3
        import json
        
        transcribe = boto3.client(
            'transcribe',
            region_name='us-west-2',
            aws_access_key_id=st.secrets["aws"]["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=st.secrets["aws"]["AWS_SECRET_ACCESS_KEY"],
            aws_session_token=st.secrets["aws"]["AWS_SESSION_TOKEN"]
        )
        
        # For real-time, we'll use Whisper as AWS Transcribe requires S3 upload
        return transcribe_audio_whisper(audio_file)
        
    except Exception as e:
        return transcribe_audio_whisper(audio_file)


def transcribe_audio_whisper(audio_bytes):
    """Fallback transcription using Whisper"""
    try:
        import whisper
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_file_path = tmp_file.name
        
        model = whisper.load_model("base")
        result = model.transcribe(tmp_file_path)
        
        os.unlink(tmp_file_path)
        return result["text"].strip()
        
    except Exception as e:
        st.error(f"Transcription error: {str(e)}")
        return None


# JavaScript for speech recognition
st.markdown("""
<script>
// Listen for speech results from iframe
window.addEventListener('message', function(event) {
    if (event.data.type === 'speech_result') {
        // Update Streamlit session state
        const transcript = event.data.transcript;
        const textArea = document.querySelector('[data-testid="stTextArea"] textarea');
        if (textArea) {
            textArea.value = transcript;
            textArea.dispatchEvent(new Event('input', { bubbles: true }));
        }
    }
});
</script>
""", unsafe_allow_html=True)

# Custom CSS
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .question-box {
        background-color: #e3f2fd;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #2196F3;
        margin: 20px 0;
    }
    .feedback-box {
        background-color: #f5f5f5;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🎤 AI Interview Coach")
st.caption(f"{'🟢 LOCAL MODE' if USE_LOCAL else '🔵 AWS CONNECTED'}")
st.markdown("*Practice interviews with real-time AI feedback powered by AWS*")
st.divider()

# Sidebar
with st.sidebar:
    st.header("⚙️ Setup")
    
    st.session_state.job_title = st.text_input(
        "Job Title*", 
        value=st.session_state.job_title,
        placeholder="e.g., Software Engineer"
    )
    
    st.session_state.job_description = st.text_area(
        "Job Description (Optional)", 
        value=st.session_state.job_description,
        placeholder="Paste job description for tailored questions...",
        height=150
    )
    
    st.divider()
    
    # Resume Upload
    st.subheader("📄 Resume")
    
    upload_method = st.radio(
        "Upload method:",
        ["📁 PDF File", "📝 Text"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    if upload_method == "📁 PDF File":
        uploaded_file = st.file_uploader(
            "Upload Resume (PDF)",
            type=['pdf'],
            label_visibility="collapsed"
        )
        
        if uploaded_file is not None:
            if st.button("📤 Process PDF", use_container_width=True):
                with st.spinner("📄 Extracting text..."):
                    resume_text = extract_text_from_pdf(uploaded_file)
                    if resume_text:
                        st.session_state.resume_text = resume_text
                        st.success(f"✅ Extracted {len(resume_text)} characters")
                        
                        with st.expander("Preview"):
                            st.text_area("", resume_text[:500] + "...", height=150, disabled=True)
    else:
        st.session_state.resume_text = st.text_area(
            "Paste Resume Text",
            value=st.session_state.resume_text,
            placeholder="Paste your resume here...",
            height=200,
            label_visibility="collapsed"
        )
    
    st.divider()
    
    # Progress
    st.subheader("📊 Progress")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Questions", st.session_state.question_number)
    with col2:
        st.metric("Answers", len(st.session_state.responses))
    
    st.divider()
    
    # Reset
    if st.button("🔄 New Session", type="secondary", use_container_width=True):
        for key in list(st.session_state.keys()):
            if key not in ['job_title', 'job_description', 'resume_text']:
                del st.session_state[key]
        st.rerun()

# Main Content
if st.session_state.session_id is None:
    # Welcome Screen
    st.markdown("## 👋 Welcome!")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 📝 How It Works
        1. Enter job details
        2. Upload resume
        3. Start practice
        4. Get AI feedback
        5. Improve!
        """)
    
    with col2:
        st.markdown("""
        ### 📊 We Analyze
        - Speaking pace
        - Filler words
        - STAR structure
        - Content quality
        - Job relevance
        """)
    
    with col3:
        st.markdown("""
        ### 🎯 Best Practices
        - 120-160 WPM
        - Specific examples
        - Include metrics
        - Avoid fillers
        - Stay focused
        """)
    
    st.divider()
    
    # Start Button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Interview Practice", type="primary", use_container_width=True):
            if start_interview_session():
                load_next_question()
                st.rerun()

elif st.session_state.get('interview_complete'):
    # Interview Complete
    st.balloons()
    st.success("🎉 **Interview Practice Complete!**")
    
    st.markdown("### 📊 Session Summary")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Questions", st.session_state.question_number)
    with col2:
        st.metric("Responses", len(st.session_state.responses))
    with col3:
        avg_score = sum([r.get('metrics', {}).get('pace_wpm', 0) for r in st.session_state.responses]) / len(st.session_state.responses) if st.session_state.responses else 0
        st.metric("Avg Pace", f"{int(avg_score)} WPM")
    
    st.divider()
    
    # Show all responses
    st.markdown("### 📝 Your Responses")
    
    for i, resp in enumerate(st.session_state.responses, 1):
        with st.expander(f"Question {i}: {resp['question'][:60]}..."):
            st.markdown(f"**Your Answer:**\n{resp['response']}")
            
            metrics = resp.get('metrics', {})
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Pace", f"{metrics.get('pace_wpm', 0)} WPM")
            with col2:
                st.metric("Filler Words", metrics.get('filler_count', 0))
            with col3:
                st.metric("Duration", f"{metrics.get('duration', 0):.0f}s")
            
            st.markdown("**AI Feedback:**")
            st.markdown(resp.get('feedback', 'No feedback available'))
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 New Interview", type="primary", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key not in ['job_title', 'job_description', 'resume_text']:
                    del st.session_state[key]
            st.rerun()

else:
    # Interview In Progress
    
    # Load question if needed
    if st.session_state.current_question is None:
        if load_next_question():
            # Auto-generate speech for new question
            question_text = st.session_state.current_question.get('question', '')
            if question_text and 'question_audio' not in st.session_state:
                with st.spinner("🎙️ Preparing voice question..."):
                    audio_data = generate_speech_aws(question_text)
                    if audio_data:
                        st.session_state.question_audio = audio_data
            st.rerun()
    
    if st.session_state.current_question:
        question_data = st.session_state.current_question
        
        # Question Header
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### Question {question_data.get('question_number', 1)} of {st.session_state.total_questions}")
        with col2:
            qtype = question_data.get('question_type', 'N/A').replace('_', ' ').title()
            st.markdown(f"**Type:** `{qtype}`")
        
        # The Question
        st.markdown(f"""
        <div class="question-box">
            <h3>❓ {question_data.get('question', 'Loading...')}</h3>
            <p><strong>Competency:</strong> {question_data.get('competency', 'N/A')}</p>
            <p><strong>Expected Duration:</strong> {question_data.get('expected_duration', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Voice Question with AWS Polly
        st.markdown("### 🔊 Listen to Question")
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("🎤 Play Question", type="primary", use_container_width=True):
                if hasattr(st.session_state, 'question_audio') and st.session_state.question_audio:
                    st.audio(st.session_state.question_audio, format='audio/mp3', autoplay=True)
                else:
                    with st.spinner("🔊 Generating speech..."):
                        question_text = question_data.get('question', '')
                        audio_data = generate_speech_aws(question_text)
                        if audio_data:
                            st.session_state.question_audio = audio_data
                            st.audio(audio_data, format='audio/mp3', autoplay=True)
                        else:
                            st.error("Failed to generate speech")
        
        with col2:
            st.info("🎯 Click to hear the AI coach ask the question")
        
        # Tips
        with st.expander("💡 Tips for This Question"):
            qtype_lower = question_data.get('question_type', '').lower()
            
            if qtype_lower == 'behavioral':
                st.markdown("""
                **STAR Method:**
                - **S**ituation: Context (20% of answer)
                - **T**ask: Your responsibility (20%)
                - **A**ction: What YOU did (40%)
                - **R**esult: Outcomes with metrics (20%)
                
                **Tips:**
                - 1.5-3 minutes total
                - 120-160 WPM pace
                - < 2% filler words
                - Include specific numbers
                """)
            elif qtype_lower == 'tell_me_about':
                st.markdown("""
                **Structure: Present → Past → Future**
                
                1. **Present** (30s): Current role/education
                2. **Past** (30-45s): Key experiences
                3. **Future** (15-30s): Why THIS job
                
                **Total:** 1-2 minutes
                """)
        
        st.divider()
        
        # Show Feedback if ready
        if st.session_state.feedback_ready and st.session_state.current_feedback:
            st.success("✅ **Analysis Complete!**")
            
            feedback_data = st.session_state.current_feedback
            
            # Transcript
            with st.expander("📝 Your Response", expanded=True):
                st.write(feedback_data['text'])
            
            # Metrics
            st.markdown("### 📊 Delivery Metrics")
            metrics = feedback_data['metrics']
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                pace = metrics.get('pace_wpm', 0)
                assessment = metrics.get('pace_assessment', '')
                color = "🟢" if assessment == "good" else "🟡"
                st.metric("Pace", f"{pace} WPM", f"{color} {assessment}")
            
            with col2:
                filler_count = metrics.get('filler_count', 0)
                filler_rate = metrics.get('filler_rate', 0)
                color = "🟢" if filler_rate < 2 else "🟡" if filler_rate < 5 else "🔴"
                st.metric("Filler Words", filler_count, f"{color} {filler_rate:.1f}%")
            
            with col3:
                st.metric("Total Words", metrics.get('word_count', 0))
            
            with col4:
                duration = metrics.get('duration', 0)
                st.metric("Duration", f"{duration:.0f}s")
            
            # Filler details
            if metrics.get('filler_details'):
                with st.expander("📋 Filler Word Breakdown"):
                    for detail in metrics['filler_details']:
                        st.write(f"- **{detail['word']}**: {detail['count']} times")
            
            st.divider()
            
            # AI Feedback
            st.markdown("### 🤖 AI Coach Feedback")
            st.markdown(f"""
            <div class="feedback-box">
                {feedback_data['feedback'].replace('**', '<strong>').replace('**', '</strong>')}
            </div>
            """, unsafe_allow_html=True)
            
            st.divider()
            
            # Next Question
            if st.button("➡️ Next Question", type="primary", use_container_width=True):
                # Increment question index for client-side cycling
                st.session_state.client_question_index += 1
                
                # Clear current state and load next question
                st.session_state.current_question = None
                st.session_state.feedback_ready = False
                st.session_state.current_feedback = None
                if hasattr(st.session_state, 'question_audio'):
                    del st.session_state.question_audio
                
                # Load next question
                if load_next_question():
                    st.rerun()
                else:
                    st.session_state.interview_complete = True
                    st.rerun()
        
        else:
            # Answer Input
            st.markdown("### 🎤 Your Answer")
            
            tab1, tab2 = st.tabs(["✍️ Type Answer", "🎙️ Voice Recording"])
            
            with tab1:
                user_response = st.text_area(
                    "Type your answer:",
                    height=200,
                    placeholder="Type your interview answer here...",
                    key="user_input",
                    label_visibility="collapsed"
                )
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    can_submit = user_response and user_response.strip()
                    if st.button("📤 Submit Answer", type="primary", use_container_width=True, disabled=not can_submit):
                        st.session_state.is_voice_response = False
                        if submit_response(user_response.strip()):
                            st.rerun()
                
                with col2:
                    if st.button("⏭️ Skip Question", use_container_width=True):
                        st.session_state.client_question_index += 1
                        st.session_state.current_question = None
                        st.rerun()
            
            with tab2:
                st.markdown("### 🎙️ Voice Recording")
                
                # Browser Speech Recognition (Primary)
                st.markdown("#### 🌐 Browser Speech Recognition")
                st.info("🎤 Click 'Start Recording' and speak your answer. Works best in Chrome/Edge.")
                
                # Web Speech API using Streamlit components
                import streamlit.components.v1 as components
                
                # Initialize session state for speech
                if 'speech_transcript' not in st.session_state:
                    st.session_state.speech_transcript = ''
                
                speech_html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <script src="https://cdn.jsdelivr.net/npm/streamlit-component-lib@1.4.1/dist/streamlit-component-lib.js"></script>
                    <style>
                        body { font-family: Arial, sans-serif; padding: 20px; margin: 0; }
                        .btn {
                            background: #ff4b4b; color: white; border: none;
                            padding: 12px 24px; border-radius: 6px; cursor: pointer;
                            margin: 5px; font-size: 16px;
                        }
                        .btn:disabled { background: #666; cursor: not-allowed; }
                        .btn:hover:not(:disabled) { background: #e63946; }
                        .status { margin: 15px 0; font-weight: bold; font-size: 18px; }
                        .transcript {
                            background: #f0f2f6; padding: 15px; border-radius: 8px;
                            min-height: 120px; margin: 15px 0; border: 2px solid #ddd;
                            font-size: 16px; line-height: 1.5;
                        }
                    </style>
                </head>
                <body>
                    <button id="start-btn" class="btn" onclick="startRecording()">
                        🎤 Start Recording
                    </button>
                    <button id="stop-btn" class="btn" onclick="stopRecording()" disabled>
                        ⏹️ Stop Recording
                    </button>
                    
                    <div id="status" class="status">Ready to record</div>
                    <div id="transcript" class="transcript">Your speech will appear here...</div>
                    
                    <script>
                        const Streamlit = window.parent.Streamlit;
                        let recognition;
                        let isRecording = false;
                        let finalTranscript = '';
                        
                        // Initialize Streamlit component
                        function onRender(event) {
                            if (!window.rendered) {
                                Streamlit.setFrameHeight();
                                window.rendered = true;
                            }
                        }
                        
                        if (Streamlit) {
                            Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
                            Streamlit.setComponentReady();
                            Streamlit.setFrameHeight();
                        }
                        
                        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                            recognition = new SpeechRecognition();
                            recognition.continuous = true;
                            recognition.interimResults = true;
                            recognition.lang = 'en-US';
                            
                            recognition.onstart = function() {
                                document.getElementById('status').innerHTML = '🎤 Listening... Speak now!';
                                document.getElementById('start-btn').disabled = true;
                                document.getElementById('stop-btn').disabled = false;
                                document.getElementById('transcript').innerHTML = 'Listening for your voice...';
                            };
                            
                            recognition.onresult = function(event) {
                                let interimTranscript = '';
                                finalTranscript = '';
                                
                                for (let i = 0; i < event.results.length; i++) {
                                    const transcript = event.results[i][0].transcript;
                                    if (event.results[i].isFinal) {
                                        finalTranscript += transcript + ' ';
                                    } else {
                                        interimTranscript += transcript;
                                    }
                                }
                                
                                document.getElementById('transcript').innerHTML = 
                                    '<strong>Final:</strong> ' + finalTranscript + 
                                    '<br><em style="color: #666;">Interim:</em> ' + interimTranscript;
                            };
                            
                            recognition.onend = function() {
                                document.getElementById('status').innerHTML = '✅ Recording complete - ' + finalTranscript.split(' ').length + ' words captured';
                                document.getElementById('start-btn').disabled = false;
                                document.getElementById('stop-btn').disabled = true;
                                isRecording = false;
                                
                                // Send finalTranscript to Streamlit using setComponentValue
                                if (finalTranscript.trim() && Streamlit) {
                                    Streamlit.setComponentValue(finalTranscript.trim());
                                }
                            };
                            
                            recognition.onerror = function(event) {
                                document.getElementById('status').innerHTML = '❌ Error: ' + event.error + ' - Please try again';
                                document.getElementById('start-btn').disabled = false;
                                document.getElementById('stop-btn').disabled = true;
                                isRecording = false;
                            };
                        } else {
                            document.body.innerHTML = 
                                '<div style="color: red; font-size: 18px; text-align: center; padding: 20px;">' +
                                '❌ Speech recognition not supported in this browser.<br>' +
                                'Please use Chrome, Edge, or Safari.</div>';
                        }
                        
                        function startRecording() {
                            if (recognition && !isRecording) {
                                finalTranscript = '';
                                recognition.start();
                                isRecording = true;
                            }
                        }
                        
                        function stopRecording() {
                            if (recognition && isRecording) {
                                recognition.stop();
                            }
                        }
                    </script>
                </body>
                </html>
                """
                
                # Render the speech component and capture return value
                transcript_result = components.html(speech_html, height=300)
                
                # Handle the transcript result from JavaScript
                if transcript_result:
                    st.session_state.speech_transcript = transcript_result
                    st.success(f"✅ Captured: {transcript_result}")
                
                # Submit captured speech or manual input
                speech_input = st.text_area(
                    "Edit transcript or type manually:",
                    value=st.session_state.speech_transcript,
                    height=100,
                    key="speech_manual"
                )
                
                if speech_input and speech_input.strip():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button("🎤 Submit Voice Response", type="primary", use_container_width=True):
                            st.session_state.is_voice_response = True
                            if submit_response(speech_input.strip()):
                                st.session_state.speech_transcript = ''
                                st.rerun()
                    with col2:
                        if st.button("🔄 Clear", use_container_width=True):
                            st.session_state.speech_transcript = ''
                            st.rerun()
                
                st.markdown("---")
                
                # File Upload Fallback
                st.markdown("#### 📁 Upload Audio File (Backup)")
                uploaded_audio = st.file_uploader(
                    "Upload audio file if browser recording doesn't work",
                    type=['wav', 'mp3', 'm4a', 'ogg', 'webm']
                )
                
                if uploaded_audio is not None:
                    st.audio(uploaded_audio)
                    if st.button("🔄 Transcribe File", use_container_width=True):
                        with st.spinner("🎯 Transcribing audio..."):
                            try:
                                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_audio.name.split('.')[-1]}") as tmp_file:
                                    tmp_file.write(uploaded_audio.read())
                                    tmp_file_path = tmp_file.name
                                
                                with open(tmp_file_path, 'rb') as f:
                                    audio_bytes = f.read()
                                transcript = transcribe_audio_aws(audio_bytes)
                                
                                os.unlink(tmp_file_path)
                                
                                if transcript:
                                    st.success(f"✅ Transcribed: {transcript}")
                                    st.session_state.speech_transcript = transcript
                                    st.rerun()
                                else:
                                    st.error("❌ Transcription failed")
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")


# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>AI Interview Coach</strong> | AWS Bedrock • Transcribe • Textract • DynamoDB • Polly</p>
    <p>Built for AWS Hackathon 2024</p>
</div>
""", unsafe_allow_html=True)