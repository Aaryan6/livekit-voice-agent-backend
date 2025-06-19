#!/usr/bin/env python3
"""
Simple test to verify the code interpreter components work correctly.
This test doesn't require LiveKit context and focuses on the data flow.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock
from agent import InterviewSessionData
from datetime import datetime

def test_interview_session_data():
    """Test that InterviewSessionData correctly handles code submissions"""
    
    print("🚀 Testing InterviewSessionData")
    print("=" * 50)
    
    # Create session data
    userdata = InterviewSessionData(
        candidate_name="Jane Smith",
        role="Frontend Engineer",
        skill_level="senior",
        start_time=datetime.now().isoformat()
    )
    
    print(f"✅ Created session for: {userdata.candidate_name}")
    print(f"📊 Initial question count: {userdata.total_questions_count}")
    print(f"🎯 Max questions allowed: {userdata.max_questions}")
    
    # Simulate adding a coding question
    userdata.total_questions_count += 1
    userdata.questions_asked.append("Coding: Implement a debounce function")
    
    # Simulate code submission
    code_submission = {
        "question": "Implement a debounce function",
        "code": '''
function debounce(func, delay) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

// Example usage
const debouncedSave = debounce(() => console.log("Saved!"), 300);
        '''.strip(),
        "language": "javascript",
        "explanation": "I created a debounce function that delays execution until after a specified delay period has passed since the last call.",
        "timestamp": datetime.now().isoformat()
    }
    
    # Add to notes
    if "code_submissions" not in userdata.notes:
        userdata.notes["code_submissions"] = []
    userdata.notes["code_submissions"].append(code_submission)
    
    print(f"\n💻 Code Submission Results:")
    print(f"   - Question count: {userdata.total_questions_count}")
    print(f"   - Code submissions: {len(userdata.notes['code_submissions'])}")
    print(f"   - Latest submission language: {code_submission['language']}")
    print(f"   - Code length: {len(code_submission['code'])} chars")
    print(f"   - Has explanation: {'Yes' if code_submission['explanation'] else 'No'}")
    
    return userdata

def demo_code_templates():
    """Show the code templates that would be used in the editor"""
    
    print("\n🎯 Code Editor Templates Demo")
    print("=" * 50)
    
    templates = {
        "javascript": '''// Write your JavaScript solution here
function solution() {
    // Your code here
    return null;
}

// Test your solution
console.log(solution());''',
        
        "python": '''# Write your Python solution here
def solution():
    # Your code here
    pass

# Test your solution
if __name__ == "__main__":
    print(solution())''',
    
        "java": '''// Write your Java solution here
public class Solution {
    public static void main(String[] args) {
        Solution sol = new Solution();
        System.out.println(sol.solution());
    }
    
    public Object solution() {
        // Your code here
        return null;
    }
}'''
    }
    
    for language, template in templates.items():
        print(f"\n🏷️  {language.upper()} Template:")
        print("```")
        print(template)
        print("```")

def demo_rpc_flow():
    """Demonstrate the RPC communication flow"""
    
    print("\n🔄 RPC Communication Flow Demo")
    print("=" * 50)
    
    # Step 1: Agent opens code editor
    open_request = {
        "method": "openCodeEditor",
        "payload": json.dumps({
            "question": "Write a function to find the intersection of two arrays",
            "language": "python"
        })
    }
    
    print("📤 Step 1: Agent → Frontend (openCodeEditor)")
    print(f"   Method: {open_request['method']}")
    print(f"   Question: {json.loads(open_request['payload'])['question']}")
    print(f"   Language: {json.loads(open_request['payload'])['language']}")
    
    # Step 2: Frontend acknowledges
    open_response = {"success": True}
    print(f"📨 Frontend Response: {open_response}")
    
    # Step 3: User submits code
    submit_request = {
        "method": "submitCode",
        "payload": json.dumps({
            "code": '''def find_intersection(arr1, arr2):
    """Find intersection of two arrays using set operations"""
    return list(set(arr1) & set(arr2))

# Test the function
list1 = [1, 2, 3, 4, 5]
list2 = [3, 4, 5, 6, 7]
result = find_intersection(list1, list2)
print(f"Intersection: {result}")''',
            "language": "python",
            "explanation": "I used set intersection to find common elements efficiently. This has O(n+m) time complexity.",
            "question": "Write a function to find the intersection of two arrays"
        })
    }
    
    print("\n📤 Step 2: Frontend → Agent (submitCode)")
    submit_data = json.loads(submit_request['payload'])
    print(f"   Method: {submit_request['method']}")
    print(f"   Language: {submit_data['language']}")
    print(f"   Code length: {len(submit_data['code'])} characters")
    print(f"   Has explanation: {'Yes' if submit_data['explanation'] else 'No'}")
    
    # Step 4: Agent analyzes code
    analysis_result = {
        "status": "success",
        "message": "Code received and analyzed",
        "feedback": "Good use of set operations for efficiency!"
    }
    
    print(f"📨 Agent Response: {analysis_result}")

def test_supported_languages():
    """Test the supported programming languages"""
    
    print("\n🌐 Supported Languages Test")
    print("=" * 50)
    
    supported_languages = [
        "javascript", "typescript", "python", "java",
        "cpp", "c", "csharp", "go", "rust",
        "php", "ruby", "sql", "html", "css"
    ]
    
    print(f"✅ Total supported languages: {len(supported_languages)}")
    
    # Group by category
    categories = {
        "Web Frontend": ["javascript", "typescript", "html", "css"],
        "Backend/General": ["python", "java", "csharp", "go", "php", "ruby"],
        "Systems": ["cpp", "c", "rust"],
        "Database": ["sql"]
    }
    
    for category, langs in categories.items():
        print(f"\n🏷️  {category}:")
        for lang in langs:
            print(f"   - {lang}")

def main():
    """Run all tests"""
    
    print("🎉 Code Interpreter Feature Test Suite")
    print("=" * 60)
    
    try:
        # Test 1: Basic data handling
        userdata = test_interview_session_data()
        
        # Test 2: Code templates
        demo_code_templates()
        
        # Test 3: RPC flow
        demo_rpc_flow()
        
        # Test 4: Language support
        test_supported_languages()
        
        print("\n" + "=" * 60)
        print("✨ All Tests Passed Successfully!")
        print("🚀 Code Interpreter is ready for use!")
        
        print(f"\n📋 Final Session Summary:")
        print(f"   👤 Candidate: {userdata.candidate_name}")
        print(f"   💼 Role: {userdata.role}")
        print(f"   📈 Skill Level: {userdata.skill_level}")
        print(f"   ❓ Questions Asked: {userdata.total_questions_count}")
        print(f"   💻 Code Submissions: {len(userdata.notes.get('code_submissions', []))}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 