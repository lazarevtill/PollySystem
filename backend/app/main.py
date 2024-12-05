from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from app.core.config import settings
from app.plugins import load_plugins

app = FastAPI(title="PollySystem", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust to your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load all plugins dynamically
load_plugins(app)

@app.get("/health")
def health_check():
    return {"status": "healthy"}

logger.info("PollySystem backend started.")
