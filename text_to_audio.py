import os
import asyncio
import boto3
from botocore.config import Config
from elevenlabs.client import AsyncElevenLabs
import uuid

class ElevenLabsTTSModel:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY is not set")
        self.client = AsyncElevenLabs(api_key=self.api_key)
        self.model = "eleven_multilingual_v2" 
        self.voice = "Daniel"
        
        # R2 configuration
        self.account_id = os.getenv("R2_ACCOUNT_ID")
        self.access_key_id = os.getenv("R2_ACCESS_KEY_ID")
        self.secret_access_key = os.getenv("R2_SECRET_ACCESS_KEY")
        self.bucket_name = os.getenv("R2_BUCKET_NAME")
        self.public_bucket_url = os.getenv("R2_PUBLIC_BUCKET_URL")
        
        if not all([self.account_id, self.access_key_id, self.secret_access_key, self.bucket_name, self.public_bucket_url]):
            raise ValueError("R2 configuration is incomplete")
        
        self.r2_client = boto3.client('s3',
            endpoint_url=f'https://{self.account_id}.r2.cloudflarestorage.com',
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            config=Config(signature_version='s3v4'),
            region_name='auto'
        )

    async def generate_audio(self, script: str) -> bytes:
        audio_stream = await self.client.generate(
            text=script,
            voice=self.voice,
            model=self.model,
            stream=True,
            
        )
        
        audio_chunks = []
        async for chunk in audio_stream:
            audio_chunks.append(chunk)
        
        return b''.join(audio_chunks)

    def save_audio_to_r2(self, audio: bytes) -> str:
        file_key = f"{uuid.uuid4()}.mp3"
        
        self.r2_client.put_object(
            Bucket=self.bucket_name,
            Key=file_key,
            Body=audio,
            ContentType='audio/mpeg',
            ACL='public-read'  # Make sure the object is publicly readable
        )
        
        # Generate a public URL for the file using the r2.dev subdomain
        url = f"{self.public_bucket_url}/{file_key}"
        return url

    async def generate_and_save_audio(self, script: str) -> str:
        audio = await self.generate_audio(script)
        public_url = self.save_audio_to_r2(audio)
        return public_url

# Usage example
async def main():
    tts_model = ElevenLabsTTSModel()
    script = "Hello, this is a test audio file."
    public_url = await tts_model.generate_and_save_audio(script)
    print(f"Audio file saved. Public URL: {public_url}")

if __name__ == "__main__":
    asyncio.run(main())