'use client';

import React, { useState } from 'react';
import { useWaveRiderStore } from '@/store/waverider-store';
import WaveRiderIDE from '@/components/ide/waverider-ide';

export function Landing() {
  const [isDemo, setIsDemo] = useState(false);
  const [demoStep, setDemoStep] = useState(0);
  const [showIDE, setShowIDE] = useState(false);
  const { setUser } = useWaveRiderStore();

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
          autoSave: true,
        },
        ai: {
          model: 'gpt-4' as const,
          temperature: 0.3,
          maxTokens: 2000,
          autoSuggestions: true,
          inlineCompletion: true,
        },
      },
    };
    setUser(mockUser);
    setShowIDE(true);
  };

  const handleViewDemo = () => {
    setIsDemo(true);
    setDemoStep(0);
    // Start demo animation
    const steps = [
      '🤖 Planner Agent: Breaking down the task...',
      '📝 Coder Agent: Generating React components...',
      '🔧 Backend Agent: Setting up API endpoints...',
      '🎨 UI Agent: Styling with Tailwind CSS...',
      '🔍 Debugger Agent: Running tests...',
      '✅ Project created successfully!',
    ];

    let currentStep = 0;
    const interval = setInterval(() => {
      if (currentStep < steps.length) {
        setDemoStep(currentStep);
        currentStep++;
      } else {
        clearInterval(interval);
        setTimeout(() => setIsDemo(false), 2000);
      }
    }, 1500);
  };

  const features = [
    {
      icon: '🤖',
      title: 'Autonomous Agents',
      description: 'AI agents that plan, code, debug, and optimize your projects automatically',
    },
    {
      icon: '💻',
      title: 'AI-Native Editor',
      description:
        'Monaco editor enhanced with predictive code completion and inline AI assistance',
    },
    {
      icon: '⚡',
      title: 'Instant Workflows',
      description: 'Automated pipelines for testing, deployment, and continuous integration',
    },
    {
      icon: '👥',
      title: 'Real-time Collaboration',
      description: 'Pair programming with AI and human developers in real-time',
    },
    {
      icon: '🛡️',
      title: 'Security Built-in',
      description: 'Automated vulnerability scanning and code provenance tracking',
    },
    {
      icon: '🚀',
      title: 'Cloud Ready',
      description: 'Deploy anywhere with Docker, Kubernetes, and cloud platform integration',
    },
  ];

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #dbeafe, #ffffff, #f3e8ff)',
        padding: '0',
      }}
    >
      {/* Hero Section */}
      <div
        style={{
          maxWidth: '1200px',
          margin: '0 auto',
          padding: '80px 16px 64px',
          textAlign: 'center',
        }}
      >
        <div style={{ marginBottom: '64px' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              marginBottom: '24px',
            }}
          >
            <div
              style={{
                background: 'linear-gradient(135deg, #3b82f6, #9333ea)',
                width: '64px',
                height: '64px',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '16px',
              }}
            >
              <span style={{ color: 'white', fontSize: '24px' }}>🌊</span>
            </div>
          </div>

          <h1
            style={{
              fontSize: '4rem',
              fontWeight: 'bold',
              background: 'linear-gradient(135deg, #2563eb, #9333ea)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              marginBottom: '24px',
              lineHeight: '1.1',
            }}
          >
            WaveRider
          </h1>

          <p
            style={{
              fontSize: '1.5rem',
              color: '#4b5563',
              marginBottom: '16px',
            }}
          >
            Agentic AI-Native IDE
          </p>

          <p
            style={{
              fontSize: '1.25rem',
              color: '#4b5563',
              maxWidth: '768px',
              margin: '0 auto 32px',
            }}
          >
            Revolutionize your development workflow with autonomous AI agents that handle planning,
            coding, debugging, and optimization - leaving you free to focus on innovation.
          </p>

          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '16px',
              justifyContent: 'center',
              alignItems: 'center',
              marginBottom: '32px',
            }}
          >
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
                transition: 'transform 0.2s ease',
              }}
              onMouseOver={e => ((e.target as HTMLButtonElement).style.transform = 'scale(1.05)')}
              onMouseOut={e => ((e.target as HTMLButtonElement).style.transform = 'scale(1)')}
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
                transition: 'all 0.2s ease',
              }}
              onMouseOver={e => {
                (e.target as HTMLButtonElement).style.borderColor = '#9333ea';
                (e.target as HTMLButtonElement).style.color = '#9333ea';
              }}
              onMouseOut={e => {
                (e.target as HTMLButtonElement).style.borderColor = '#d1d5db';
                (e.target as HTMLButtonElement).style.color = '#374151';
              }}
            >
              {isDemo ? 'Demo Running...' : 'View Demo'}
            </button>
          </div>

          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '8px',
              justifyContent: 'center',
            }}
          >
            {['TypeScript', 'Next.js', 'FastAPI', 'LangGraph', 'Docker'].map(tech => (
              <span
                key={tech}
                style={{
                  background: '#f3f4f6',
                  color: '#374151',
                  padding: '4px 12px',
                  borderRadius: '16px',
                  fontSize: '14px',
                }}
              >
                {tech}
              </span>
            ))}
          </div>
        </div>

        {/* Features Grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '32px',
            marginBottom: '64px',
          }}
        >
          {features.map((feature, index) => (
            <div
              key={index}
              style={{
                background: 'white',
                padding: '24px',
                borderRadius: '12px',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.07)',
                border: '1px solid #f3f4f6',
                transition: 'box-shadow 0.3s ease',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  marginBottom: '16px',
                }}
              >
                <span style={{ fontSize: '32px' }}>{feature.icon}</span>
                <h3
                  style={{
                    fontSize: '1.25rem',
                    fontWeight: '600',
                    color: '#1f2937',
                    margin: '0',
                  }}
                >
                  {feature.title}
                </h3>
              </div>
              <p
                style={{
                  color: '#4b5563',
                  lineHeight: '1.6',
                  margin: '0',
                }}
              >
                {feature.description}
              </p>
            </div>
          ))}
        </div>

        {/* Demo Section */}
        <div style={{ textAlign: 'center' }}>
          <h2
            style={{
              fontSize: '2rem',
              fontWeight: 'bold',
              marginBottom: '32px',
              color: '#1f2937',
            }}
          >
            See WaveRider in Action
          </h2>
          <div
            style={{
              background: '#111827',
              borderRadius: '12px',
              padding: '32px',
              maxWidth: '1000px',
              margin: '0 auto',
              boxShadow: '0 20px 25px rgba(0, 0, 0, 0.15)',
            }}
          >
            <div
              style={{
                textAlign: 'left',
                fontFamily: 'monospace',
                fontSize: '14px',
              }}
            >
              <div style={{ color: '#10b981', marginBottom: '8px' }}>
                $ waverider create "Build a full-stack todo app"
              </div>
              <div style={{ color: '#d1d5db', marginBottom: '4px' }}>
                🤖 Planner Agent: Breaking down the task...
              </div>
              <div style={{ color: '#d1d5db', marginBottom: '4px' }}>
                📝 Coder Agent: Generating React components...
              </div>
              <div style={{ color: '#d1d5db', marginBottom: '4px' }}>
                🔧 Backend Agent: Setting up API endpoints...
              </div>
              <div style={{ color: '#10b981' }}>✅ Project created successfully!</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Show IDE if user clicked Get Started
  if (showIDE) {
    return <WaveRiderIDE />;
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #dbeafe, #ffffff, #f3e8ff)',
        padding: '0',
      }}
    >
      {/* Rest of landing content already exists */}
      {/* This will continue with the existing structure */}
    </div>
  );
}
