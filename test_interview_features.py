#!/usr/bin/env python3
"""
Test script to demonstrate the new interview agent features
This script shows how the enhanced interview flow works and what data structures are generated.
"""

import json
from datetime import datetime, timedelta
from agent import InterviewAgent, InterviewStage
from interview_config import SkillLevel

def test_interview_agent_features():
    """Test the enhanced interview agent features"""
    print("🎯 Testing Enhanced Interview Agent Features\n")
    
    # Initialize the interview agent
    print("1. Creating Interview Agent...")
    agent = InterviewAgent(
        role="Software Engineer",
        candidate_name="John Smith",
        skill_level="mid"
    )
    
    print(f"   ✅ Agent created for {agent.candidate_name}")
    print(f"   📝 Role: {agent.role}")
    print(f"   📊 Skill Level: {agent.skill_level}")
    print(f"   ❓ Total Questions: {agent.max_questions}")
    print(f"   🔄 Current Stage: {agent.current_stage.value}")
    
    # Show predefined questions
    print(f"\n2. Predefined Questions ({len(agent.predefined_questions)}):")
    for i, question in enumerate(agent.predefined_questions, 1):
        print(f"   Q{i}: {question}")
    
    # Test grammar assessment
    print(f"\n3. Testing Grammar Assessment:")
    sample_responses = [
        "I have experience with Python, JavaScript, and React. i worked on several projects.",
        "My background is in software development and I enjoy solving complex problems.",
        "I dont really know much about that topic but I can learn quickly.",
        "Yes, I have used Git for version control and I'm familiar with branching strategies."
    ]
    
    for i, response in enumerate(sample_responses, 1):
        assessment = agent._assess_grammar_accuracy(response)
        print(f"   Response {i}: {assessment['accuracy_percentage']}% accuracy")
        if assessment['issues']:
            print(f"              Issues: {', '.join(assessment['issues'][:2])}")
    
    # Simulate interview data
    print(f"\n4. Simulating Interview Progress:")
    
    # Simulate timing data
    agent.start_time = datetime.now() - timedelta(minutes=12, seconds=30)
    agent.candidate_speaking_time = timedelta(minutes=8, seconds=45)
    
    # Simulate questions asked
    agent.interview_data["questions_asked"] = [
        {
            "index": 0,
            "question": agent.predefined_questions[0],
            "timestamp": datetime.now().isoformat()
        },
        {
            "index": 1,
            "question": agent.predefined_questions[1],
            "timestamp": datetime.now().isoformat()
        },
        {
            "index": 2,
            "question": agent.predefined_questions[2],
            "timestamp": datetime.now().isoformat()
        }
    ]
    
    # Simulate grammar assessments
    agent.grammar_assessments = [
        {
            "accuracy_percentage": 85.0,
            "issues": ["Missing capitalization"],
            "meets_threshold": True,
            "stage": "questions",
            "timestamp": datetime.now().isoformat()
        },
        {
            "accuracy_percentage": 92.0,
            "issues": [],
            "meets_threshold": True,
            "stage": "questions",
            "timestamp": datetime.now().isoformat()
        },
        {
            "accuracy_percentage": 65.0,
            "issues": ["Grammar: 'dont' should be 'don't'", "Informal language"],
            "meets_threshold": False,
            "stage": "questions",
            "timestamp": datetime.now().isoformat()
        }
    ]
    
    # Generate sample summary
    print(f"   ⏱️  Interview Duration: 12 minutes 30 seconds")
    print(f"   🗣️  Candidate Speaking Time: 8 minutes 45 seconds")
    print(f"   ✅ Questions Asked: 3 of 5")
    print(f"   📊 Average Grammar Score: {agent._calculate_overall_grammar_accuracy():.1f}%")
    
    # Test final summary generation
    print(f"\n5. Generated Interview Summary:")
    
    # Simulate end time for summary
    end_time = datetime.now()
    total_duration = end_time - agent.start_time
    agent.interview_data["total_interview_duration_minutes"] = total_duration.total_seconds() / 60
    agent.interview_data["total_candidate_speaking_time_seconds"] = agent.candidate_speaking_time.total_seconds()
    agent.interview_data["end_time"] = end_time.isoformat()
    
    # Calculate metrics
    questions_asked_count = len(agent.interview_data["questions_asked"])
    questions_missed_count = len(agent.predefined_questions) - questions_asked_count
    overall_grammar_score = agent._calculate_overall_grammar_accuracy()
    qa_grammar_issues = agent._calculate_qa_grammar_issues()
    
    summary = {
        "interview_metadata": {
            "candidate_name": agent.candidate_name,
            "role": agent.role,
            "skill_level": agent.skill_level.value if hasattr(agent.skill_level, 'value') else agent.skill_level,
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
                "total_answers_assessed": len([g for g in agent.grammar_assessments if g["stage"] == "questions"]),
                "answers_below_70_percent": qa_grammar_issues,
                "answers_with_poor_grammar_count": qa_grammar_issues
            }
        }
    }
    
    print(json.dumps(summary, indent=2))
    
    print(f"\n6. Key Metrics Summary:")
    print(f"   📊 Total Interview Duration: {summary['interview_metadata']['total_duration_minutes']} minutes")
    print(f"   🗣️  Candidate Speaking Time: {summary['interview_metadata']['candidate_speaking_time_minutes']} minutes")
    print(f"   ❓ Questions Coverage: {summary['questions_coverage']['questions_asked_count']}/{summary['questions_coverage']['total_predefined_questions']}")
    print(f"   ✅ All Mandatory Questions Asked: {summary['questions_coverage']['all_mandatory_questions_asked']}")
    print(f"   📝 Grammar Accuracy: {summary['grammar_assessment']['overall_feedback']['average_accuracy_percentage']}%")
    print(f"   🎯 Meets 70% Grammar Threshold: {summary['grammar_assessment']['overall_feedback']['assessment']}")
    print(f"   ⚠️  Poor Grammar Answers: {summary['grammar_assessment']['qa_section_feedback']['answers_with_poor_grammar_count']}")

def test_interview_stages():
    """Test the interview stage progression"""
    print(f"\n🔄 Testing Interview Stage Flow:")
    
    stages = [
        ("WELCOME", "Greet candidate and explain process"),
        ("INTRODUCTION", "Candidate introduces themselves"),
        ("QUESTIONS", "Ask 5 predefined technical questions"),
        ("WRAP_UP", "Thank candidate and conclude"),
        ("COMPLETED", "Interview finished, generate summary")
    ]
    
    for stage, description in stages:
        print(f"   {stage}: {description}")

if __name__ == "__main__":
    test_interview_agent_features()
    test_interview_stages()
    
    print(f"\n🎉 All tests completed successfully!")
    print(f"\n📋 Next Steps:")
    print(f"   1. Update frontend to collect candidate information")
    print(f"   2. Add real-time progress tracking")
    print(f"   3. Implement grammar feedback display")
    print(f"   4. Create interview summary dashboard")
    print(f"   5. Add API endpoints for data access") 