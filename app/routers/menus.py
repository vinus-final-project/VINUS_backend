from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel
from app.db.database import get_db
from app.db.scheme.menus import SchemeMenusRead
from app.db.crud.menus import CrudMenus

router = APIRouter(prefix="/menus", tags=["Menus"])

# 명세서의 menus: Array 구조를 맞추기 위한 래퍼 스키마
class RoutersMenuListResponse(BaseModel):
    menus: List[SchemeMenusRead]

@router.get("", response_model=RoutersMenuListResponse, status_code=status.HTTP_200_OK)
async def read_menus(c_id: int, db: AsyncSession = Depends(get_db)):
    db_menus = await CrudMenus.get_menus_by_category(db, category_id=c_id)
    
    # 명세서 필드명 구조에 매칭되도록 변환 리스트 구축
    response_menus = []
    for m in db_menus:
        # sold_outs 테이블 데이터가 있으면 해당 sold 여부 확인 (기본값 False 가정)
        is_sold = m.sold_outs[0].soldout_sold if m.sold_outs else False
        
        response_menus.append({
            "m_id": m.menu_id,
            "c_id": m.category_id,
            "m_name": m.menu_name,
            "m_price": m.menu_price,
            "m_description": m.menu_description,
            "so_sold": is_sold
        })
        
    return {"menus": response_menus}