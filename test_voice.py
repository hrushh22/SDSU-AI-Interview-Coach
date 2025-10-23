#!/usr/bin/env python3
"""
Test voice recording functionality
"""
import streamlit as st

st.title("Voice Recording Test")

try:
    from streamlit_audiorecorder import audiorecorder
    
    st.info("Click START to begin recording. Recording continues even during pauses. Click STOP when finished.")
    
    # Audio recording
    audio_data = audiorecorder("Click to record", "Click to stop recording")
    
    if len(audio_data) > 0:
        st.success("Recording captured successfully!")
        st.audio(audio_data, format='audio/wav')
        
        # Test transcription
        if st.button("Test Transcription"):
            try:
                import whisper
                import tempfile
                import os
                
                # Save audio to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                    tmp_file.write(audio_data.tobytes())
                    tmp_file_path = tmp_file.name
                
                # Load Whisper model
                model = whisper.load_model("base")
                
                # Transcribe
                result = model.transcribe(tmp_file_path)
                
                # Clean up
                os.unlink(tmp_file_path)
                
                st.success(f"Transcription: {result['text']}")
                
            except Exception as e:
                st.error(f"Transcription error: {e}")
    else:
        st.info("No recording yet. Click the record button above.")
        
except ImportError as e:
    st.error(f"Import error: {e}")
    st.info("Run: pip install streamlit-audiorecorder")