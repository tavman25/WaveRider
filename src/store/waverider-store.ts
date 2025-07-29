'use client';

import React from 'react';
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

// Types
interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  preferences: UserPreferences;
}

interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  editor: EditorPreferences;
  ai: AIPreferences;
}

interface EditorPreferences {
  fontSize: number;
  tabSize: number;
  wordWrap: boolean;
  minimap: boolean;
  lineNumbers: boolean;
  autoSave: boolean;
}

interface AIPreferences {
  model: 'gpt-4' | 'claude-3-sonnet' | 'grok-beta';
  temperature: number;
  maxTokens: number;
  autoSuggestions: boolean;
  inlineCompletion: boolean;
}

interface Project {
  id: string;
  name: string;
  description: string;
  path: string;
  type: 'web' | 'mobile' | 'desktop' | 'api' | 'library';
  framework: string;
  lastOpened: Date;
  aiEnabled: boolean;
  agents: string[];
}

interface WaveRiderState {
  // User & Auth
  user: User | null;
  isAuthenticated: boolean;

  // Projects
  currentProject: Project | null;
  projects: Project[];
  recentProjects: Project[];

  // Editor State
  openFiles: string[];
  activeFile: string | null;
  currentFile: string | null; // Currently viewed file path
  fileContent: Record<string, string>; // Map of file paths to their content

  // AI State
  aiConnected: boolean;
  activeAgents: string[];
  agentStatus: Record<string, { 
    status: 'idle' | 'thinking' | 'working' | 'error'; 
    message?: string; 
    progress?: number; 
    timestamp?: Date 
  }>;

  // UI State
  sidebarOpen: boolean;
  panelOpen: boolean;
  terminalOpen: boolean;
  aiChatOpen: boolean;
  terminalOutput: string[]; // Terminal command history
  chatHistory: Array<{ role: 'user' | 'assistant'; content: string; timestamp: Date }>;

  // Settings
  settings: {
    theme: 'light' | 'dark' | 'auto';
    fontSize: number;
    fontFamily: string;
    tabSize: number;
    wordWrap: boolean;
    minimap: boolean;
    autoSave: boolean;
    ai: AIPreferences;
  };

  // System
  initialized: boolean;
  loading: boolean;
  error: string | null;
}

interface WaveRiderActions {
  // User & Auth
  setUser: (user: User | null) => void;
  updateUserPreferences: (preferences: Partial<UserPreferences>) => void;

  // Projects
  setCurrentProject: (project: Project | null) => void;
  addProject: (project: Project) => void;
  updateProject: (id: string, updates: Partial<Project>) => void;
  removeProject: (id: string) => void;

  // Editor
  openFile: (filePath: string) => void;
  closeFile: (filePath: string) => void;
  setActiveFile: (filePath: string | null) => void;
  setCurrentFile: (filePath: string | null) => void;
  setFileContent: (filePath: string, content: string) => void;
  getFileContent: (filePath: string) => string | undefined;

  // Settings
  updateSettings: (settings: Partial<WaveRiderState['settings']>) => void;

  // AI
  setAIConnected: (connected: boolean) => void;
  setAgentStatus: (agentId: string, status: WaveRiderState['agentStatus'][string]) => void;
  addActiveAgent: (agentId: string) => void;
  removeActiveAgent: (agentId: string) => void;

  // UI
  toggleSidebar: () => void;
  togglePanel: () => void;
  toggleTerminal: () => void;
  toggleAIChat: () => void;
  addToTerminal: (message: string) => void;
  clearTerminal: () => void;
  addToChatHistory: (role: 'user' | 'assistant', content: string) => void;
  clearChatHistory: () => void;

