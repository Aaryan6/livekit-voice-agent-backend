#!/usr/bin/env python3
"""
Quick test to validate the code interpreter agent starts without errors.
This test checks imports and basic functionality.
"""

def test_agent_imports():
    """Test that the agent imports successfully"""
    try:
        from agent import (
            TechnicalQuestionsAgent, 
            InterviewSessionData, 
            IntroductionAgent,
            ProjectsAgent,
            HobbiesAgent,
            InterviewConclusionAgent
        )
        print("✅ All agent classes imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_session_data():
    """Test that InterviewSessionData works correctly"""
    try:
        from agent import InterviewSessionData
        from datetime import datetime
        
        session = InterviewSessionData(
            candidate_name="Test User",
            role="Software Engineer", 
            skill_level="mid",
            start_time=datetime.now().isoformat()
        )
        
        print(f"✅ Session data created: {session.candidate_name} ({session.role})")
        return True
    except Exception as e:
        print(f"❌ Session data error: {e}")
        return False

def test_technical_agent():
    """Test that TechnicalQuestionsAgent can be instantiated"""
    try:
        from agent import TechnicalQuestionsAgent
        
        agent = TechnicalQuestionsAgent()
        print("✅ TechnicalQuestionsAgent created successfully")
        
        # Check if the new tools exist
        tool_names = [tool.name for tool in agent.tools]
        
        if "open_code_editor" in tool_names:
            print("✅ open_code_editor tool found")
        else:
            print("❌ open_code_editor tool missing")
            return False
            
        if "analyze_submitted_code" in tool_names:
            print("✅ analyze_submitted_code tool found")
        else:
            print("❌ analyze_submitted_code tool missing")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Technical agent error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Quick Agent Validation Test")
    print("=" * 40)
    
    tests = [
        ("Agent Imports", test_agent_imports),
        ("Session Data", test_session_data), 
        ("Technical Agent", test_technical_agent)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}...")
        if test_func():
            passed += 1
        
    print(f"\n{'='*40}")
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Code interpreter is ready to use.")
        print("\n🚀 Next steps:")
        print("1. Start agent: python agent.py dev")
        print("2. Start frontend: cd ../feedback-v0-ui-custom && pnpm dev")
        print("3. Begin coding interviews!")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 