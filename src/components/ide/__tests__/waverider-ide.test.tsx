import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import WaveRiderIDE from '../waverider-ide';

// Mock Monaco Editor
jest.mock('@monaco-editor/react', () => {
  return function MockedMonacoEditor(props: any) {
    return (
      <div data-testid="monaco-editor">
        <textarea
          value={props.value}
          onChange={e => props.onChange?.(e.target.value)}
          data-testid="editor-textarea"
        />
      </div>
    );
  };
});

// Mock Socket.IO
jest.mock('socket.io-client', () => ({
  io: jest.fn(() => ({
    on: jest.fn(),
    emit: jest.fn(),
    disconnect: jest.fn(),
  })),
}));

// Mock fetch for API calls
global.fetch = jest.fn();

describe('WaveRiderIDE', () => {
  beforeEach(() => {
    // Reset fetch mock
    (fetch as jest.Mock).mockClear();
  });

  test('renders WaveRider IDE header', () => {
    render(<WaveRiderIDE />);
    expect(screen.getByText('🌊 WaveRider IDE')).toBeInTheDocument();
  });

  test('displays editor tab by default', () => {
    render(<WaveRiderIDE />);
    expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
  });

  test('can switch between tabs', () => {
    render(<WaveRiderIDE />);

    // Click on chat tab
    fireEvent.click(screen.getByText('AI Chat'));
    expect(screen.getByPlaceholderText('Ask AI anything about your code...')).toBeInTheDocument();

    // Click on tasks tab
    fireEvent.click(screen.getByText('Agents'));
    expect(screen.getByText('Select Agent:')).toBeInTheDocument();

    // Click on terminal tab
    fireEvent.click(screen.getByText('Terminal'));
    expect(screen.getByPlaceholderText('Enter command...')).toBeInTheDocument();
  });

  test('can send chat messages', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        response: 'Hello! How can I help you?',
        timestamp: new Date().toISOString(),
      }),
    });

    render(<WaveRiderIDE />);

    // Switch to chat tab
    fireEvent.click(screen.getByText('AI Chat'));

    // Type and send message
    const input = screen.getByPlaceholderText('Ask AI anything about your code...');
    fireEvent.change(input, { target: { value: 'Hello AI' } });
    fireEvent.click(screen.getByText('Send'));

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/chat'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        })
      );
    });
  });

  test('can create agent tasks', () => {
    render(<WaveRiderIDE />);

    // Switch to tasks tab
    fireEvent.click(screen.getByText('Agents'));

    // Select an agent
    fireEvent.click(screen.getByText('Code Generator'));

    // Enter task description
    const taskInput = screen.getByPlaceholderText('Describe what you want the agent to do...');
    fireEvent.change(taskInput, { target: { value: 'Create a React component' } });

    // Execute task button should be present
    expect(screen.getByText('Execute')).toBeInTheDocument();
  });

  test('displays save button when file is selected', () => {
    render(<WaveRiderIDE />);

    const saveButton = screen.getByText('Save');
    expect(saveButton).toBeInTheDocument();
    // Should be disabled when no file is selected
    expect(saveButton).toBeDisabled();
  });
});
