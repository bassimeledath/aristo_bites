import os
import asyncio
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from lumaai import AsyncLumaAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

MAX_ATTEMPTS = 30
POLL_INTERVAL = 5

client = AsyncLumaAI()

@retry(
    stop=stop_after_attempt(5),
    wait=wait_fixed(2),
    retry=retry_if_exception_type(Exception),
)
async def generate_luma_video(
    prompt: Optional[str] = None,
    start_image_url: Optional[str] = None,
    aspect_ratio: str = "16:9",
):
    # Start the generation process
    generation = await client.generations.create(
        prompt=prompt,
        keyframes={"frame0": {"type": "image", "url": start_image_url}}
        if start_image_url
        else {},
        aspect_ratio=aspect_ratio,
    )

    # Poll the generation to get progress logs
    await poll_generation(generation.id)

    # Once the generation is completed, retrieve the final status
    final_status = await client.generations.get(generation.id)
    print(f'final status {final_status}')
    if final_status.state == "completed":
        # Return the public URL
        return final_status.assets.video
    else:
        raise Exception(f"Generation failed with state: {final_status.state}")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
    retry=retry_if_exception_type(Exception),
)
async def extend_video(
    prompt: str,
    start_video_id: str,
    end_image_url: Optional[str] = None,
    aspect_ratio: str = "16:9",
):
    # Start the video extension process
    generation = await client.generations.create(
        prompt=prompt,
        keyframes={
            "frame0": {
                "type": "generation",
                "id": start_video_id
            },
            "frame1": {
                "type": "image",
                "url": end_image_url
            } if end_image_url else {}
        },
        aspect_ratio=aspect_ratio,
    )

    # Poll the generation to get progress logs
    await poll_generation(generation.id)

    # Once the generation is completed, retrieve the final status
    final_status = await client.generations.get(generation.id)
    print(f'final status {final_status}')
    if final_status.state == "completed":
        # Return the public URL
        return final_status.assets.video
    else:
        raise Exception(f"Video extension failed with state: {final_status.state}")

async def poll_generation(
    generation_id: str,
    max_attempts=MAX_ATTEMPTS,
    delay=POLL_INTERVAL,
):
    for attempt in range(max_attempts):
        print(
            f"Attempt {attempt + 1}/{max_attempts} to poll generation {generation_id}"
        )
        try:
            status = await client.generations.get(generation_id)
        except Exception as e:
            print(f"Error getting generation status: {e}")
            print(f"Waiting {delay} seconds before next attempt")
            await asyncio.sleep(delay)
            continue

        print(f"Current status: {status.state}")

        # You can add more detailed progress logs here if available
        if status.state == "completed":
            print(f"Generation {generation_id} completed successfully")
            return
        elif status.state == "failed":
            print(f"Generation {generation_id} failed")
            raise Exception(f"Generation failed: {status.failure_reason}")

        print(f"Waiting {delay} seconds before next attempt")
        await asyncio.sleep(delay)

    print(f"Max attempts ({max_attempts}) reached for generation {generation_id}")
    raise Exception("Max attempts reached")
