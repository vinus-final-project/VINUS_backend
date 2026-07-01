from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.voice import Voice as VoiceModel


class Voice:
    @staticmethod
    async def get_voice_by_code_crud_voice(db: AsyncSession, v_code: str):
        query = select(VoiceModel).where(VoiceModel.v_code == v_code)
        result = await db.execute(query)
        return result.scalar_one_or_none()