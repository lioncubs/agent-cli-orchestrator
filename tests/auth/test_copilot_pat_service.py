"""Tests for Copilot PAT service."""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from src.auth.copilot_pat_service import CopilotPATService
from src.auth.models import CopilotPATCreate, CopilotPATUpdate


@pytest.fixture
def pat_service():
    """Create PAT service instance for testing."""
    with patch('src.auth.copilot_pat_service.get_db_manager'):
        return CopilotPATService()


@pytest.fixture
def user_id():
    """Create test user ID."""
    return uuid4()


@pytest.mark.asyncio
async def test_hash_pat(pat_service):
    """Test PAT hashing."""
    pat = "ghp_test1234567890"
    hash1 = pat_service._hash_pat(pat)
    hash2 = pat_service._hash_pat(pat)
    
    # Same PAT should produce same hash
    assert hash1 == hash2
    
    # Different PAT should produce different hash
    hash3 = pat_service._hash_pat("ghp_different")
    assert hash1 != hash3


@pytest.mark.asyncio
async def test_validate_pat_with_github_success(pat_service):
    """Test successful PAT validation against GitHub."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"X-OAuth-Scopes": "copilot"}
        
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )
        
        result = await pat_service.validate_pat_with_github("ghp_valid")
        assert result is True


@pytest.mark.asyncio
async def test_validate_pat_with_github_failure(pat_service):
    """Test failed PAT validation against GitHub."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 401
        
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )
        
        result = await pat_service.validate_pat_with_github("ghp_invalid")
        assert result is False


@pytest.mark.asyncio
async def test_validate_pat_with_github_error(pat_service):
    """Test PAT validation with network error."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            side_effect=Exception("Network error")
        )
        
        result = await pat_service.validate_pat_with_github("ghp_error")
        assert result is False


def test_to_response(pat_service):
    """Test conversion of PAT model to response model."""
    from src.auth.models import CopilotPAT
    
    pat = CopilotPAT(
        id=uuid4(),
        user_id=uuid4(),
        pat_encrypted="encrypted_value",
        pat_hash="hash_value",
        label="Test PAT",
        scopes=["copilot"],
        created_at=datetime.now(timezone.utc),
        is_active=True,
        validation_failures=0
    )
    
    response = pat_service._to_response(pat)
    
    assert response.id == pat.id
    assert response.user_id == pat.user_id
    assert response.label == pat.label
    assert response.scopes == pat.scopes
    assert response.is_active == pat.is_active
    # Encrypted value should not be in response
    assert not hasattr(response, 'pat_encrypted')
    assert not hasattr(response, 'pat_hash')


def test_from_db_model(pat_service):
    """Test conversion from database model to response model."""
    from src.metrics.models import CopilotPAT as CopilotPATModel
    
    user_id = uuid4()
    pat_id = uuid4()
    
    db_pat = CopilotPATModel(
        id=str(pat_id),
        user_id=str(user_id),
        pat_encrypted="encrypted_value",
        pat_hash="hash_value",
        label="Test PAT",
        scopes="copilot",
        created_at=datetime.now(timezone.utc),
        is_active=1,
        validation_failures=0
    )
    
    response = pat_service._from_db_model(db_pat)
    
    assert response.id == pat_id
    assert response.user_id == user_id
    assert response.label == "Test PAT"
    assert response.scopes == ["copilot"]
    assert response.is_active is True
    assert response.validation_failures == 0


@pytest.mark.asyncio
async def test_encryption_decryption(pat_service):
    """Test PAT encryption and decryption."""
    original_pat = "ghp_test1234567890abcdef"
    
    # Encrypt
    encrypted = pat_service.encryption_service.encrypt(original_pat)
    assert encrypted != original_pat
    
    # Decrypt
    decrypted = pat_service.encryption_service.decrypt(encrypted)
    assert decrypted == original_pat


@pytest.mark.asyncio
async def test_create_pat_invalid_raises_error(pat_service, user_id):
    """Test that creating PAT with invalid token raises error."""
    with patch.object(pat_service, 'validate_pat_with_github', return_value=False):
        pat_create = CopilotPATCreate(
            pat="ghp_invalid",
            label="Invalid PAT"
        )
        
        with pytest.raises(ValueError, match="Invalid GitHub Copilot PAT"):
            await pat_service.create_pat(user_id, pat_create, validate=True)


def test_pat_create_model():
    """Test PAT creation model validation."""
    pat_create = CopilotPATCreate(
        pat="ghp_test1234567890",
        label="Test PAT",
        expires_at=datetime.now(timezone.utc) + timedelta(days=90)
    )
    
    assert pat_create.pat == "ghp_test1234567890"
    assert pat_create.label == "Test PAT"
    assert pat_create.expires_at is not None


def test_pat_update_model():
    """Test PAT update model validation."""
    pat_update = CopilotPATUpdate(
        label="Updated Label",
        is_active=False
    )
    
    assert pat_update.label == "Updated Label"
    assert pat_update.is_active is False


def test_pat_update_model_partial():
    """Test partial PAT update."""
    # Only update label
    pat_update = CopilotPATUpdate(label="New Label")
    assert pat_update.label == "New Label"
    assert pat_update.is_active is None
    
    # Only update status
    pat_update = CopilotPATUpdate(is_active=False)
    assert pat_update.label is None
    assert pat_update.is_active is False
