"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useState, useRef } from "react";

export default function Home() {
  const [jobTitle, setJobTitle] = useState("Software Engineer");
  const [jobDescription, setJobDescription] = useState("");
  const [resumeText, setResumeText] = useState("");
  const [started, setStarted] = useState(false);
  const [question, setQuestion] = useState("");
  const [questionNum, setQuestionNum] = useState(1);
  const [totalQuestions, setTotalQuestions] = useState(5);
  const [recording, setRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [feedback, setFeedback] = useState("");
  const [loading, setLoading] = useState(false);
  const [responses, setResponses] = useState<any[]>([]);
  const [complete, setComplete] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const handleResumeUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);
    
    try {
      const res = await fetch("http://localhost:8000/upload-resume", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (data.resume_text) {
        setResumeText(data.resume_text);
        alert(`✅ Resume uploaded: ${data.chars} characters`);
      }
    } catch (err) {
      alert("Error uploading resume");
    } finally {
      setLoading(false);
    }
  };

  const startInterview = async () => {
    if (!jobTitle.trim()) {
      alert("Please enter a job title");
      return;
    }
    
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/start-interview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          job_title: jobTitle, 
          job_description: jobDescription,
          resume_text: resumeText,
          question_number: questionNum 
        }),
      });
      const data = await res.json();
      setQuestion(data.question);
      setTotalQuestions(data.total_questions);
      setStarted(true);
    } catch (err) {
      alert("Error starting interview");
    } finally {
      setLoading(false);
    }
  };

  const playQuestion = async () => {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("text", question);
      
      const res = await fetch("http://localhost:8000/text-to-speech", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      
      if (data.audio) {
        const audio = new Audio(`data:audio/mp3;base64,${data.audio}`);
        audio.play();
      }
    } catch (err) {
      alert("Error playing audio");
    } finally {
      setLoading(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      setRecordingTime(0);

      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        if (timerRef.current) clearInterval(timerRef.current);
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" });
        await transcribeAudio(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setRecording(true);
    } catch (err) {
      alert("Microphone access denied");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  };

  const transcribeAudio = async (audioBlob: Blob) => {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("audio", audioBlob, "recording.wav");

      const res = await fetch("http://localhost:8000/transcribe-audio", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setTranscript(data.transcript);
    } catch (err) {
      alert("Transcription failed");
    } finally {
      setLoading(false);
    }
  };

  const submitAnswer = async () => {
    setLoading(true);
    try {
      const words = transcript.split(/\s+/).filter(w => w.length > 0);
      
      const res = await fetch("http://localhost:8000/get-feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          response: transcript,
          question_type: "behavioral",
          word_count: words.length,
          duration: recordingTime
        }),
      });
      const data = await res.json();
      setFeedback(data.feedback);
      
      setResponses([...responses, {
        question,
        response: transcript,
        feedback: data.feedback,
        pace_wpm: data.pace_wpm
      }]);
    } catch (err) {
      alert("Error getting feedback");
    } finally {
      setLoading(false);
    }
  };

  const nextQuestion = () => {
    if (questionNum >= totalQuestions) {
      setComplete(true);
      return;
    }
    
    setQuestionNum(questionNum + 1);
    setTranscript("");
    setFeedback("");
    setRecordingTime(0);
    startInterview();
  };

  const resetInterview = () => {
    setStarted(false);
    setComplete(false);
    setQuestionNum(1);
    setTranscript("");
    setFeedback("");
    setResponses([]);
    setRecordingTime(0);
  };

  if (complete) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-100 to-slate-300 p-8">
        <div className="max-w-4xl mx-auto space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-2xl">🎉 Interview Complete!</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-blue-50 p-4 rounded">
                  <p className="text-sm text-gray-600">Questions</p>
                  <p className="text-2xl font-bold">{responses.length}</p>
                </div>
                <div className="bg-green-50 p-4 rounded">
                  <p className="text-sm text-gray-600">Avg Pace</p>
                  <p className="text-2xl font-bold">
                    {Math.round(responses.reduce((a, b) => a + (b.pace_wpm || 0), 0) / responses.length)} WPM
                  </p>
                </div>
                <div className="bg-purple-50 p-4 rounded">
                  <p className="text-sm text-gray-600">Total Words</p>
                  <p className="text-2xl font-bold">
                    {responses.reduce((a, b) => a + b.response.split(/\s+/).length, 0)}
                  </p>
                </div>
              </div>
              
              <div className="space-y-4 mt-6">
                <h3 className="font-semibold text-lg">Your Responses:</h3>
                {responses.map((r, i) => (
                  <details key={i} className="bg-white p-4 rounded border">
                    <summary className="cursor-pointer font-medium">
                      Question {i + 1}: {r.question.substring(0, 60)}...
                    </summary>
                    <div className="mt-4 space-y-2">
                      <p className="text-sm"><strong>Your Answer:</strong> {r.response}</p>
                      <div className="bg-green-50 p-3 rounded mt-2">
                        <p className="text-sm whitespace-pre-wrap">{r.feedback}</p>
                      </div>
                    </div>
                  </details>
                ))}
              </div>
              
              <Button onClick={resetInterview} className="w-full mt-4">
                🔄 Start New Interview
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (!started) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-100 to-slate-300 p-8">
        <div className="max-w-4xl mx-auto">
          <Card>
            <CardHeader>
              <CardTitle className="text-3xl">🎤 AI Interview Coach</CardTitle>
              <p className="text-gray-600">Practice interviews with real-time AI feedback powered by AWS</p>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="job-title">Job Title *</Label>
                    <Input
                      id="job-title"
                      value={jobTitle}
                      onChange={(e) => setJobTitle(e.target.value)}
                      placeholder="e.g., Software Engineer"
                      className="mt-2"
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="job-desc">Job Description (Optional)</Label>
                    <textarea
                      id="job-desc"
                      value={jobDescription}
                      onChange={(e) => setJobDescription(e.target.value)}
                      placeholder="Paste job description for tailored questions..."
                      className="mt-2 w-full p-2 border rounded min-h-[100px]"
                    />
                  </div>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="resume">Resume (Optional)</Label>
                    <Input
                      id="resume"
                      type="file"
                      accept=".pdf,.txt"
                      onChange={handleResumeUpload}
                      className="mt-2"
                    />
                    {resumeText && (
                      <p className="text-sm text-green-600 mt-2">
                        ✅ Resume loaded ({resumeText.length} chars)
                      </p>
                    )}
                  </div>
                  
                  <div>
                    <Label>Or paste resume text:</Label>
                    <textarea
                      value={resumeText}
                      onChange={(e) => setResumeText(e.target.value)}
                      placeholder="Paste your resume here..."
                      className="mt-2 w-full p-2 border rounded min-h-[100px]"
                    />
                  </div>
                </div>
              </div>
              
              <Button 
                onClick={startInterview} 
                disabled={loading || !jobTitle.trim()} 
                className="w-full"
                size="lg"
              >
                {loading ? "Starting..." : "🚀 Start Interview Practice"}
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 to-slate-300 p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold">Question {questionNum} of {totalQuestions}</h1>
          <Button variant="outline" onClick={resetInterview}>🏠 Home</Button>
        </div>
        
        <Card>
          <CardHeader>
            <CardTitle>❓ Interview Question</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <p className="text-lg font-medium">{question}</p>
            </div>
            
            <Button onClick={playQuestion} disabled={loading} variant="outline">
              🔊 Play Question
            </Button>
            
            <div className="border-t pt-4">
              <h3 className="font-semibold mb-3">🎤 Your Answer</h3>
              
              {!recording && !transcript && (
                <Button onClick={startRecording} className="w-full" size="lg">
                  🎤 Start Recording
                </Button>
              )}
              
              {recording && (
                <div className="space-y-4">
                  <div className="bg-red-50 p-4 rounded text-center">
                    <p className="text-red-600 font-semibold">🔴 Recording... {recordingTime}s</p>
                  </div>
                  <Button onClick={stopRecording} variant="destructive" className="w-full" size="lg">
                    ⏹️ Stop Recording
                  </Button>
                </div>
              )}
              
              {loading && <p className="text-center py-4">Processing...</p>}
              
              {transcript && (
                <div className="space-y-4">
                  <div className="bg-slate-100 p-4 rounded">
                    <p className="font-semibold mb-2">📝 Your Answer:</p>
                    <p className="whitespace-pre-wrap">{transcript}</p>
                    <p className="text-sm text-gray-600 mt-2">
                      {transcript.split(/\s+/).length} words • {recordingTime}s
                    </p>
                  </div>
                  
                  {!feedback && (
                    <Button onClick={submitAnswer} disabled={loading} className="w-full">
                      Get AI Feedback
                    </Button>
                  )}
                </div>
              )}
              
              {feedback && (
                <div className="space-y-4">
                  <div className="bg-green-50 p-4 rounded">
                    <p className="font-semibold mb-2">🤖 AI Feedback:</p>
                    <div className="whitespace-pre-wrap text-sm">{feedback}</div>
                  </div>
                  <Button onClick={nextQuestion} className="w-full" size="lg">
                    {questionNum >= totalQuestions ? "🎉 Complete Interview" : "➡️ Next Question"}
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
