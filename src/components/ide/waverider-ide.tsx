'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import dynamic from 'next/dynamic';
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
  Loader2,
  Plus,
  Edit,
  Trash2,
  RefreshCw,
  FolderPlus,
  ChevronRight,
  ChevronDown,
  Folder,
  Upload,
  Download,
  ExternalLink,
} from 'lucide-react';

// Monaco Editor with SSR disabled
const MonacoEditor = dynamic(() => import('@monaco-editor/react'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full bg-gray-900 text-white">
      Loading Editor...
    </div>
  ),
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

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

export default function WaveRiderIDE() {
  // State management
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [files, setFiles] = useState<FileNode[]>([]);
  const [currentFile, setCurrentFile] = useState<string>('');
  const [fileContent, setFileContent] = useState<string>(
    '// Welcome to WaveRider IDE\n// Start coding with AI assistance'
  );
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'editor' | 'chat' | 'tasks' | 'terminal'>('editor');

  // AI Chat
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [thinkingMessage, setThinkingMessage] = useState('');
  const [thinkingProgress, setThinkingProgress] = useState(0);

  // Agent Tasks
  const [activeTasks, setActiveTasks] = useState<AgentTask[]>([]);
  const [taskInput, setTaskInput] = useState('');
  const [selectedAgent, setSelectedAgent] = useState<
    'coder' | 'debugger' | 'analyzer' | 'optimizer'
  >('coder');

  // Terminal
  const [terminalOutput, setTerminalOutput] = useState<string[]>([]);
  const [terminalInput, setTerminalInput] = useState('');

  // File operations
  const [isCreatingFile, setIsCreatingFile] = useState(false);
  const [newFileName, setNewFileName] = useState('');
  const [isRenamingFile, setIsRenamingFile] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState('');
  const [expandedDirectories, setExpandedDirectories] = useState<Set<string>>(new Set());
  const [isImporting, setIsImporting] = useState(false);
  const [importPath, setImportPath] = useState('');
  const [isBrowsing, setIsBrowsing] = useState(false);
  const [browseDirs, setBrowseDirs] = useState<any[]>([]);
  const [currentBrowsePath, setCurrentBrowsePath] = useState('');

  // WebSocket
  const socketRef = useRef<WebSocket | null>(null);
  const editorRef = useRef<any>(null);

  // Initialize WebSocket connection
  useEffect(() => {
    const clientId = Math.random().toString(36).substring(7);
    const wsUrl = BACKEND_URL.replace('http', 'ws') + `/ws/${clientId}`;
    
    socketRef.current = new WebSocket(wsUrl);

    socketRef.current.onopen = () => {
      console.log('Connected to WaveRider backend');
      addToTerminal('🌊 Connected to WaveRider backend');
    };

    socketRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'agent_progress') {
          handleAgentProgress(data);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    socketRef.current.onclose = () => {
      console.log('Disconnected from backend');
      addToTerminal('❌ Disconnected from backend');
    };

    socketRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      addToTerminal('❌ WebSocket connection error');
    };

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
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

  // AI Thinking Messages
  const getThinkingMessages = (context: string = '') => {
    const baseMessages = [
      '• Analyzing your request...',
      '• Processing context...',
      '• Generating solution...',
      '• Reviewing code patterns...',
      '• Optimizing approach...',
      '• Crafting response...',
      '• Running final checks...',
      '• Almost ready...'
    ];

    const codeMessages = [
      '• Parsing code structure...',
      '• Analyzing dependencies...',
      '• Checking best practices...',
      '• Generating implementation...',
      '• Validating syntax...',
      '• Optimizing performance...',
      '• Adding documentation...',
      '• Finalizing code...'
    ];

    const fileMessages = [
      '• Planning file structure...',
      '• Creating directories...',
      '• Generating boilerplate...',
      '• Writing configuration...',
      '• Setting up dependencies...',
      '• Creating entry points...',
      '• Adding documentation...',
      '• Finalizing project...'
    ];

    // Determine message set based on context
    if (context.toLowerCase().includes('create') || context.toLowerCase().includes('file')) {
      return fileMessages;
    } else if (context.toLowerCase().includes('code') || context.toLowerCase().includes('function')) {
      return codeMessages;
    }
    return baseMessages;
  };

  // Animate thinking messages and progress
  useEffect(() => {
    if (!isChatLoading) {
      setThinkingMessage('');
      setThinkingProgress(0);
      return;
    }

    const messages = getThinkingMessages(chatInput);
    let messageIndex = 0;
    let progress = 0;
    
    const messageInterval = setInterval(() => {
      setThinkingMessage(messages[messageIndex]);
      messageIndex = (messageIndex + 1) % messages.length;
    }, 1500);

    const progressInterval = setInterval(() => {
      progress += Math.random() * 15 + 5; // Random progress between 5-20%
      if (progress > 85) progress = 85; // Cap at 85% until actual completion
      setThinkingProgress(progress);
    }, 800);

    return () => {
      clearInterval(messageInterval);
      clearInterval(progressInterval);
    };
  }, [isChatLoading, chatInput]);

  // Execute terminal command
  const executeTerminalCommand = async (command: string) => {
    if (!command.trim() || !currentProject) return;

    addToTerminal(`$ ${command}`);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/terminal/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          command: command.trim(),
          project_id: currentProject.id,
        }),
      });

      const result = await response.json();
      
      if (response.ok) {
        if (result.output) {
          // Split output into lines and add each line
          const lines = result.output.split('\n');
          lines.forEach((line: string) => {
            if (line.trim()) {
              addToTerminal(line);
            }
          });
        }
        if (result.error) {
          addToTerminal(`❌ Error: ${result.error}`);
        }
      } else {
        addToTerminal(`❌ Command failed: ${result.detail || 'Unknown error'}`);
      }
    } catch (error) {
      addToTerminal(`❌ Failed to execute command: ${error}`);
    }
  };

  // File operations
  const createNewFile = async () => {
    if (!newFileName.trim() || !currentProject) return;

    try {
      const response = await fetch(`${BACKEND_URL}/api/files`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          operation: 'write',
          project_id: currentProject.id,
          path: newFileName,
          content: '// New file\n',
        }),
      });

      if (response.ok) {
        addToTerminal(`✅ Created file: ${newFileName}`);
        await loadProjectFiles(currentProject.id);
        setNewFileName('');
        setIsCreatingFile(false);
      }
    } catch (error) {
      addToTerminal(`❌ Failed to create file: ${newFileName}`);
    }
  };

  const deleteFile = async (filePath: string) => {
    if (!currentProject || !confirm(`Delete file: ${filePath}?`)) return;

    try {
      const response = await fetch(`${BACKEND_URL}/api/files`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          operation: 'delete',
          project_id: currentProject.id,
          path: filePath,
        }),
      });

      if (response.ok) {
        addToTerminal(`🗑️ Deleted file: ${filePath}`);
        await loadProjectFiles(currentProject.id);
        if (currentFile === filePath) {
          setCurrentFile('');
          setFileContent('');
        }
      }
    } catch (error) {
      addToTerminal(`❌ Failed to delete file: ${filePath}`);
    }
  };

  const renameFile = async (oldPath: string, newName: string) => {
    if (!currentProject || !newName.trim()) return;

    try {
      // Read old file content
      const readResponse = await fetch(`${BACKEND_URL}/api/files`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          operation: 'read',
          project_id: currentProject.id,
          path: oldPath,
        }),
      });

      if (readResponse.ok) {
        const { content } = await readResponse.json();
        
        // Create new file with content
        const writeResponse = await fetch(`${BACKEND_URL}/api/files`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            operation: 'write',
            project_id: currentProject.id,
            path: newName,
            content,
          }),
        });

        if (writeResponse.ok) {
          // Delete old file
          await fetch(`${BACKEND_URL}/api/files`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              operation: 'delete',
              project_id: currentProject.id,
              path: oldPath,
            }),
          });

          addToTerminal(`📝 Renamed: ${oldPath} → ${newName}`);
          await loadProjectFiles(currentProject.id);
          if (currentFile === oldPath) {
            setCurrentFile(newName);
          }
        }
      }
    } catch (error) {
      addToTerminal(`❌ Failed to rename file: ${oldPath}`);
    }
    
    setIsRenamingFile(null);
    setRenameValue('');
  };

  const handleAgentProgress = useCallback(
    (data: any) => {
      if (data.data && data.data.session_id) {
        setActiveTasks(prev =>
          prev.map(task =>
            task.session_id === data.data.session_id ? { ...task, progress: data.data } : task
          )
        );

        addToTerminal(`🤖 Agent Update: ${data.data.message} (${data.data.progress}%)`);
      }
    },
    [addToTerminal]
  );

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
          owner_id: 'user',
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const newProject: Project = {
          id: data.project_id,
          name: 'My WaveRider Project',
          description: 'Default project for WaveRider IDE',
          created_at: new Date().toISOString(),
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
          content: fileContent,
        }),
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

  const importProject = async () => {
    if (!importPath.trim()) return;

    try {
      const response = await fetch(`${BACKEND_URL}/api/projects/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_path: importPath,
          project_name: importPath.split(/[/\\]/).pop() || 'imported-project'
        }),
      });

      if (response.ok) {
        const data = await response.json();
        addToTerminal(`✅ Imported project: ${importPath}`);
        await loadProjects();
        setImportPath('');
        setIsImporting(false);
        
        // Switch to the imported project
        const importedProject: Project = {
          id: data.project_id,
          name: data.project_name,
          description: `Imported from ${importPath}`,
          created_at: new Date().toISOString()
        };
        setCurrentProject(importedProject);
        await loadProjectFiles(data.project_id);
      } else {
        const error = await response.text();
        addToTerminal(`❌ Failed to import: ${error}`);
      }
    } catch (error) {
      console.error('Import failed:', error);
      addToTerminal(`❌ Import error: ${error}`);
    }
  };

  const browseFilesystem = async (path: string = '') => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/browse?path=${encodeURIComponent(path)}`);
      if (response.ok) {
        const data = await response.json();
        setBrowseDirs(data.directories);
        setCurrentBrowsePath(data.current_path || path);
      } else {
        addToTerminal('❌ Failed to browse filesystem');
      }
    } catch (error) {
      console.error('Browse failed:', error);
      addToTerminal(`❌ Browse error: ${error}`);
    }
  };

  const selectImportPath = (path: string) => {
    setImportPath(path);
    setIsBrowsing(false);
  };

  const toggleDirectory = (dirPath: string) => {
    setExpandedDirectories(prev => {
      const newSet = new Set(prev);
      if (newSet.has(dirPath)) {
        newSet.delete(dirPath);
        addToTerminal(`📁 Collapsed: ${dirPath}`);
      } else {
        newSet.add(dirPath);
        addToTerminal(`📂 Expanded: ${dirPath}`);
      }
      return newSet;
    });
  };

  // Recursive function to render file tree
  const renderFileTree = (files: FileNode[], depth = 0): JSX.Element[] => {
    return files.map((file, index) => {
      const isExpanded = expandedDirectories.has(file.path);
      const isDirectory = file.type === 'directory';
      
      return (
        <div key={`${file.path}-${index}`}>
          {isRenamingFile === file.path ? (
            <div style={{ paddingLeft: `${depth * 16}px` }}>
              <input
                type="text"
                value={renameValue}
                onChange={e => setRenameValue(e.target.value)}
                onKeyPress={e => {
                  if (e.key === 'Enter') renameFile(file.path, renameValue);
                  if (e.key === 'Escape') setIsRenamingFile(null);
                }}
                className="w-full bg-gray-700 border border-gray-600 rounded px-2 py-1 text-xs focus:outline-none focus:border-wave-400"
                autoFocus
              />
            </div>
          ) : (
            <div className="group">
              <div
                className={`flex items-center justify-between py-1 rounded text-sm transition-colors border ${
                  currentFile === file.path ? 'bg-wave-600 border-wave-400' : 'hover:bg-gray-700 border-transparent'
                }`}
                style={{ paddingLeft: `${depth * 16 + 8}px`, paddingRight: '8px' }}
              >
                <div 
                  className="flex items-center space-x-1 flex-1 min-w-0 cursor-pointer py-1 -m-1 p-1 rounded hover:bg-gray-600"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    console.log('File clicked:', file);
                    addToTerminal(`🖱️ Clicked: ${file.path}`);
                    openFile(file);
                  }}
                  title={`Click to ${isDirectory ? 'expand/collapse' : 'open'}: ${file.path}`}
                >
                  {isDirectory && (
                    <div className="w-3 h-3 flex-shrink-0">
                      {isExpanded ? (
                        <ChevronDown className="w-3 h-3 text-gray-400" />
                      ) : (
                        <ChevronRight className="w-3 h-3 text-gray-400" />
                      )}
                    </div>
                  )}
                  
                  {isDirectory ? (
                    <Folder className={`w-3 h-3 flex-shrink-0 ${isExpanded ? 'text-yellow-400' : 'text-blue-400'}`} />
                  ) : (
                    <FileText className="w-3 h-3 flex-shrink-0 text-blue-400" />
                  )}
                  
                  <span className="truncate text-gray-200 font-medium">{file.name}</span>
                  <span className="text-xs text-gray-500 ml-2">
                    {isDirectory ? '📁 DIR' : '📄 FILE'}
                  </span>
                </div>

                <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100">
                  <button
                    onClick={e => {
                      e.stopPropagation();
                      setIsRenamingFile(file.path);
                      setRenameValue(file.name);
                    }}
                    className="p-1 hover:bg-gray-600 rounded"
                    title="Rename"
                  >
                    <Edit className="w-3 h-3" />
                  </button>
                  <button
                    onClick={e => {
                      e.stopPropagation();
                      deleteFile(file.path);
                    }}
                    className="p-1 hover:bg-red-600 rounded"
                    title="Delete"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </div>
          )}
          
          {/* Render children if directory is expanded */}
          {isDirectory && isExpanded && file.children && file.children.length > 0 && (
            <div>
              {renderFileTree(file.children, depth + 1)}
            </div>
          )}
        </div>
      );
    });
  };

  const openFile = async (file: FileNode) => {
    console.log('OpenFile called with:', file); // Debug log
    
    if (file.type === 'directory') {
      toggleDirectory(file.path);
      return;
    }
    
    if (!currentProject) {
      addToTerminal(`❌ No project selected`);
      return;
    }

    addToTerminal(`🔄 Opening file: ${file.path}`);
    setIsLoading(true);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/files`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          operation: 'read',
          project_id: currentProject.id,
          path: file.path,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentFile(file.path);
        setFileContent(data.content || '');
        setActiveTab('editor'); // Switch to editor tab when opening a file
        addToTerminal(`✅ Opened: ${file.path}`);
      } else {
        const errorText = await response.text();
        addToTerminal(`❌ Failed to open: ${file.path} - ${response.status} ${errorText}`);
      }
    } catch (error) {
      console.error('Failed to open file:', error);
      addToTerminal(`❌ Failed to open: ${file.path} - ${error}`);
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
      timestamp: new Date().toISOString(),
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
          project_id: currentProject?.id,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        
        // Create AI response message
        let aiResponse = data.response;
        
        // If files were created, add them to the response and refresh file list
        if (data.files_created && data.files_created.length > 0) {
          aiResponse += `\n\n✅ Created files:\n${data.files_created.map((f: string) => `• ${f}`).join('\n')}`;
          
          if (data.instructions) {
            aiResponse += `\n\n📋 Instructions: ${data.instructions}`;
          }
          
          // Refresh the file list to show new files
          if (currentProject) {
            addToTerminal(`📁 Refreshing files after creation...`);
            await loadProjectFiles(currentProject.id);
            addToTerminal(`✅ Created ${data.files_created.length} files`);
            
            // If a main file was created, open it automatically
            const mainFile = data.files_created.find((f: string) => 
              f.includes('App.') || f.includes('index.') || f.includes('main.') || f.endsWith('.html')
            );
            if (mainFile) {
              setTimeout(() => {
                const fileToOpen = files.find(f => f.path === mainFile);
                if (fileToOpen) {
                  openFile(fileToOpen);
                }
              }, 500); // Give time for files to load
            }
          }
        }
        
        const aiMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          content: aiResponse,
          sender: 'ai',
          timestamp: data.timestamp,
        };

        setChatMessages(prev => [...prev, aiMessage]);
      }
    } catch (error) {
      console.error('Chat failed:', error);
      addToTerminal('❌ Chat service unavailable');
    } finally {
      // Complete the progress animation
      setThinkingProgress(100);
      setThinkingMessage('• Response ready!');
      
      // Brief delay to show completion before hiding
      setTimeout(() => {
        setIsChatLoading(false);
        setChatInput('');
      }, 800);
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
          files: currentFile ? [currentFile] : [],
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const newTask: AgentTask = {
          session_id: data.session_id,
          task: taskInput,
          agent_type: selectedAgent,
          status: 'pending',
          created_at: new Date().toISOString(),
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
      case 'coder':
        return <Code className="w-4 h-4" />;
      case 'debugger':
        return <Bug className="w-4 h-4" />;
      case 'analyzer':
        return <Zap className="w-4 h-4" />;
      case 'optimizer':
        return <GitBranch className="w-4 h-4" />;
      default:
        return <Bot className="w-4 h-4" />;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'running':
        return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
      default:
        return <Clock className="w-4 h-4 text-yellow-500" />;
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

      <div className="flex flex-1 h-0">
        {/* Sidebar - Fixed position */}
        <aside className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col flex-shrink-0">
          {/* File Explorer */}
          <div className="p-4 border-b border-gray-700">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <FolderOpen className="w-4 h-4" />
                <span className="text-sm font-medium">Files</span>
              </div>
              
              {/* File Operation Buttons */}
              <div className="flex items-center space-x-1">
                <button
                  onClick={() => setIsCreatingFile(true)}
                  className="p-1 hover:bg-gray-700 rounded"
                  title="New File"
                >
                  <Plus className="w-3 h-3" />
                </button>
                <button
                  onClick={() => setIsImporting(true)}
                  className="p-1 hover:bg-gray-700 rounded"
                  title="Import Project"
                >
                  <Upload className="w-3 h-3" />
                </button>
                <button
                  onClick={() => currentProject && loadProjectFiles(currentProject.id)}
                  className="p-1 hover:bg-gray-700 rounded"
                  title="Refresh"
                >
                  <RefreshCw className="w-3 h-3" />
                </button>
              </div>
            </div>

            {/* New File Input */}
            {isCreatingFile && (
              <div className="mb-3 space-y-2">
                <input
                  type="text"
                  value={newFileName}
                  onChange={e => setNewFileName(e.target.value)}
                  onKeyPress={e => {
                    if (e.key === 'Enter') createNewFile();
                    if (e.key === 'Escape') setIsCreatingFile(false);
                  }}
                  placeholder="filename.ext"
                  className="w-full bg-gray-700 border border-gray-600 rounded px-2 py-1 text-xs focus:outline-none focus:border-wave-400"
                  autoFocus
                />
                <div className="flex space-x-1">
                  <button
                    onClick={createNewFile}
                    className="flex-1 bg-wave-600 hover:bg-wave-700 text-xs px-2 py-1 rounded"
                  >
                    Create
                  </button>
                  <button
                    onClick={() => setIsCreatingFile(false)}
                    className="flex-1 bg-gray-600 hover:bg-gray-700 text-xs px-2 py-1 rounded"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {/* Import Project Input */}
            {isImporting && (
              <div className="mb-3 space-y-2">
                <div className="flex space-x-1">
                  <input
                    type="text"
                    value={importPath}
                    onChange={e => setImportPath(e.target.value)}
                    onKeyPress={e => {
                      if (e.key === 'Enter') importProject();
                      if (e.key === 'Escape') setIsImporting(false);
                    }}
                    placeholder="C:\path\to\existing\project"
                    className="flex-1 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-xs focus:outline-none focus:border-wave-400"
                  />
                  <button
                    onClick={() => {
                      setIsBrowsing(true);
                      browseFilesystem();
                    }}
                    className="px-2 py-1 bg-gray-600 hover:bg-gray-500 rounded text-xs"
                    title="Browse"
                  >
                    <FolderOpen className="w-3 h-3" />
                  </button>
                </div>
                
                {isBrowsing && (
                  <div className="bg-gray-800 border border-gray-600 rounded p-2 max-h-48 overflow-y-auto">
                    <div className="text-xs text-gray-400 mb-2">
                      {currentBrowsePath || 'Select a directory:'}
                    </div>
                    <div className="space-y-1">
                      {browseDirs.map((dir, index) => (
                        <div key={index} className="flex items-center space-x-2">
                          <button
                            onClick={() => browseFilesystem(dir.path)}
                            className="flex items-center space-x-1 p-1 hover:bg-gray-700 rounded text-xs flex-1 text-left"
                          >
                            <Folder className="w-3 h-3" />
                            <span className="truncate">{dir.name}</span>
                          </button>
                          <button
                            onClick={() => selectImportPath(dir.path)}
                            className="px-2 py-1 bg-wave-600 hover:bg-wave-700 rounded text-xs"
                            title="Select this directory"
                          >
                            Select
                          </button>
                        </div>
                      ))}
                    </div>
                    <div className="mt-2 pt-2 border-t border-gray-600">
                      <button
                        onClick={() => setIsBrowsing(false)}
                        className="w-full bg-gray-600 hover:bg-gray-700 text-xs px-2 py-1 rounded"
                      >
                        Close Browser
                      </button>
                    </div>
                  </div>
                )}
                
                <div className="text-xs text-gray-400 px-1">
                  Enter full path to existing project directory or use Browse
                </div>
                <div className="flex space-x-1">
                  <button
                    onClick={importProject}
                    className="flex-1 bg-wave-600 hover:bg-wave-700 text-xs px-2 py-1 rounded"
                  >
                    Import
                  </button>
                  <button
                    onClick={() => setIsImporting(false)}
                    className="flex-1 bg-gray-600 hover:bg-gray-700 text-xs px-2 py-1 rounded"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            <div className="space-y-1 max-h-48 overflow-y-auto">
              {/* Debug info */}
              <div className="text-xs text-gray-500 mb-2">
                Files: {files.length} | Current: {currentFile || 'none'} | Expanded: {expandedDirectories.size}
              </div>
              
              {/* Render file tree */}
              <div className="space-y-1">
                {renderFileTree(files)}
              </div>

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
                { id: 'terminal', icon: Terminal, label: 'Terminal' },
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
        <main className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
          {activeTab === 'editor' && (
            <div className="flex-1 flex flex-col">
              {/* Editor Toolbar */}
              <div className="bg-gray-800 border-b border-gray-700 px-4 py-2 flex items-center justify-between">
                <div className="text-sm text-gray-400">{currentFile || 'No file selected'}</div>

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
                  onChange={value => setFileContent(value || '')}
                  onMount={editor => {
                    editorRef.current = editor;
                  }}
                  options={{
                    minimap: { enabled: false },
                    fontSize: 14,
                    lineNumbers: 'on',
                    automaticLayout: true,
                    scrollBeyondLastLine: false,
                    wordWrap: 'on',
                    tabSize: 2,
                  }}
                />
              </div>
            </div>
          )}

          {activeTab === 'chat' && (
            <div className="flex-1 flex flex-col h-full overflow-hidden">
              {/* Chat Messages */}
              <div className="flex-1 p-4 overflow-y-auto space-y-4 min-h-0">
                {chatMessages.map(message => (
                  <div
                    key={message.id}
                    className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg whitespace-pre-wrap ${
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
                    <div className="bg-gray-700 px-4 py-3 rounded-lg min-w-64 border border-gray-600">
                      <div className="flex items-center space-x-2 mb-2">
                        <div className="relative">
                          <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                          <div className="absolute inset-0 w-4 h-4 rounded-full border border-blue-400 animate-ping opacity-30"></div>
                        </div>
                        <span className="text-sm text-blue-400 font-medium">AI Assistant</span>
                        <div className="ml-auto">
                          <div className="flex space-x-1">
                            <div className="w-1 h-1 bg-blue-400 rounded-full animate-pulse"></div>
                            <div className="w-1 h-1 bg-blue-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                            <div className="w-1 h-1 bg-blue-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                          </div>
                        </div>
                      </div>
                      <div className="text-sm text-gray-300 mb-3 transition-all duration-500 min-h-5">
                        {thinkingMessage || '• Initializing...'}
                      </div>
                      <div className="w-full bg-gray-600 rounded-full h-2 overflow-hidden">
                        <div 
                          className="bg-gradient-to-r from-blue-500 via-purple-500 to-blue-600 h-2 rounded-full transition-all duration-700 ease-out relative" 
                          style={{ width: `${thinkingProgress}%` }}
                        >
                          <div className="absolute inset-0 bg-white opacity-20 animate-pulse"></div>
                        </div>
                      </div>
                      <div className="flex justify-between text-xs text-gray-400 mt-1">
                        <span>Processing</span>
                        <span>{Math.round(thinkingProgress)}% complete</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Chat Input */}
              <div className="border-t border-gray-700 p-4 flex-shrink-0">
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={e => setChatInput(e.target.value)}
                    onKeyPress={e => e.key === 'Enter' && sendChatMessage()}
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
            <div className="flex-1 flex flex-col h-full overflow-hidden">
              {/* Agent Selection */}
              <div className="border-b border-gray-700 p-4 flex-shrink-0">
                <div className="mb-3">
                  <label className="block text-sm font-medium mb-2">Select Agent:</label>
                  <div className="grid grid-cols-2 gap-2">
                    {[
                      { id: 'coder', name: 'Code Generator', icon: Code },
                      { id: 'debugger', name: 'Debug Assistant', icon: Bug },
                      { id: 'analyzer', name: 'Code Analyzer', icon: Zap },
                      { id: 'optimizer', name: 'Performance Optimizer', icon: GitBranch },
                    ].map(agent => (
                      <button
                        key={agent.id}
                        onClick={() => setSelectedAgent(agent.id as any)}
                        className={`flex items-center space-x-2 px-3 py-2 rounded text-sm ${
                          selectedAgent === agent.id
                            ? 'bg-wave-600'
                            : 'bg-gray-700 hover:bg-gray-600'
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
                    onChange={e => setTaskInput(e.target.value)}
                    onKeyPress={e => e.key === 'Enter' && executeAgentTask()}
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
              <div className="flex-1 p-4 overflow-y-auto min-h-0">
                <h3 className="text-sm font-medium mb-3">Active Tasks</h3>
                <div className="space-y-3">
                  {activeTasks.map(task => (
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
                        <div className="space-y-2">
                          <div className="flex justify-between text-xs">
                            <div className="flex items-center space-x-2">
                              {task.progress.status === 'thinking' && (
                                <Loader2 className="w-3 h-3 animate-spin text-blue-400" />
                              )}
                              <span className="text-blue-400">
                                {task.progress.message}
                              </span>
                            </div>
                            <span className="text-gray-400">{task.progress.progress}%</span>
                          </div>
                          <div className="w-full bg-gray-700 rounded-full h-2">
                            <div
                              className="bg-gradient-to-r from-wave-400 to-wave-500 h-2 rounded-full transition-all duration-500"
                              style={{ width: `${task.progress.progress}%` }}
                            />
                          </div>
                          {task.progress.status === 'thinking' && (
                            <div className="text-xs text-gray-400 animate-pulse">
                              • Agent is analyzing and planning...
                            </div>
                          )}
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
            <div className="flex-1 flex flex-col bg-black h-full overflow-hidden">
              {/* Terminal Output */}
              <div className="flex-1 p-4 overflow-y-auto font-mono text-sm min-h-0">
                {terminalOutput.map((line, index) => (
                  <div key={index} className="text-green-400 mb-1">
                    {line}
                  </div>
                ))}
              </div>

              {/* Terminal Input */}
              <div className="border-t border-gray-700 p-4 flex-shrink-0">
                <div className="flex items-center space-x-2 font-mono text-sm">
                  <span className="text-green-400">$</span>
                  <input
                    type="text"
                    value={terminalInput}
                    onChange={e => setTerminalInput(e.target.value)}
                    onKeyPress={e => {
                      if (e.key === 'Enter') {
                        const command = terminalInput.trim();
                        if (command) {
                          executeTerminalCommand(command);
                        }
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
