# Code Interpreter Usage Example

## Quick Start Guide

### 1. Frontend Setup

Install the required dependencies:

```bash
cd feedback-v0-ui-custom
pnpm install @monaco-editor/react @radix-ui/react-dialog
```

### 2. Backend Setup

The backend tools are already integrated into the `TechnicalQuestionsAgent`. No additional setup required.

### 3. Running the System

**Start the Backend:**

```bash
cd feedback-v0-custom
python agent.py
```

**Start the Frontend:**

```bash
cd feedback-v0-ui-custom
pnpm dev
```

## How to Use in Interviews

### Example Interview Flow

Here's a complete example of how the code interpreter works in practice:

#### 1. AI Agent Asks a Coding Question

```
AI: "Now I'd like to test your coding skills. I'm going to open a code editor for you where you can write a solution to this problem: Write a function that finds the two numbers in an array that add up to a target sum."
```

**Behind the scenes:**

- Agent calls `open_code_editor(question="Write a function that finds two numbers...", language="python")`
- RPC call sent to frontend: `openCodeEditor`
- Code editor modal opens with Python template

#### 2. Candidate Writes Code

The candidate sees a Monaco Editor with this template:

```python
# Write your Python solution here
def solution():
    # Your code here
    pass

# Test your solution
if __name__ == "__main__":
    print(solution())
```

The candidate writes their solution:

```python
def two_sum(nums, target):
    """
    Find two numbers in array that add up to target sum.
    Returns indices of the two numbers.
    """
    num_to_index = {}

    for i, num in enumerate(nums):
        complement = target - num
        if complement in num_to_index:
            return [num_to_index[complement], i]
        num_to_index[num] = i

    return []  # No solution found

# Test the function
test_array = [2, 7, 11, 15]
target_sum = 9
result = two_sum(test_array, target_sum)
print(f"Indices: {result}")  # Should print [0, 1]
```

#### 3. Candidate Adds Explanation

In the explanation field:

```
I used a hash map approach to solve this in O(n) time complexity. For each number, I check if its complement (target - current number) exists in the hash map. If it does, I've found the pair. If not, I store the current number and its index for future lookups.
```

#### 4. Code Submission and Analysis

When the candidate clicks "Submit Code":

- Frontend sends RPC: `submitCode` with code, language, and explanation
- Backend calls `analyze_submitted_code()`
- AI provides immediate feedback:

```
AI: "Excellent! I can see you've implemented an efficient O(n) solution using a hash map. Your explanation clearly shows you understand the time complexity trade-off. The code is clean and well-commented. Let me ask you a follow-up: How would you modify this if the array could contain duplicate numbers?"
```

## Sample Coding Questions by Role

### Frontend Engineer

**Junior Level:**

```python
# Agent usage
await agent.open_code_editor(
    context,
    question="Write a function to toggle a CSS class on an element",
    language="javascript"
)
```

**Mid Level:**

```python
await agent.open_code_editor(
    context,
    question="Implement a simple debounce function for search input",
    language="javascript"
)
```

**Senior Level:**

```python
await agent.open_code_editor(
    context,
    question="Create a React hook for managing async API calls with loading states",
    language="typescript"
)
```

### Backend Engineer

**Junior Level:**

```python
await agent.open_code_editor(
    context,
    question="Write a function to validate an email address",
    language="python"
)
```

**Mid Level:**

```python
await agent.open_code_editor(
    context,
    question="Implement a simple caching mechanism with TTL support",
    language="python"
)
```

**Senior Level:**

```python
await agent.open_code_editor(
    context,
    question="Design a rate limiting algorithm using sliding window",
    language="python"
)
```

### Full Stack Engineer

**Data Structures:**

```python
await agent.open_code_editor(
    context,
    question="Implement a LRU cache with O(1) operations",
    language="java"
)
```

**System Design (Code):**

```python
await agent.open_code_editor(
    context,
    question="Write a simple URL shortener service core logic",
    language="python"
)
```

## Advanced Usage Patterns

### 1. Language-Specific Questions

```python
# For a Python role
await agent.open_code_editor(
    context,
    question="Write a decorator that measures function execution time",
    language="python"
)

# For a JavaScript role
await agent.open_code_editor(
    context,
    question="Implement Promise.all from scratch",
    language="javascript"
)

# For a systems role
await agent.open_code_editor(
    context,
    question="Write a memory-efficient string reversal function",
    language="cpp"
)
```

### 2. Progressive Difficulty

```python
# Start simple
await agent.ask_technical_question(
    context,
    question="Explain the difference between let, const, and var in JavaScript",
    competency="JavaScript Fundamentals"
)

# Then add coding
await agent.open_code_editor(
    context,
    question="Now implement a function that demonstrates closure in JavaScript",
    language="javascript"
)

# Follow up based on their solution
# Agent can see their code in context.userdata.notes["code_submissions"]
```

### 3. Multi-Part Problems

```python
# Part 1: Basic implementation
await agent.open_code_editor(
    context,
    question="Implement a basic stack data structure",
    language="python"
)

# After code submission, extend the problem
await agent.say("Great! Now let's extend this...")
await agent.open_code_editor(
    context,
    question="Add a min() method that returns the minimum element in O(1) time",
    language="python"
)
```

## Best Practices for Interviewers

### 1. Question Selection

- **Match skill level**: Junior gets basic problems, senior gets design challenges
- **Consider role**: Frontend focuses on DOM/React, backend on algorithms/systems
- **Time management**: 1-2 coding questions per interview max

### 2. Providing Good Problems

```python
# ✅ Good: Clear, specific, testable
await agent.open_code_editor(
    context,
    question="Write a function that takes an array of integers and returns the most frequent element. If there's a tie, return the first one encountered.",
    language="python"
)

# ❌ Avoid: Vague, too broad
await agent.open_code_editor(
    context,
    question="Write some code to process data",
    language="python"
)
```

### 3. Follow-up Questions

After code submission, the agent can ask:

- "How would you test this function?"
- "What's the time complexity?"
- "How would you handle edge cases like empty arrays?"
- "How would this scale with larger datasets?"

## Troubleshooting Common Issues

### Frontend Issues

**Code editor doesn't open:**

```javascript
// Check if RPC method is registered
console.log("Registering RPC method...");
room.localParticipant.registerRpcMethod("openCodeEditor", openCodeEditor);
```

**Code submission fails:**

```javascript
// Add error handling
try {
  await room.localParticipant.performRpc({
    destinationIdentity: agentParticipant.identity,
    method: "submitCode",
    payload: JSON.stringify({ code, language, explanation }),
    responseTimeout: 10000,
  });
} catch (error) {
  console.error("Failed to submit code:", error);
  // Show user-friendly error message
}
```

### Backend Issues

**Agent not receiving code:**

```python
# Check if RPC handler is registered
print("Registering submitCode RPC handler...")
await ctx.room.local_participant.register_rpc_method("submitCode", handle_code_submission)
```

**Tool not being called:**

```python
# Verify agent instructions mention the tool
instructions = """
...
Use open_code_editor for coding problems like: algorithm implementation, data structures
Choose appropriate language: "javascript", "python", "java", "cpp", etc.
...
"""
```

## Integration with Existing Interview Flow

The code interpreter seamlessly integrates with the existing interview stages:

1. **Introduction** → Get to know candidate
2. **Projects** → Discuss past work
3. **Technical Questions** → Mix of theory + coding
   - Use `ask_technical_question()` for concepts
   - Use `open_code_editor()` for implementation
4. **Hobbies** → Personal interests
5. **Conclusion** → Wrap up

## Data Collection and Analysis

All code submissions are automatically stored in the interview session:

```python
# Access submitted code later
for submission in userdata.notes["code_submissions"]:
    print(f"Question: {submission['question']}")
    print(f"Language: {submission['language']}")
    print(f"Code: {submission['code']}")
    print(f"Explanation: {submission['explanation']}")
    print(f"Timestamp: {submission['timestamp']}")
```

This enables:

- Post-interview code review
- Candidate skill assessment
- Interview quality metrics
- Training data for AI improvements

---

**Ready to start coding interviews with AI assistance!** 🚀