  // System
  initialize: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

type WaveRiderStore = WaveRiderState & WaveRiderActions;

const initialState: WaveRiderState = {
  user: null,
  isAuthenticated: false,
  currentProject: null,
  projects: [],
  recentProjects: [],
  openFiles: [],
  activeFile: null,
  currentFile: null,
  fileContent: {},
  aiConnected: false,
  activeAgents: [],
  agentStatus: {},
  sidebarOpen: true,
  panelOpen: false,
  terminalOpen: false,
  aiChatOpen: false,
  terminalOutput: [],
  chatHistory: [],
  settings: {
    theme: 'dark',
    fontSize: 14,
    fontFamily: 'Consolas, Monaco, "Courier New", monospace',
    tabSize: 2,
    wordWrap: true,
    minimap: true,
    autoSave: true,
    ai: {
      model: 'grok-beta',
      temperature: 0.7,
      maxTokens: 4000,
      autoSuggestions: true,
      inlineCompletion: true,
    },
  },
  initialized: false,
  loading: false,
  error: null,
};

export const useWaveRiderStore = create<WaveRiderStore>()(
  persist(
    (set, get) => ({
      ...initialState,

      // User & Auth
      setUser: user => set({ user, isAuthenticated: !!user }),

      updateUserPreferences: preferences =>
        set(state => ({
          user: state.user
            ? {
                ...state.user,
                preferences: { ...state.user.preferences, ...preferences },
              }
            : null,
        })),

      // Projects
      setCurrentProject: currentProject => set({ currentProject }),

      addProject: project =>
        set(state => ({
          projects: [...state.projects, project],
          recentProjects: [project, ...state.recentProjects.filter(p => p.id !== project.id)].slice(
            0,
            10
          ),
        })),

      updateProject: (id, updates) =>
        set(state => ({
          projects: state.projects.map(p => (p.id === id ? { ...p, ...updates } : p)),
          currentProject:
            state.currentProject?.id === id
              ? { ...state.currentProject, ...updates }
              : state.currentProject,
        })),

      removeProject: id =>
        set(state => ({
          projects: state.projects.filter(p => p.id !== id),
          recentProjects: state.recentProjects.filter(p => p.id !== id),
          currentProject: state.currentProject?.id === id ? null : state.currentProject,
        })),

      // Editor
      openFile: filePath =>
        set(state => ({
          openFiles: state.openFiles.includes(filePath)
            ? state.openFiles
            : [...state.openFiles, filePath],
          activeFile: filePath,
        })),

      closeFile: filePath =>
        set(state => {
          const newOpenFiles = state.openFiles.filter(f => f !== filePath);
          const newActiveFile =
            state.activeFile === filePath
              ? newOpenFiles.length > 0
                ? newOpenFiles[newOpenFiles.length - 1]
                : null
              : state.activeFile;
          return { openFiles: newOpenFiles, activeFile: newActiveFile };
        }),

      setActiveFile: activeFile => set({ activeFile }),

      setCurrentFile: currentFile => set({ currentFile }),

      setFileContent: (filePath, content) =>
        set(state => ({
          fileContent: { ...state.fileContent, [filePath]: content },
        })),

      getFileContent: filePath => get().fileContent[filePath],

      // Settings
      updateSettings: settings =>
        set(state => ({
          settings: { ...state.settings, ...settings },
        })),

      // AI
      setAIConnected: aiConnected => set({ aiConnected }),

      setAgentStatus: (agentId, status) =>
        set(state => ({
          agentStatus: { ...state.agentStatus, [agentId]: status },
        })),

      addActiveAgent: agentId =>
        set(state => ({
          activeAgents: state.activeAgents.includes(agentId)
            ? state.activeAgents
            : [...state.activeAgents, agentId],
        })),

      removeActiveAgent: agentId =>
        set(state => ({
          activeAgents: state.activeAgents.filter(id => id !== agentId),
        })),

      // UI
      toggleSidebar: () => set(state => ({ sidebarOpen: !state.sidebarOpen })),
      togglePanel: () => set(state => ({ panelOpen: !state.panelOpen })),
      toggleTerminal: () => set(state => ({ terminalOpen: !state.terminalOpen })),
      toggleAIChat: () => set(state => ({ aiChatOpen: !state.aiChatOpen })),

      addToTerminal: message =>
        set(state => ({
          terminalOutput: [...state.terminalOutput, message],
        })),

      clearTerminal: () => set({ terminalOutput: [] }),

      addToChatHistory: (role, content) =>
        set(state => ({
          chatHistory: [...state.chatHistory, { role, content, timestamp: new Date() }],
        })),

      clearChatHistory: () => set({ chatHistory: [] }),

      // System
      initialize: () => set({ initialized: true }),
      setLoading: loading => set({ loading }),
      setError: error => set({ error }),
      reset: () => set(initialState),
    }),
    {
      name: 'waverider-store',
      storage: createJSONStorage(() => localStorage),
      partialize: state => ({
        user: state.user,
        projects: state.projects,
        recentProjects: state.recentProjects,
        currentProject: state.currentProject,
        currentFile: state.currentFile,
        fileContent: state.fileContent,
        openFiles: state.openFiles,
        activeFile: state.activeFile,
        terminalOutput: state.terminalOutput,
        chatHistory: state.chatHistory,
        sidebarOpen: state.sidebarOpen,
        panelOpen: state.panelOpen,
        terminalOpen: state.terminalOpen,
        aiChatOpen: state.aiChatOpen,
        settings: state.settings,
      }),
    }
  )
);

// Provider component for React context if needed
export function WaveRiderStoreProvider({ children }: { children: React.ReactNode }) {
  return children;
}
