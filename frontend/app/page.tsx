"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useState } from "react";
import { PracticeInterview } from "@/components/PracticeInterview";
import { MockInterview } from "@/components/MockInterview";

export default function Home() {
  const [mode, setMode] = useState<"landing" | "practice" | "mock">("landing");

  if (mode === "practice") {
    return <PracticeInterview onBack={() => setMode("landing")} />;
  }

  if (mode === "mock") {
    return <MockInterview onBack={() => setMode("landing")} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent mb-4">
            🎤 AI Interview Coach
          </h1>
          <p className="text-xl text-gray-600">
            Master your interviews with AI-powered feedback and real-time coaching
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 mt-12">
          <Card className="hover:shadow-2xl transition-all duration-300 border-2 hover:border-indigo-400">
            <CardHeader className="bg-gradient-to-br from-indigo-50 to-blue-50">
              <div className="text-5xl mb-4">📚</div>
              <CardTitle className="text-2xl">Practice Interview</CardTitle>
              <p className="text-gray-600 text-sm mt-2">
                Get instant feedback after each question
              </p>
            </CardHeader>
            <CardContent className="space-y-4 pt-6">
              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <span className="text-green-500 text-xl">✓</span>
                  <p className="text-sm">Immediate AI feedback after every answer</p>
                </div>
                <div className="flex items-start gap-3">
                  <span className="text-green-500 text-xl">✓</span>
                  <p className="text-sm">Detailed analysis of strengths & weaknesses</p>
                </div>
                <div className="flex items-start gap-3">
                  <span className="text-green-500 text-xl">✓</span>
                  <p className="text-sm">Personalized improvement suggestions</p>
                </div>
                <div className="flex items-start gap-3">
                  <span className="text-green-500 text-xl">✓</span>
                  <p className="text-sm">End interview anytime and get summary</p>
                </div>
                <div className="flex items-start gap-3">
                  <span className="text-green-500 text-xl">✓</span>
                  <p className="text-sm">Perfect for learning and skill building</p>
                </div>
              </div>
              
              <Button 
                onClick={() => setMode("practice")} 
                className="w-full bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700 text-lg py-6"
              >
                Start Practice Mode
              </Button>
            </CardContent>
          </Card>

          <Card className="hover:shadow-2xl transition-all duration-300 border-2 hover:border-purple-400">
            <CardHeader className="bg-gradient-to-br from-purple-50 to-pink-50">
              <div className="text-5xl mb-4">🎯</div>
              <CardTitle className="text-2xl">Full Mock Interview</CardTitle>
              <p className="text-gray-600 text-sm mt-2">
                Simulate real interview with 10-minute session
              </p>
            </CardHeader>
            <CardContent className="space-y-4 pt-6">
              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <span className="text-purple-500 text-xl">✓</span>
                  <p className="text-sm">10-minute timed interview experience</p>
                </div>
                <div className="flex items-start gap-3">
                  <span className="text-purple-500 text-xl">✓</span>
                  <p className="text-sm">Comprehensive feedback at the end</p>
                </div>
                <div className="flex items-start gap-3">
                  <span className="text-purple-500 text-xl">✓</span>
                  <p className="text-sm">Compare your answers vs. expected responses</p>
                </div>
                <div className="flex items-start gap-3">
                  <span className="text-purple-500 text-xl">✓</span>
                  <p className="text-sm">Overall performance score & metrics</p>
                </div>
                <div className="flex items-start gap-3">
                  <span className="text-purple-500 text-xl">✓</span>
                  <p className="text-sm">Realistic interview simulation</p>
                </div>
              </div>
              
              <Button 
                onClick={() => setMode("mock")} 
                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-lg py-6"
              >
                Start Mock Interview
              </Button>
            </CardContent>
          </Card>
        </div>

        <div className="mt-12 text-center">
          <Card className="bg-gradient-to-r from-slate-50 to-gray-50">
            <CardContent className="py-8">
              <h3 className="text-xl font-semibold mb-4">Powered by AWS AI Services</h3>
              <div className="flex justify-center gap-8 text-sm text-gray-600">
                <span>🎙️ Amazon Transcribe</span>
                <span>🤖 Claude (Bedrock)</span>
                <span>🔊 Amazon Polly</span>
                <span>💾 DynamoDB</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
