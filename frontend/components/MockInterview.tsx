"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useState, useRef, useEffect } from "react";

interface MockInterviewProps {
  onBack: () => void;
}

export function MockInterview({ onBack }: MockInterviewProps) {
  const [step, setStep] = useState<"setup" | "interview" | "complete">("setup");
  const [jobTitle, setJobTitle] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [resumeText, setResumeText] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [questions, setQuestions] = useState<string[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [recording, setRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [loading, setLoading] = useState(false);
  const [responses, setResponses] = useState<any[]>([]);
  const [recordingTime, setRecordingTime] = useState(0);
  const [totalTime, setTotalTime] = useState(0);
  const [timerStarted, setTimerStarted] = useState(false);
  const [playingAudio, setPlayingAudio] = useState(false);
  const [bodyLanguageEnabled, setBodyLanguageEnabled] = useState(true);
  const [bodyLanguageAlerts, setBodyLanguageAlerts] = useState<any[]>([]);
  const [bodyLanguageReport, setBodyLanguageReport] = useState<any>(null);
  const [showAlert, setShowAlert] = useState(false);
  const [currentAlert, setCurrentAlert] = useState("");
  const [captureCount, setCaptureCount] = useState(0);
  const recognitionRef = useRef<any>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const totalTimerRef = useRef<NodeJS.Timeout | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const bodyLanguageTimerRef = useRef<NodeJS.Timeout | null>(null);

  const MAX_TIME = 600; // 10 minutes

  useEffect(() => {
    if (timerStarted && totalTime < MAX_TIME) {
      totalTimerRef.current = setInterval(() => {
        setTotalTime(prev => {
          if (prev >= MAX_TIME - 1) {
            endInterview();
            return MAX_TIME;
          }
          return prev + 1;
        });
      }, 1000);
    }
    return () => {
      if (totalTimerRef.current) clearInterval(totalTimerRef.current);
    };
  }, [timerStarted]);

  useEffect(() => {
    if (step === "interview" && bodyLanguageEnabled && sessionId) {
      startWebcam();
      setTimeout(() => {
        captureAndAnalyzeFrame();
        bodyLanguageTimerRef.current = setInterval(() => {
          captureAndAnalyzeFrame();
        }, 5000);
      }, 3000);
    }
    return () => {
      if (bodyLanguageTimerRef.current) clearInterval(bodyLanguageTimerRef.current);
      stopWebcam();
    };
  }, [step, bodyLanguageEnabled, sessionId]);

  const startWebcam = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
    } catch (err) {
      console.error("Webcam error:", err);
      setBodyLanguageEnabled(false);
    }
  };

  const stopWebcam = () => {
    if (videoRef.current?.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach(track => track.stop());
    }
  };

  const captureAndAnalyzeFrame = async () => {
    if (!videoRef.current || !canvasRef.current || !sessionId) {
      console.log("Skipping capture - missing refs or sessionId");
      return;
    }
    
    const video = videoRef.current;
    if (video.readyState !== video.HAVE_ENOUGH_DATA) {
      console.log("Video not ready yet");
      return;
    }
    
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const imageData = canvas.toDataURL('image/jpeg', 0.7);
    const base64Image = imageData.split(',')[1];
    
    if (!base64Image || base64Image.length < 100) {
      console.log("Invalid image data");
      return;
    }
    
    console.log(`Capturing frame #${captureCount + 1} at ${totalTime}s`);
    setCaptureCount(prev => prev + 1);
    
    try {
      const res = await fetch("http://localhost:8000/analyze-body-language", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          image_base64: base64Image,
          timestamp: totalTime,
          question: questions[currentQuestionIndex] || "",
          question_type: "behavioral",
          user_state: recording ? "speaking" : "listening"
        }),
      });
      const data = await res.json();
      const severity = data.severity_level || "low";
      const tip = data.actionable_tip || "";
      console.log(`${severity === 'high' ? '🚨' : severity === 'medium' ? '⚠️' : '✅'} [${totalTime}s] ${severity.toUpperCase()}: ${tip}`);
      
      if (!data.error) {
        if (severity === "high" || severity === "medium") {
          const alertMsg = tip || "Check your posture and eye contact";
          setBodyLanguageAlerts(prev => [...prev, { timestamp: totalTime, tip: alertMsg, severity }]);
          setCurrentAlert(alertMsg);
          setShowAlert(true);
          setTimeout(() => setShowAlert(false), severity === "high" ? 8000 : 5000);
        }
      } else {
        console.error("Body language API error:", data.error);
      }
    } catch (err) {
      console.error("Body language analysis error:", err);
    }
  };

  const handleResumeUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch("http://localhost:8000/upload-resume", { method: "POST", body: formData });
      const data = await res.json();
      if (data.resume_text) setResumeText(data.resume_text);
    } catch (err) {
      alert("Error uploading resume");
    } finally {
      setLoading(false);
    }
  };

  const startInterview = async () => {
    if (!jobTitle.trim() || !jobDescription.trim() || !resumeText.trim()) {
      alert("Please provide all required fields");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/start-interview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_title: jobTitle, job_description: jobDescription, resume_text: resumeText }),
      });
      const data = await res.json();
      if (data.error) {
        alert(data.error);
        return;
      }
      setSessionId(data.session_id);
      const allQuestions = [data.question];
      for (let i = 1; i < data.total_questions; i++) {
        const nextRes = await fetch("http://localhost:8000/get-next-question", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: data.session_id, question_index: i }),
        });
        const nextData = await nextRes.json();
        if (!nextData.completed) allQuestions.push(nextData.question);
      }
      setQuestions(allQuestions);
      setStep("interview");
      setTimerStarted(true);
      playQuestionAudio(allQuestions[0]);
    } catch (err) {
      alert("Error starting interview");
    } finally {
      setLoading(false);
    }
  };

  const startRecording = async () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Speech recognition not supported. Use Chrome.");
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    let finalTranscript = '';
    recognition.onresult = (event: any) => {
      let interimTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript + ' ';
        } else {
          interimTranscript += transcript;
        }
      }
      setTranscript(finalTranscript + interimTranscript);
    };
    recognition.onend = () => {
      setRecording(false);
      if (timerRef.current) clearInterval(timerRef.current);
    };
    recognitionRef.current = recognition;
    recognition.start();
    setRecording(true);
    setRecordingTime(0);
    setTranscript('');
    timerRef.current = setInterval(() => setRecordingTime(prev => prev + 1), 1000);
  };

  const stopRecording = () => {
    if (recognitionRef.current) recognitionRef.current.stop();
    if (timerRef.current) clearInterval(timerRef.current);
    setRecording(false);
  };

  const playQuestionAudio = async (text: string) => {
    try {
      setPlayingAudio(true);
      const formData = new FormData();
      formData.append("text", text);
      const res = await fetch("http://localhost:8000/text-to-speech", { method: "POST", body: formData });
      const data = await res.json();
      if (data.audio) {
        const audio = new Audio(`data:audio/mp3;base64,${data.audio}`);
        audioRef.current = audio;
        audio.onended = () => setPlayingAudio(false);
        await audio.play();
      }
    } catch (err) {
      console.error("Audio playback error:", err);
      setPlayingAudio(false);
    }
  };

  const saveAnswer = () => {
    setResponses([...responses, { question: questions[currentQuestionIndex], response: transcript, time: recordingTime }]);
    if (currentQuestionIndex < questions.length - 1) {
      const nextIndex = currentQuestionIndex + 1;
      setCurrentQuestionIndex(nextIndex);
      setTranscript("");
      setRecordingTime(0);
      playQuestionAudio(questions[nextIndex]);
    } else {
      endInterview();
    }
  };

  const endInterview = async () => {
    if (totalTimerRef.current) clearInterval(totalTimerRef.current);
    if (bodyLanguageTimerRef.current) clearInterval(bodyLanguageTimerRef.current);
    stopWebcam();
    setLoading(true);
    const allResponses = transcript ? [...responses, { question: questions[currentQuestionIndex], response: transcript, time: recordingTime }] : responses;
    
    const feedbackPromises = allResponses.map(async (r) => {
      try {
        const res = await fetch("http://localhost:8000/get-feedback", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_id: sessionId,
            question: r.question,
            response: r.response,
            question_type: "behavioral",
            word_count: r.response.split(/\s+/).length,
            duration: r.time,
            request_followup: false
          }),
        });
        const data = await res.json();
        return { ...r, feedback: data.feedback, score: data.score || 0, expected: data.expected_answer || "N/A" };
      } catch {
        return { ...r, feedback: "Error getting feedback", score: 0, expected: "N/A" };
      }
    });

    const responsesWithFeedback = await Promise.all(feedbackPromises);
    setResponses(responsesWithFeedback);
    
    // Get body language report
    if (bodyLanguageEnabled && sessionId) {
      try {
        console.log("Fetching body language report for session:", sessionId);
        const blRes = await fetch(`http://localhost:8000/body-language-report/${sessionId}`);
        const blData = await blRes.json();
        console.log("Body language report received:", blData);
        if (!blData.error && blData.overall_scores) {
          setBodyLanguageReport(blData);
        } else {
          console.log("No body language data or error:", blData);
        }
      } catch (err) {
        console.error("Error fetching body language report:", err);
      }
    }
    
    await fetch(`http://localhost:8000/complete-session/${sessionId}`, { method: "POST" });
    setStep("complete");
    setLoading(false);
  };

  if (step === "complete") {
    const avgScore = responses.length > 0 ? responses.reduce((a, b) => a + b.score, 0) / responses.length : 0;
    const strengths = ["Structured responses", "Good examples"];
    const weaknesses = ["Could be more concise", "Add more technical details"];

    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50 p-8">
        <div className="max-w-5xl mx-auto space-y-6">
          <Card>
            <CardHeader className="bg-gradient-to-r from-purple-50 to-pink-50">
              <CardTitle className="text-3xl">🎯 Mock Interview Complete!</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6 pt-6">
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-purple-50 p-6 rounded-lg text-center border-2 border-purple-200">
                  <p className="text-sm text-gray-600">Questions Answered</p>
                  <p className="text-4xl font-bold text-purple-600">{responses.length}</p>
                </div>
                <div className="bg-green-50 p-6 rounded-lg text-center border-2 border-green-200">
                  <p className="text-sm text-gray-600">Average Score</p>
                  <p className="text-4xl font-bold text-green-600">{avgScore.toFixed(1)}/10</p>
                </div>
                <div className="bg-blue-50 p-6 rounded-lg text-center border-2 border-blue-200">
                  <p className="text-sm text-gray-600">Total Time</p>
                  <p className="text-4xl font-bold text-blue-600">{Math.floor(totalTime / 60)}:{(totalTime % 60).toString().padStart(2, '0')}</p>
                </div>
              </div>

              <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-200">
                <CardHeader>
                  <CardTitle className="text-xl text-green-700">💪 Strengths</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {strengths.map((s, i) => <li key={i} className="flex items-center gap-2"><span className="text-green-600 text-xl">✓</span>{s}</li>)}
                  </ul>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-br from-orange-50 to-red-50 border-2 border-orange-200">
                <CardHeader>
                  <CardTitle className="text-xl text-orange-700">⚠️ Areas to Improve</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {weaknesses.map((w, i) => <li key={i} className="flex items-center gap-2"><span className="text-orange-600 text-xl">→</span>{w}</li>)}
                  </ul>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200">
                <CardHeader>
                  <CardTitle className="text-xl text-blue-700">📈 How to Improve</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 text-sm">
                    <li>• Practice answering within 2 minutes per question</li>
                    <li>• Include specific metrics and outcomes in your examples</li>
                    <li>• Research common questions for {jobTitle} roles</li>
                  </ul>
                </CardContent>
              </Card>

              {bodyLanguageReport && bodyLanguageReport.overall_scores && (
                <Card className="bg-gradient-to-br from-indigo-50 to-purple-50 border-2 border-indigo-200">
                  <CardHeader>
                    <CardTitle className="text-xl text-indigo-700">📹 Body Language Analysis</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-white p-4 rounded-lg">
                        <p className="text-sm text-gray-600">Eye Contact</p>
                        <p className="text-2xl font-bold text-indigo-600">{bodyLanguageReport.overall_scores.eye_contact}/10</p>
                      </div>
                      <div className="bg-white p-4 rounded-lg">
                        <p className="text-sm text-gray-600">Posture</p>
                        <p className="text-2xl font-bold text-indigo-600">{bodyLanguageReport.overall_scores.posture}/10</p>
                      </div>
                      <div className="bg-white p-4 rounded-lg">
                        <p className="text-sm text-gray-600">Engagement</p>
                        <p className="text-2xl font-bold text-indigo-600">{bodyLanguageReport.overall_scores.engagement}/10</p>
                      </div>
                      <div className="bg-white p-4 rounded-lg">
                        <p className="text-sm text-gray-600">Professionalism</p>
                        <p className="text-2xl font-bold text-indigo-600">{bodyLanguageReport.overall_scores.professionalism}/10</p>
                      </div>
                    </div>
                    {bodyLanguageReport.top_strengths?.length > 0 && (
                      <div>
                        <p className="font-semibold text-sm mb-2">💪 Body Language Strengths:</p>
                        <ul className="space-y-1">
                          {bodyLanguageReport.top_strengths.map((s: string, i: number) => (
                            <li key={i} className="text-sm flex items-center gap-2">
                              <span className="text-green-600">✓</span>{s}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {bodyLanguageReport.top_improvements?.length > 0 && (
                      <div>
                        <p className="font-semibold text-sm mb-2">⚠️ Body Language Improvements:</p>
                        <ul className="space-y-1">
                          {bodyLanguageReport.top_improvements.map((i: string, idx: number) => (
                            <li key={idx} className="text-sm flex items-center gap-2">
                              <span className="text-orange-600">→</span>{i}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    <p className="text-xs text-gray-500">Analyzed {bodyLanguageReport.total_frames_analyzed} frames during interview</p>
                  </CardContent>
                </Card>
              )}

              <div className="space-y-4">
                <h3 className="font-semibold text-xl">📊 Question-by-Question Analysis</h3>
                {responses.map((r, i) => (
                  <details key={i} className="bg-white p-4 rounded-lg border-2 hover:border-purple-300">
                    <summary className="cursor-pointer font-medium text-lg">Q{i + 1}: {r.question.substring(0, 80)}... (Score: {r.score}/10)</summary>
                    <div className="mt-4 space-y-3">
                      <div className="bg-slate-50 p-3 rounded border">
                        <p className="font-semibold text-sm text-gray-600">Your Answer:</p>
                        <p className="text-sm mt-1">{r.response}</p>
                      </div>
                      <div className="bg-blue-50 p-3 rounded border border-blue-200">
                        <p className="font-semibold text-sm text-blue-700">Expected Answer:</p>
                        <p className="text-sm mt-1">{r.expected}</p>
                      </div>
                      <div className="bg-green-50 p-3 rounded border border-green-200">
                        <p className="font-semibold text-sm text-green-700">AI Feedback:</p>
                        <p className="text-sm mt-1 whitespace-pre-wrap">{r.feedback}</p>
                      </div>
                    </div>
                  </details>
                ))}
              </div>

              <div className="flex gap-4">
                <Button onClick={onBack} className="flex-1" variant="outline">🏠 Back to Home</Button>
                <Button onClick={() => window.location.reload()} className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600">🔄 New Mock Interview</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (step === "interview") {
    const timeLeft = MAX_TIME - totalTime;
    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;

    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50 p-8">
        <div className="max-w-4xl mx-auto space-y-6">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold">Question {currentQuestionIndex + 1} of {questions.length}</h1>
            <div className="flex gap-4 items-center">
              <div className={`text-xl font-bold px-4 py-2 rounded-lg ${timeLeft < 60 ? 'bg-red-100 text-red-600' : 'bg-blue-100 text-blue-600'}`}>
                ⏱️ {minutes}:{seconds.toString().padStart(2, '0')}
              </div>
              <Button variant="destructive" onClick={endInterview}>End Interview</Button>
            </div>
          </div>

          {showAlert && currentAlert && (
            <div className="fixed top-20 right-8 z-50 animate-pulse">
              <Card className="bg-gradient-to-r from-red-500 to-orange-500 border-4 border-red-600 shadow-2xl max-w-md">
                <CardContent className="py-4 px-6">
                  <div className="flex items-center gap-3">
                    <span className="text-4xl animate-bounce">🚨</span>
                    <div className="flex-1">
                      <p className="text-white font-bold text-lg">IMMEDIATE ACTION!</p>
                      <p className="text-white font-semibold text-sm">{currentAlert}</p>
                    </div>
                    <button onClick={() => setShowAlert(false)} className="text-white text-2xl hover:text-gray-200">×</button>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          <Card>
            <CardHeader className="bg-gradient-to-r from-purple-50 to-pink-50">
              <CardTitle className="text-xl flex items-center justify-between">
                <span>❓ {questions[currentQuestionIndex]}</span>
                <Button onClick={() => playQuestionAudio(questions[currentQuestionIndex])} disabled={playingAudio} variant="outline" size="sm">
                  {playingAudio ? "🔊 Playing..." : "🔊 Replay"}
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 pt-6">
              {bodyLanguageEnabled && (
                <div className="bg-gradient-to-r from-indigo-50 to-purple-50 p-4 rounded-lg border-2 border-indigo-300 shadow-md">
                  <div className="flex items-center gap-4">
                    <div className="relative">
                      <video ref={videoRef} autoPlay playsInline className="w-48 h-36 rounded-lg border-2 border-indigo-400 object-cover shadow-lg" muted />
                      <div className="absolute top-2 right-2 bg-red-500 rounded-full w-3 h-3 animate-pulse"></div>
                      <div className="absolute bottom-2 left-2 bg-black bg-opacity-60 text-white text-xs px-2 py-1 rounded">🔴 LIVE</div>
                    </div>
                    <div className="flex-1">
                      <p className="text-base font-bold text-indigo-900 flex items-center gap-2">
                        <span className="text-2xl">👁️</span> AI Monitoring Active
                      </p>
                      <p className="text-sm text-indigo-700 mt-1">Analyzing posture, eye contact, and engagement</p>
                      <div className="mt-2 flex gap-2 flex-wrap">
                        <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded flex items-center gap-1">
                          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span> Active
                        </span>
                      </div>
                    </div>
                  </div>
                  <canvas ref={canvasRef} className="hidden" />
                </div>
              )}
              {!recording && !transcript && (
                <Button onClick={startRecording} className="w-full py-8 text-lg bg-gradient-to-r from-red-500 to-pink-500 hover:from-red-600 hover:to-pink-600">
                  🎤 Start Recording Answer
                </Button>
              )}

              {recording && (
                <div className="space-y-4">
                  <div className="bg-red-50 p-6 rounded-lg text-center border-2 border-red-200">
                    <p className="text-red-600 font-bold text-xl">🔴 Recording... {recordingTime}s</p>
                    <p className="text-sm text-gray-600 mt-2">{transcript}</p>
                  </div>
                  <Button onClick={stopRecording} variant="destructive" className="w-full py-6">⏹️ Stop Recording</Button>
                </div>
              )}

              {transcript && !recording && (
                <div className="space-y-4">
                  <div className="bg-slate-50 p-4 rounded-lg border">
                    <p className="font-semibold mb-2">Your Answer:</p>
                    <p className="whitespace-pre-wrap">{transcript}</p>
                    <p className="text-sm text-gray-600 mt-2">{transcript.split(/\s+/).length} words • {recordingTime}s</p>
                  </div>
                  <div className="flex gap-4">
                    <Button onClick={() => setTranscript("")} variant="outline" className="flex-1">🔄 Re-record</Button>
                    <Button onClick={saveAnswer} className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 py-6">
                      {currentQuestionIndex < questions.length - 1 ? "➡️ Next Question" : "🎉 Finish Interview"}
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <div className="bg-white p-4 rounded-lg border">
            <p className="text-sm text-gray-600">Progress: {responses.length} of {questions.length} questions answered</p>
            <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
              <div className="bg-gradient-to-r from-purple-600 to-pink-600 h-2 rounded-full" style={{ width: `${(responses.length / questions.length) * 100}%` }}></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50 p-8">
      <div className="max-w-4xl mx-auto">
        <Button onClick={onBack} variant="outline" className="mb-6">← Back</Button>
        <Card>
          <CardHeader className="bg-gradient-to-r from-purple-50 to-pink-50">
            <CardTitle className="text-3xl">🎯 Mock Interview Setup</CardTitle>
            <p className="text-gray-600 mt-2">10-minute timed interview with comprehensive feedback at the end</p>
          </CardHeader>
          <CardContent className="space-y-6 pt-6">
            <div className="space-y-4">
              <div className="bg-indigo-50 p-4 rounded-lg border border-indigo-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-indigo-900">📹 Body Language Analysis</p>
                    <p className="text-sm text-indigo-700">Real-time feedback on posture, eye contact, and engagement</p>
                  </div>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" checked={bodyLanguageEnabled} onChange={(e) => setBodyLanguageEnabled(e.target.checked)} className="w-5 h-5" />
                    <span className="text-sm font-medium">{bodyLanguageEnabled ? "Enabled" : "Disabled"}</span>
                  </label>
                </div>
              </div>
              <div>
                <Label>Job Title *</Label>
                <Input value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} placeholder="e.g., Software Engineer" className="mt-2" />
              </div>
              <div>
                <Label>Job Description *</Label>
                <textarea value={jobDescription} onChange={(e) => setJobDescription(e.target.value)} placeholder="Paste job description..." className="mt-2 w-full p-3 border rounded-lg min-h-[120px]" />
              </div>
              <div>
                <Label>Upload Resume *</Label>
                <Input type="file" accept=".pdf,.txt" onChange={handleResumeUpload} className="mt-2" />
                {resumeText && <p className="text-sm text-green-600 mt-2">✅ Resume loaded</p>}
              </div>
              <div>
                <Label>Or Paste Resume</Label>
                <textarea value={resumeText} onChange={(e) => setResumeText(e.target.value)} placeholder="Paste resume text..." className="mt-2 w-full p-3 border rounded-lg min-h-[120px]" />
              </div>
            </div>
            <Button onClick={startInterview} disabled={loading} className="w-full py-6 text-lg bg-gradient-to-r from-purple-600 to-pink-600">
              {loading ? "Starting..." : "🚀 Start 10-Minute Mock Interview"}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
