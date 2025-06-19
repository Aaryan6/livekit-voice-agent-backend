# Code Interpreter Feature

## Overview

The Code Interpreter feature allows the AI interviewer to open a code editor in the UI for coding questions. When the interviewer asks a coding question, a Monaco Editor (VS Code editor) opens as a modal dialog where candidates can write and submit their code solutions.

## Architecture

### Frontend (React/Next.js)

- **CodeEditor Component**: Monaco Editor with syntax highlighting, language selection, and explanation field
- **RPC Integration**: Listens for `openCodeEditor` RPC calls and sends code back via `submitCode` RPC

### Backend (Python/LiveKit)

- **Tools**: `open_code_editor` and `analyze_submitted_code` function tools
- **RPC Handler**: Processes code submissions from the frontend

## Flow Diagram

```
AI Agent → open_code_editor() → RPC: openCodeEditor → Frontend opens CodeEditor
                                                      ↓
Frontend: User writes code → Submit → RPC: submitCode → Backend: analyze_submitted_code()
                                                      ↓
AI Agent provides feedback based on submitted code
```

## Usage

### For AI Interviewers

The agent can now ask coding questions using the `open_code_editor` tool:

```python
@function_tool()
async def open_code_editor(self, context: RunContext, question: str, language: str = "javascript"):
    """Opens a code editor in the UI for coding questions."""
```

**Example usage in agent instructions:**

- "Write a function to reverse a string" (Python)
- "Implement a binary search algorithm" (JavaScript)
- "Create a simple sorting function" (Java)

### Supported Languages

The code editor supports 14 programming languages with syntax highlighting:

- JavaScript, TypeScript, Python, Java
- C++, C, C#, Go, Rust
- PHP, Ruby, SQL, HTML, CSS

### Code Templates

Each language comes with a starter template to help candidates get started quickly.

## Implementation Details

### Frontend Components

#### CodeEditor.tsx

```typescript
interface CodeEditorProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (code: string, language: string, explanation?: string) => void;
  question: string;
  language?: string;
}
```

Key features:

- Monaco Editor with VS Code-like experience
- Language selector with syntax highlighting
- Optional explanation field for thought process
- Responsive design that works in modal dialog

#### RPC Integration

```typescript
// Listen for code editor requests
const openCodeEditor = async (data: RpcInvocationData) => {
  const params = JSON.parse(data.payload);
  setCurrentQuestion(params.question);
  setCurrentLanguage(params.language);
  setCodeEditorOpen(true);
  return JSON.stringify({ success: true });
};

// Send code back to agent
await room.localParticipant.performRpc({
  destinationIdentity: agentParticipant.identity,
  method: "submitCode",
  payload: JSON.stringify({ code, language, explanation, question }),
});
```

### Backend Tools

#### open_code_editor Tool

```python
@function_tool()
async def open_code_editor(self, context: RunContext[InterviewSessionData], question: str, language: str = "javascript"):
    """Use this tool to open a code editor in the UI for coding questions."""
```

Features:

- Sends RPC call to frontend to open editor
- Tracks question count and logs activity
- Graceful fallback to verbal questions if RPC fails

#### analyze_submitted_code Tool

```python
@function_tool()
async def analyze_submitted_code(self, context: RunContext[InterviewSessionData],
                               code: str, language: str, explanation: str, question: str):
    """Called when candidate submits code. Analyzes and provides feedback."""
```

Features:

- Stores code submission in session data
- Provides immediate feedback to candidate
- Logs code metrics (length, language, etc.)

## Sample Coding Questions by Skill Level

### Junior Level

- "Write a function to check if a number is even or odd" (JavaScript)
- "Create a function that finds the maximum number in an array" (Python)
- "Write a function to count vowels in a string" (Java)

### Mid Level

- "Implement a function to reverse a linked list" (Python)
- "Write a function to find the first non-repeating character in a string" (JavaScript)
- "Create a simple binary search algorithm" (C++)

### Senior Level

- "Design and implement a LRU cache" (Python)
- "Write a function to serialize and deserialize a binary tree" (Java)
- "Implement a rate limiter using sliding window" (JavaScript)

## Testing

Run the test script to verify the code interpreter functionality:

```bash
cd feedback-v0-custom
python test_code_interpreter.py
```

This will test:

1. Opening the code editor
2. Code submission and analysis
3. Data persistence in interview session

## Configuration

### Environment Variables

No additional environment variables needed. The feature works with existing LiveKit configuration.

### Package Dependencies

**Frontend:**

```json
{
  "@monaco-editor/react": "^4.6.0",
  "@radix-ui/react-dialog": "^1.1.14"
}
```

**Backend:**
Uses existing LiveKit agents dependencies.

## Error Handling

### Frontend Errors

- Editor loading failures: Graceful fallback message
- RPC timeout: User-friendly error notification
- Validation: Prevents submission of empty code

### Backend Errors

- RPC failure: Falls back to verbal question asking
- Context errors: Logs error and continues interview
- Code analysis errors: Simple acknowledgment message

## Interview Integration

The code interpreter is seamlessly integrated into the technical interview flow:

1. **Introduction Stage**: Regular conversation
2. **Projects Discussion**: Talk about past work
3. **Technical Questions**: Mix of conceptual questions AND coding questions
4. **Code Editor**: Opens automatically for coding questions
5. **Code Analysis**: Immediate feedback and discussion
6. **Hobbies**: Personal interests
7. **Conclusion**: Interview wrap-up

## Best Practices

### For Interviewers (Agent)

- Ask 1-2 coding questions per interview
- Choose appropriate language based on candidate background
- Provide clear, specific problem statements
- Allow time for explanation and discussion

### For Candidates

- Read the problem statement carefully
- Use the explanation field to describe your approach
- Test your code with example inputs
- Ask clarifying questions if needed

## Future Enhancements

Potential improvements:

- Code execution and testing
- Collaborative editing features
- Code review and commenting
- Integration with external code judges
- Video recording of coding sessions
- Time tracking for coding problems

## Troubleshooting

### Common Issues

**Code editor doesn't open:**

- Check browser console for JavaScript errors
- Verify RPC connection is established
- Ensure Monaco Editor loaded properly

**Code submission fails:**

- Check network connectivity
- Verify agent is in TechnicalQuestionsAgent stage
- Look at backend logs for RPC errors

**Syntax highlighting not working:**

- Ensure language is supported
- Check Monaco Editor language configuration
- Verify language string matches supported values

### Debug Mode

Enable debug logging in the backend:

```python
logger.setLevel(logging.DEBUG)
```

Check browser console for frontend debug information.

## Conclusion

The Code Interpreter feature provides a professional, interactive coding experience that closely mimics real-world technical interviews. It combines the convenience of modern code editors with the structure of AI-driven interviews, creating an efficient and comprehensive evaluation tool.
