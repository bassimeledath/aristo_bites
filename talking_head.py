import os
import replicate
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

load_dotenv()

# Ensure that the Replicate API token is set
if not os.getenv("REPLICATE_API_TOKEN"):
    raise EnvironmentError("REPLICATE_API_TOKEN is not set in the environment variables.")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
def talking_head(input_audio: str, audio_duration: int) -> str:
    try:
        input_params = {
            "face": "https://storage.cdn-luma.com/lit_lite_inference_v1.6-xl/dbe81771-52bc-40e7-b227-523f22d10b58/bbcbe7c8-e0e4-4938-832a-d17a6b1bd9fb_video0d12435cb38724cfaba3e01cbc071e934.mp4",# "https://storage.cdn-luma.com/lit_lite_inference_v1.6-xl/68c2c974-aa93-4330-981d-a664d5e0fdf3/64ef6f78-c41d-4407-9291-c8a4967d2cc8_video03f1515e784de4ec5af1d9831093ba434.mp4",
            "input_audio": input_audio,
            "audio_duration": audio_duration
        }
        output = replicate.run(
            "xiankgx/video-retalking:1e959997f54af5daa345d6c063f9abeef361029e730d4f57e876e2d5b31b5e9b",
            input=input_params
        )
        if not output:
            raise Exception("No output received from Replicate.")
        
    except Exception as e:
        raise Exception("Failed to generate video using Replicate.") from e

    return output
