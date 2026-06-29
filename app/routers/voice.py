from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.scheme.voice import SchemeVoiceRead
from app.services.voice import ServicesVoice

router = APIRouter(prefix="/voices", tags=["Voices"])


@router.get("/{v_code}", response_model=SchemeVoiceRead, status_code=status.HTTP_200_OK)
async def read_voice(v_code: str, db: AsyncSession = Depends(get_db)):
    return await ServicesVoice.get_voice_by_code(v_code, db)