from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.scheme.voice import VoiceRead
from app.services.voice import Voice

router = APIRouter(prefix="/voices", tags=["Voices"])


@router.get("/{v_code}", response_model=VoiceRead, status_code=status.HTTP_200_OK)
async def read_voice_routers_voice(v_code: str, db: AsyncSession = Depends(get_db)):
    return await Voice.get_voice_by_code_services_voice(db, v_code)