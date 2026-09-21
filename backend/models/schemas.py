

from pydantic import BaseModel, EmailStr, Field


#Authentification
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, description="8 caractères minimum")
    full_name: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


#Chat
class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class ChatResponse(BaseModel):
    answer: str

class SQLAgentRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class AnalyticsAgentRequest(BaseModel):
    metric: str = Field(min_length=1, max_length=200)
    context: str = ""


class ForecastAgentRequest(BaseModel):
    horizon: str = Field(min_length=1, max_length=100)
    segment: str = ""


class ReportAgentRequest(BaseModel):
    results: str = Field(min_length=1, max_length=5000)