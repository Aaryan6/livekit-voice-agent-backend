import logging
import json
import os
import aiohttp
import re
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import random

from dotenv import load_dotenv
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.agents import (
    Agent,
    AgentSession,
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    metrics,
    RoomInputOptions,
)
from livekit.plugins import (
    openai,
    noise_cancellation,
    silero,
    groq,
    deepgram
)

# Import our interview configuration
try:
    from interview_config import (
        ROLE_TEMPLATES, 
        SCORING_RUBRIC, 
        SkillLevel,
        get_questions_for_role_and_level,
        get_evaluation_criteria
    )
except ImportError:
    # Fallback if config file doesn't exist
    ROLE_TEMPLATES = {}
    SCORING_RUBRIC = {}
    SkillLevel = None

load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("interview-agent")


class InterviewStage(Enum):
    WELCOME = "welcome"
    INTRODUCTION = "introduction"
    QUESTIONS = "questions"
    WRAP_UP = "wrap_up"
    COMPLETED = "completed"


class InterviewAgent(Agent):
    def __init__(self, 
                 role: str = "Software Engineer", 
                 candidate_name: str = "Candidate",
                 skill_level: str = "mid") -> None:
        super().__init__(
            instructions=get_interview_instructions(role, candidate_name, skill_level),
            stt=deepgram.STT(model="nova-2-meeting"),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=openai.TTS(voice="alloy"),
            turn_detection=MultilingualModel(),
        )
        self.role = role
        self.candidate_name = candidate_name
        self.skill_level = SkillLevel(skill_level) if SkillLevel else skill_level
        self.current_stage = InterviewStage.WELCOME
        self.current_question_index = 0
        self.max_questions = 5
        
        # Get predefined questions for this role and skill level
        self.predefined_questions = self._get_predefined_questions()
        self.mandatory_questions = self.predefined_questions.copy()  # All are mandatory
        
        # Timing tracking
        self.start_time = datetime.now()
        self.stage_start_time = datetime.now()
        self.candidate_speaking_time = timedelta()
        self.last_candidate_start = None
        
        # Grammar tracking
        self.candidate_responses = []
        self.grammar_assessments = []
        
        self.interview_data = {
            "start_time": self.start_time.isoformat(),
            "role": role,
            "candidate_name": candidate_name,
            "skill_level": skill_level,
            "predefined_questions": self.predefined_questions,
            "questions_asked": [],
            "questions_missed": [],
            "candidate_responses": [],
            "grammar_assessments": [],
            "stage_timings": {},
            "total_candidate_speaking_time_seconds": 0,
            "total_interview_duration_minutes": 0,
            "current_stage": self.current_stage.value
        }

    def _get_predefined_questions(self) -> List[str]:
        """Get exactly 5 predefined questions for the role and skill level"""
        if self.role not in ROLE_TEMPLATES or not SkillLevel:
            # Fallback questions if config not available
            return [
                "Tell me about your experience with programming languages.",
                "Describe a challenging project you've worked on.",
                "How do you approach debugging complex issues?",
                "What's your experience with version control systems?",
                "How do you stay updated with new technologies?"
            ]
        
        template = ROLE_TEMPLATES[self.role]
        all_questions = []
        
        # Collect questions from all competencies for the skill level
        for competency in template.competencies:
            competency_questions = competency.questions.get(self.skill_level, [])
            all_questions.extend(competency_questions)
        
        # Select exactly 5 questions, prioritizing diverse competencies
        if len(all_questions) <= 5:
            return all_questions
        else:
            # Randomly select 5 questions to ensure variety
            return random.sample(all_questions, 5)

    def _assess_grammar_accuracy(self, response_text: str) -> Dict:
        """Assess grammar accuracy of candidate response"""
        # Basic grammar assessment using simple heuristics
        # In production, this could use an NLP service like Grammarly API
        
        # Count basic grammar issues
        issues = []
        words = response_text.split()
        word_count = len(words)
        
        # Basic checks
        if not response_text.strip():
            return {"accuracy_percentage": 0, "issues": ["Empty response"], "word_count": 0}
        
        # Check for basic punctuation
        sentences = response_text.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and not sentence[0].isupper():
                issues.append("Missing capitalization")
        
        # Check for common grammar patterns
        text_lower = response_text.lower()
        common_errors = [
            ("i ", "I "),  # Lowercase 'i'
            ("dont", "don't"),
            ("cant", "can't"),
            ("wont", "won't"),
            ("its ", "it's " if "it is" in text_lower else "its "),
        ]
        
        for error, correction in common_errors:
            if error in text_lower:
                issues.append(f"Grammar: '{error.strip()}' should be '{correction.strip()}'")
        
        # Calculate accuracy (simplified approach)
        accuracy_percentage = max(0, 100 - (len(issues) * 10))  # Each issue reduces by 10%
        
        assessment = {
            "accuracy_percentage": accuracy_percentage,
            "issues": issues[:5],  # Limit to 5 issues for brevity
            "word_count": word_count,
            "meets_threshold": accuracy_percentage >= 70
        }
        
        return assessment

    def _update_candidate_speaking_time(self, start_time: datetime, end_time: datetime):
        """Update the total time candidate has been speaking"""
        duration = end_time - start_time
        self.candidate_speaking_time += duration
        self.interview_data["total_candidate_speaking_time_seconds"] = self.candidate_speaking_time.total_seconds()

    def _log_stage_timing(self, stage: str):
        """Log timing for stage transitions"""
        now = datetime.now()
        if hasattr(self, 'stage_start_time'):
            duration = now - self.stage_start_time
            self.interview_data["stage_timings"][stage] = {
                "start_time": self.stage_start_time.isoformat(),
                "end_time": now.isoformat(),
                "duration_seconds": duration.total_seconds()
            }
        self.stage_start_time = now

    async def on_enter(self):
        """Start the interview with welcome message"""
        self.current_stage = InterviewStage.WELCOME
        self._log_stage_timing("welcome")
        
        welcome_message = f"""Hello {self.candidate_name}! Welcome to your interview for the {self.role} position. 

I'm excited to speak with you today. Please feel free to take your time with your answers and ask for clarification if needed.

Let's begin! Could you please introduce yourself and tell me about your background?"""

        await self.session.say(welcome_message, allow_interruptions=True)
        self.current_stage = InterviewStage.INTRODUCTION
        await self._send_progress_update()

    async def on_user_speech_committed(self, msg):
        """Handle candidate responses and track timing/grammar"""
        now = datetime.now()
        
        # Track candidate speaking time
        if self.last_candidate_start:
            self._update_candidate_speaking_time(self.last_candidate_start, now)
        
        response_text = msg.transcript.strip()
        if not response_text:
            return
        
        # Store the response
        self.candidate_responses.append({
            "timestamp": now.isoformat(),
            "stage": self.current_stage.value,
            "question_index": self.current_question_index if self.current_stage == InterviewStage.QUESTIONS else None,
            "response": response_text
        })
        
        # Assess grammar if it's a substantial response (more than 5 words)
        if len(response_text.split()) > 5:
            grammar_assessment = self._assess_grammar_accuracy(response_text)
            grammar_assessment["timestamp"] = now.isoformat()
            grammar_assessment["stage"] = self.current_stage.value
            grammar_assessment["response_text"] = response_text
            self.grammar_assessments.append(grammar_assessment)
            self.interview_data["grammar_assessments"] = self.grammar_assessments
        
        # Handle automatic stage progression
        await self._handle_stage_progression(response_text)

    async def on_user_started_speaking(self):
        """Track when candidate starts speaking"""
        self.last_candidate_start = datetime.now()

    async def on_session_disconnected(self):
        """Handle session disconnect and generate final summary"""
        logger.info(f"Session disconnected - current stage: {self.current_stage.value}")
        if self.current_stage != InterviewStage.COMPLETED:
            logger.info("Session disconnected, generating final summary...")
            await self.generate_final_summary()
            self.current_stage = InterviewStage.COMPLETED
        else:
            logger.info("Session disconnected but interview already completed")

    async def on_participant_disconnected(self, participant):
        """Handle participant disconnect and generate final summary"""
        logger.info(f"Participant {participant.identity} disconnected - current stage: {self.current_stage.value}")
        if self.current_stage != InterviewStage.COMPLETED:
            logger.info(f"Participant {participant.identity} disconnected, generating final summary...")
            await self.generate_final_summary()
            self.current_stage = InterviewStage.COMPLETED
        else:
            logger.info("Participant disconnected but interview already completed")

    async def on_shutdown(self):
        """Handle agent shutdown and generate final summary"""
        if self.current_stage != InterviewStage.COMPLETED:
            logger.info("Agent shutting down, generating final summary...")
            await self.generate_final_summary()
            self.current_stage = InterviewStage.COMPLETED

    async def _send_progress_update(self):
        """Send progress update to frontend"""
        try:
            progress_data = {
                "type": "progress_update",
                "current_stage": self.current_stage.value,
                "questions_asked": len(self.interview_data["questions_asked"]),
                "total_questions": self.max_questions,
                "current_question_index": self.current_question_index,
                "elapsed_time": int((datetime.now() - self.start_time).total_seconds()),
                "candidate_speaking_time": int(self.candidate_speaking_time.total_seconds())
            }
            
            # Send data to frontend via room data channel
            await self.session.room.local_participant.publish_data(
                json.dumps(progress_data).encode("utf-8"),
                reliable=True
            )
            logger.info(f"Sent progress update: {progress_data}")
        except Exception as e:
            logger.error(f"Failed to send progress update: {e}")

    async def _handle_stage_progression(self, response_text: str):
        """Handle automatic progression through interview stages"""
        # Don't interrupt if agent is currently speaking
        if self.session.agent_is_speaking:
            return
            
        # Introduction stage: after candidate introduces themselves, start questions
        if self.current_stage == InterviewStage.INTRODUCTION:
            # Look for introduction keywords or substantial response
            if len(response_text.split()) > 10:  # Substantial introduction
                # Wait a moment then transition to questions
                await asyncio.sleep(2)
                await self.session.say(
                    "Thank you for that introduction! Now I'd like to ask you some specific technical questions.",
                    allow_interruptions=True
                )
                await asyncio.sleep(1)
                await self._ask_next_question()
        
        # Questions stage: after each answer, ask next question
        elif self.current_stage == InterviewStage.QUESTIONS:
            # Check if this was a response to a question
            if len(response_text.split()) > 3:  # Substantial answer
                await asyncio.sleep(1.5)  # Brief pause
                await self._ask_next_question()

    async def _ask_next_question(self):
        """Ask the next predefined question"""
        if self.current_question_index >= len(self.predefined_questions):
            await self._wrap_up_interview()
            return
        
        if self.current_stage != InterviewStage.QUESTIONS:
            self.current_stage = InterviewStage.QUESTIONS
            self._log_stage_timing("questions")
            await self._send_progress_update()
        
        question = self.predefined_questions[self.current_question_index]
        
        # Log the question as asked
        self.interview_data["questions_asked"].append({
            "index": self.current_question_index,
            "question": question,
            "timestamp": datetime.now().isoformat()
        })
        
        # Varied ways to introduce questions naturally
        question_intros = [
            f"Great! {question}",
            f"Perfect. {question}",
            f"Thank you for that. {question}",
            f"Excellent. Now, {question}",
            f"That's good. {question}"
        ]
        
        # Use different intro based on question index to sound natural
        intro_index = self.current_question_index % len(question_intros)
        question_intro = question_intros[intro_index]
        
        await self.session.say(question_intro, allow_interruptions=True)
        self.current_question_index += 1
        await self._send_progress_update()

    async def _wrap_up_interview(self):
        """Wrap up the interview and generate summary"""
        self.current_stage = InterviewStage.WRAP_UP
        self._log_stage_timing("wrap_up")
        await self._send_progress_update()
        
        wrap_up_message = f"""Thank you {self.candidate_name}, that completes our technical discussion. 

Do you have any questions about the role, the team, or our company that I can answer for you?

We'll review your responses and follow up with next steps within a few business days. Thank you for your time today!"""

        await self.session.say(wrap_up_message, allow_interruptions=True)
        
        # Generate final summary
        await self.generate_final_summary()
        self.current_stage = InterviewStage.COMPLETED
        await self._send_progress_update()

    async def generate_final_summary(self):
        """Generate comprehensive interview summary"""
        logger.info("Starting generation of final interview summary...")
        end_time = datetime.now()
        total_duration = end_time - self.start_time
        
        # Update final timing data
        self.interview_data["total_interview_duration_minutes"] = total_duration.total_seconds() / 60
        self.interview_data["end_time"] = end_time.isoformat()
        
        # Calculate mandatory questions coverage
        questions_asked_count = len(self.interview_data["questions_asked"])
        questions_missed_count = len(self.predefined_questions) - questions_asked_count
        self.interview_data["questions_missed"] = self.predefined_questions[questions_asked_count:] if questions_missed_count > 0 else []
        
        # Calculate grammar accuracy metrics
        overall_grammar_score = self._calculate_overall_grammar_accuracy()
        qa_grammar_issues = self._calculate_qa_grammar_issues()
        
        # Generate comprehensive summary
        summary = {
            "interview_metadata": {
                "candidate_name": self.candidate_name,
                "role": self.role,
                "skill_level": self.skill_level.value if hasattr(self.skill_level, 'value') else self.skill_level,
                "interview_date": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_duration_minutes": round(self.interview_data["total_interview_duration_minutes"], 2),
                "candidate_speaking_time_minutes": round(self.interview_data["total_candidate_speaking_time_seconds"] / 60, 2),
                "interviewer_time_percentage": round((1 - (self.interview_data["total_candidate_speaking_time_seconds"] / total_duration.total_seconds())) * 100, 1)
            },
            
            "questions_coverage": {
                "total_predefined_questions": len(self.predefined_questions),
                "questions_asked_count": questions_asked_count,
                "questions_missed_count": questions_missed_count,
                "all_mandatory_questions_asked": questions_missed_count == 0,
                "questions_asked": [q["question"] for q in self.interview_data["questions_asked"]],
                "questions_missed": self.interview_data["questions_missed"]
            },
            
            "grammar_assessment": {
                "overall_feedback": {
                    "average_accuracy_percentage": round(overall_grammar_score, 1),
                    "meets_70_percent_threshold": overall_grammar_score >= 70,
                    "assessment": "Yes" if overall_grammar_score >= 70 else "No"
                },
                "qa_section_feedback": {
                    "total_answers_assessed": len([g for g in self.grammar_assessments if g["stage"] == "questions"]),
                    "answers_below_70_percent": qa_grammar_issues,
                    "answers_with_poor_grammar_count": qa_grammar_issues
                }
            },
            
            "stage_timings": self.interview_data["stage_timings"],
            "detailed_responses": self.candidate_responses,
            "detailed_grammar_assessments": self.grammar_assessments
        }
        
        # Log the comprehensive summary
        logger.info("=== INTERVIEW SUMMARY ===")
        logger.info(json.dumps(summary, indent=2))
        
        # Store in interview_data for potential API access
        self.interview_data["final_summary"] = summary
        
        # Send summary to frontend
        await self._send_summary_to_frontend(summary)
        
        return summary

    async def _send_summary_to_frontend(self, summary):
        """Send final summary to frontend"""
        try:
            logger.info("Preparing to send interview summary to frontend...")
            summary_data = {
                "type": "interview_complete",
                "summary": summary
            }
            
            # Check if session and room are still available
            if not self.session or not self.session.room:
                logger.warning("Session or room not available, cannot send summary to frontend")
                return
            
            # Send summary data to frontend
            await self.session.room.local_participant.publish_data(
                json.dumps(summary_data).encode("utf-8"),
                reliable=True
            )
            logger.info("Successfully sent interview summary to frontend")
        except Exception as e:
            logger.error(f"Failed to send summary to frontend: {e}")
            logger.error(f"Exception details: {type(e).__name__}: {str(e)}")

    def _calculate_overall_grammar_accuracy(self) -> float:
        """Calculate overall grammar accuracy across all responses"""
        if not self.grammar_assessments:
            return 0.0
        
        total_accuracy = sum(assessment["accuracy_percentage"] for assessment in self.grammar_assessments)
        return total_accuracy / len(self.grammar_assessments)

    def _calculate_qa_grammar_issues(self) -> int:
        """Count number of Q&A answers with grammar accuracy below 70%"""
        qa_assessments = [g for g in self.grammar_assessments if g["stage"] == "questions"]
        return sum(1 for assessment in qa_assessments if assessment["accuracy_percentage"] < 70)

    def log_interview_data(self, stage: str, data: Dict):
        """Log interview progress and data for quality assurance"""
        self.interview_data["stage"] = stage
        self.interview_data[stage] = data
        logger.info(f"Interview stage: {stage}, Data: {json.dumps(data, indent=2)}")




