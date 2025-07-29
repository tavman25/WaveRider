<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# WaveRider - Agentic AI IDE Instructions

## Project Overview
WaveRider is an advanced agentic AI-native IDE built on Next.js frontend with FastAPI backend and LangGraph-based autonomous agents. It provides seamless human-AI collaboration for coding, debugging, and optimization tasks.

## Architecture Guidelines
- **Frontend**: Next.js 14 with TypeScript, Tailwind CSS, Monaco Editor
- **Backend**: FastAPI with Python, async/await patterns
- **AI Agents**: LangGraph orchestration with specialized agents (Planner, Coder, Debugger, Optimizer)
- **Real-time**: Socket.IO for collaboration and live updates
- **State Management**: Zustand for client state, Redis for backend caching
- **Styling**: Tailwind CSS with custom WaveRider theme colors (wave-* and rider-*)

## Code Style Preferences
- Use TypeScript with strict type checking
- Prefer functional components with hooks
- Use async/await over Promises
- Implement proper error boundaries and loading states
- Follow Next.js App Router patterns
- Use server components where possible
- Implement proper SEO and accessibility

## AI Agent Integration
- All agent communications should be typed with proper interfaces
- Use WebSocket connections for real-time agent updates
- Implement proper error handling for agent failures
- Use context management for infinite context capability
- Implement tool calling patterns for agent extensibility

## Security Considerations
- Implement proper authentication and authorization
- Sanitize all user inputs
- Use environment variables for sensitive data
- Implement rate limiting for AI API calls
- Follow OWASP security guidelines

## Performance Optimization
- Use React.memo and useMemo for expensive computations
- Implement proper code splitting and lazy loading
- Use Monaco Editor efficiently with web workers
- Optimize bundle size and reduce dependencies
- Implement proper caching strategies

## Testing Strategy
- Write unit tests for utility functions
- Implement integration tests for API endpoints
- Use React Testing Library for component tests
- Mock AI agent responses for consistent testing
- Implement E2E tests for critical user flows
