import asyncio
from langchain_ollama import ChatOllama
from langchain.messages import AIMessage
from langchain.tools import tool
from datetime import datetime
#from duckduckgo_search import DDGS
import speech_to_text_whisper as speech_to_text
import spotify_player
import os



###Turn on spotify on boot
os.system("spotify")

@tool
def write_file(filename, content):
    """Writes content to a file with the given filename, and returns a success message,
    Args:
        filename (str): The name of the file to write to.
        content (str): The content to write to the file.
    Returns:    str: A success message indicating that the file was written successfully.
    """
    with open(f"{filename}.txt", "w") as f:
        f.write(content)
        f.close()
    return f"File {filename} written successfully to"

@tool
def web_search(question: str, max_results: int = 5):
    """Search the web for `question` and return results.

    Args:
        question (str): Query to search for.
        max_results (int): Maximum number of results to return.

    Returns:
        list: A list of search result dicts from `duckduckgo_search.ddg`.
    """
    #try:
    #    results = ddg(question, max_results=max_results)
    #    return results or []
    #except Exception as e:
    #    return [{"error": str(e)}]

@tool
def play_song(song_name, artist=None):
    """Plays a song on Spotify given its name.
    Args:
        song_name (str): The name of the song to play.
    Returns:
        str: A message indicating that the song is being played, or an error message if the song is not found.
    """
    try:
        spotify_player.play_song(song_name, artist)
    except Exception as e:
        return f"Error playing song {song_name}: {e}"
@tool
def pause_song():
    """Pauses the currently playing song on Spotify."""
    try:
        spotify_player.pause_song()
        return "Playback paused."
    except Exception as e:
        return f"Error pausing song: {e}"
@tool
def resume_song():
    """Resumes the currently paused song on Spotify."""
    try:
        spotify_player.resume_song()
    except Exception as e:
        return f"Error resuming song: {e}"
@tool
def get_current_time():
    """Returns the current time as a string."""
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

@tool
def set_reminder(reminder_time: str, message: str):
    """Sets a reminder for a specific time with a message.
    Args:
        reminder_time (str): The time to set the reminder for (in "YYYY-MM-DD HH:MM:SS" format).
        message (str): The message to display when the reminder is triggered.
    Returns:
        str: A confirmation message indicating that the reminder has been set, or an error message if the time format is incorrect.
    """
    try:
        reminder_datetime = datetime.strptime(reminder_time, "%Y-%m-%d %H:%M:%S")
        # Here you would add code to actually schedule the reminder using a task scheduler or similar
        return f"Reminder set for {reminder_datetime.strftime('%Y-%m-%d %H:%M:%S')}: {message}"
    except ValueError:
        return "Invalid time format. Please use 'YYYY-MM-DD HH:MM:SS'."





template = """You are a virtual assistant named Blair. You can perform various tasks such as writing files, playing songs on Spotify, getting the current time, setting reminders, and performing web searches.
            You should only use the tools provided to you when necessary and relevant to the user's query.
            Always provide clear and concise responses to the user's requests."""

# Lazy-loaded model — avoids the 5-30s startup delay until first use
_model = None


def get_model():
    """Return the shared model instance, creating it on first use."""
    global _model
    if _model is None:
        _model = ChatOllama(
            model="qwen3.5:2b",
            temperature=0.5,
            system_prompt=template,
        ).bind_tools([write_file, play_song, get_current_time, set_reminder, web_search, pause_song])
    return _model


async def listen_for_wake_and_command() -> str:
    """Listen for the 'azul' wake word, then return the command.

    If the command is spoken in the same breath as the wake word, the second
    recording is skipped — cutting latency by 1-4 seconds per interaction.
    """
    while True:
        call = await asyncio.to_thread(speech_to_text.transcribe_from_microphone, 2)
        print(f"{call}")
        if "azul" in call.lower():
            # Check if a command was spoken after the wake word in this recording
            remainder = call.lower().replace("azul", "", 1).strip()
            if remainder:
                print(f"{remainder}")
                return remainder
            # Wake word only — listen for the command in a fresh recording
            sentence = await asyncio.to_thread(speech_to_text.transcribe_from_microphone)
            print(f"{sentence}")
            if sentence and sentence != "wait_timeout":
                return sentence


async def dispatch_tool(tool_name: str, tool_args: dict):
    """Invoke the named tool in a thread so it doesn't block the event loop."""
    if tool_name == "write_file":
        return await asyncio.to_thread(write_file.invoke, tool_args)
    elif tool_name == "play_song":
        return await asyncio.to_thread(play_song.invoke, tool_args)
    elif tool_name == "get_current_time":
        return await asyncio.to_thread(get_current_time.invoke, tool_args)
    elif tool_name == "set_reminder":
        return await asyncio.to_thread(set_reminder.invoke, tool_args)
    else:
        print(f"Unknown tool: {tool_name}")


async def main():
    print("Listening... say 'azul' to activate.")
    model = get_model()
    while True:
        #sentence = await listen_for_wake_and_command()
        #sentence = input("Enter your command: ")
        #print(f"Query: {sentence}")
        sentence = input(">>> ")
        try:
            print("Awaiting Model")
            result = await asyncio.to_thread(model.invoke, sentence)
        except Exception as e:
            print(f"Error invoking model: {e}")
            continue

        if result.tool_calls:
            try:
                tool_call = result.tool_calls[0]
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})
                await dispatch_tool(tool_name, tool_args)
            except Exception as e:
                print(f"Tool error: {e}")

        print(result.tool_calls)

asyncio.run(main())