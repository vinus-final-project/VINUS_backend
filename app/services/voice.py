from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud.voice import Voice as VoiceCrud          # 4번 줄


class Voice:
    @staticmethod
    async def get_voice_by_code_services_voice(v_code: str, db: AsyncSession):
        db_voice = await VoiceCrud.get_voice_by_code_crud_voice(db, v_code=v_code)

        if not db_voice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 음성 템플릿을 찾을 수 없습니다.",
            )

        return db_voice