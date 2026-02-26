import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from backend.config import settings
from backend.dependencies import get_current_user, get_db
from backend.models.user import User
from backend.schemas.auth import LoginRequest, SignupRequest, TokenResponse, UserResponse
from backend.services.auth_service import authenticate, create_access_token, signup
from backend.utils.redis_client import delete, exists, setex

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# Google OAuth2 endpoints
_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
_OAUTH_STATE_TTL = 300  # seconds — state key expires after 5 minutes


# ---------------------------------------------------------------------------
# Email / password auth (existing)
# ---------------------------------------------------------------------------


@router.post("/signup", response_model=TokenResponse)
def signup_route(body: SignupRequest, db: Session = Depends(get_db)):
    try:
        user = signup(db, body.email, body.password, body.full_name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login_route(body: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate(db, body.email, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def me_route(current_user: User = Depends(get_current_user)):
    return current_user


# ---------------------------------------------------------------------------
# Google OAuth2 SSO
# ---------------------------------------------------------------------------


@router.get("/google/login")
def google_login():
    """Redirect the user to Google's OAuth2 consent screen.

    A cryptographically random state token is stored in Redis (5-minute TTL)
    to protect against CSRF attacks.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google SSO is not configured on this server.",
        )

    state = secrets.token_urlsafe(32)
    setex(f"oauth:state:{state}", _OAUTH_STATE_TTL, "pending")

    params = urlencode({
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    })
    return RedirectResponse(f"{_GOOGLE_AUTH_URL}?{params}")


@router.get("/google/callback")
def google_callback(code: str, state: str, db: Session = Depends(get_db)):
    """Handle Google OAuth2 callback.

    Validates the state token from Redis, exchanges the authorization code
    for an access token, fetches the user profile, upserts the user in the
    database, and redirects the frontend with a JWT token in the query string.
    """
    # Validate CSRF state
    state_key = f"oauth:state:{state}"
    if not exists(state_key):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OAuth state. Please try signing in again.",
        )
    delete(state_key)

    # Exchange authorization code for tokens
    token_resp = httpx.post(
        _GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        headers={"Accept": "application/json"},
        timeout=15,
    )
    if token_resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to exchange authorization code with Google.",
        )
    access_token = token_resp.json().get("access_token")

    # Fetch Google user profile
    userinfo_resp = httpx.get(
        _GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    if userinfo_resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch user info from Google.",
        )
    google_user = userinfo_resp.json()

    email: str = google_user["email"]
    google_id: str = google_user["sub"]
    full_name: str = google_user.get("name", email)
    picture_url: str | None = google_user.get("picture")

    # Upsert user — link Google account to existing email if present
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = User(
            email=email,
            google_id=google_id,
            full_name=full_name,
            profile_picture_url=picture_url,
            hashed_password=None,
        )
        db.add(user)
    else:
        user.google_id = google_id
        user.profile_picture_url = picture_url

    db.commit()
    db.refresh(user)

    jwt_token = create_access_token(user.id)
    # Redirect to Streamlit frontend with token in query param
    redirect_url = f"{settings.APP_BASE_URL}?token={jwt_token}"
    return RedirectResponse(redirect_url)
