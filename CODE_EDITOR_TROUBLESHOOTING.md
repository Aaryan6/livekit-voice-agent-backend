# Code Editor Troubleshooting Guide

## Issues Fixed ✅

### 1. TypeError: object function can't be used in 'await' expression

**Status**: ✅ FIXED

- **Problem**: RPC registration was using `await` incorrectly
- **Solution**: Removed `await` from `register_rpc_method` call
- **File**: `agent.py` line 674

### 2. AI Reading Question Aloud Instead of Silent Code Editor

**Status**: ✅ FIXED

- **Problem**: AI was saying the full question after opening code editor
- **Solution**: Changed message to not repeat the question
- **File**: `agent.py` open_code_editor function

## Current Status 🚀

✅ **Backend Tests Passing**: All agent imports and tools working  
✅ **RPC Payloads Valid**: JSON serialization working correctly  
✅ **Frontend Integration**: CodeEditor component properly included  
✅ **Logging Added**: Enhanced debugging in both frontend and backend

## Testing the Code Editor 🧪

### Step 1: Start Backend

```bash
cd feedback-v0-custom
python agent.py dev
```

### Step 2: Start Frontend (New Terminal)

```bash
cd feedback-v0-ui-custom
pnpm dev
```

### Step 3: Test the Flow

1. Open browser to `http://localhost:3000`
2. Fill in user info and connect
3. Wait for technical questions stage
4. AI should use `open_code_editor` tool for coding questions
5. Code editor modal should open with the question displayed
6. User writes code and submits
7. AI receives code and provides feedback

## Browser Console Debugging 🔍

When the code editor works correctly, you should see these logs:

### On Connection:

```
RPC Setup: Setting up RPC methods for code editor
RPC method 'openCodeEditor' registered successfully
```

### When AI Opens Code Editor:

```
Received openCodeEditor RPC call: {payload: "{"question":"...", "language":"..."}"}
Parsed parameters: {question: "Write a function...", language: "javascript"}
Code editor opened successfully
```

### When User Submits Code:

```
Submitting code: {code: "function...", language: "javascript", explanation: "...", question: "..."}
Sending code to agent: participant-identity
Code submission response: "success"
```

## Common Issues & Solutions 🔧

### Issue: Code Editor Not Opening

**Symptoms**: AI asks coding question but modal doesn't appear

**Check**:

1. Browser console shows RPC registration logs
2. No JavaScript errors in console
3. Agent logs show RPC being sent

**Solution**:

- Refresh browser page
- Check participant connection status
- Verify both services are running

### Issue: AI Still Reading Question Aloud

**Symptoms**: AI says the full coding question verbally

**Check**:

- Agent instructions updated correctly
- `open_code_editor` function modified
- AI using correct tool

**Solution**: The fix has been applied to reduce verbal description

### Issue: Code Submission Not Working

**Symptoms**: User clicks submit but AI doesn't receive code

**Check**:

1. Browser console shows submission logs
2. Agent logs show RPC received
3. Network connectivity

**Solution**:

- Check RPC method registration
- Verify participant identities
- Increase timeout values

## Advanced Debugging 🛠️

### Backend Agent Logs

```bash
# Run with debug logging
LIVEKIT_LOG_LEVEL=debug python agent.py dev
```

### Frontend Network Tab

- Check for RPC calls in Network tab
- Look for WebSocket connections
- Verify payload contents

### Manual Test Commands

```bash
# Test agent syntax
python syntax_test.py

# Test RPC functionality
python debug_code_editor.py
```

## Expected Behavior ✨

1. **AI asks coding question**: Uses `open_code_editor` tool
2. **Code editor opens**: Modal appears with question in header
3. **User codes**: Monaco editor with syntax highlighting
4. **User submits**: Code sent via RPC to agent
5. **AI provides feedback**: Analyzes code and responds
6. **Modal closes**: Automatically after submission

## File Modifications Made 📝

### Backend (`feedback-v0-custom/`)

- `agent.py`: Fixed RPC registration, improved error handling
- `debug_code_editor.py`: New debugging script
- `CODE_EDITOR_TROUBLESHOOTING.md`: This guide

### Frontend (`feedback-v0-ui-custom/`)

- `app/page.tsx`: Added extensive logging for RPC debugging
- `components/CodeEditor.tsx`: Already properly implemented

## Success Indicators 🎯

✅ No TypeScript/Python errors  
✅ RPC methods register successfully  
✅ Code editor opens on AI command  
✅ Code submissions reach the agent  
✅ Interview flow continues smoothly

The code editor should now work correctly! If issues persist, check the browser console logs and agent logs for specific error messages.
