'use client'

import React, { useState } from 'react'
import { useWaveRiderStore } from '@/store/waverider-store'
import WaveRiderIDE from '@/components/ide/waverider-ide'

export function Landing() {
  const [isDemo, setIsDemo] = useState(false)
  const [demoStep, setDemoStep] = useState(0)
  const [showIDE, setShowIDE] = useState(false)
  const { setUser } = useWaveRiderStore()

  const handleGetStarted = () => {
    // Simulate user authentication and move to IDE
    const mockUser = {
      id: '1',
      email: 'demo@waverider.dev',
      name: 'Demo User',
      preferences: {
        theme: 'dark' as const,
        editor: {
          fontSize: 14,
          tabSize: 2,
          wordWrap: true,
          minimap: true,
          lineNumbers: true,
          autoSave: true
        },
        ai: {
          model: 'gpt-4' as const,
          temperature: 0.3,
          maxTokens: 2000,
          autoSuggestions: true,
          inlineCompletion: true
        }
      }
    }
    setUser(mockUser)
    setShowIDE(true)
  }

  const handleViewDemo = () => {
    setIsDemo(true)
    setDemoStep(0)
    // Start demo animation
    const steps = [
      "🤖 Planner Agent: Breaking down the task...",
      "📝 Coder Agent: Generating React components...",
      "🔧 Backend Agent: Setting up API endpoints...",
      "🎨 UI Agent: Styling with Tailwind CSS...",
      "🔍 Debugger Agent: Running tests...",
      "✅ Project created successfully!"
    ]
    
    let currentStep = 0
    const interval = setInterval(() => {
      if (currentStep < steps.length) {
        setDemoStep(currentStep)
        currentStep++
      } else {
        clearInterval(interval)
        setTimeout(() => setIsDemo(false), 2000)
      }
    }, 1500)
  }

  const features = [
    {
      icon: "🤖",
      title: "Autonomous Agents",
      description: "AI agents that plan, code, debug, and optimize your projects automatically"
    },
    {
      icon: "💻",
      title: "AI-Native Editor",
      description: "Monaco editor enhanced with predictive code completion and inline AI assistance"
    },
    {
      icon: "⚡",
      title: "Instant Workflows",
      description: "Automated pipelines for testing, deployment, and continuous integration"
    },
    {
      icon: "👥",
      title: "Real-time Collaboration",
      description: "Pair programming with AI and human developers in real-time"
    },
    {
      icon: "🛡️",
      title: "Security Built-in",
      description: "Automated vulnerability scanning and code provenance tracking"
    },
    {
      icon: "🚀",
      title: "Cloud Ready",
      description: "Deploy anywhere with Docker, Kubernetes, and cloud platform integration"
    }
  ]

  // Show IDE if user clicked Get Started
  if (showIDE) {
    return <WaveRiderIDE />
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #dbeafe, #ffffff, #f3e8ff)',
      padding: '0'
    }}>
      {/* Hero Section */}
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '80px 16px 64px',
        textAlign: 'center'
      }}>
        <div style={{ marginBottom: '64px' }}>
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            marginBottom: '24px'
          }}>
            <div style={{
              fontSize: '48px',
              marginRight: '16px',
              background: 'linear-gradient(135deg, #3b82f6, #9333ea)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}>
              🌊
            </div>
            <h1 style={{
              fontSize: '56px',
              fontWeight: 'bold',
              background: 'linear-gradient(135deg, #1f2937, #3b82f6)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              margin: 0
            }}>
              WaveRider
            </h1>
          </div>
          
          <p style={{
            fontSize: '24px',
            color: '#6b7280',
            marginBottom: '32px',
            maxWidth: '800px',
            margin: '0 auto 32px'
          }}>
            The Agentic AI-Native IDE that evolves beyond traditional coding
          </p>
          
          <p style={{
            fontSize: '18px',
            color: '#9ca3af',
            marginBottom: '48px',
            maxWidth: '600px',
            margin: '0 auto 48px'
          }}>
            Autonomous agents for planning, coding, debugging, and optimizing your projects while you focus on innovation
          </p>
          
          <div style={{
            display: 'flex',
            gap: '16px',
            justifyContent: 'center',
            alignItems: 'center',
            flexWrap: 'wrap'
          }}>
            <button 
              onClick={handleGetStarted}
              style={{
                background: 'linear-gradient(135deg, #3b82f6, #9333ea)',
                color: 'white',
                padding: '12px 32px',
                borderRadius: '8px',
                fontWeight: '600',
                border: 'none',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                cursor: 'pointer',
                fontSize: '16px',
                transition: 'transform 0.2s ease'
              }}
              onMouseOver={(e) => (e.target as HTMLButtonElement).style.transform = 'scale(1.05)'}
              onMouseOut={(e) => (e.target as HTMLButtonElement).style.transform = 'scale(1)'}
            >
              Get Started
            </button>
            <button 
              onClick={handleViewDemo}
              style={{
                border: '2px solid #d1d5db',
                color: '#374151',
                padding: '12px 32px',
                borderRadius: '8px',
                fontWeight: '600',
                background: 'white',
                cursor: 'pointer',
                fontSize: '16px',
                transition: 'all 0.2s ease'
              }}
              onMouseOver={(e) => {
                (e.target as HTMLButtonElement).style.borderColor = '#9333ea';
                (e.target as HTMLButtonElement).style.color = '#9333ea';
              }}
              onMouseOut={(e) => {
                (e.target as HTMLButtonElement).style.borderColor = '#d1d5db';
                (e.target as HTMLButtonElement).style.color = '#374151';
              }}
            >
              {isDemo ? 'Demo Running...' : 'View Demo'}
            </button>
          </div>
        </div>

        {/* Features Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '32px',
          marginBottom: '64px'
        }}>
          {features.map((feature, index) => (
            <div
              key={index}
              style={{
                background: 'rgba(255, 255, 255, 0.8)',
                backdropFilter: 'blur(10px)',
                padding: '32px',
                borderRadius: '16px',
                textAlign: 'center',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
                cursor: 'pointer',
                transition: 'transform 0.3s ease, box-shadow 0.3s ease'
              }}
              onMouseOver={(e) => {
                (e.currentTarget as HTMLElement).style.transform = 'translateY(-8px)';
                (e.currentTarget as HTMLElement).style.boxShadow = '0 12px 48px rgba(0, 0, 0, 0.15)';
              }}
              onMouseOut={(e) => {
                (e.currentTarget as HTMLElement).style.transform = 'translateY(0)';
                (e.currentTarget as HTMLElement).style.boxShadow = '0 8px 32px rgba(0, 0, 0, 0.1)';
              }}
            >
              <div style={{
                fontSize: '48px',
                marginBottom: '16px'
              }}>
                {feature.icon}
              </div>
              <h3 style={{
                fontSize: '20px',
                fontWeight: 'bold',
                color: '#1f2937',
                marginBottom: '12px'
              }}>
                {feature.title}
              </h3>
              <p style={{
                color: '#6b7280',
                lineHeight: '1.6'
              }}>
                {feature.description}
              </p>
            </div>
          ))}
        </div>

        {/* Demo Terminal */}
        <div style={{
          background: 'rgba(15, 23, 42, 0.95)',
          borderRadius: '12px',
          padding: '24px',
          marginTop: '64px',
          maxWidth: '800px',
          margin: '64px auto 0',
          boxShadow: '0 20px 64px rgba(0, 0, 0, 0.3)'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            marginBottom: '16px'
          }}>
            <div style={{
              display: 'flex',
              gap: '8px',
              marginRight: '16px'
            }}>
              <div style={{
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                background: '#ef4444'
              }}></div>
              <div style={{
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                background: '#f59e0b'
              }}></div>
              <div style={{
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                background: '#10b981'
              }}></div>
            </div>
            <div style={{
              color: '#94a3b8',
              fontSize: '14px',
              fontWeight: '500'
            }}>
              WaveRider Terminal
            </div>
          </div>
          
          <div style={{
            color: '#e2e8f0',
            fontFamily: 'monospace',
            fontSize: '14px'
          }}>
            <div style={{ color: '#10b981', marginBottom: '8px' }}>$ waverider create "Build a full-stack todo app"</div>
            <div style={{ color: '#d1d5db', marginBottom: '4px' }}>🤖 Planner Agent: Breaking down the task...</div>
            <div style={{ color: '#d1d5db', marginBottom: '4px' }}>📝 Coder Agent: Generating React components...</div>
            <div style={{ color: '#d1d5db', marginBottom: '4px' }}>🔧 Backend Agent: Setting up API endpoints...</div>
            <div style={{ color: '#10b981' }}>✅ Project created successfully!</div>
          </div>
        </div>
      </div>
    </div>
  )
}
