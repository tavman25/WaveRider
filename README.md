# 🌊 WaveRider - Agentic AI-Native IDE

![WaveRider Banner](https://img.shields.io/badge/WaveRider-AI%20IDE-blue?style=for-the-badge&logo=react)

> **The future of software development is here.** WaveRider is an advanced agentic AI-native IDE that provides seamless human-AI collaboration for coding, debugging, and optimization tasks through autonomous AI agents.

## ✨ Features

### 🤖 **Autonomous AI Agents**
- **Planner Agent**: Breaks down complex tasks into actionable steps
- **Coder Agent**: Generates and modifies code with context awareness
- **Debugger Agent**: Identifies and fixes bugs automatically
- **Optimizer Agent**: Improves performance and code quality
- **Reviewer Agent**: Provides code reviews and suggestions

### 🎯 **Core Capabilities**
- **Real-time Collaboration**: WebSocket-powered live updates
- **State Persistence**: Never lose your work through browser refreshes
- **Multi-Model AI**: Support for GPT-4, Claude, and Grok
- **File Operations**: Full filesystem integration with project management
- **Terminal Integration**: Execute commands directly within the IDE
- **Progress Tracking**: Visual feedback with contextual thinking indicators

### 🔧 **Developer Experience**
- **Monaco Editor**: VS Code-like editing experience
- **Syntax Highlighting**: Support for 100+ programming languages
- **Auto-completion**: AI-powered code suggestions
- **Error Detection**: Real-time syntax and semantic error checking
- **Project Templates**: Quick start with pre-configured setups

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   AI Agents     │
│   Next.js 14    │◄──►│   FastAPI       │◄──►│   LangGraph     │
│   TypeScript     │    │   Python        │    │   Orchestrator  │
│   Tailwind CSS  │    │   SQLite/PgSQL  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   UI Components │    │   API Routes    │    │   Specialized   │
│   • IDE Layout  │    │   • Chat        │    │   Agents        │
│   • Editor      │    │   • Tasks       │    │   • Planning    │
│   • Terminal    │    │   • Files       │    │   • Coding      │
│   • Chat        │    │   • Projects    │    │   • Debugging   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- **Node.js** 18+ 
- **Python** 3.9+
- **Git**

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/tavman25/WaveRider.git
   cd WaveRider
   ```

2. **Install dependencies**
   ```bash
   # Frontend dependencies
   npm install
   
   # Backend dependencies
   cd backend
   pip install -r requirements-dev.txt
   cd ..
   ```

3. **Environment setup**
   ```bash
   # Copy environment template
   cp .env.example .env.local
   
   # Add your API keys
   nano .env.local
   ```

4. **Start development servers**
   ```bash
   # Windows
   .\start-waverider.bat
   
   # macOS/Linux
   npm run dev:full
   ```

5. **Access the application**
   - **Frontend**: http://localhost:3000
   - **Backend**: http://localhost:8002
   - **API Docs**: http://localhost:8002/docs

## 🔑 Environment Variables

Create a `.env.local` file in the root directory:

```env
# AI Service API Keys
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
XAI_API_KEY=your_xai_key_here

# Database Configuration
DATABASE_URL=sqlite:///./waverider.db
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET=your_jwt_secret_here

# Optional Services
PINECONE_API_KEY=your_pinecone_key_here
VECTOR_DB_URL=http://localhost:8080
```

## 📖 Usage Guide

### Creating Your First Project

1. **Launch WaveRider** and click "New Project"
2. **Choose a template** or start from scratch
3. **Select AI agents** for your project type
4. **Start coding** with AI assistance

### Working with AI Agents

#### Chat Interface
```
💬 Ask anything: "Create a React component for user authentication"
🤖 AI responds with code and explanations
📁 Files are automatically created and organized
```

#### Agent Tasks
```
🎯 Select agent: Coder, Debugger, Optimizer, or Planner
📝 Describe task: "Optimize database queries in user service"
⚡ Watch real-time progress with thinking indicators
✅ Review results and iterate
```

### Terminal Integration
```bash
# Run commands directly in the IDE
npm install express
npm run build
git commit -m "Add new feature"
```

## 🧪 Testing

```bash
# Frontend tests
npm test

# Backend tests
cd backend && python -m pytest

# E2E tests
npm run test:e2e

# Coverage report
npm run test:coverage
```

## 📦 Deployment

### Docker Deployment
```bash
# Build containers
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

### Manual Deployment
```bash
# Build frontend
npm run build

# Start production servers
npm start
cd backend && python -m uvicorn server:app --host 0.0.0.0 --port 8002
```

## 🛠️ Development

### Project Structure
```
WaveRider/
├── src/                     # Frontend source
│   ├── components/          # React components
│   ├── hooks/              # Custom React hooks
│   ├── types/              # TypeScript definitions
│   ├── utils/              # Utility functions
│   └── store/              # State management
├── backend/                 # Backend source
│   ├── api/                # API route handlers
│   ├── models/             # Database models
│   ├── services/           # Business logic
│   └── server.py           # Main server file
├── agents/                  # AI agent definitions
├── docs/                   # Documentation
└── scripts/                # Utility scripts
```

### Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Code Style

- **Frontend**: ESLint + Prettier with TypeScript strict mode
- **Backend**: Black + isort with type hints
- **Commits**: Conventional Commits format

## 📚 API Documentation

### REST Endpoints

#### Projects
```typescript
GET    /api/projects          // List all projects
POST   /api/projects          // Create new project
GET    /api/projects/:id      // Get project details
PUT    /api/projects/:id      // Update project
DELETE /api/projects/:id      // Delete project
```

#### AI Chat
```typescript
POST   /api/chat             // Send message to AI
GET    /api/chat/history     // Get chat history
DELETE /api/chat/history     // Clear chat history
```

#### Agent Tasks
```typescript
POST   /api/tasks            // Create agent task
GET    /api/tasks            // List active tasks
GET    /api/tasks/:id        // Get task status
DELETE /api/tasks/:id        // Cancel task
```

### WebSocket Events

```typescript
// Client → Server
{
  "type": "ping",
  "data": { "timestamp": 1234567890 }
}

// Server → Client
{
  "type": "agent_progress",
  "data": {
    "taskId": "uuid",
    "progress": 75,
    "message": "Generating code...",
    "status": "executing"
  }
}
```

## 🔧 Configuration

### Customizing AI Behavior

```typescript
// User preferences
{
  "ai": {
    "model": "grok-beta",           // Primary AI model
    "temperature": 0.7,             // Creativity level
    "maxTokens": 4000,             // Response length
    "autoSuggestions": true,       // Real-time suggestions
    "inlineCompletion": true       // Autocomplete
  }
}
```

### Project Settings

```typescript
// Project configuration
{
  "buildCommand": "npm run build",
  "startCommand": "npm start",
  "testCommand": "npm test",
  "packageManager": "npm",        // npm, yarn, pnpm
  "autoSave": true,
  "linting": true,
  "formatting": true
}
```

## 🐛 Troubleshooting

### Common Issues

#### WebSocket Connection Failed
```bash
# Check if backend is running
curl http://localhost:8002/

# Verify environment variables
echo $REDIS_URL
```

#### AI Responses Not Working
```bash
# Verify API keys
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Check API quotas and limits
```

#### File Operations Failing
```bash
# Check file permissions
ls -la projects/

# Verify project directory structure
```

## 📊 Performance

### Benchmarks

- **Initial Load**: < 2s
- **File Operations**: < 100ms
- **AI Response**: 2-5s (depending on model)
- **WebSocket Latency**: < 50ms

### Optimization Tips

- Use **code splitting** for large projects
- Enable **Redis caching** for faster responses
- Configure **CDN** for static assets
- Monitor **AI usage** to optimize costs

## 🔐 Security

### Best Practices

- ✅ **API Keys**: Never commit to repository
- ✅ **HTTPS**: Required for production
- ✅ **Input Validation**: Sanitize all user inputs
- ✅ **Rate Limiting**: Prevent API abuse
- ✅ **CORS**: Configure for specific domains

### Security Features

- **JWT Authentication**: Secure user sessions
- **Role-based Access**: Control feature access
- **Audit Logging**: Track all user actions
- **File Sandboxing**: Isolated project environments

## 📈 Roadmap

### Q1 2025
- [ ] Advanced debugging tools
- [ ] Git integration
- [ ] Plugin system
- [ ] Team collaboration

### Q2 2025
- [ ] Mobile companion app
- [ ] Advanced AI models
- [ ] Performance profiling
- [ ] Cloud deployment

### Q3 2025
- [ ] Enterprise features
- [ ] Advanced security
- [ ] Custom agent creation
- [ ] Marketplace

## 🤝 Community

- **Discord**: [Join our community](https://discord.gg/waverider)
- **Twitter**: [@WaveRiderIDE](https://twitter.com/WaveRiderIDE)
- **Blog**: [WaveRider Blog](https://blog.waverider.dev)
- **Documentation**: [Full Docs](https://docs.waverider.dev)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for GPT models
- **Anthropic** for Claude
- **xAI** for Grok
- **Vercel** for Next.js
- **FastAPI** team for the amazing framework

---

<div align="center">

**Built with ❤️ by the WaveRider team**

[🌊 Try WaveRider](https://waverider.dev) • [📖 Documentation](https://docs.waverider.dev) • [🐛 Report Bug](https://github.com/tavman25/WaveRider/issues)

</div>
