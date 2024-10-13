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
def generate_image(prompt: str) -> str:
    try:
        output = replicate.run(
            "black-forest-labs/flux-schnell",
            input={
                "prompt": prompt,
                "go_fast": True,
                "megapixels": "1",
                "num_outputs": 1,
                "aspect_ratio": "16:9",
                "output_format": "png",
                "output_quality": 80,
                "num_inference_steps": 4,
            },
        )
        if not output:
            raise Exception("No output received from Replicate.")
        image_url = output[0]
    except Exception as e:
        raise Exception("Failed to generate image using Replicate.") from e

    return image_url
