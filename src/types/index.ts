// WaveRider Core Types
// Centralized type definitions for the entire application

export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  preferences: UserPreferences;
  createdAt: Date;
  lastLogin?: Date;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  notifications: boolean;
  ai: AIPreferences;
}

export interface AIPreferences {
  model: 'gpt-4' | 'claude-3-sonnet' | 'grok-beta';
  temperature: number;
  maxTokens: number;
  autoSuggestions: boolean;
  inlineCompletion: boolean;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  path: string;
  type: 'web' | 'mobile' | 'desktop' | 'api' | 'library';
  framework: string;
  lastOpened: Date;
  aiEnabled: boolean;
  agents: string[];
  ownerId: string;
  settings: ProjectSettings;
  createdAt: Date;
  updatedAt?: Date;
}

export interface ProjectSettings {
  buildCommand?: string;
  startCommand?: string;
  testCommand?: string;
  nodeVersion?: string;
  packageManager: 'npm' | 'yarn' | 'pnpm';
  autoSave: boolean;
  linting: boolean;
  formatting: boolean;
}

export interface FileNode {
  path: string;
  name: string;
  type: 'file' | 'directory';
  size?: number;
  lastModified?: Date;
  children?: FileNode[];
  isExpanded?: boolean;
}

export interface ChatMessage {
  id: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  projectId?: string;
  metadata?: {
    model?: string;
    tokensUsed?: number;
    executionTime?: number;
  };
}

export interface AgentTask {
  id: string;
  sessionId: string;
  projectId: string;
  agentType: 'planner' | 'coder' | 'debugger' | 'optimizer' | 'reviewer';
  task: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress?: AgentProgress;
  result?: AgentResult;
  createdAt: Date;
  completedAt?: Date;
}

export interface AgentProgress {
  percentage: number;
  status: 'thinking' | 'analyzing' | 'executing' | 'reviewing';
  message: string;
  currentStep?: string;
  totalSteps?: number;
  timestamp: Date;
}

export interface AgentResult {
  success: boolean;
  output?: string;
  filesCreated?: string[];
  filesModified?: string[];
  errors?: string[];
  warnings?: string[];
  suggestions?: string[];
  nextActions?: string[];
}

export interface WebSocketMessage {
  type: 'agent_progress' | 'file_changed' | 'project_updated' | 'error' | 'ping' | 'pong';
  data?: any;
  timestamp: Date;
  clientId?: string;
}

export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  timestamp: Date;
}

// Utility types
export type AgentType = AgentTask['agentType'];
export type ProjectType = Project['type'];
export type FileType = FileNode['type'];
export type TaskStatus = AgentTask['status'];
export type MessageSender = ChatMessage['sender'];

// Form types
export interface CreateProjectRequest {
  name: string;
  description?: string;
  type: ProjectType;
  framework?: string;
  template?: string;
}

export interface ChatRequest {
  message: string;
  projectId?: string;
  context?: string;
}

export interface AgentTaskRequest {
  task: string;
  agentType: AgentType;
  projectId: string;
  context?: string;
  files?: string[];
}

// Store types
export interface AppState {
  user: User | null;
  currentProject: Project | null;
  projects: Project[];
  openFiles: FileNode[];
  activeFile: string | null;
  chatHistory: ChatMessage[];
  activeTasks: AgentTask[];
  isLoading: boolean;
  error: string | null;
}
