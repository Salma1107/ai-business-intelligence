

from fastapi import APIRouter, Depends

from backend.core.deps import get_current_user_email
from backend.models.schemas import (
    SQLAgentRequest,
    AnalyticsAgentRequest,
    ForecastAgentRequest,
    ReportAgentRequest,
)
from sql_agent import sql_agent
from analytics_agent import analytics_agent
from forecast_agent import forecast_agent
from report_agent import report_agent

router = APIRouter(prefix="/agents", tags=["Agents (accès direct)"])


@router.post("/sql")
def call_sql_agent(request: SQLAgentRequest, user_email: str = Depends(get_current_user_email)):
    return sql_agent(request.question)


@router.post("/analytics")
def call_analytics_agent(request: AnalyticsAgentRequest, user_email: str = Depends(get_current_user_email)):
    return analytics_agent(request.metric, request.context)


@router.post("/forecast")
def call_forecast_agent(request: ForecastAgentRequest, user_email: str = Depends(get_current_user_email)):
    return forecast_agent(request.horizon, request.segment)


@router.post("/report")
def call_report_agent(request: ReportAgentRequest, user_email: str = Depends(get_current_user_email)):
    return report_agent(request.results)