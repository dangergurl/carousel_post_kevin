import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
    FAL_KEY = os.getenv("FAL_KEY")  # For FAL.ai Gemini 2.5 Flash image generation
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # For Google Imagen 4.0 Ultra
    KIE_AI_API_KEY = os.getenv("KIE_AI_API_KEY")  # For kie.ai Flux Kontext (UGC-style product photography)
    
    # Service Configuration
    DEFAULT_IMAGE_SERVICE = os.getenv("DEFAULT_IMAGE_SERVICE", "dalle3")
    BACKUP_IMAGE_SERVICE = os.getenv("BACKUP_IMAGE_SERVICE", "replicate_flux")
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    
    # Directories
    OUTPUT_DIRECTORY = os.getenv("OUTPUT_DIRECTORY", "./output")
    TEMP_DIRECTORY = os.getenv("TEMP_DIRECTORY", "./temp")
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required_keys = [
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY", 
            "REPLICATE_API_TOKEN"
        ]
        
        missing_keys = []
        for key in required_keys:
            if not getattr(cls, key):
                missing_keys.append(key)
        
        if missing_keys:
            raise ValueError(f"Missing required API keys: {', '.join(missing_keys)}")
        
        # Create directories if they don't exist
        os.makedirs(cls.OUTPUT_DIRECTORY, exist_ok=True)
        os.makedirs(cls.TEMP_DIRECTORY, exist_ok=True)
        
        return True