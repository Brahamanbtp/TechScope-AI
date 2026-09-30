import os

from fastapi import Depends, Header, HTTPException
from storage.user_repo import get_session

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


API_KEY = os.getenv("TECHSCOPE_API_KEY")

def verify_api_key(
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
):
    """
    Verifies that the API key sent in the header is valid.
    """
    if not API_KEY:
        if authorization and authorization.lower().startswith("bearer "):
            user = get_session(authorization[7:].strip())
            if user:
                return user
        raise HTTPException(status_code=503, detail="API authentication is not configured")
    if x_api_key == API_KEY:
        return {"username": "environment", "role": "admin"}
    if authorization and authorization.lower().startswith("bearer "):
        user = get_session(authorization[7:].strip())
        if user:
            return user
    raise HTTPException(status_code=403, detail="Invalid or missing API key")


def verify_admin(user=Depends(verify_api_key)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required")
    return user
