from typing import List, Tuple
from pydantic import BaseModel
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

class SceneDescription(BaseModel):
    image_description: str
    video_description: str

class ScriptAnalysis(BaseModel):
    scenes: List[SceneDescription]

def split_script(script: str, num_parts: int) -> List[str]:
    # Split the script into words
    words = script.split()
    num_words = len(words)
    words_per_part = num_words // num_parts

    parts = []
    for i in range(num_parts):
        start_index = i * words_per_part
        end_index = start_index + words_per_part if i != num_parts - 1 else num_words
        part = ' '.join(words[start_index:end_index])
        parts.append(part)
    return parts

def extract_descriptions(script: str, num_images: int):
    client = OpenAI()

    system_message = """
    You are an AI assistant specialized in analyzing scripts and extracting descriptions for images and videos.
    """

    # Split the script into num_images parts
    script_parts = split_script(script, num_images)

    scenes = []

    for idx, part in enumerate(script_parts):
        user_message = f"""
        Analyze the following part of a script and provide an image and a video description that corresponds sequentially to the content. The image description should be 1-2 sentences (about 15 words). The video description should describe a suitable action for the image description.
        Make sure the image and video description do not violate any ethical standards (even if the script content does so).

        Part {idx+1} of the script:

        {part}
        """

        completion = client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            response_format=SceneDescription
        )

        scene_description = completion.choices[0].message.parsed
        scenes.append(scene_description)

    # Return a ScriptAnalysis object with the scenes
    return ScriptAnalysis(scenes=scenes)