def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def fetch_user_info_from_api(participant_id: str, room_name: str) -> Optional[Dict]:
    """Fetch user information from Next.js API endpoint"""
    api_url = os.getenv('NEXTJS_API_URL', 'http://localhost:3000')
    endpoint = f"{api_url}/api/interview-info"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                endpoint,
                params={'participantId': participant_id, 'roomName': room_name},
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"API request failed with status: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"Failed to fetch user info from API: {e}")
        return None


async def entrypoint(ctx: JobContext):
    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for the first participant to connect
    participant = await ctx.wait_for_participant()
    logger.info(f"starting technical interview for participant {participant.identity}")

    # Extract user information from room name and participant metadata
    role = "Software Engineer"  # default
    skill_level = "mid"  # default
    candidate_name = participant.identity or "Candidate"
    
    # Option 1: Parse from room name (format: interview-name-skill-timestamp)
    room_parts = ctx.room.name.split('-')
    if len(room_parts) >= 3 and room_parts[0] == 'interview':
        candidate_name = room_parts[1].replace('_', ' ')
        skill_level = room_parts[2]
    
    # Option 2: Parse from participant metadata (preferred)
    if participant.metadata:
        try:
            metadata = json.loads(participant.metadata)
            role = metadata.get('role', role)
            skill_level = metadata.get('skill', skill_level)
            logger.info(f"Using metadata - Role: {role}, Skill: {skill_level}")
        except json.JSONDecodeError:
            logger.warning("Failed to parse participant metadata")
    
    # Option 3: Fetch from Next.js API endpoint
    api_user_info = await fetch_user_info_from_api(participant.identity, ctx.room.name)
    if api_user_info:
        candidate_name = api_user_info.get('candidateName', candidate_name)
        skill_level = api_user_info.get('skillLevel', skill_level)
        role = api_user_info.get('role', role)
        logger.info(f"Using API data - Name: {candidate_name}, Role: {role}, Skill: {skill_level}")
    
    # Option 4: Parse from environment variables (fallback)
    role = os.getenv('INTERVIEW_ROLE', role)
    skill_level = os.getenv('INTERVIEW_SKILL_LEVEL', skill_level)

    usage_collector = metrics.UsageCollector()

    # Log metrics and collect usage data
    def on_metrics_collected(agent_metrics: metrics.AgentMetrics):
        metrics.log_metrics(agent_metrics)
        usage_collector.collect(agent_metrics)

    session = AgentSession(
        vad=ctx.proc.userdata["vad"],
        # Adjusted for interview context - longer delays for thinking time
        min_endpointing_delay=1.0,
        max_endpointing_delay=8.0,
    )

    # Trigger the on_metrics_collected function when metrics are collected
    session.on("metrics_collected", on_metrics_collected)

    await session.start(
        room=ctx.room,
        agent=InterviewAgent(
            role=role,
            candidate_name=candidate_name,
            skill_level=skill_level
        ),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )


