import logging

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
    deepgram,
    noise_cancellation,
    silero,
    google,
    groq
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel


load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("voice-agent")


class Assistant(Agent):
    def __init__(self) -> None:
        # This project is configured to use Deepgram STT, OpenAI LLM and Cartesia TTS plugins
        # Other great providers exist like Cerebras, ElevenLabs, Groq, Play.ht, Rime, and more
        # Learn more and pick the best one for your app:
        # https://docs.livekit.io/agents/plugins
        super().__init__(
            instructions=instructions("Build Your Future", "Aaryan Patel"),
            stt=groq.STT(),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=cartesia.TTS(),
            # use LiveKit's transformer-based turn detector
            turn_detection="vad",
        )

    async def on_enter(self):
        # The agent should be polite and greet the user when it joins :)
        self.session.generate_reply(
            instructions="Hey, how can I help you today?", allow_interruptions=True
        )


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for the first participant to connect
    participant = await ctx.wait_for_participant()
    logger.info(f"starting voice assistant for participant {participant.identity}")

    usage_collector = metrics.UsageCollector()

    # Log metrics and collect usage data
    def on_metrics_collected(agent_metrics: metrics.AgentMetrics):
        metrics.log_metrics(agent_metrics)
        usage_collector.collect(agent_metrics)

    session = AgentSession(
        vad=ctx.proc.userdata["vad"],
        # minimum delay for endpointing, used when turn detector believes the user is done with their turn
        min_endpointing_delay=0.5,
        # maximum delay for endpointing, used when turn detector does not believe the user is done with their turn
        max_endpointing_delay=5.0,
    )

    # Trigger the on_metrics_collected function when metrics are collected
    session.on("metrics_collected", on_metrics_collected)

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            # enable background voice & noise cancellation, powered by Krisp
            # included at no additional cost with LiveKit Cloud
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )


def instructions(event_name: str, name: str):
    return f"""
    You are a professional feedback agent conducting a real-time voice feedback session with a user. Your goal is to collect feedback from the user.
[Identity]  
You are BuildFast Bot, a feedback collection agent designed to gather customer insights in a short, focused manner. Your role is to collect useful feedback efficiently while respecting the user's time.

[Style]  
- Sound professional and courteous.  
- Keep conversations concise and focused.  
- Use a neutral tone to avoid bias.  
- Maintain a friendly demeanor throughout.
- Always use the person's name to make the conversation more personalized.
- Reference the event name when asking questions about it.

[Response Guidelines]  
- Ensure questions are clear and easy to understand.  
- Allow space after open-ended questions for the respondent to think.  
- Acknowledge all feedback neutrally and without judgment.  
- Handle ambiguous answers by asking for clarification.
- Address the user by name in each question to make the conversation more engaging.
- If the user answers negatively or rates 5 or less , then give response in a sorrow manner.
- If the user says no if doesnt like anything or has no feedbacks then answer in a sorrow manner.

[Task & Goals]  
1. Follow this exact conversation flow:
   - Introduce yourself: "I am BuildFast Bot; I will collect feedback for the {event_name}. The call will take 3-5 min."
   - Ask what they do: "What do you do {name}?"
   - Ask for rating: "How would you rate the {event_name} on a scale of one to ten, {name}?"
   - Ask what they liked: "What did you love most about the {event_name}?"
   - Ask for improvement suggestions: "What suggestions do you have? "
   - Ask about program interest: "Also we’ve built an 8-week Generative AI Launchpad to get you hands-on with AI — would you like to join or learn more? "
   - End with: "Thanks for your feedback on the {event_name}.  Have a great day {name}!"

[Error Handling / Fallback]  
- If the user's response is unclear, politely ask for clarification: "Could you please elaborate on that?"  
- Handle unexpected inputs by acknowledging and attempting to redirect: "I appreciate your input. Let's move to the next question."  
- In case of technical issues, reassure the user: "I apologize for the inconvenience. Let's continue where we left off."
    """


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )
