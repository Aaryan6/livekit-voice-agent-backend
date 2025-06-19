#!/usr/bin/env python3
"""
Debug script for code editor RPC functionality
"""

import json

def test_rpc_payloads():
    """Test that RPC payloads are properly formatted"""
    print("🧪 Testing RPC Payload Formats")
    print("=" * 40)
    
    # Test openCodeEditor payload
    question = "Write a function to reverse a string"
    language = "javascript"
    
    open_payload = {
        "question": question,
        "language": language
    }
    
    try:
        open_json = json.dumps(open_payload)
        parsed = json.loads(open_json)
        print(f"✅ openCodeEditor payload: {open_json}")
        print(f"✅ Question: {parsed['question']}")
        print(f"✅ Language: {parsed['language']}")
    except Exception as e:
        print(f"❌ openCodeEditor payload error: {e}")
        return False
    
    # Test submitCode payload
    submit_payload = {
        "code": "function reverseString(str) { return str.split('').reverse().join(''); }",
        "language": "javascript", 
        "explanation": "Using built-in JavaScript methods",
        "question": question
    }
    
    try:
        submit_json = json.dumps(submit_payload)
        parsed = json.loads(submit_json)
        print(f"\n✅ submitCode payload created successfully")
        print(f"✅ Code length: {len(parsed['code'])} characters")
        print(f"✅ Language: {parsed['language']}")
        print(f"✅ Has explanation: {bool(parsed['explanation'])}")
    except Exception as e:
        print(f"❌ submitCode payload error: {e}")
        return False
    
    return True

def test_agent_tools():
    """Test that agent tools are properly defined"""
    print(f"\n🧪 Testing Agent Tools")
    print("=" * 40)
    
    try:
        from agent import TechnicalQuestionsAgent
        
        # Check if we can create an agent (without LiveKit context)
        print("✅ TechnicalQuestionsAgent import successful")
        
        # Check if the methods exist
        if hasattr(TechnicalQuestionsAgent, 'open_code_editor'):
            print("✅ open_code_editor method exists")
        else:
            print("❌ open_code_editor method missing")
            return False
            
        if hasattr(TechnicalQuestionsAgent, 'analyze_submitted_code'):
            print("✅ analyze_submitted_code method exists") 
        else:
            print("❌ analyze_submitted_code method missing")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Agent tools test failed: {e}")
        return False

def main():
    """Run debug tests"""
    print("🔧 Code Editor Debug Tests")
    print("=" * 50)
    
    tests = [
        ("RPC Payloads", test_rpc_payloads),
        ("Agent Tools", test_agent_tools)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - PASSED")
            else:
                print(f"❌ {test_name} - FAILED")
        except Exception as e:
            print(f"❌ {test_name} - ERROR: {e}")
    
    print(f"\n{'='*50}")
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All debug tests passed!")
        print("\n🔍 Debugging Tips:")
        print("1. Check browser console for RPC logs when testing")
        print("2. Look for 'Setting up RPC methods for code editor' message")
        print("3. When AI calls open_code_editor, you should see RPC logs")
        print("4. Make sure both frontend and backend are running")
        print("\n🚀 Ready to test live!")
    else:
        print(f"❌ {total - passed} test(s) failed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 