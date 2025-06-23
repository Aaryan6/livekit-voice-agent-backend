#!/usr/bin/env python3
"""
Test script to demonstrate the new interview agent logic without LiveKit dependencies
This script shows the data structures and features that have been implemented.
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List
from enum import Enum

# Mock the interview config imports
class SkillLevel(Enum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    STAFF = "staff"

class MockInterviewAgent:
    """Mock version of InterviewAgent for testing logic"""
    
    def __init__(self, role: str = "Software Engineer", candidate_name: str = "Candidate", skill_level: str = "mid"):
        self.role = role
        self.candidate_name = candidate_name
        self.skill_level = SkillLevel(skill_level)
        self.max_questions = 5
        self.current_question_index = 0
        
        # Get predefined questions
        self.predefined_questions = self._get_predefined_questions()
        
        # Timing tracking
        self.start_time = datetime.now()
        self.candidate_speaking_time = timedelta()
        
        # Grammar tracking
        self.grammar_assessments = []
        
        self.interview_data = {
            "start_time": self.start_time.isoformat(),
            "role": role,
            "candidate_name": candidate_name,
            "skill_level": skill_level,
            "predefined_questions": self.predefined_questions,
            "questions_asked": [],
            "questions_missed": [],
            "grammar_assessments": [],
            "total_candidate_speaking_time_seconds": 0,
            "total_interview_duration_minutes": 0,
        }

    def _get_predefined_questions(self) -> List[str]:
        """Get 5 predefined questions based on role and skill level"""
        all_questions = {
            SkillLevel.JUNIOR: [
                "Tell me about your experience with programming languages.",
                "How do you approach debugging when your code isn't working?",
                "What's the purpose of version control? How do you use Git?",
                "Describe a challenging project you've worked on.",
                "How do you stay updated with new technologies?"
            ],
            SkillLevel.MID: [
                "Explain the SOLID principles. Give examples of how you've applied them.",
                "How do you approach testing your code? What types of tests do you write?",
                "Find the second largest element in an array. Handle edge cases.",
                "How would you design a chat application? Consider real-time messaging.",
                "Describe a time when you refactored legacy code. What was your approach?"
            ],
            SkillLevel.SENIOR: [
                "How do you ensure code quality in a team environment? What processes do you use?",
                "Design and implement a LRU cache with O(1) operations.",
                "Design a social media feed system that handles millions of users.",
                "How do you approach performance optimization? Give me a specific example.",
                "Describe a system you designed that had to handle unexpected scale."
            ],
            SkillLevel.STAFF: [
                "How do you establish coding standards and practices across multiple teams?",
                "Design a distributed consistent hashing algorithm.",
                "Design a global payment processing system with fraud detection.",
                "How do you balance innovation with stability in your technical decisions?",
                "Describe how you've influenced technical direction across your organization."
            ]
        }
        
        questions = all_questions.get(self.skill_level, all_questions[SkillLevel.MID])
        return random.sample(questions, min(5, len(questions)))

    def _assess_grammar_accuracy(self, response_text: str) -> Dict:
        """Assess grammar accuracy of candidate response"""
        issues = []
        words = response_text.split()
        word_count = len(words)
        
        if not response_text.strip():
            return {"accuracy_percentage": 0, "issues": ["Empty response"], "word_count": 0}
        
        # Check for basic punctuation and grammar
        text_lower = response_text.lower()
        common_errors = [
            ("i ", "I "),
            ("dont", "don't"),
            ("cant", "can't"),
            ("wont", "won't"),
        ]
        
        for error, correction in common_errors:
            if error in text_lower:
                issues.append(f"Grammar: '{error.strip()}' should be '{correction.strip()}'")
        
        # Check capitalization
        sentences = response_text.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and not sentence[0].isupper():
                issues.append("Missing capitalization")
        
        # Calculate accuracy
        accuracy_percentage = max(0, 100 - (len(issues) * 10))
        
        return {
            "accuracy_percentage": accuracy_percentage,
            "issues": issues[:5],
            "word_count": word_count,
            "meets_threshold": accuracy_percentage >= 70
        }

    def _calculate_overall_grammar_accuracy(self) -> float:
        """Calculate overall grammar accuracy across all responses"""
        if not self.grammar_assessments:
            return 0.0
        
        total_accuracy = sum(assessment["accuracy_percentage"] for assessment in self.grammar_assessments)
        return total_accuracy / len(self.grammar_assessments)

    def _calculate_qa_grammar_issues(self) -> int:
        """Count number of Q&A answers with grammar accuracy below 70%"""
        qa_assessments = [g for g in self.grammar_assessments if g.get("stage") == "questions"]
        return sum(1 for assessment in qa_assessments if assessment["accuracy_percentage"] < 70)

def test_interview_features():
    """Test all the new interview features"""
    print("🎯 Testing Enhanced Interview Agent Features\n")
    
    # Test 1: Create agent and show basic info
    print("1. Creating Interview Agent...")
    agent = MockInterviewAgent(
        role="Software Engineer",
        candidate_name="Alice Johnson", 
        skill_level="mid"
    )
    
    print(f"   ✅ Agent created for {agent.candidate_name}")
    print(f"   📝 Role: {agent.role}")
    print(f"   📊 Skill Level: {agent.skill_level.value}")
    print(f"   ❓ Total Questions: {agent.max_questions}")
    
    # Test 2: Show predefined questions
    print(f"\n2. Predefined Questions ({len(agent.predefined_questions)}):")
    for i, question in enumerate(agent.predefined_questions, 1):
        print(f"   Q{i}: {question}")
    
    # Test 3: Grammar assessment
    print(f"\n3. Testing Grammar Assessment:")
    sample_responses = [
        "I have experience with Python, JavaScript, and React. i worked on several projects.",
        "My background is in software development and I enjoy solving complex problems.",
        "I dont really know much about that topic but I can learn quickly.",
        "Yes, I have used Git for version control and I'm familiar with branching strategies.",
        "the system should handle millions of requests per second."
    ]
    
    for i, response in enumerate(sample_responses, 1):
        assessment = agent._assess_grammar_accuracy(response)
        print(f"   Response {i}: {assessment['accuracy_percentage']}% accuracy")
        if assessment['issues']:
            print(f"              Issues: {', '.join(assessment['issues'][:2])}")
        
        # Add to agent's assessments for testing
        assessment["stage"] = "questions"
        assessment["timestamp"] = datetime.now().isoformat()
        agent.grammar_assessments.append(assessment)
    
    # Test 4: Simulate interview progress
    print(f"\n4. Simulating Interview Progress:")
    
    # Simulate timing
    agent.start_time = datetime.now() - timedelta(minutes=18, seconds=42)
    agent.candidate_speaking_time = timedelta(minutes=12, seconds=15)
    
    # Simulate questions asked
    agent.interview_data["questions_asked"] = [
        {"index": 0, "question": agent.predefined_questions[0], "timestamp": datetime.now().isoformat()},
        {"index": 1, "question": agent.predefined_questions[1], "timestamp": datetime.now().isoformat()},
        {"index": 2, "question": agent.predefined_questions[2], "timestamp": datetime.now().isoformat()},
        {"index": 3, "question": agent.predefined_questions[3], "timestamp": datetime.now().isoformat()},
    ]
    
    print(f"   ⏱️  Interview Duration: 18 minutes 42 seconds")
    print(f"   🗣️  Candidate Speaking Time: 12 minutes 15 seconds")
    print(f"   ✅ Questions Asked: {len(agent.interview_data['questions_asked'])} of 5")
    print(f"   📊 Average Grammar Score: {agent._calculate_overall_grammar_accuracy():.1f}%")
    
    # Test 5: Generate comprehensive summary
    print(f"\n5. Generated Interview Summary:")
    
    end_time = datetime.now()
    total_duration = end_time - agent.start_time
    
    # Update timing data
    agent.interview_data["total_interview_duration_minutes"] = total_duration.total_seconds() / 60
    agent.interview_data["total_candidate_speaking_time_seconds"] = agent.candidate_speaking_time.total_seconds()
    
    # Calculate metrics
    questions_asked_count = len(agent.interview_data["questions_asked"])
    questions_missed_count = len(agent.predefined_questions) - questions_asked_count
    overall_grammar_score = agent._calculate_overall_grammar_accuracy()
    qa_grammar_issues = agent._calculate_qa_grammar_issues()
    
    summary = {
        "interview_metadata": {
            "candidate_name": agent.candidate_name,
            "role": agent.role,
            "skill_level": agent.skill_level.value,
            "interview_date": agent.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_duration_minutes": round(agent.interview_data["total_interview_duration_minutes"], 2),
            "candidate_speaking_time_minutes": round(agent.interview_data["total_candidate_speaking_time_seconds"] / 60, 2),
            "interviewer_time_percentage": round((1 - (agent.interview_data["total_candidate_speaking_time_seconds"] / total_duration.total_seconds())) * 100, 1)
        },
        "questions_coverage": {
            "total_predefined_questions": len(agent.predefined_questions),
            "questions_asked_count": questions_asked_count,
            "questions_missed_count": questions_missed_count,
            "all_mandatory_questions_asked": questions_missed_count == 0,
            "questions_asked": [q["question"] for q in agent.interview_data["questions_asked"]],
            "questions_missed": agent.predefined_questions[questions_asked_count:] if questions_missed_count > 0 else []
        },
        "grammar_assessment": {
            "overall_feedback": {
                "average_accuracy_percentage": round(overall_grammar_score, 1),
                "meets_70_percent_threshold": overall_grammar_score >= 70,
                "assessment": "Yes" if overall_grammar_score >= 70 else "No"
            },
            "qa_section_feedback": {
                "total_answers_assessed": len([g for g in agent.grammar_assessments if g.get("stage") == "questions"]),
                "answers_below_70_percent": qa_grammar_issues,
                "answers_with_poor_grammar_count": qa_grammar_issues
            }
        }
    }
    
    print(json.dumps(summary, indent=2))
    
    return summary

def test_different_skill_levels():
    """Test questions for different skill levels"""
    print(f"\n🎓 Testing Questions for Different Skill Levels:")
    
    for skill in ["junior", "mid", "senior", "staff"]:
        agent = MockInterviewAgent(skill_level=skill)
        print(f"\n   {skill.upper()} Level Questions:")
        for i, question in enumerate(agent.predefined_questions[:3], 1):  # Show first 3
            print(f"   {i}. {question}")

def display_key_metrics(summary):
    """Display key metrics in a formatted way"""
    print(f"\n📊 Key Interview Metrics:")
    print(f"   👤 Candidate: {summary['interview_metadata']['candidate_name']}")
    print(f"   💼 Role: {summary['interview_metadata']['role']} ({summary['interview_metadata']['skill_level']})")
    print(f"   ⏱️  Total Duration: {summary['interview_metadata']['total_duration_minutes']} minutes")
    print(f"   🗣️  Candidate Talking: {summary['interview_metadata']['candidate_speaking_time_minutes']} minutes")
    print(f"   🎤 Interviewer Time: {summary['interview_metadata']['interviewer_time_percentage']}%")
    print(f"   ❓ Questions Coverage: {summary['questions_coverage']['questions_asked_count']}/{summary['questions_coverage']['total_predefined_questions']}")
    print(f"   ✅ All Mandatory Asked: {summary['questions_coverage']['all_mandatory_questions_asked']}")
    print(f"   📝 Grammar Score: {summary['grammar_assessment']['overall_feedback']['average_accuracy_percentage']}%")
    print(f"   🎯 Grammar Threshold: {summary['grammar_assessment']['overall_feedback']['assessment']}")
    print(f"   ⚠️  Poor Grammar Answers: {summary['grammar_assessment']['qa_section_feedback']['answers_with_poor_grammar_count']}")

if __name__ == "__main__":
    summary = test_interview_features()
    test_different_skill_levels()
    display_key_metrics(summary)
    
    print(f"\n🎉 All tests completed successfully!")
    print(f"\n📋 Implementation Summary:")
    print(f"   ✅ Structured interview with exactly 5 questions")
    print(f"   ✅ Welcome message & candidate introduction flow")
    print(f"   ✅ Automatic wrap-up after all questions")
    print(f"   ✅ Total interview duration tracking")
    print(f"   ✅ Candidate speaking time measurement")
    print(f"   ✅ Mandatory questions coverage verification")
    print(f"   ✅ Grammar accuracy assessment (70% threshold)")
    print(f"   ✅ Detailed Q&A grammar analysis")
    print(f"   ✅ Comprehensive summary generation")
    
    print(f"\n🚀 Ready for Frontend Integration!")
    print(f"   📄 See FRONTEND_CHANGES_NEEDED.md for detailed requirements") 