# video_processing.py

import os
import asyncio
import math
import uuid
import aiohttp
import aiofiles
import subprocess
from typing import List
from pydantic import ValidationError

from talking_head import talking_head
from transcription import generate_transcription
from text_to_audio import ElevenLabsTTSModel
from text_to_image import generate_image
from img_to_video import generate_luma_video
from structured_output_model import extract_descriptions, ScriptAnalysis, SceneDescription

# R2 configuration (Assuming the same as in ElevenLabsTTSModel)
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
R2_PUBLIC_BUCKET_URL = os.getenv("R2_PUBLIC_BUCKET_URL")
if not all([R2_BUCKET_NAME, R2_PUBLIC_BUCKET_URL]):
    raise ValueError("R2_BUCKET_NAME and R2_PUBLIC_BUCKET_URL must be set in environment variables.")

async def generate_final_video(intro_script: str, main_script: str) -> str:
    """
    Generates the final video by concurrently processing the intro (talking head video)
    and the main video, combines them, adds transcriptions, uploads it to R2 storage,
    and returns the public URL.

    Args:
        intro_script (str): The script for the intro talking head video.
        main_script (str): The script for the main video.

    Returns:
        str: The R2 public URL of the final video.
    """
    # Step 1: Concurrently process the talking head video and main video
    print("Processing the talking head and main videos concurrently...")

    # Run both processes concurrently using asyncio.gather
    talking_head_task = asyncio.create_task(process_talking_head(intro_script))
    main_video_task = asyncio.create_task(process_main_video(main_script))

    # Await both tasks to complete
    talking_head_video_url, main_video_path = await asyncio.gather(
        talking_head_task, main_video_task
    )

    # Step 2: Download the talking head video
    talking_head_video_path = f"data/videos/talking_head_{uuid.uuid4()}.mp4"
    await download_file(talking_head_video_url, talking_head_video_path)
    print(f"Talking head video downloaded to {talking_head_video_path}")

    # main_video_path is already a local path returned by process_main_video
    print(f"Main video generated at {main_video_path}")

    # Step 3: Combine the two videos
    print("Combining the talking head and main videos...")
    combined_video_path = f"data/videos/combined_{uuid.uuid4()}.mp4"
    combine_videos([talking_head_video_path, main_video_path], combined_video_path)
    print(f"Combined video saved at {combined_video_path}")

    # Step 4: Generate transcription on the combined video
    print("Generating transcription and adding subtitles...")
    transcribed_video_path = generate_transcription(combined_video_path)
    print(f"Transcribed video saved at {transcribed_video_path}")

    # Step 5: Upload the final video to R2
    print("Uploading the final video to R2 storage...")
    final_video_url = await upload_file_to_r2(transcribed_video_path)
    print(f"Final video uploaded to R2: {final_video_url}")

    # Step 6: Clean up temporary files
    print("Cleaning up temporary files...")
    temp_files = [
        talking_head_video_path,
        main_video_path,
        combined_video_path,
        transcribed_video_path,
    ]
    for file in temp_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"Deleted temporary file: {file}")

    return final_video_url

# Ensure ffmpeg is installed
def check_ffmpeg_installed():
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        raise EnvironmentError("ffmpeg is not installed or not found in PATH.")

check_ffmpeg_installed()

# Helper function to get audio duration using ffmpeg
def get_audio_duration(file_path: str) -> float:
    """
    Get the duration of an audio file in seconds from a local file path.
    """
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            file_path,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    return float(result.stdout.strip())

