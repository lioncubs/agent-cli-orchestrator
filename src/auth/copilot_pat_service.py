"""Service for managing GitHub Copilot Personal Access Tokens."""

import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

import httpx
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import (
    CopilotPAT,
    CopilotPATCreate,
    CopilotPATUpdate,
    CopilotPATResponse
)
from src.metrics.models import CopilotPAT as CopilotPATModel
from src.metrics.database import get_db_manager
from src.storage.encrypted import EncryptionService

logger = logging.getLogger(__name__)


class CopilotPATService:
    """Service for managing Copilot Personal Access Tokens."""
    
    def __init__(self, encryption_service: Optional[EncryptionService] = None):
        """
        Initialize the Copilot PAT service.
        
        Args:
            encryption_service: Service for encrypting PATs (optional, creates new if not provided)
        """
        self.encryption_service = encryption_service or EncryptionService()
        # Activity logging via metrics system
        self.db_manager = get_db_manager()
    
    def _hash_pat(self, pat: str) -> str:
        """
        Create SHA-256 hash of PAT for validation.
        
        Args:
            pat: Plaintext PAT
            
        Returns:
            SHA-256 hash of the PAT
        """
        return hashlib.sha256(pat.encode()).hexdigest()
    
    async def create_pat(
        self,
        user_id: UUID,
        pat_create: CopilotPATCreate,
        validate: bool = True
    ) -> CopilotPATResponse:
        """
        Create a new Copilot PAT.
        
        Args:
            user_id: User ID owning this PAT
            pat_create: PAT creation data
            validate: Whether to validate PAT against GitHub API
            
        Returns:
            Created PAT (without encrypted value)
            
        Raises:
            ValueError: If PAT validation fails
        """
        # Validate PAT if requested
        if validate:
            is_valid = await self.validate_pat_with_github(pat_create.pat)
            if not is_valid:
                raise ValueError("Invalid GitHub Copilot PAT")
        
        # Create PAT model
        pat_id = uuid4()
        pat_encrypted = self.encryption_service.encrypt(pat_create.pat)
        pat_hash = self._hash_pat(pat_create.pat)
        
        pat = CopilotPAT(
            id=pat_id,
            user_id=user_id,
            pat_encrypted=pat_encrypted,
            pat_hash=pat_hash,
            label=pat_create.label,
            scopes=["copilot"],
            expires_at=pat_create.expires_at,
            last_validated_at=datetime.now(timezone.utc) if validate else None
        )
        
        # Store in database
        async with self.db_manager.get_session() as session:
            db_pat = CopilotPATModel(
                id=str(pat.id),
                user_id=str(pat.user_id),
                pat_encrypted=pat.pat_encrypted,
                pat_hash=pat.pat_hash,
                label=pat.label,
                scopes=",".join(pat.scopes),
                created_at=pat.created_at,
                expires_at=pat.expires_at,
                last_validated_at=pat.last_validated_at,
                is_active=1 if pat.is_active else 0,
                validation_failures=pat.validation_failures
            )
            session.add(db_pat)
            await session.commit()
        
        # Audit log
        logger.info(f"PAT operation completed")
        
        logger.info(f"Created Copilot PAT {pat_id} for user {user_id}")
        
        return self._to_response(pat)
    
    async def get_pat(self, pat_id: UUID, user_id: UUID) -> Optional[CopilotPATResponse]:
        """
        Get a PAT by ID.
        
        Args:
            pat_id: PAT ID
            user_id: User ID (for authorization check)
            
        Returns:
            PAT if found and owned by user, None otherwise
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(CopilotPATModel).where(
                    CopilotPATModel.id == str(pat_id),
                    CopilotPATModel.user_id == str(user_id)
                )
            )
            db_pat = result.scalar_one_or_none()
            
            if not db_pat:
                return None
            
            return self._from_db_model(db_pat)
    
    async def list_pats(
        self,
        user_id: UUID,
        include_inactive: bool = False
    ) -> List[CopilotPATResponse]:
        """
        List all PATs for a user.
        
        Args:
            user_id: User ID
            include_inactive: Whether to include inactive/revoked PATs
            
        Returns:
            List of PATs
        """
        async with self.db_manager.get_session() as session:
            query = select(CopilotPATModel).where(
                CopilotPATModel.user_id == str(user_id)
            )
            
            if not include_inactive:
                query = query.where(CopilotPATModel.is_active == 1)
            
            query = query.order_by(CopilotPATModel.created_at.desc())
            
            result = await session.execute(query)
            db_pats = result.scalars().all()
            
            return [self._from_db_model(db_pat) for db_pat in db_pats]
    
    async def update_pat(
        self,
        pat_id: UUID,
        user_id: UUID,
        pat_update: CopilotPATUpdate
    ) -> Optional[CopilotPATResponse]:
        """
        Update a PAT.
        
        Args:
            pat_id: PAT ID
            user_id: User ID (for authorization check)
            pat_update: Update data
            
        Returns:
            Updated PAT if found and owned by user, None otherwise
        """
        async with self.db_manager.get_session() as session:
            # Build update dict
            update_data = {}
            if pat_update.label is not None:
                update_data["label"] = pat_update.label
            if pat_update.is_active is not None:
                update_data["is_active"] = 1 if pat_update.is_active else 0
            
            if not update_data:
                # Nothing to update
                return await self.get_pat(pat_id, user_id)
            
            # Update
            result = await session.execute(
                update(CopilotPATModel)
                .where(
                    CopilotPATModel.id == str(pat_id),
                    CopilotPATModel.user_id == str(user_id)
                )
                .values(**update_data)
            )
            await session.commit()
            
            if result.rowcount == 0:
                return None
            
            # Audit log
            logger.info(f"PAT operation completed")
            
            return await self.get_pat(pat_id, user_id)
    
    async def revoke_pat(
        self,
        pat_id: UUID,
        user_id: UUID,
        reason: Optional[str] = None
    ) -> bool:
        """
        Revoke a PAT.
        
        Args:
            pat_id: PAT ID
            user_id: User ID (for authorization check)
            reason: Reason for revocation
            
        Returns:
            True if revoked, False if not found
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                update(CopilotPATModel)
                .where(
                    CopilotPATModel.id == str(pat_id),
                    CopilotPATModel.user_id == str(user_id)
                )
                .values(
                    is_active=0,
                    revoked_at=datetime.now(timezone.utc),
                    revoked_reason=reason or "User revoked"
                )
            )
            await session.commit()
            
            if result.rowcount == 0:
                return False
            
            # Audit log
            logger.info(f"PAT operation completed")
            
            logger.info(f"Revoked Copilot PAT {pat_id} for user {user_id}")
            
            return True
    
    async def delete_pat(self, pat_id: UUID, user_id: UUID) -> bool:
        """
        Permanently delete a PAT.
        
        Args:
            pat_id: PAT ID
            user_id: User ID (for authorization check)
            
        Returns:
            True if deleted, False if not found
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                delete(CopilotPATModel).where(
                    CopilotPATModel.id == str(pat_id),
                    CopilotPATModel.user_id == str(user_id)
                )
            )
            await session.commit()
            
            if result.rowcount == 0:
                return False
            
            # Audit log
            logger.info(f"PAT operation completed")
            
            logger.info(f"Deleted Copilot PAT {pat_id} for user {user_id}")
            
            return True
    
    async def get_decrypted_pat(self, pat_id: UUID, user_id: UUID) -> Optional[str]:
        """
        Get decrypted PAT value.
        
        Args:
            pat_id: PAT ID
            user_id: User ID (for authorization check)
            
        Returns:
            Decrypted PAT if found and active, None otherwise
        """
        async with self.db_manager.get_session() as session:
            result = await session.execute(
                select(CopilotPATModel).where(
                    CopilotPATModel.id == str(pat_id),
                    CopilotPATModel.user_id == str(user_id),
                    CopilotPATModel.is_active == 1
                )
            )
            db_pat = result.scalar_one_or_none()
            
            if not db_pat:
                return None
            
            # Update last used timestamp
            await session.execute(
                update(CopilotPATModel)
                .where(CopilotPATModel.id == str(pat_id))
                .values(last_used_at=datetime.now(timezone.utc))
            )
            await session.commit()
            
            try:
                return self.encryption_service.decrypt(db_pat.pat_encrypted)
            except Exception as e:
                logger.error(f"Failed to decrypt PAT {pat_id}: {e}")
                return None
    
    async def validate_pat_with_github(self, pat: str) -> bool:
        """
        Validate PAT against GitHub API.
        
        Args:
            pat: Plaintext PAT
            
        Returns:
            True if valid, False otherwise
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.github.com/user",
                    headers={
                        "Authorization": f"token {pat}",
                        "Accept": "application/vnd.github.v3+json"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    # Check if PAT has copilot access
                    scopes = response.headers.get("X-OAuth-Scopes", "")
                    logger.info(f"GitHub PAT validation successful. Scopes: {scopes}")
                    return True
                else:
                    logger.warning(f"GitHub PAT validation failed: {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"Error validating PAT with GitHub: {e}")
            return False
    
    async def validate_pat(self, pat_id: UUID, user_id: UUID) -> bool:
        """
        Validate an existing PAT against GitHub API.
        
        Args:
            pat_id: PAT ID
            user_id: User ID (for authorization check)
            
        Returns:
            True if valid, False otherwise
        """
        # Get decrypted PAT
        pat = await self.get_decrypted_pat(pat_id, user_id)
        if not pat:
            return False
        
        # Validate with GitHub
        is_valid = await self.validate_pat_with_github(pat)
        
        # Update validation status
        async with self.db_manager.get_session() as session:
            if is_valid:
                await session.execute(
                    update(CopilotPATModel)
                    .where(CopilotPATModel.id == str(pat_id))
                    .values(
                        last_validated_at=datetime.now(timezone.utc),
                        validation_failures=0
                    )
                )
            else:
                # Increment failure counter
                result = await session.execute(
                    select(CopilotPATModel).where(CopilotPATModel.id == str(pat_id))
                )
                db_pat = result.scalar_one_or_none()
                if db_pat:
                    new_failures = db_pat.validation_failures + 1
                    # Deactivate after 3 consecutive failures
                    should_deactivate = new_failures >= 3
                    
                    await session.execute(
                        update(CopilotPATModel)
                        .where(CopilotPATModel.id == str(pat_id))
                        .values(
                            validation_failures=new_failures,
                            is_active=0 if should_deactivate else db_pat.is_active
                        )
                    )
            
            await session.commit()
        
        # Audit log
        logger.info(f"PAT operation completed")
        
        return is_valid
    
    def _to_response(self, pat: CopilotPAT) -> CopilotPATResponse:
        """Convert CopilotPAT to response model."""
        return CopilotPATResponse(
            id=pat.id,
            user_id=pat.user_id,
            label=pat.label,
            scopes=pat.scopes,
            created_at=pat.created_at,
            expires_at=pat.expires_at,
            last_used_at=pat.last_used_at,
            last_validated_at=pat.last_validated_at,
            is_active=pat.is_active,
            validation_failures=pat.validation_failures,
            revoked_at=pat.revoked_at,
            revoked_reason=pat.revoked_reason
        )
    
    def _from_db_model(self, db_pat: CopilotPATModel) -> CopilotPATResponse:
        """Convert database model to response model."""
        return CopilotPATResponse(
            id=UUID(db_pat.id),
            user_id=UUID(db_pat.user_id),
            label=db_pat.label,
            scopes=db_pat.scopes.split(",") if db_pat.scopes else ["copilot"],
            created_at=db_pat.created_at,
            expires_at=db_pat.expires_at,
            last_used_at=db_pat.last_used_at,
            last_validated_at=db_pat.last_validated_at,
            is_active=bool(db_pat.is_active),
            validation_failures=db_pat.validation_failures,
            revoked_at=db_pat.revoked_at,
            revoked_reason=db_pat.revoked_reason
        )
