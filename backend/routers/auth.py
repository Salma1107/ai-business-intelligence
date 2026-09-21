from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from backend.db.connection import engine
from backend.models.schemas import UserRegister, UserLogin, TokenResponse
from backend.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: UserRegister):
    with engine.begin() as conn:
        existing = conn.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": user.email},
        ).fetchone()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un compte existe déjà avec cet email.",
            )
        conn.execute(
            text(
                "INSERT INTO users (email, hashed_password, full_name) "
                "VALUES (:email, :hashed_password, :full_name)"
            ),
            {
                "email": user.email,
                "hashed_password": hash_password(user.password),
                "full_name": user.full_name,
            },
        )

        return {"message": "Compte créé avec succès."}


@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin):
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT email, hashed_password FROM users WHERE email = :email"),
            {"email": credentials.email},
        ).fetchone()

        invalid_credentials = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect.",
        )

        if not row:
            raise invalid_credentials

        if not verify_password(credentials.password, row.hashed_password):
            raise invalid_credentials

        token = create_access_token({"sub": row.email})
        return TokenResponse(access_token=token)
