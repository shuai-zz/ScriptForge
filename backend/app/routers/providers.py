"""LLM Provider CRUD endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import encrypt, mask_key
from app.database import get_db
from app.models.conversion import LLMProvider
from app.schemas.provider import (
    ProviderCreate,
    ProviderResponse,
    ProviderUpdate,
)

router = APIRouter(prefix="/api/projects/{project_id}/providers", tags=["providers"])


def _to_response(provider: LLMProvider) -> ProviderResponse:
    return ProviderResponse(
        id=str(provider.id),
        provider_id=provider.provider_id,
        label=provider.label,
        provider_type=provider.provider_type,
        model_name=provider.model_name,
        base_url=provider.base_url,
        api_key_masked=mask_key(
            provider.encrypted_api_key[:20] if len(provider.encrypted_api_key) > 20 else "***"
        ),
        assigned_stages=provider.assigned_stages,
        parameters=provider.parameters,
    )


@router.post("", response_model=ProviderResponse, status_code=201)
async def create_provider(
    project_id: uuid.UUID,
    data: ProviderCreate,
    db: AsyncSession = Depends(get_db),
) -> ProviderResponse:
    """Create a new LLM provider with encrypted API key."""
    provider = LLMProvider(
        project_id=project_id,
        provider_id=f"prov-{data.label.lower().replace(' ', '-')}"
        if not hasattr(data, "provider_id")
        else data.provider_id,
        label=data.label,
        provider_type=data.provider_type.value,
        model_name=data.model_name,
        base_url=data.base_url,
        encrypted_api_key=encrypt(data.api_key),
        assigned_stages=[s.value for s in data.assigned_stages],
        parameters=data.parameters.model_dump(),
    )
    db.add(provider)
    await db.commit()
    await db.refresh(provider)
    return _to_response(provider)


@router.get("", response_model=list[ProviderResponse])
async def list_providers(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[ProviderResponse]:
    """List all providers for a project (keys masked)."""
    result = await db.execute(
        select(LLMProvider).where(LLMProvider.project_id == project_id)
    )
    providers = result.scalars().all()
    return [_to_response(p) for p in providers]


@router.get("/{provider_id}", response_model=ProviderResponse)
async def get_provider(
    project_id: uuid.UUID,
    provider_id: str,
    db: AsyncSession = Depends(get_db),
) -> ProviderResponse:
    """Get a single provider by its business ID."""
    result = await db.execute(
        select(LLMProvider).where(
            LLMProvider.project_id == project_id,
            LLMProvider.provider_id == provider_id,
        )
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return _to_response(provider)


@router.put("/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    project_id: uuid.UUID,
    provider_id: str,
    data: ProviderUpdate,
    db: AsyncSession = Depends(get_db),
) -> ProviderResponse:
    """Update a provider. If api_key is provided, it will be re-encrypted."""
    result = await db.execute(
        select(LLMProvider).where(
            LLMProvider.project_id == project_id,
            LLMProvider.provider_id == provider_id,
        )
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    if data.label is not None:
        provider.label = data.label
    if data.provider_type is not None:
        provider.provider_type = data.provider_type.value
    if data.model_name is not None:
        provider.model_name = data.model_name
    if data.base_url is not None:
        provider.base_url = data.base_url
    if data.api_key is not None:
        provider.encrypted_api_key = encrypt(data.api_key)
    if data.assigned_stages is not None:
        provider.assigned_stages = [s.value for s in data.assigned_stages]
    if data.parameters is not None:
        provider.parameters = data.parameters.model_dump()

    await db.commit()
    await db.refresh(provider)
    return _to_response(provider)


@router.delete("/{provider_id}", status_code=204)
async def delete_provider(
    project_id: uuid.UUID,
    provider_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a provider."""
    result = await db.execute(
        select(LLMProvider).where(
            LLMProvider.project_id == project_id,
            LLMProvider.provider_id == provider_id,
        )
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    await db.delete(provider)
    await db.commit()
