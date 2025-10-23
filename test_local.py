#!/usr/bin/env python3
"""
Test local functionality without API calls
"""
import streamlit as st

st.title("Local Test - AI Interview Coach")

# Test local feedback generation
def generate_local_feedback(response_text, question_type, metrics):
    """Generate feedback locally without API calls"""
    
    feedback_parts = []
    
    # Content analysis
    if len(response_text.split()) < 50:
        feedback_parts.append("⚠️ **Too Brief**: Your response is quite short. Aim for 100-200 words to provide sufficient detail.")
    elif len(response_text.split()) > 300:
        feedback_parts.append("⚠️ **Too Long**: Consider being more concise. Aim for 100-200 words.")
    else:
        feedback_parts.append("✅ **Good Length**: Your response length is appropriate.")
    
    # STAR method check for behavioral questions
    if question_type == 'behavioral':
        star_keywords = {
            'situation': ['situation', 'context', 'background', 'company', 'project', 'team'],
            'task': ['task', 'responsibility', 'role', 'assigned', 'needed', 'required'],
            'action': ['did', 'implemented', 'created', 'developed', 'analyzed', 'managed'],
            'result': ['result', 'outcome', 'achieved', 'improved', 'saved', 'increased']
        }
        
        star_score = 0
        missing_elements = []
        
        for element, keywords in star_keywords.items():
            if any(keyword in response_text.lower() for keyword in keywords):
                star_score += 1
            else:
                missing_elements.append(element.title())
        
        if star_score >= 3:
            feedback_parts.append(f"✅ **STAR Structure**: Good use of STAR method ({star_score}/4 elements).")
        else:
            feedback_parts.append(f"⚠️ **STAR Structure**: Missing {', '.join(missing_elements)}. Use Situation-Task-Action-Result format.")
    
    # Delivery feedback
    pace = metrics.get('pace_wpm', 0)
    if pace < 120:
        feedback_parts.append("🐢 **Pace**: Speaking too slowly. Aim for 120-160 WPM.")
    elif pace > 160:
        feedback_parts.append("🏃 **Pace**: Speaking too fast. Slow down for clarity.")
    else:
        feedback_parts.append("✅ **Pace**: Good speaking pace.")
    
    filler_rate = metrics.get('filler_rate', 0)
    if filler_rate > 5:
        feedback_parts.append(f"⚠️ **Filler Words**: {filler_rate:.1f}% filler words. Practice reducing 'um', 'uh', 'like'.")
    else:
        feedback_parts.append("✅ **Clarity**: Minimal filler words, good clarity.")
    
    return "\n\n".join(feedback_parts)

# Test interface
st.write("## Test Local Feedback Generation")

test_response = st.text_area(
    "Enter a test response:",
    value="At my previous company, I was assigned the task of migrating our database to AWS. I analyzed the requirements, created a migration plan, and implemented it successfully. The result was 40% faster queries and $50k annual savings.",
    height=100
)

question_type = st.selectbox("Question Type:", ["behavioral", "tell_me_about", "why_this_job"])

if st.button("Generate Feedback"):
    # Calculate metrics
    words = test_response.split()
    word_count = len(words)
    estimated_duration = max((word_count / 145) * 60, 30)
    
    filler_words = ['um', 'uh', 'like', 'you know', 'so', 'actually', 'basically']
    filler_count = sum(test_response.lower().count(filler) for filler in filler_words)
    filler_rate = (filler_count / word_count * 100) if word_count > 0 else 0
    
    pace_wpm = int((word_count / estimated_duration) * 60) if estimated_duration > 0 else 0
    
    metrics = {
        'word_count': word_count,
        'duration': estimated_duration,
        'pace_wpm': pace_wpm,
        'filler_count': filler_count,
        'filler_rate': filler_rate
    }
    
    # Generate feedback
    feedback = generate_local_feedback(test_response, question_type, metrics)
    
    st.write("### Metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Words", word_count)
    with col2:
        st.metric("Pace", f"{pace_wpm} WPM")
    with col3:
        st.metric("Filler Rate", f"{filler_rate:.1f}%")
    
    st.write("### AI Feedback")
    st.markdown(feedback)

st.write("---")
st.write("✅ **Local feedback generation working!**")
st.write("🎯 **No API calls needed - everything runs locally**")