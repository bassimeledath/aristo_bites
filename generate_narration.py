import instructor
from anthropic import Anthropic
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

# Define the Pydantic model for the narration
class Narration(BaseModel):
    intro: str
    body: str

def generate_narration(user_query, context):
    # Initialize the Instructor client with Anthropic
    client = instructor.from_anthropic(Anthropic())

    prompt = f"""Given the
    user query: {user_query}
   
    and context: {context}

    Generate the following:
    1. "intro": A catchy one-sentence introduction that begins with "Welcome to AristoBites. In today's episode...".
    2. "body": You are a David Mitchell impersonator, famous British comedian and actor. Craft an engaging paragraph for a short-form philosophy video, structured as follows:
    - Start with a vivid unique analogy or example that introduces the main concept.
    - Present two interesting, lesser-known ideas that explore this concept.
    - Each idea should be explained in 3 sentences, using accessible language and concrete examples.
    - Conclude with a brief, witty observation that ties the ideas together.

    Remember:
    - Speak in the style of David Mitchell.
    - Aim for a total length of about 6-8 sentences.
    - Do not use puns.
    - Use the style of a YouTube science educator: informative yet entertaining. Avoid filler words and phrases.
    - Balance accessibility with depth; explain complex ideas using relatable analogies.
    - Keep the language simple. Avoid overly academic language; keep it engaging, but not too casual.
    - Introduce novel concepts that viewers are unlikely to be familiar with.
    """

    # Create the message with the defined system prompt and user prompt
    message = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=5000,
        temperature=0.9,
        system="You are a witty expert in creating engaging content for short-form philosophy videos.",
        messages=[
            {"role": "user", "content": prompt}
        ],
        response_model=Narration,
    )

    # The response is automatically parsed into the Narration model
    narration = message

    return narration

