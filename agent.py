import logging
import json
import os
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
# from eleven_tts import ElevenLabsTTSe

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
    ChatContext,
    function_tool,
    RunContext,
    get_job_context,
)
from livekit.plugins import (
    openai,
    noise_cancellation,
    silero,
    elevenlabs,
    groq,
    deepgram,
    cartesia
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
    INTRODUCTION = "introduction"
    PROJECTS_DISCUSSION = "projects_discussion"
    TECHNICAL_QUESTIONS = "technical_questions"
    HOBBIES = "hobbies"
    CONCLUSION = "conclusion"


@dataclass
class InterviewSessionData:
    candidate_name: str
    role: str
    skill_level: str
    start_time: str
    duration_minutes: float = 0
    competencies_covered: List[str] = None
    scores: Dict = None
    notes: Dict = None
    questions_asked: List[str] = None
    evaluation_summary: Dict = None
    projects_mentioned: List[str] = None
    hobbies_mentioned: List[str] = None
    total_questions_count: int = 0
    max_questions: int = 4  # Reduced for testing
    
    def __post_init__(self):
        if self.competencies_covered is None:
            self.competencies_covered = []
        if self.scores is None:
            self.scores = {}
        if self.notes is None:
            self.notes = {}
        if self.questions_asked is None:
            self.questions_asked = []
        if self.evaluation_summary is None:
            self.evaluation_summary = {}
        if self.projects_mentioned is None:
            self.projects_mentioned = []
        if self.hobbies_mentioned is None:
            self.hobbies_mentioned = []


class IntroductionAgent(Agent):
    def __init__(self, chat_ctx: ChatContext = None) -> None:
        super().__init__(
            instructions=self.get_introduction_instructions(),
            stt=openai.STT(model="whisper-1"),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=openai.TTS(),
            # tts=ElevenLabsTTS(),
            turn_detection=MultilingualModel(),
            chat_ctx=chat_ctx
        )

    async def on_enter(self) -> None:
        userdata: InterviewSessionData = self.session.userdata
        await self.session.say(
            f"Hello {userdata.candidate_name}! I'm your interviewer for this {userdata.role} position. "
            f"Thank you for taking the time to interview with us today. "
            f"To start, could you please introduce yourself and tell me a bit about your background?"
        )
        userdata.total_questions_count += 1

    @function_tool()
    async def ask_follow_up_question(self, context: RunContext[InterviewSessionData], question: str):
        """Use this tool to ask a follow-up question about their background."""
        context.userdata.total_questions_count += 1
        context.userdata.questions_asked.append(f"Introduction: {question}")
        logger.info(f"Asked introduction question {context.userdata.total_questions_count}/{context.userdata.max_questions}")

    @function_tool()
    async def proceed_to_projects(self, context: RunContext[InterviewSessionData]):
        """Use this tool when the candidate has completed their introduction and you're ready to move to discussing their projects."""
        context.userdata.notes["introduction"] = f"Completed introduction stage - {context.userdata.total_questions_count} questions asked so far"
        logger.info(f"Moving from introduction to projects discussion. Questions so far: {context.userdata.total_questions_count}")
        
        if context.userdata.total_questions_count >= context.userdata.max_questions:
            logger.info("Reached maximum questions, skipping to conclusion")
            return InterviewConclusionAgent(chat_ctx=self.session.chat_ctx)
        
        return ProjectsAgent(chat_ctx=self.session.chat_ctx)

    def get_introduction_instructions(self) -> str:
        return """
You are conducting the INTRODUCTION stage of a technical interview. Your role is to:

1. Welcome the candidate warmly  
2. Let them introduce themselves and their background
3. Ask 1-2 focused follow-up questions using the ask_follow_up_question tool
4. Keep this stage efficient (aim for 2-3 questions total including the initial introduction)
5. When they've given a good overview, use the proceed_to_projects tool

BEHAVIOR:
- Be welcoming and professional
- Listen actively to their background
- Ask 1-2 targeted follow-up questions using ask_follow_up_question tool
- Keep it concise - this is just the opening of the interview
- Track that we're aiming for about 10 questions total across the entire interview

Use ask_follow_up_question for questions like:
- "What drew you to software engineering?"
- "Can you tell me more about your current role?"

Use proceed_to_projects when:
- You've asked 2-3 questions including the introduction
- You have a basic understanding of their background
"""


class ProjectsAgent(Agent):
    def __init__(self, chat_ctx: ChatContext = None) -> None:
        super().__init__(
            instructions=self.get_projects_instructions(),
            stt=openai.STT(model="whisper-1"),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=openai.TTS(),
            turn_detection=MultilingualModel(),
            chat_ctx=chat_ctx
        )

    async def on_enter(self) -> None:
        userdata: InterviewSessionData = self.session.userdata
        await self.session.say(
            "Great! Now I'd love to hear about a project you've worked on. "
            "Could you walk me through one project you're particularly proud of?"
        )
        userdata.total_questions_count += 1

    @function_tool()
    async def record_project(self, context: RunContext[InterviewSessionData], project_name: str, technologies: str, description: str):
        """Use this tool to record details about a project the candidate mentions."""
        project_info = {
            "name": project_name,
            "technologies": technologies,
            "description": description
        }
        context.userdata.projects_mentioned.append(project_info)
        logger.info(f"Recorded project: {project_name}")

    @function_tool()
    async def ask_project_follow_up(self, context: RunContext[InterviewSessionData], question: str):
        """Use this tool to ask follow-up questions about their projects."""
        context.userdata.total_questions_count += 1
        context.userdata.questions_asked.append(f"Projects: {question}")
        logger.info(f"Asked project question {context.userdata.total_questions_count}/{context.userdata.max_questions}")

    @function_tool()
    async def proceed_to_technical(self, context: RunContext[InterviewSessionData]):
        """Use this tool when you've discussed their projects sufficiently and are ready to move to technical questions."""
        context.userdata.notes["projects"] = f"Discussed {len(context.userdata.projects_mentioned)} projects - {context.userdata.total_questions_count} questions total so far"
        logger.info(f"Moving from projects to technical questions. Questions so far: {context.userdata.total_questions_count}")
        
        if context.userdata.total_questions_count >= context.userdata.max_questions:
            logger.info("Reached maximum questions, skipping to conclusion")
            return InterviewConclusionAgent(chat_ctx=self.session.chat_ctx)
        
        return TechnicalQuestionsAgent(chat_ctx=self.session.chat_ctx)

    def get_projects_instructions(self) -> str:
        return """
You are conducting the PROJECTS DISCUSSION stage of a technical interview. Your role is to:

1. Ask about 1-2 specific projects they've worked on
2. Understand the technologies they used and their role
3. Record project details using the record_project tool
4. Ask 2-3 follow-up questions using ask_project_follow_up tool
5. Keep this efficient (aim for 3-4 questions total in this stage)

BEHAVIOR:
- Focus on 1-2 significant projects to understand their experience
- Use record_project tool for each project they mention
- Use ask_project_follow_up for questions like:
  - "What technologies did you use in this project?"
  - "What was the biggest challenge you faced?"
  - "What was your specific role?"
- Remember we're aiming for about 10 questions total across the entire interview

Use proceed_to_technical when:
- You've discussed 1-2 projects with 3-4 questions total
- You have a good understanding of their technical experience
- You're ready to ask more specific technical questions
"""


class TechnicalQuestionsAgent(Agent):
    def __init__(self, chat_ctx: ChatContext = None) -> None:
        super().__init__(
            instructions=self.get_technical_instructions(),
            stt=openai.STT(model="whisper-1"),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=openai.TTS(),
            # tts=elevenlabs.TTS(                # ← built‑in plugin
            #     voice_id="sarah",  # optional
            #     model="eleven_multilingual_v2",  # try a different model if you like
            # ),            
            turn_detection=MultilingualModel(),
            chat_ctx=chat_ctx
        )

    async def on_enter(self) -> None:
        userdata: InterviewSessionData = self.session.userdata
        
        await self.session.say(
            "Hello! I'm going to test the coding interface with you. "
            "I'll open a Python code interpreter for you now."
        )
        
        # Force the tool call immediately without waiting for LLM
        await self.open_code_interpreter(
            self.session.run_context,
            question="Write a Python function that takes a list of integers and returns the sum of all even numbers in the list. For example, if the input is [1, 2, 3, 4, 5, 6], your function should return 12 (2 + 4 + 6).",
            language="python"
        )

    @function_tool()
    async def ask_technical_question(self, context: RunContext[InterviewSessionData], question: str, competency: str):
        """Use this tool to ask a technical question and track it."""
        context.userdata.total_questions_count += 1
        technical_response = {
            "question": question,
            "competency": competency,
            "timestamp": datetime.now().isoformat()
        }
        context.userdata.questions_asked.append(f"Technical: {question}")
        logger.info(f"Asked technical question {context.userdata.total_questions_count}/{context.userdata.max_questions}: {competency}")

    @function_tool()
    async def open_code_editor(self, context: RunContext[InterviewSessionData], question: str, language: str = "javascript"):
        """Use this tool to open a code editor in the UI for coding questions. The candidate will write code and submit it back."""
        try:
            # Get the participant identity (assuming single participant for now)
            job_ctx = get_job_context()
            
            # Get the first remote participant
            remote_participants = list(job_ctx.room.remote_participants.keys())
            if not remote_participants:
                raise Exception("No remote participants found")
            
            participant_identity = remote_participants[0]
            logger.info(f"Sending RPC to participant: {participant_identity}")
            
            response = await job_ctx.room.local_participant.perform_rpc(
                destination_identity=participant_identity,
                method="openCodeEditor",
                payload=json.dumps({
                    "question": question,
                    "language": language
                }),
                response_timeout=10.0,
            )
            
            logger.info(f"Code editor opened successfully for question: {question}")
            context.userdata.total_questions_count += 1
            context.userdata.questions_asked.append(f"Coding: {question}")
            
            # Don't say the question aloud - it will be displayed in the code editor
            await context.session.say(
                "I've opened a code editor for you. Please write your solution and click submit when ready."
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to open code editor: {e}")
            await context.session.say(
                "I'm having trouble opening the code editor. Let me ask you the question verbally instead."
            )
            # Fall back to asking the question normally
            context.userdata.total_questions_count += 1
            context.userdata.questions_asked.append(f"Coding (verbal): {question}")
            return f"Error opening code editor: {str(e)}"

    @function_tool()
    async def open_code_interpreter(self, context: RunContext[InterviewSessionData], question: str, language: str = "python"):
        """Use this tool to open a code interpreter for Python coding questions. This provides an interactive environment where the candidate can write and execute Python code."""
        try:
            # Get the participant identity (assuming single participant for now)
            job_ctx = get_job_context()
            
            # Get the first remote participant
            remote_participants = list(job_ctx.room.remote_participants.keys())
            if not remote_participants:
                raise Exception("No remote participants found")
            
            participant_identity = remote_participants[0]
            logger.info(f"Sending RPC to participant for code interpreter: {participant_identity}")
            
            response = await job_ctx.room.local_participant.perform_rpc(
                destination_identity=participant_identity,
                method="openCodeInterpreter",
                payload=json.dumps({
                    "question": question,
                    "language": language,
                    "type": "interpreter"
                }),
                response_timeout=10.0,
            )
            
            logger.info(f"Code interpreter opened successfully for question: {question}")
            context.userdata.total_questions_count += 1
            context.userdata.questions_asked.append(f"Python Interpreter: {question}")
            
            # Don't say the question aloud - it will be displayed in the code interpreter
            await context.session.say(
                "I've opened a Python code interpreter for you. You can write and execute your code directly. Please solve the problem and submit your solution when ready."
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to open code interpreter: {e}")
            await context.session.say(
                "I'm having trouble opening the code interpreter. Let me ask you the question verbally instead."
            )
            # Fall back to asking the question normally
            context.userdata.total_questions_count += 1
            context.userdata.questions_asked.append(f"Python (verbal): {question}")
            return f"Error opening code interpreter: {str(e)}"

    @function_tool()
    async def analyze_submitted_code(self, context: RunContext[InterviewSessionData], code: str, language: str, explanation: str, question: str, execution_output: str = ""):
        """This tool is called when the candidate submits code from the editor. Analyze and provide feedback."""
        try:
            # Store the code submission
            code_submission = {
                "question": question,
                "code": code,
                "language": language,
                "explanation": explanation,
                "execution_output": execution_output,
                "timestamp": datetime.now().isoformat()
            }
            
            # Add to notes
            if "code_submissions" not in context.userdata.notes:
                context.userdata.notes["code_submissions"] = []
            context.userdata.notes["code_submissions"].append(code_submission)
            
            logger.info(f"Code submitted for question: {question}")
            logger.info(f"Language: {language}, Code length: {len(code)} chars")
            
            # Actually analyze the submitted code
            code_words = len(code.split()) if code.strip() else 0
            
            if not code.strip():
                await context.session.say(
                    f"I notice you submitted empty code. Please try to implement a solution to the problem. "
                    f"Let me open another coding question for you to try."
                )
            elif code_words < 5:
                await context.session.say(
                    f"Your submission seems quite short with only {code_words} words. "
                    f"Make sure you've implemented a complete solution. Let me continue with another question."
                )
            elif language.lower() == "python":
                # Check for basic Python function structure
                has_def = "def " in code
                has_return = "return" in code
                
                if has_def and has_return:
                    await context.session.say(
                        f"Good! I can see you've implemented a Python function with a return statement. "
                        f"Your code has {code_words} words and appears to have the basic structure needed. "
                        f"{'Your explanation helps me understand your approach.' if explanation else ''} "
                        f"Let me continue with another coding question."
                    )
                elif has_def:
                    await context.session.say(
                        f"I see you've defined a function, but it might be missing a return statement. "
                        f"Make sure your function returns the expected result. Let me continue with another question."
                    )
                else:
                    await context.session.say(
                        f"I see you've written some Python code, but it doesn't appear to define a function as requested. "
                        f"Remember to use 'def function_name():' to define functions. Let me continue with another question."
                    )
            else:
                await context.session.say(
                    f"Thank you for submitting your {language} code with {code_words} words. "
                    f"{'Your explanation helps me understand your thought process.' if explanation else ''} "
                    f"Let me continue with another question."
                )
            
            # After analyzing, automatically ask the next question
            if context.userdata.total_questions_count < context.userdata.max_questions:
                # Ask another coding question automatically
                if language.lower() == "python":
                    await self.open_code_interpreter(
                        context,
                        question="Write a Python function that checks if a string is a palindrome (reads the same forwards and backwards). For example, 'racecar' should return True, and 'hello' should return False.",
                        language="python"
                    )
                else:
                    await self.open_code_editor(
                        context,
                        question="Write a JavaScript function to reverse a string without using built-in reverse methods.",
                        language="javascript"
                    )
            
            return "Code analyzed successfully"
            
        except Exception as e:
            logger.error(f"Error analyzing code: {e}")
            await context.session.say("I received your code submission. Thank you!")
            return f"Error analyzing code: {str(e)}"

    @function_tool()
    async def proceed_to_hobbies(self, context: RunContext[InterviewSessionData]):
        """Use this tool when you've asked sufficient technical questions and are ready to move to discussing hobbies."""
        context.userdata.notes["technical"] = f"Asked technical questions - {context.userdata.total_questions_count} questions total so far"
        logger.info(f"Moving from technical questions to hobbies. Questions so far: {context.userdata.total_questions_count}")
        
        if context.userdata.total_questions_count >= context.userdata.max_questions:
            logger.info("Reached maximum questions, going to conclusion")
            return InterviewConclusionAgent(chat_ctx=self.session.chat_ctx)
        
        return HobbiesAgent(chat_ctx=self.session.chat_ctx)

    def get_technical_instructions(self) -> str:
        return """
You are conducting a CODING-FOCUSED technical interview for testing purposes. Your role is to:

1. IMMEDIATELY call the open_code_interpreter tool as your first action - do not wait
2. Ask 2-3 additional CODING questions using open_code_interpreter or open_code_editor tools
3. Focus ONLY on coding problems - no conceptual questions
4. Keep the session short for testing (3-4 coding questions total)

CRITICAL: You must call the open_code_interpreter tool immediately after greeting the user.
CRITICAL: You must only use the word interpreter while u want the user to open the interpreter.

PRIORITY BEHAVIOR - FIRST ACTION:
- IMMEDIATELY use the open_code_interpreter tool as your very first action
- Use this exact question: "Write a Python function that takes a list of integers and returns the sum of all even numbers in the list. For example, if the input is [1, 2, 3, 4, 5, 6], your function should return 12 (2 + 4 + 6)."
- Do not wait for user input - call the tool right after entering the stage
- Other Python questions for subsequent actions:
  * "Write a Python function to find the maximum number in a list without using the max() function"
  * "Write a Python function that checks if a string is a palindrome"
  * "Create a Python function that removes duplicates from a list while preserving order"

CODING QUESTIONS FOR TESTING:
- Python (use open_code_interpreter): 
  * "Write a function that finds the sum of even numbers in a list"
  * "Create a function to check if a string is a palindrome"
  * "Implement a function to find the second largest number in a list"
  * "Write a function to count vowels in a string"
  * "Create a function that reverses a string without using built-in reverse"

- JavaScript/Other languages (use open_code_editor):
  * "Write a JavaScript function to reverse a string" 
  * "Implement a simple sorting algorithm"
  * "Create a function to find duplicates in an array"

TESTING BEHAVIOR:
- Ask ONLY coding questions - no conceptual or theory questions
- Limit to 3-4 coding questions total for quick testing
- DO NOT read the question aloud - it will be displayed in the interface
- Wait for code submission before proceeding
- After 3-4 coding questions, conclude the session

Use proceed_to_hobbies when:
- You've asked 3-4 coding questions OR
- You have tested the coding interface sufficiently
"""


class HobbiesAgent(Agent):
    def __init__(self, chat_ctx: ChatContext = None) -> None:
        super().__init__(
            instructions=self.get_hobbies_instructions(),
            stt=openai.STT(model="whisper-1"),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=openai.TTS(),
            turn_detection=MultilingualModel(),
            chat_ctx=chat_ctx
        )

    async def on_enter(self) -> None:
        userdata: InterviewSessionData = self.session.userdata
        remaining_questions = userdata.max_questions - userdata.total_questions_count
        
        if remaining_questions <= 1:
            await self.session.say(
                "Before we wrap up, what's one hobby or interest you have outside of work?"
            )
            userdata.total_questions_count += 1
        elif remaining_questions <= 2:
            await self.session.say(
                "Now I'd like to get to know you better as a person. "
                "What do you like to do outside of work?"
            )
            userdata.total_questions_count += 1
        else:
            await self.session.say(
                "That covers the technical portion. "
                "Now I'd like to learn about your interests outside of work. "
                "What are your hobbies and what do you enjoy doing in your free time?"
            )
            userdata.total_questions_count += 1

    @function_tool()
    async def record_hobby(self, context: RunContext[InterviewSessionData], hobby: str, description: str):
        """Use this tool to record hobbies and interests mentioned by the candidate."""
        hobby_info = {
            "hobby": hobby,
            "description": description
        }
        context.userdata.hobbies_mentioned.append(hobby_info)
        logger.info(f"Recorded hobby: {hobby}")

    @function_tool()
    async def ask_hobby_follow_up(self, context: RunContext[InterviewSessionData], question: str):
        """Use this tool to ask a follow-up question about their hobbies, only if we haven't reached the question limit."""
        if context.userdata.total_questions_count < context.userdata.max_questions:
            context.userdata.total_questions_count += 1
            context.userdata.questions_asked.append(f"Hobbies: {question}")
            logger.info(f"Asked hobby follow-up {context.userdata.total_questions_count}/{context.userdata.max_questions}")
        else:
            logger.info("Reached question limit, skipping hobby follow-up")

    @function_tool()
    async def conclude_interview(self, context: RunContext[InterviewSessionData]):
        """Use this tool when you've discussed their hobbies and are ready to conclude the interview."""
        context.userdata.notes["hobbies"] = f"Discussed hobbies - {context.userdata.total_questions_count} total questions asked"
        logger.info(f"Moving to interview conclusion. Total questions asked: {context.userdata.total_questions_count}")
        return InterviewConclusionAgent(chat_ctx=self.session.chat_ctx)

    def get_hobbies_instructions(self) -> str:
        return """
You are conducting the HOBBIES AND PERSONAL INTERESTS stage of a technical interview. Your role is to:

1. Learn about their interests outside of work (1-2 questions max)
2. Record their hobbies using the record_hobby tool  
3. Ask 1 follow-up question using ask_hobby_follow_up tool only if we haven't reached 10 questions total
4. Keep this stage brief since we're near the end of our question limit

BEHAVIOR:
- Be genuinely interested but keep it concise
- Use record_hobby tool for interests they mention
- Use ask_hobby_follow_up for ONE follow-up question like "What got you into that?" only if under question limit
- Remember we're aiming for exactly 10 questions total across the entire interview

IMPORTANT: Check the total question count:
- If we're at 10 questions total, proceed immediately to conclusion
- If we're at 9 questions, ask at most 1 more question
- Always use conclude_interview when ready to wrap up

Use conclude_interview when:
- You've learned about their main hobbies (1-2 exchanges) OR
- We've reached the 10 question limit OR
- You have a sense of their personality
"""


class InterviewConclusionAgent(Agent):
    def __init__(self, chat_ctx: ChatContext = None) -> None:
        super().__init__(
            instructions=self.get_conclusion_instructions(),
            stt=openai.STT(model="whisper-1"),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=openai.TTS(),
            turn_detection=MultilingualModel(),
            chat_ctx=chat_ctx
        )

    async def on_enter(self) -> None:
        userdata: InterviewSessionData = self.session.userdata
        
        # Calculate interview duration
        start_time = datetime.fromisoformat(userdata.start_time)
        duration = (datetime.now() - start_time).total_seconds() / 60
        userdata.duration_minutes = duration
        
        # Generate summary
        summary = self.generate_interview_summary(userdata)
        
        # Log final summary
        logger.info(f"Interview completed for {userdata.candidate_name}")
        logger.info(f"Duration: {duration:.1f} minutes")
        logger.info(f"Projects discussed: {len(userdata.projects_mentioned)}")
        logger.info(f"Technical questions: {len(userdata.questions_asked)}")
        logger.info(f"Hobbies mentioned: {len(userdata.hobbies_mentioned)}")
        
        await self.session.say(
            f"Thank you so much for your time today, {userdata.candidate_name}. "
            f"This concludes our interview. Do you have any questions about the role, "
            f"the team, or our company? We'll follow up with next steps within a few business days."
        )

    def generate_interview_summary(self, userdata: InterviewSessionData) -> Dict:
        """Generate a comprehensive interview summary"""
        return {
            "candidate": userdata.candidate_name,
            "role": userdata.role,
            "skill_level": userdata.skill_level,
            "duration_minutes": userdata.duration_minutes,
            "stages_completed": [
                "introduction",
                "projects_discussion", 
                "technical_questions",
                "hobbies",
                "conclusion"
            ],
            "projects_discussed": userdata.projects_mentioned,
            "technical_questions_count": len(userdata.questions_asked),
            "hobbies_mentioned": userdata.hobbies_mentioned,
            "notes": userdata.notes,
            "completion_time": datetime.now().isoformat()
        }

    def get_conclusion_instructions(self) -> str:
        return """
You are concluding the technical interview. Your role is to:

1. Thank the candidate for their time
2. Ask if they have any questions about the role or company
3. Provide next steps information
4. End the interview professionally

BEHAVIOR:
- Be warm and professional
- Give them an opportunity to ask questions
- Provide clear next steps
- Thank them for their time
- Keep it brief but personable
"""


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

    session = AgentSession[InterviewSessionData](
        vad=ctx.proc.userdata["vad"],
        # Adjusted for interview context - longer delays for thinking time
        min_endpointing_delay=1.0,
        max_endpointing_delay=8.0,
        userdata=InterviewSessionData(
            candidate_name=candidate_name,
            role=role,
            skill_level=skill_level,
            start_time=datetime.now().isoformat()
        )
    )

    # Set up RPC handler for code submissions
    async def handle_code_submission(rpc_invocation):
        """Handle code submissions from the frontend"""
        try:
            data = json.loads(rpc_invocation.payload)
            code = data.get('code', '')
            language = data.get('language', 'javascript')
            explanation = data.get('explanation', '')
            question = data.get('question', '')
            
            # Find the current agent and call analyze_submitted_code
            current_agent = session.agent
            if isinstance(current_agent, TechnicalQuestionsAgent):
                await current_agent.analyze_submitted_code(
                    session.run_context,
                    code=code,
                    language=language,
                    explanation=explanation,
                    question=question,
                    execution_output=execution_output
                )
            
            return json.dumps({"status": "success", "message": "Code received and analyzed"})
            
        except Exception as e:
            logger.error(f"Error handling code submission: {e}")
            return json.dumps({"status": "error", "message": str(e)})

    # Set up RPC handler for code interpreter submissions
    async def handle_code_interpreter_submission(rpc_invocation):
        """Handle code interpreter submissions from the frontend"""
        try:
            data = json.loads(rpc_invocation.payload)
            code = data.get('code', '')
            language = data.get('language', 'python')
            explanation = data.get('explanation', '')
            question = data.get('question', '')
            execution_output = data.get('output', '')
            
            logger.info(f"Code interpreter submission: {len(code)} chars of {language} code")
            logger.info(f"Execution output: {execution_output[:200]}..." if len(execution_output) > 200 else f"Execution output: {execution_output}")
            
            # Find the current agent and call analyze_submitted_code
            current_agent = session.agent
            if isinstance(current_agent, TechnicalQuestionsAgent):
                await current_agent.analyze_submitted_code(
                    session.run_context,
                    code=code,
                    language=language,
                    explanation=explanation,
                    question=question
                )
            
            return json.dumps({"status": "success", "message": "Code interpreter submission received and analyzed"})
            
        except Exception as e:
            logger.error(f"Error handling code interpreter submission: {e}")
            return json.dumps({"status": "error", "message": str(e)})

    # Register the RPC methods
    ctx.room.local_participant.register_rpc_method("submitCode", handle_code_submission)
    ctx.room.local_participant.register_rpc_method("submitCodeInterpreter", handle_code_interpreter_submission)

    # Trigger the on_metrics_collected function when metrics are collected
    session.on("metrics_collected", on_metrics_collected)

    await session.start(
        room=ctx.room,
        agent=TechnicalQuestionsAgent(),  # Start directly with technical questions for testing
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )
