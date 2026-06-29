from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.voice import ModelsVoice


class CrudVoice:
    @staticmethod
    async def get_voice_by_code_crud_voice(db: AsyncSession, v_code: str):
        query = select(ModelsVoice).where(ModelsVoice.v_code == v_code)
        result = await db.execute(query)
        return result.scalar_one_or_none()