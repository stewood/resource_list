"""
API Keys Configuration

This file contains API key configurations for the application.
In production, these should be set as environment variables.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenRouter API Key for AI Review functionality
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

# Fallback for development (remove in production)
if not OPENROUTER_API_KEY:
    print("Warning: OPENROUTER_API_KEY not found in environment variables")
    print("Please set OPENROUTER_API_KEY in your .env file or environment variables")
    print("You can get your API key from: https://openrouter.ai/keys")

