import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Configuration values (adjust as needed)
    # For simplicity, hardcoded values here:
    SSH_DEFAULT_PORT = 22
    JWT_SECRET = "supersecretjwtkey"  # Auth not implemented yet
    # You can expand this class as needed
    DEBUG = True

settings = Settings()
