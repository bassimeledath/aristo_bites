# transcription.py

import os
import whisper
from moviepy.editor import VideoFileClip
import subprocess

def generate_transcription(video_path):
    # Extract audio from the video
    video_clip = VideoFileClip(video_path)
    audio_path = video_path.replace('.mp4', '_audio.wav')
    video_clip.audio.write_audiofile(audio_path)
    
    # Transcribe audio using Whisper
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    
    # Write the transcription to an SRT file
    srt_path = video_path.replace('.mp4', '.srt')
    write_srt(result['segments'], srt_path)
    
    # Overlay subtitles onto the video using ffmpeg
    output_video = video_path.replace('.mp4', '_with_subtitles.mp4')
    cmd = [
        'ffmpeg', '-i', video_path, '-vf',
        f"subtitles='{srt_path}'",
        '-c:a', 'copy', output_video
    ]
    subprocess.run(cmd)
    
    # Clean up temporary files
    os.remove(audio_path)
    os.remove(srt_path)
    
    return output_video

def write_srt(segments, srt_path):
    with open(srt_path, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(segments):
            # SRT index
            f.write(f"{i+1}\n")
            # Start and end times
            start = format_timestamp(segment['start'])
            end = format_timestamp(segment['end'])
            f.write(f"{start} --> {end}\n")
            # Subtitle text
            f.write(f"{segment['text'].strip()}\n\n")

def format_timestamp(seconds):
    # Convert seconds to SRT timestamp format
    total_milliseconds = int(seconds * 1000)
    hours = total_milliseconds // (3600 * 1000)
    minutes = (total_milliseconds % (3600 * 1000)) // (60 * 1000)
    secs = (total_milliseconds % (60 * 1000)) // 1000
    milliseconds = total_milliseconds % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
