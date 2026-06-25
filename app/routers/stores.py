from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.scheme.stores import SchemeStoresRead
from app.db.crud.stores import CrudStores

router = APIRouter(prefix="/store", tags=["Stores"])

@router.get("", response_model=SchemeStoresRead, status_code=status.HTTP_200_OK)
async def read_store_info(db: AsyncSession = Depends(get_db)):
    db_store = await CrudStores.get_store_info(db)
    
    if not db_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="매장 정보가 존재하지 않습니다."
        )
        
    # 명세서가 요구하는 b_name을 하위 brand 관계선에서 추출하여 매핑 구조로 리턴
    return {
        "s_id": db_store.store_id,
        "s_name": db_store.store_name,
        "b_id": db_store.brand_id,
        "b_name": db_store.brand.brand_name if db_store.brand else "",
        "ad_id": db_store.admin_id
    }