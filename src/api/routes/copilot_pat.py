"""API routes for Copilot PAT management."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel

from src.auth.copilot_pat_service import CopilotPATService
from src.auth.models import (
    CopilotPATCreate,
    CopilotPATUpdate,
    CopilotPATResponse
)
from src.api.middleware.auth import get_current_user
from src.storage.encrypted import EncryptionService

router = APIRouter(prefix="/api/copilot/pats", tags=["Copilot PAT"])


# Dependency to get PAT service
def get_pat_service() -> CopilotPATService:
    """Get Copilot PAT service instance."""
    return CopilotPATService()


class ValidationResponse(BaseModel):
    """Response model for PAT validation."""
    is_valid: bool
    message: str


@router.post("", response_model=CopilotPATResponse, status_code=status.HTTP_201_CREATED)
async def create_pat(
    pat_create: CopilotPATCreate,
    validate: bool = True,
    current_user: dict = Depends(get_current_user),
    pat_service: CopilotPATService = Depends(get_pat_service)
) -> CopilotPATResponse:
    """
    Create a new Copilot PAT.
    
    Args:
        pat_create: PAT creation data
        validate: Whether to validate PAT against GitHub API
        current_user: Currently authenticated user
        pat_service: PAT service instance
        
    Returns:
        Created PAT (without encrypted value)
        
    Raises:
        HTTPException: If validation fails or creation error occurs
    """
    try:
        user_id = UUID(current_user["id"])
        pat = await pat_service.create_pat(user_id, pat_create, validate=validate)
        return pat
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create PAT: {str(e)}"
        )


@router.get("", response_model=List[CopilotPATResponse])
async def list_pats(
    include_inactive: bool = False,
    current_user: dict = Depends(get_current_user),
    pat_service: CopilotPATService = Depends(get_pat_service)
) -> List[CopilotPATResponse]:
    """
    List all PATs for the current user.
    
    Args:
        include_inactive: Whether to include inactive/revoked PATs
        current_user: Currently authenticated user
        pat_service: PAT service instance
        
    Returns:
        List of PATs
    """
    try:
        user_id = UUID(current_user["id"])
        pats = await pat_service.list_pats(user_id, include_inactive=include_inactive)
        return pats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list PATs: {str(e)}"
        )


@router.get("/{pat_id}", response_model=CopilotPATResponse)
async def get_pat(
    pat_id: UUID,
    current_user: dict = Depends(get_current_user),
    pat_service: CopilotPATService = Depends(get_pat_service)
) -> CopilotPATResponse:
    """
    Get a specific PAT by ID.
    
    Args:
        pat_id: PAT ID
        current_user: Currently authenticated user
        pat_service: PAT service instance
        
    Returns:
        PAT details
        
    Raises:
        HTTPException: If PAT not found
    """
    try:
        user_id = UUID(current_user["id"])
        pat = await pat_service.get_pat(pat_id, user_id)
        
        if not pat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"PAT {pat_id} not found"
            )
        
        return pat
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get PAT: {str(e)}"
        )


@router.put("/{pat_id}", response_model=CopilotPATResponse)
async def update_pat(
    pat_id: UUID,
    pat_update: CopilotPATUpdate,
    current_user: dict = Depends(get_current_user),
    pat_service: CopilotPATService = Depends(get_pat_service)
) -> CopilotPATResponse:
    """
    Update a PAT.
    
    Args:
        pat_id: PAT ID
        pat_update: Update data
        current_user: Currently authenticated user
        pat_service: PAT service instance
        
    Returns:
        Updated PAT
        
    Raises:
        HTTPException: If PAT not found
    """
    try:
        user_id = UUID(current_user["id"])
        pat = await pat_service.update_pat(pat_id, user_id, pat_update)
        
        if not pat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"PAT {pat_id} not found"
            )
        
        return pat
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update PAT: {str(e)}"
        )


@router.delete("/{pat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_pat(
    pat_id: UUID,
    reason: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    pat_service: CopilotPATService = Depends(get_pat_service)
):
    """
    Revoke a PAT.
    
    Args:
        pat_id: PAT ID
        reason: Reason for revocation
        current_user: Currently authenticated user
        pat_service: PAT service instance
        
    Raises:
        HTTPException: If PAT not found
    """
    try:
        user_id = UUID(current_user["id"])
        success = await pat_service.revoke_pat(pat_id, user_id, reason)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"PAT {pat_id} not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke PAT: {str(e)}"
        )


@router.post("/{pat_id}/validate", response_model=ValidationResponse)
async def validate_pat(
    pat_id: UUID,
    current_user: dict = Depends(get_current_user),
    pat_service: CopilotPATService = Depends(get_pat_service)
) -> ValidationResponse:
    """
    Validate a PAT against GitHub API.
    
    Args:
        pat_id: PAT ID
        current_user: Currently authenticated user
        pat_service: PAT service instance
        
    Returns:
        Validation result
        
    Raises:
        HTTPException: If PAT not found
    """
    try:
        user_id = UUID(current_user["id"])
        is_valid = await pat_service.validate_pat(pat_id, user_id)
        
        return ValidationResponse(
            is_valid=is_valid,
            message="PAT is valid" if is_valid else "PAT validation failed"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate PAT: {str(e)}"
        )


def init_copilot_pat_routes(app):
    """
    Initialize Copilot PAT routes.
    
    Args:
        app: FastAPI application instance
    """
    app.include_router(router)
