from fastapi import Header, HTTPException, Depends

# Define a basic API key (in production, store securely)
API_KEY = "your-secure-api-key"

def verify_api_key(x_api_key: str = Header(...)):
    """
    Verifies that the API key sent in the header is valid.
    """
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail=" Invalid or missing API Key")
