import os

from fastapi import APIRouter
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from pydantic import BaseModel

from services.auth_store import upsert_user
from utils.exception_handler import ExceptionBase

router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")


class GoogleSignInRequest(BaseModel):
    credential: str  # the ID token from Google Identity Services


@router.post("/auth/google")
async def google_sign_in(payload: GoogleSignInRequest):
    if not GOOGLE_CLIENT_ID:
        raise ExceptionBase(status_code=503, message="Google sign-in is not configured on this server yet.")

    try:
        claims = id_token.verify_oauth2_token(
            payload.credential, google_requests.Request(), GOOGLE_CLIENT_ID
        )
    except ValueError as e:
        raise ExceptionBase(status_code=401, message="Invalid Google sign-in token.") from e

    user_id = claims["sub"]
    try:
        user = upsert_user(
            user_id=user_id,
            email=claims.get("email"),
            name=claims.get("name"),
            picture=claims.get("picture"),
        )
    except Exception as e:
        raise ExceptionBase(status_code=503, message="Sign-in storage is unavailable right now.") from e

    return {
        "result": {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
        }
    }
