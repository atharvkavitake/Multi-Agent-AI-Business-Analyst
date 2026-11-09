"""
Business Query & Chat REST API Endpoints.

Handles natural language dataset queries executed safely via Agent 7 (Business Query Agent).
"""

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.agents.query_agent import BusinessQueryAgent
from backend.app.orchestration.orchestrator import AgentOrchestrator
from backend.app.schemas.agent import QueryAgentResult
from backend.app.services.data_service import DataService
from backend.app.utils.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/analysis", tags=["Business Query Chat"])
query_agent = BusinessQueryAgent()

# In-memory chat history: {analysis_id: [QueryAgentResult]}
_CHAT_HISTORY: Dict[str, List[QueryAgentResult]] = {}


class ChatRequest(BaseModel):
    question: str = Field(..., description="Natural language question about the dataset")


@router.post(
    "/{analysis_id}/chat",
    response_model=QueryAgentResult,
    summary="Query dataset with natural language",
    description=(
        "Converts user question into an Abstract Analytical Query Plan (AAQP), "
        "executes safe Pandas aggregations (zero arbitrary code execution), "
        "and returns factual text, evidence table, and chart configurations."
    ),
)
async def query_dataset(analysis_id: str, body: ChatRequest):
    """
    Handle natural language query for a specific analysis session.
    """
    state = AgentOrchestrator.get_analysis_state(analysis_id)
    df = DataService.get_dataset_dataframe(state.dataset_id)

    result = query_agent.run(
        query=body.question,
        payload=state.deterministic_payload,
        df=df,
    )

    if analysis_id not in _CHAT_HISTORY:
        _CHAT_HISTORY[analysis_id] = []
    _CHAT_HISTORY[analysis_id].append(result)

    return result


@router.get(
    "/{analysis_id}/chat/history",
    response_model=List[QueryAgentResult],
    summary="Get chat history",
    description="Returns previous queries and answers for an analysis session.",
)
async def get_chat_history(analysis_id: str):
    """
    Retrieve question/answer history.
    """
    return _CHAT_HISTORY.get(analysis_id, [])