def get_interview_instructions(role: str, candidate_name: str, skill_level: str) -> str:
    """Generate interview instructions for structured interview with exactly 5 questions"""
    
    return f"""
You are an INTERVIEWER conducting a structured technical interview for a {role} position. {candidate_name} is the CANDIDATE you are evaluating.

INTERVIEW STRUCTURE (4 STAGES):
1. WELCOME: Greet candidate and explain the interview process (already handled)
2. INTRODUCTION: Listen to candidate's self-introduction and background  
3. QUESTIONS: Ask exactly 5 predefined technical questions (agent will provide them)
4. WRAP-UP: Thank candidate and conclude the interview

CRITICAL BEHAVIOR RULES:
- You are the interviewer, NOT the candidate
- NEVER provide answers to your own questions
- NEVER give solutions, hints, or technical explanations during the interview
- NEVER ask about personal life, family, age, religion, politics, or any non-professional topics
- Be conversational and acknowledge their answers naturally
- NEVER speak ratings, scores, or evaluations out loud
- Keep all assessment completely silent and internal
- The interview system will automatically manage question flow

FORBIDDEN TOPICS AND BEHAVIORS:
- Do NOT provide answers or solutions to technical questions
- Do NOT give hints or clues about correct answers
- Do NOT ask about personal relationships, marital status, family plans
- Do NOT discuss politics, religion, or controversial topics
- Do NOT ask about age, health conditions, or disabilities
- Do NOT make assumptions about candidate's background based on name or accent
- Do NOT share your own technical opinions or preferences during evaluation

CURRENT STAGE BEHAVIOR:

INTRODUCTION STAGE:
- Listen to {candidate_name}'s PROFESSIONAL self-introduction and background
- Ask 1-2 natural follow-up questions about their WORK experience if needed
- Keep questions focused on professional experience, skills, and career
- Once you have good understanding of their background, acknowledge and transition to technical questions
- The system will automatically provide the next question

QUESTIONS STAGE:
- Acknowledge each answer they give naturally WITHOUT revealing correctness
- Ask for clarification if an answer is unclear or incomplete
- NEVER provide the correct answer if they struggle
- After they complete their answer, the system will automatically provide the next question
- You will ask exactly 5 technical questions total
- Be encouraging and professional throughout
- If they don't know an answer, simply say "That's okay" and move on

WRAP-UP STAGE:
- After 5 questions, thank them for their responses
- Ask if they have any questions about the role, team, or company
- Conclude professionally and mention next steps

SAFE CONVERSATIONAL PATTERNS:
- Good answer: "Thank you for that explanation."
- Partial answer: "I see. Could you elaborate on [specific part]?"
- Unclear answer: "Could you help me understand what you mean by...?"
- Don't know: "No problem, that's perfectly fine."
- NEVER say: "That's correct/incorrect" or "The right answer is..."

EVALUATION (COMPLETELY SILENT):
- Observe and assess {candidate_name}'s responses internally
- Track grammar, clarity, technical knowledge, problem-solving approach
- NEVER speak any evaluation out loud
- All assessment happens silently in the background

REMEMBER: 
- Be a professional, neutral interviewer
- Let candidates provide their own answers without help
- Keep the conversation strictly professional and technical
- Acknowledge their answers before moving on
- The system handles question progression automatically
- Focus on being responsive and encouraging while maintaining professionalism
"""


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )
