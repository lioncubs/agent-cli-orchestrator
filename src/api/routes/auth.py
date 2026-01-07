"""Authentication API routes."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr

from src.auth.models import User, UserCreate, APIKey, APIKeyCreate
from src.auth.service import AuthService
from src.identity.models import GitCredential
from src.storage.yaml_backend import YAMLBackend
from src.storage.encrypted import EncryptionService

router = APIRouter(prefix="/auth", tags=["authentication"])

# Global instances (will be initialized in init_auth_routes)
_auth_service: Optional[AuthService] = None
_encryption_service: Optional[EncryptionService] = None


def init_auth_routes(storage_dir: str = "./data/auth"):
    """
    Initialize authentication routes with storage backend.
    
    Args:
        storage_dir: Directory for authentication data storage
    """
    global _auth_service, _encryption_service
    
    storage = YAMLBackend(storage_dir=storage_dir)
    _auth_service = AuthService(storage=storage)
    _encryption_service = EncryptionService()


def get_auth_service() -> AuthService:
    """Get the authentication service instance."""
    if _auth_service is None:
        raise HTTPException(
            status_code=500,
            detail="Authentication service not initialized"
        )
    return _auth_service


def get_encryption_service() -> EncryptionService:
    """Get the encryption service instance."""
    if _encryption_service is None:
        raise HTTPException(
            status_code=500,
            detail="Encryption service not initialized"
        )
    return _encryption_service


# Request/Response models
class LoginRequest(BaseModel):
    """Request model for user login."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Response model for user login."""
    user: User
    message: str = "Login successful"


class APIKeyResponse(BaseModel):
    """Response model for API key creation."""
    api_key: APIKey
    plaintext_key: str
    message: str = "API key created successfully. Save this key - it won't be shown again."


class APIKeyListItem(BaseModel):
    """List item for API keys (without sensitive data)."""
    id: UUID
    name: str
    scopes: List[str]
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]


class UserUpdateRequest(BaseModel):
    """Request model for updating user settings."""
    display_name: Optional[str] = None
    default_model: Optional[str] = None
    git_name: Optional[str] = None
    git_email: Optional[EmailStr] = None


class GitCredentialCreate(BaseModel):
    """Request model for creating a git credential."""
    name: str
    credential_type: str  # "ssh_key", "https_token", "oauth"
    credential_value: str
    remote_url: Optional[str] = None
    remote_name: Optional[str] = "origin"
    expires_at: Optional[datetime] = None


class GitCredentialResponse(BaseModel):
    """Response model for git credential (masked)."""
    id: UUID
    name: str
    credential_type: str
    remote_url: Optional[str]
    remote_name: Optional[str]
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]


# Routes

