"""Read-only workflow projection used by the guided workspace shell."""

from fastapi import APIRouter, HTTPException

from backend.domain.journey import WorkspaceJourney
from backend.services.workspace_journey import WorkspaceJourneyService

router = APIRouter(prefix="/api", tags=["workspace-journey"])


@router.get("/workspaces/{workspace_id}/journey", response_model=WorkspaceJourney)
def get_workspace_journey(workspace_id: str):
    try:
        return WorkspaceJourneyService().snapshot(workspace_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Workspace not found") from exc