# Helper function to download a file from a URL
async def download_file(url: str, dest_path: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise Exception(f"Failed to download file from {url}, status code {resp.status}")
            f = await aiofiles.open(dest_path, mode='wb')
            await f.write(await resp.read())
            await f.close()

# Helper function to upload a file to R2
async def upload_file_to_r2(file_path: str) -> str:
    """
    Upload a file to R2 and return its public URL.
    """
    import boto3
    from botocore.config import Config

    # R2 configuration
    account_id = os.getenv("R2_ACCOUNT_ID")
    access_key_id = os.getenv("R2_ACCESS_KEY_ID")
    secret_access_key = os.getenv("R2_SECRET_ACCESS_KEY")
    bucket_name = os.getenv("R2_BUCKET_NAME")
    public_bucket_url = os.getenv("R2_PUBLIC_BUCKET_URL")
    
    if not all([account_id, access_key_id, secret_access_key, bucket_name, public_bucket_url]):
        raise ValueError("R2 configuration is incomplete")

    r2_client = boto3.client('s3',
        endpoint_url=f'https://{account_id}.r2.cloudflarestorage.com',
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        config=Config(signature_version='s3v4'),
        region_name='auto'
    )

    file_key = f"{uuid.uuid4()}{os.path.splitext(file_path)[1]}"
    with open(file_path, 'rb') as f:
        r2_client.put_object(
            Bucket=bucket_name,
            Key=file_key,
            Body=f,
            ContentType='video/mp4',
            ACL='public-read'
        )
    
    url = f"{public_bucket_url}/{file_key}"
    return url

# Function to combine multiple videos into one using ffmpeg
def combine_videos(video_paths: List[str], output_path: str):
    """
    Combine multiple video files into a single video file.
    """
    with open("file_list.txt", "w") as f:
        for path in video_paths:
            f.write(f"file '{os.path.abspath(path)}'\n")
    
    subprocess.run(
        ["ffmpeg", "-f", "concat", "-safe", "0", "-i", "file_list.txt", "-c", "copy", output_path],
        check=True
    )
    os.remove("file_list.txt")

# Function to add audio to a video using ffmpeg
def add_audio_to_video(video_path: str, audio_path: str, output_path: str):
    """
    Add audio to a video file.
    """
    subprocess.run(
        [
            "ffmpeg",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-strict", "experimental",
            output_path
        ],
        check=True
    )

# Process Talking Head Function
async def process_talking_head(script: str) -> str:
    """
    Generates a talking head video from the given script.
    
    Args:
        script (str): The script text.
        
    Returns:
        str: R2 URL to the generated MP4 video.
    """
    # Initialize TTS model
    tts_model = ElevenLabsTTSModel()
    
    # Generate and save audio, get public URL
    audio_url = await tts_model.generate_and_save_audio(script)
    audio_duration = get_audio_duration(audio_url) + 0.50
    print(f'audio duration {audio_duration}')
    
    # Generate talking head video using the audio URL
    video_url = talking_head(audio_url, audio_duration)
    
    return video_url

# Process Main Video Function
async def process_main_video(script: str) -> str:
    """
    Generates a main video by creating scenes based on the script.
    
    Args:
        script (str): The script text.
        
    Returns:
        str: R2 URL to the combined MP4 video with audio.
    """
    # Initialize TTS model
    tts_model = ElevenLabsTTSModel()
    
    # Generate and save audio, get public URL
    audio_url = await tts_model.generate_and_save_audio(script)
    print(f'audio url {audio_url}')

    # Download the audio file
    audio_file_path = f"data/videos/temp_audio_{uuid.uuid4()}.mp3"
    await download_file(audio_url, audio_file_path)
    print(f"Audio file downloaded to {audio_file_path}")

    audio_duration = get_audio_duration(audio_file_path)
    print(f'audio duration {audio_duration}')
    
    # Calculate number of images
    num_images = math.ceil(audio_duration / 5)
    print(f'num images {num_images}')
    
    # Extract descriptions
    try:
        script_analysis: ScriptAnalysis = extract_descriptions(script, num_images)
        print(f'script analysis {script_analysis}')
    except ValidationError as ve:
        raise Exception(f"Script analysis failed: {ve}")
    
    # Make sure length of scenes is equal to num_images
    if len(script_analysis.scenes) != num_images:
        raise Exception(f"Number of scenes ({len(script_analysis.scenes)}) does not match the expected number of images ({num_images})")
    
    # Generate images and corresponding videos
    video_paths = []
    for i, scene in enumerate(script_analysis.scenes):
        print(f"Processing scene {i+1} of {len(script_analysis.scenes)}")
        # Generate image
        image_url = generate_image(scene.image_description)
        print(f"Image generated from scene {i+1}")
        
        # Download the image
        image_file_path = f"data/images/temp_image_{uuid.uuid4()}.png"
        await download_file(image_url, image_file_path)
        print(f"Image downloaded from scene {i+1}")
        
        # Generate video from image
        video_file_path = f"data/videos/temp_video_{uuid.uuid4()}.mp4"
        video_url = await generate_luma_video(
            prompt=scene.video_description,
            start_image_url=image_url,
            aspect_ratio="16:9" 
        )
        print(f"Video generated from scene {i+1}")
        
        # Download the video file
        await download_file(video_url, video_file_path)
        print(f"Video downloaded from scene {i+1}")
        
        video_paths.append(video_file_path)
    
    # Combine all video segments
    combined_video_path = f"data/videos/combined_{uuid.uuid4()}.mp4"
    combine_videos(video_paths, combined_video_path)
    
    # Add audio to the combined video
    final_video_path = f"data/final_video/final_{uuid.uuid4()}.mp4"
    add_audio_to_video(combined_video_path, audio_file_path, final_video_path)

    
    # Upload the final video to R2
    # final_video_url = await upload_file_to_r2(final_video_path)
    
    # Clean up temporary files
    # temp_files = [audio_file_path, combined_video_path, final_video_path] + video_paths
    # for file in temp_files:
    #     if os.path.exists(file):
    #         os.remove(file)
    
    return final_video_path




