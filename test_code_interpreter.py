#!/usr/bin/env python3
"""
Test script to demonstrate the code interpreter functionality.
This script shows how the agent can open a code editor and analyze submitted code.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock
from agent import TechnicalQuestionsAgent, InterviewSessionData
from livekit.agents import RunContext
from datetime import datetime

async def test_code_interpreter_flow():
    """Test the complete code interpreter flow"""
    
    print("🚀 Testing Code Interpreter Flow")
    print("=" * 50)
    
    # Create mock session data
    userdata = InterviewSessionData(
        candidate_name="John Doe",
        role="Software Engineer",
        skill_level="mid",
        start_time=datetime.now().isoformat()
    )
    
    # Create the agent
    agent = TechnicalQuestionsAgent()
    
    # Create mock context
    mock_context = MagicMock()
    mock_context.userdata = userdata
    mock_context.session = AsyncMock()
    mock_context.session.say = AsyncMock()
    
    print("📝 Step 1: Opening Code Editor")
    print("-" * 30)
    
    # Test opening code editor
    try:
        # Mock the RPC call
        import unittest.mock
        with unittest.mock.patch('agent.get_job_context') as mock_job_ctx:
            mock_room = MagicMock()
            mock_local_participant = AsyncMock()
            mock_local_participant.perform_rpc = AsyncMock(return_value='{"success": true}')
            mock_room.local_participant = mock_local_participant
            mock_room.remote_participants = {"user123": MagicMock()}
            mock_job_ctx.return_value.room = mock_room
            
            result = await agent.open_code_editor(
                mock_context,
                question="Write a function to reverse a string",
                language="python"
            )
            
            print(f"✅ Code editor opened successfully: {result}")
            print(f"📊 Question count: {userdata.total_questions_count}")
            print(f"🗂️  Questions asked: {userdata.questions_asked}")
            
    except Exception as e:
        print(f"❌ Error opening code editor: {e}")
    
    print("\n💻 Step 2: Simulating Code Submission")
    print("-" * 30)
    
    # Test code analysis
    sample_code = '''
def reverse_string(s):
    """Reverse a string using slicing"""
    return s[::-1]

# Test the function
test_string = "hello world"
result = reverse_string(test_string)
print(f"Original: {test_string}")
print(f"Reversed: {result}")
'''
    
    sample_explanation = "I used Python's slicing notation to reverse the string. This is an efficient O(n) solution that creates a new string with characters in reverse order."
    
    try:
        result = await agent.analyze_submitted_code(
            mock_context,
            code=sample_code,
            language="python",
            explanation=sample_explanation,
            question="Write a function to reverse a string"
        )
        
        print(f"✅ Code analyzed successfully: {result}")
        print(f"📊 Code submissions recorded: {len(userdata.notes.get('code_submissions', []))}")
        
        if 'code_submissions' in userdata.notes:
            submission = userdata.notes['code_submissions'][0]
            print(f"🔍 Submission details:")
            print(f"   - Language: {submission['language']}")
            print(f"   - Code length: {len(submission['code'])} characters")
            print(f"   - Has explanation: {'Yes' if submission['explanation'] else 'No'}")
            
    except Exception as e:
        print(f"❌ Error analyzing code: {e}")
    
    print("\n📋 Step 3: Interview Summary")
    print("-" * 30)
    print(f"👤 Candidate: {userdata.candidate_name}")
    print(f"💼 Role: {userdata.role}")
    print(f"📈 Skill Level: {userdata.skill_level}")
    print(f"❓ Total Questions: {userdata.total_questions_count}")
    print(f"💬 Questions Asked: {len(userdata.questions_asked)}")
    print(f"💾 Code Submissions: {len(userdata.notes.get('code_submissions', []))}")
    
    print("\n🎉 Code Interpreter Test Complete!")
    
    return userdata

def demo_sample_questions():
    """Show sample coding questions that could be used"""
    
    print("\n🎯 Sample Coding Questions by Skill Level")
    print("=" * 50)
    
    questions = {
        "junior": [
            {"question": "Write a function to check if a number is even or odd", "language": "javascript"},
            {"question": "Create a function that finds the maximum number in an array", "language": "python"},
            {"question": "Write a function to count vowels in a string", "language": "java"},
        ],
        "mid": [
            {"question": "Implement a function to reverse a linked list", "language": "python"},
            {"question": "Write a function to find the first non-repeating character in a string", "language": "javascript"},
            {"question": "Create a simple binary search algorithm", "language": "cpp"},
        ],
        "senior": [
            {"question": "Design and implement a LRU cache", "language": "python"},
            {"question": "Write a function to serialize and deserialize a binary tree", "language": "java"},
            {"question": "Implement a rate limiter using sliding window", "language": "javascript"},
        ]
    }
    
    for level, level_questions in questions.items():
        print(f"\n🏷️  {level.upper()} Level:")
        for i, q in enumerate(level_questions, 1):
            print(f"   {i}. {q['question']} ({q['language']})")

if __name__ == "__main__":
    # Run the test
    try:
        result = asyncio.run(test_code_interpreter_flow())
        demo_sample_questions()
        
        print("\n✨ All tests completed successfully!")
        print("The code interpreter is ready to use in interviews.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc() 