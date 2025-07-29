'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { io, Socket } from 'socket.io-client';
import { 
  Play, 
  Square, 
  Save, 
  FolderOpen, 
  FileText, 
  Terminal, 
  Settings,
  Bot,
  MessageSquare,
  Code,
  Bug,
  Zap,
  GitBranch,
  CheckCircle,
  XCircle,
  Clock,
  Loader2
} from 'lucide-react';

// Monaco Editor with SSR disabled
const MonacoEditor = dynamic(() => import('@monaco-editor/react'), {
  ssr: false,
  loading: () => <div className="flex items-center justify-center h-full bg-gray-900 text-white">Loading Editor...</div>
});

// Types
interface FileNode {
  name: string;
  type: 'file' | 'directory';
  path: string;
  size?: number;
  modified?: string;
  children?: FileNode[];
}

interface Project {
  id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at?: string;
}

interface AgentTask {
  session_id: string;
  task: string;
  agent_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress?: {
    progress: number;
    status: string;
    message: string;
    timestamp: string;
  };
  result?: any;
  created_at: string;
  completed_at?: string;
}

interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: string;
  agent_type?: string;
}

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8002';

export default function WaveRiderIDE() {
  // State management
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [files, setFiles] = useState<FileNode[]>([]);
  const [currentFile, setCurrentFile] = useState<string>('');
  const [fileContent, setFileContent] = useState<string>('// Welcome to WaveRider IDE\n// Start coding with AI assistance');
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'editor' | 'chat' | 'tasks' | 'terminal'>('editor');
  
  // AI Chat
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  
  // Agent Tasks
  const [activeTasks, setActiveTasks] = useState<AgentTask[]>([]);
  const [taskInput, setTaskInput] = useState('');
  const [selectedAgent, setSelectedAgent] = useState<'coder' | 'debugger' | 'analyzer' | 'optimizer'>('coder');
  
  // Terminal
  const [terminalOutput, setTerminalOutput] = useState<string[]>([]);
  const [terminalInput, setTerminalInput] = useState('');
  
  // WebSocket
  const socketRef = useRef<Socket | null>(null);
  const editorRef = useRef<any>(null);

  // Initialize WebSocket connection
  useEffect(() => {
    const clientId = Math.random().toString(36).substring(7);
    socketRef.current = io(`${BACKEND_URL}/ws/${clientId}`);
    
    socketRef.current.on('connect', () => {
      console.log('Connected to WaveRider backend');
      addToTerminal('🌊 Connected to WaveRider backend');
    });
    
    socketRef.current.on('agent_progress', (data) => {
      handleAgentProgress(data);
    });
    
    socketRef.current.on('disconnect', () => {
      console.log('Disconnected from backend');
      addToTerminal('❌ Disconnected from backend');
    });
    
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, []);

  // Load initial data
  useEffect(() => {
    loadProjects();
    initializeDefaultProject();
  }, []);

  const addToTerminal = useCallback((message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setTerminalOutput(prev => [...prev, `[${timestamp}] ${message}`]);
  }, []);

  const handleAgentProgress = useCallback((data: any) => {
    if (data.data && data.data.session_id) {
      setActiveTasks(prev => prev.map(task => 
        task.session_id === data.data.session_id 
          ? { ...task, progress: data.data }
          : task
      ));
      
      addToTerminal(`🤖 Agent Update: ${data.data.message} (${data.data.progress}%)`);
    }
  }, [addToTerminal]);

  const loadProjects = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/projects`);
      if (response.ok) {
        const data = await response.json();
        setProjects(data.projects || []);
      }
    } catch (error) {
      console.error('Failed to load projects:', error);
      addToTerminal('❌ Failed to load projects');
    }
  };

  const initializeDefaultProject = async () => {
    try {
      // Create a default project if none exists
      const response = await fetch(`${BACKEND_URL}/api/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: 'My WaveRider Project',
          description: 'Default project for WaveRider IDE',
          owner_id: 'user'
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        const newProject: Project = {
          id: data.project_id,
          name: 'My WaveRider Project',
          description: 'Default project for WaveRider IDE',
          created_at: new Date().toISOString()
        };
        
        setCurrentProject(newProject);
        setProjects(prev => [newProject, ...prev]);
        loadProjectFiles(data.project_id);
        addToTerminal(`✅ Created project: ${newProject.name}`);
      }
    } catch (error) {
      console.error('Failed to initialize project:', error);
      addToTerminal('❌ Failed to initialize project');
    }
  };

  const loadProjectFiles = async (projectId: string) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/projects/${projectId}/files`);
      if (response.ok) {
        const data = await response.json();
        setFiles(data.files || []);
      }
    } catch (error) {
      console.error('Failed to load files:', error);
      addToTerminal('❌ Failed to load project files');
    }
  };

  const saveFile = async () => {
    if (!currentProject || !currentFile) return;
    
    setIsLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/files`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          operation: 'write',
          project_id: currentProject.id,
          path: currentFile,
          content: fileContent
        })
      });
      
      if (response.ok) {
        addToTerminal(`✅ Saved: ${currentFile}`);
      } else {
        addToTerminal(`❌ Failed to save: ${currentFile}`);
      }
    } catch (error) {
      console.error('Save failed:', error);
      addToTerminal(`❌ Save error: ${error}`);
    } finally {
      setIsLoading(false);
    }
  };

  const openFile = async (file: FileNode) => {
    if (file.type === 'directory' || !currentProject) return;
    
    setIsLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/files`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          operation: 'read',
          project_id: currentProject.id,
          path: file.path
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setCurrentFile(file.path);
        setFileContent(data.content || '');
        addToTerminal(`📂 Opened: ${file.path}`);
      }
    } catch (error) {
      console.error('Failed to open file:', error);
      addToTerminal(`❌ Failed to open: ${file.path}`);
    } finally {
      setIsLoading(false);
    }
  };

  const sendChatMessage = async () => {
    if (!chatInput.trim()) return;
    
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content: chatInput,
      sender: 'user',
      timestamp: new Date().toISOString()
    };
    
    setChatMessages(prev => [...prev, userMessage]);
    setIsChatLoading(true);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: chatInput,
          context: fileContent,
          project_id: currentProject?.id
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        const aiMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          content: data.response,
          sender: 'ai',
          timestamp: data.timestamp
        };
        
        setChatMessages(prev => [...prev, aiMessage]);
      }
    } catch (error) {
      console.error('Chat failed:', error);
      addToTerminal('❌ Chat service unavailable');
    } finally {
      setIsChatLoading(false);
      setChatInput('');
    }
  };

  const executeAgentTask = async () => {
    if (!taskInput.trim() || !currentProject) return;
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task: taskInput,
          type: selectedAgent,
          context: fileContent,
          project_id: currentProject.id,
          files: currentFile ? [currentFile] : []
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        const newTask: AgentTask = {
          session_id: data.session_id,
          task: taskInput,
          agent_type: selectedAgent,
          status: 'pending',
          created_at: new Date().toISOString()
        };
        
        setActiveTasks(prev => [newTask, ...prev]);
        setTaskInput('');
        addToTerminal(`🚀 Started ${selectedAgent} task: ${taskInput.substring(0, 50)}...`);
      }
    } catch (error) {
      console.error('Task creation failed:', error);
      addToTerminal('❌ Failed to create agent task');
    }
  };

  const getAgentIcon = (agentType: string) => {
    switch (agentType) {
      case 'coder': return <Code className="w-4 h-4" />;
      case 'debugger': return <Bug className="w-4 h-4" />;
      case 'analyzer': return <Zap className="w-4 h-4" />;
      case 'optimizer': return <GitBranch className="w-4 h-4" />;
      default: return <Bot className="w-4 h-4" />;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed': return <XCircle className="w-4 h-4 text-red-500" />;
      case 'running': return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
      default: return <Clock className="w-4 h-4 text-yellow-500" />;
    }
  };

  return (
    <div className="h-screen bg-gray-900 text-white flex flex-col">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h1 className="text-xl font-bold text-wave-400">🌊 WaveRider IDE</h1>
          <div className="text-sm text-gray-400">
            {currentProject ? `Project: ${currentProject.name}` : 'No Project'}
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={saveFile}
            disabled={!currentFile || isLoading}
            className="flex items-center space-x-1 px-3 py-1 bg-wave-600 hover:bg-wave-700 disabled:opacity-50 rounded text-sm"
          >
            <Save className="w-4 h-4" />
            <span>Save</span>
          </button>
          
          <button className="flex items-center space-x-1 px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-sm">
            <Settings className="w-4 h-4" />
            <span>Settings</span>
          </button>
        </div>
      </header>

      <div className="flex flex-1">
        {/* Sidebar */}
        <aside className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col">
          {/* File Explorer */}
          <div className="p-4 border-b border-gray-700">
            <div className="flex items-center space-x-2 mb-3">
              <FolderOpen className="w-4 h-4" />
              <span className="text-sm font-medium">Files</span>
            </div>
            
            <div className="space-y-1 max-h-48 overflow-y-auto">
              {files.map((file, index) => (
                <div
                  key={index}
                  onClick={() => openFile(file)}
                  className={`flex items-center space-x-2 px-2 py-1 rounded cursor-pointer hover:bg-gray-700 text-sm ${
                    currentFile === file.path ? 'bg-wave-600' : ''
                  }`}
                >
                  <FileText className="w-3 h-3" />
                  <span className="truncate">{file.name}</span>
                </div>
              ))}
              
              {files.length === 0 && (
                <div className="text-gray-500 text-xs text-center py-4">
                  No files yet. Create your first file!
                </div>
              )}
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex-1 flex flex-col">
            <div className="border-b border-gray-700">
              {[
                { id: 'editor', icon: Code, label: 'Editor' },
                { id: 'chat', icon: MessageSquare, label: 'AI Chat' },
                { id: 'tasks', icon: Bot, label: 'Agents' },
                { id: 'terminal', icon: Terminal, label: 'Terminal' }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`w-full flex items-center space-x-2 px-4 py-2 text-sm hover:bg-gray-700 ${
                    activeTab === tab.id ? 'bg-gray-700 border-r-2 border-wave-400' : ''
                  }`}
                >
                  <tab.icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              ))}
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 flex flex-col">
          {activeTab === 'editor' && (
            <div className="flex-1 flex flex-col">
              {/* Editor Toolbar */}
              <div className="bg-gray-800 border-b border-gray-700 px-4 py-2 flex items-center justify-between">
                <div className="text-sm text-gray-400">
                  {currentFile || 'No file selected'}
                </div>
                
                <div className="flex items-center space-x-2">
                  <button className="p-1 hover:bg-gray-700 rounded">
                    <Play className="w-4 h-4" />
                  </button>
                  <button className="p-1 hover:bg-gray-700 rounded">
                    <Square className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Monaco Editor */}
              <div className="flex-1">
                <MonacoEditor
                  height="100%"
                  defaultLanguage="javascript"
                  theme="vs-dark"
                  value={fileContent}
                  onChange={(value) => setFileContent(value || '')}
                  onMount={(editor) => {
                    editorRef.current = editor;
                  }}
                  options={{
                    minimap: { enabled: false },
                    fontSize: 14,
                    lineNumbers: 'on',
                    automaticLayout: true,
                    scrollBeyondLastLine: false,
                    wordWrap: 'on',
                    tabSize: 2
                  }}
                />
              </div>
            </div>
          )}

          {activeTab === 'chat' && (
            <div className="flex-1 flex flex-col">
              {/* Chat Messages */}
              <div className="flex-1 p-4 overflow-y-auto space-y-4">
                {chatMessages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                        message.sender === 'user'
                          ? 'bg-wave-600 text-white'
                          : 'bg-gray-700 text-gray-100'
                      }`}
                    >
                      <div className="text-sm">{message.content}</div>
                      <div className="text-xs opacity-75 mt-1">
                        {new Date(message.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                ))}
                
                {isChatLoading && (
                  <div className="flex justify-start">
                    <div className="bg-gray-700 px-4 py-2 rounded-lg">
                      <Loader2 className="w-4 h-4 animate-spin" />
                    </div>
                  </div>
                )}
              </div>

              {/* Chat Input */}
              <div className="border-t border-gray-700 p-4">
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendChatMessage()}
                    placeholder="Ask AI anything about your code..."
                    className="flex-1 bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm focus:outline-none focus:border-wave-400"
                    disabled={isChatLoading}
                  />
                  <button
                    onClick={sendChatMessage}
                    disabled={isChatLoading || !chatInput.trim()}
                    className="px-4 py-2 bg-wave-600 hover:bg-wave-700 disabled:opacity-50 rounded text-sm"
                  >
                    Send
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'tasks' && (
            <div className="flex-1 flex flex-col">
              {/* Agent Selection */}
              <div className="border-b border-gray-700 p-4">
                <div className="mb-3">
                  <label className="block text-sm font-medium mb-2">Select Agent:</label>
                  <div className="grid grid-cols-2 gap-2">
                    {[
                      { id: 'coder', name: 'Code Generator', icon: Code },
                      { id: 'debugger', name: 'Debug Assistant', icon: Bug },
                      { id: 'analyzer', name: 'Code Analyzer', icon: Zap },
                      { id: 'optimizer', name: 'Performance Optimizer', icon: GitBranch }
                    ].map(agent => (
                      <button
                        key={agent.id}
                        onClick={() => setSelectedAgent(agent.id as any)}
                        className={`flex items-center space-x-2 px-3 py-2 rounded text-sm ${
                          selectedAgent === agent.id ? 'bg-wave-600' : 'bg-gray-700 hover:bg-gray-600'
                        }`}
                      >
                        <agent.icon className="w-4 h-4" />
                        <span>{agent.name}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Task Input */}
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={taskInput}
                    onChange={(e) => setTaskInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && executeAgentTask()}
                    placeholder="Describe what you want the agent to do..."
                    className="flex-1 bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm focus:outline-none focus:border-wave-400"
                  />
                  <button
                    onClick={executeAgentTask}
                    disabled={!taskInput.trim() || !currentProject}
                    className="px-4 py-2 bg-wave-600 hover:bg-wave-700 disabled:opacity-50 rounded text-sm"
                  >
                    Execute
                  </button>
                </div>
              </div>

              {/* Active Tasks */}
              <div className="flex-1 p-4 overflow-y-auto">
                <h3 className="text-sm font-medium mb-3">Active Tasks</h3>
                <div className="space-y-3">
                  {activeTasks.map((task) => (
                    <div key={task.session_id} className="bg-gray-800 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          {getAgentIcon(task.agent_type)}
                          <span className="text-sm font-medium capitalize">{task.agent_type}</span>
                          {getStatusIcon(task.status)}
                        </div>
                        <div className="text-xs text-gray-400">
                          {new Date(task.created_at).toLocaleTimeString()}
                        </div>
                      </div>
                      
                      <div className="text-sm text-gray-300 mb-2">{task.task}</div>
                      
                      {task.progress && (
                        <div className="space-y-1">
                          <div className="flex justify-between text-xs">
                            <span>{task.progress.message}</span>
                            <span>{task.progress.progress}%</span>
                          </div>
                          <div className="w-full bg-gray-700 rounded-full h-1">
                            <div
                              className="bg-wave-400 h-1 rounded-full transition-all duration-300"
                              style={{ width: `${task.progress.progress}%` }}
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                  
                  {activeTasks.length === 0 && (
                    <div className="text-center text-gray-500 text-sm py-8">
                      No active tasks. Create an agent task to get started!
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'terminal' && (
            <div className="flex-1 flex flex-col bg-black">
              {/* Terminal Output */}
              <div className="flex-1 p-4 overflow-y-auto font-mono text-sm">
                {terminalOutput.map((line, index) => (
                  <div key={index} className="text-green-400 mb-1">
                    {line}
                  </div>
                ))}
              </div>

              {/* Terminal Input */}
              <div className="border-t border-gray-700 p-4">
                <div className="flex items-center space-x-2 font-mono text-sm">
                  <span className="text-green-400">$</span>
                  <input
                    type="text"
                    value={terminalInput}
                    onChange={(e) => setTerminalInput(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        addToTerminal(`$ ${terminalInput}`);
                        addToTerminal('Command executed (terminal integration coming soon)');
                        setTerminalInput('');
                      }
                    }}
                    placeholder="Enter command..."
                    className="flex-1 bg-transparent border-none outline-none text-green-400 placeholder-gray-500"
                  />
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Status Bar */}
      <footer className="bg-gray-800 border-t border-gray-700 px-4 py-1 flex items-center justify-between text-xs">
        <div className="flex items-center space-x-4">
          <span>WaveRider v1.0.0</span>
          <span className="text-gray-400">|</span>
          <span>{currentFile || 'No file'}</span>
        </div>
        
        <div className="flex items-center space-x-4">
          <span className="text-gray-400">Connected</span>
          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
        </div>
      </footer>
    </div>
  );
}
