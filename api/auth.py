import os

from fastapi import Header, HTTPException

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


API_KEY = os.getenv("TECHSCOPE_API_KEY")

def verify_api_key(x_api_key: str | None = Header(default=None)):
    """
    Verifies that the API key sent in the header is valid.
    """
    if not API_KEY:
        raise HTTPException(status_code=503, detail="API authentication is not configured")
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