@router.post("/register", response_model=User)
async def register(
    user_create: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user.
    
    Args:
        user_create: User creation data
        auth_service: Authentication service
        
    Returns:
        Created user
        
    Raises:
        HTTPException: If user already exists or validation fails
    """
    try:
        user = await auth_service.create_user(user_create)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@router.post("/login", response_model=LoginResponse)
async def login(
    login_request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Login with email and password.
    
    Args:
        login_request: Login credentials
        auth_service: Authentication service
        
    Returns:
        User and success message
        
    Raises:
        HTTPException: If authentication fails
    """
    user = await auth_service.authenticate_user(
        login_request.email,
        login_request.password
    )
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    return LoginResponse(user=user)


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    api_key_create: APIKeyCreate,
    user_id: UUID,  # In production, get from auth token
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Create a new API key for a user.
    
    Args:
        api_key_create: API key creation data
        user_id: User ID (from auth context)
        auth_service: Authentication service
        
    Returns:
        Created API key with plaintext key
        
    Raises:
        HTTPException: If user not found or creation fails
    """
    try:
        # Verify user exists
        user = await auth_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        api_key, plaintext_key = await auth_service.create_api_key(
            user_id,
            api_key_create
        )
        
        return APIKeyResponse(
            api_key=api_key,
            plaintext_key=plaintext_key
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create API key: {str(e)}"
        )


@router.get("/api-keys", response_model=List[APIKeyListItem])
async def list_api_keys(
    user_id: UUID,  # In production, get from auth token
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    List all API keys for a user.
    
    Args:
        user_id: User ID (from auth context)
        auth_service: Authentication service
        
    Returns:
        List of API keys (without sensitive data)
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        api_keys = await auth_service.list_user_api_keys(user_id)
        
        # Convert to list items (without key_hash)
        return [
            APIKeyListItem(
                id=key.id,
                name=key.name,
                scopes=key.scopes,
                created_at=key.created_at,
                expires_at=key.expires_at,
                last_used_at=key.last_used_at
            )
            for key in api_keys
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list API keys: {str(e)}"
        )


@router.delete("/api-keys/{api_key_id}")
async def revoke_api_key(
    api_key_id: UUID,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Revoke an API key.
    
    Args:
        api_key_id: API key ID
        auth_service: Authentication service
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If key not found or revocation fails
    """
    success = await auth_service.revoke_api_key(api_key_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return {"status": "success", "message": "API key revoked"}


@router.get("/me", response_model=User)
async def get_current_user(
    user_id: UUID,  # In production, get from auth token
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Get current user information.
    
    Args:
        user_id: User ID (from auth context)
        auth_service: Authentication service
        
    Returns:
        Current user
        
    Raises:
        HTTPException: If user not found
    """
    user = await auth_service.get_user(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.put("/me", response_model=User)
async def update_current_user(
    update_request: UserUpdateRequest,
    user_id: UUID,  # In production, get from auth token
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Update current user settings.
    
    Args:
        update_request: Update data
        user_id: User ID (from auth context)
        auth_service: Authentication service
        
    Returns:
        Updated user
        
    Raises:
        HTTPException: If user not found or update fails
    """
    updates = {}
    
    if update_request.display_name is not None:
        updates["display_name"] = update_request.display_name
    
    if update_request.default_model is not None:
        updates["default_model"] = update_request.default_model
    
    if update_request.git_name is not None or update_request.git_email is not None:
        user = await auth_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        from src.session.models import GitIdentity
        git_identity = GitIdentity(
            name=update_request.git_name or user.git_identity.name,
            email=update_request.git_email or user.git_identity.email
        )
        updates["git_identity"] = git_identity
    
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    user = await auth_service.update_user(user_id, **updates)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.post("/credentials", response_model=GitCredentialResponse)
async def create_credential(
    credential_create: GitCredentialCreate,
    user_id: UUID,  # In production, get from auth token
    auth_service: AuthService = Depends(get_auth_service),
    encryption_service: EncryptionService = Depends(get_encryption_service)
):
    """
    Add a new Git credential.
    
    Args:
        credential_create: Credential data
        user_id: User ID (from auth context)
        auth_service: Authentication service
        encryption_service: Encryption service
        
    Returns:
        Created credential (masked)
        
    Raises:
        HTTPException: If user not found or creation fails
    """
    try:
        # Verify user exists
        user = await auth_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Encrypt credential value
        encrypted_value = encryption_service.encrypt(credential_create.credential_value)
        
        # Create credential
        credential = GitCredential(
            user_id=user_id,
            name=credential_create.name,
            credential_type=credential_create.credential_type,
            encrypted_value=encrypted_value,
            remote_url=credential_create.remote_url,
            remote_name=credential_create.remote_name,
            expires_at=credential_create.expires_at
        )
        
        # Store credential
        await auth_service.storage.set(
            f"credentials/{credential.id}",
            credential.model_dump()
        )
        
        # Index by user
        user_creds = await auth_service.storage.get(f"credentials/by_user/{user_id}")
        if user_creds is None:
            user_creds = []
        user_creds.append(str(credential.id))
        await auth_service.storage.set(f"credentials/by_user/{user_id}", user_creds)
        
        return GitCredentialResponse(
            id=credential.id,
            name=credential.name,
            credential_type=credential.credential_type,
            remote_url=credential.remote_url,
            remote_name=credential.remote_name,
            created_at=credential.created_at,
            last_used_at=credential.last_used_at,
            expires_at=credential.expires_at
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create credential: {str(e)}"
        )


@router.get("/credentials", response_model=List[GitCredentialResponse])
async def list_credentials(
    user_id: UUID,  # In production, get from auth token
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    List all Git credentials for a user (masked).
    
    Args:
        user_id: User ID (from auth context)
        auth_service: Authentication service
        
    Returns:
        List of credentials (without decrypted values)
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        user_creds = await auth_service.storage.get(f"credentials/by_user/{user_id}")
        if not user_creds:
            return []
        
        credentials = []
        for cred_id in user_creds:
            data = await auth_service.storage.get(f"credentials/{cred_id}")
            if data:
                credential = GitCredential(**data)
                credentials.append(GitCredentialResponse(
                    id=credential.id,
                    name=credential.name,
                    credential_type=credential.credential_type,
                    remote_url=credential.remote_url,
                    remote_name=credential.remote_name,
                    created_at=credential.created_at,
                    last_used_at=credential.last_used_at,
                    expires_at=credential.expires_at
                ))
        
        return credentials
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list credentials: {str(e)}"
        )


@router.delete("/credentials/{credential_id}")
async def delete_credential(
    credential_id: UUID,
    user_id: UUID,  # In production, get from auth token
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Remove a Git credential.
    
    Args:
        credential_id: Credential ID
        user_id: User ID (from auth context)
        auth_service: Authentication service
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If credential not found or deletion fails
    """
    try:
        # Get credential to verify ownership
        data = await auth_service.storage.get(f"credentials/{credential_id}")
        if not data:
            raise HTTPException(status_code=404, detail="Credential not found")
        
        credential = GitCredential(**data)
        if credential.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Remove from user's credential list
        user_creds = await auth_service.storage.get(f"credentials/by_user/{user_id}")
        if user_creds and str(credential_id) in user_creds:
            user_creds.remove(str(credential_id))
            await auth_service.storage.set(f"credentials/by_user/{user_id}", user_creds)
        
        # Delete credential
        success = await auth_service.storage.delete(f"credentials/{credential_id}")
        
        if not success:
            raise HTTPException(status_code=404, detail="Credential not found")
        
        return {"status": "success", "message": "Credential removed"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete credential: {str(e)}"
        )
