import logging
import json
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

from dotenv import load_dotenv
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
    cartesia,
    openai,
    noise_cancellation,
    silero,
    groq
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
    ONBOARDING = "onboarding"
    TECHNICAL_ASSESSMENT = "technical_assessment"
    CANDIDATE_QUESTIONS = "candidate_questions"
    WRAP_UP = "wrap_up"
    COMPLETED = "completed"


class InterviewAgent(Agent):
    def __init__(self, 
                 role: str = "Software Engineer", 
                 candidate_name: str = "Candidate",
                 skill_level: str = "mid") -> None:
        super().__init__(
            instructions=get_interview_instructions(role, candidate_name, skill_level),
            stt=groq.STT(),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=cartesia.TTS(),
            turn_detection="vad",
        )
        self.role = role
        self.candidate_name = candidate_name
        self.skill_level = SkillLevel(skill_level) if SkillLevel else skill_level
        self.current_stage = InterviewStage.ONBOARDING
        self.current_competency_index = 0
        self.interview_data = {
            "start_time": datetime.now().isoformat(),
            "role": role,
            "candidate_name": candidate_name,
            "skill_level": skill_level,
            "competencies_covered": [],
            "scores": {},
            "notes": {},
            "stage": self.current_stage.value,
            "duration_minutes": 0,
            "questions_asked": [],
            "evaluation_summary": {}
        }

    async def on_enter(self):
        # Start the interview immediately with a direct greeting and first question
        await self.session.say(
            self.get_introduction_script(),
            allow_interruptions=True
        )

    def get_introduction_script(self) -> str:
        """Get concise role-specific introduction script"""
        return f"Hello {self.candidate_name}! I'm your interviewer for this {self.role} position. Let's start with our first question: Can you explain the time complexity of binary search?"

    def get_competencies(self) -> List:
        """Get competencies for the current role"""
        if self.role in ROLE_TEMPLATES:
            return ROLE_TEMPLATES[self.role].competencies
        return []

    def log_interview_data(self, stage: str, data: Dict):
        """Log interview progress and data for quality assurance"""
        self.interview_data["stage"] = stage
        self.interview_data[stage] = data
        self.interview_data["duration_minutes"] = (
            datetime.now() - datetime.fromisoformat(self.interview_data["start_time"])
        ).total_seconds() / 60
        logger.info(f"Interview stage: {stage}, Data: {json.dumps(data, indent=2)}")

    def update_competency_score(self, competency_name: str, score: int, evidence: str):
        """Update score for a specific competency"""
        self.interview_data["scores"][competency_name] = {
            "score": score,
            "evidence": evidence,
            "timestamp": datetime.now().isoformat()
        }

    def get_interview_summary(self) -> Dict:
        """Generate final interview summary"""
        competencies = self.get_competencies()
        total_weighted_score = 0
        total_weight = 0
        
        summary = {
            "candidate": self.candidate_name,
            "role": self.role,
            "duration_minutes": self.interview_data["duration_minutes"],
            "competency_scores": {},
            "overall_recommendation": "",
            "strengths": [],
            "areas_for_improvement": [],
            "detailed_feedback": {}
        }
        
        for competency in competencies:
            if competency.name in self.interview_data["scores"]:
                score_data = self.interview_data["scores"][competency.name]
                weighted_score = score_data["score"] * competency.weight
                total_weighted_score += weighted_score
                total_weight += competency.weight
                
                summary["competency_scores"][competency.name] = {
                    "score": score_data["score"],
                    "weight": competency.weight,
                    "weighted_score": weighted_score,
                    "evidence": score_data["evidence"]
                }
        
        # Calculate overall score
        overall_score = total_weighted_score / total_weight if total_weight > 0 else 0
        summary["overall_score"] = round(overall_score, 2)
        
        # Generate recommendation
        if overall_score >= 4.0:
            summary["overall_recommendation"] = "Strong Hire"
        elif overall_score >= 3.5:
            summary["overall_recommendation"] = "Hire"
        elif overall_score >= 2.5:
            summary["overall_recommendation"] = "Borderline - Additional Assessment Needed"
        else:
            summary["overall_recommendation"] = "No Hire"
        
        return summary


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for the first participant to connect
    participant = await ctx.wait_for_participant()
    logger.info(f"starting technical interview for participant {participant.identity}")

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
            role="Software Engineer",  # This can be customized via environment variables
            candidate_name=participant.identity or "Candidate",
            skill_level="mid"  # This can also be customized
        ),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )


def get_interview_instructions(role: str, candidate_name: str, skill_level: str) -> str:
    """Generate concise interview instructions for brief, focused responses"""
    
    return f"""
You are the INTERVIEWER conducting a technical interview for a {role} position. {candidate_name} is the CANDIDATE you are evaluating.

CRITICAL RULES:
- You are the interviewer, NOT the candidate
- Keep ALL responses brief - maximum 1-2 sentences
- NEVER speak ratings or scores out loud (e.g., never say "Rating: 1")
- Keep all evaluation completely silent and internal
- Never explain the interview agenda or structure to the candidate
- Never say "This interview will take 60 minutes" or list the areas you'll cover
- Never ask "Do you have questions before we begin?"
- Just greet and immediately ask technical questions

YOUR ROLE: 
- YOU ask technical questions to evaluate {candidate_name}
- {candidate_name} provides answers to YOUR questions
- Keep questions short and direct

CORE GUIDELINES:
- Be extremely concise - no verbose explanations
- Ask one technical question at a time
- Never provide interview overviews or agendas
- Skip pleasantries and get straight to technical questions

RESPONSE STYLE:
- Maximum 1-2 sentences per response
- Ask one clear technical question
- No agenda explanations or time breakdowns
- No "welcome speeches" or procedural explanations

EVALUATION (SILENT - NEVER SPEAK RATINGS):
- Rate competencies 1-5 based on {candidate_name}'s answers
- NEVER say ratings out loud to the candidate
- Keep all scoring completely silent and internal
- Never say "Rating: 1" or mention scores verbally

Start with brief greeting and immediate technical question - no agenda or explanations.
"""


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )
