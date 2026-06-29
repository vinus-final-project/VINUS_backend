from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.crud.menus import Menus

class Menus:
    @staticmethod
    async def get_menus_list_by_category_services_menus(c_id: int, db: AsyncSession):
        # [메뉴 조회 API]
        db_menus = await Menus.get_menus_by_category_crud_menuCrud(db, c_id=c_id)
        
        response_menus = []
        for m in db_menus:
            # 모델 변수명 규칙(m_id, c_id, m_name, m_price) 적용
            response_menus.append({
                "m_id": m.m_id,
                "c_id": m.c_id,
                "m_name": m.m_name,
                "m_price": m.m_price
            })
            
        return {"menus": response_menus}

    @staticmethod
    async def get_single_menu_detail_services_menus(m_id: int, db: AsyncSession):
        # [메뉴 상세 조회 API]
        db_menu = await Menus.get_menu_detail_crud_menuCrud(db, m_id=m_id)
        
        if not db_menu:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="해당 메뉴를 찾을 수 없습니다."
            )
            
        # 1. 알레르기 배열 조립 (a_id, a_name 규칙 반영)
        allergies_list = []
        if hasattr(db_menu, "menu_allergies") and db_menu.menu_allergies:
            for ma in db_menu.menu_allergies:
                if ma.allergy:
                    allergies_list.append({
                        "a_id": ma.allergy.a_id,
                        "a_name": ma.allergy.a_name
                    })

        # 2. 성분 배열 조립 (i_id, i_name 규칙 반영)
        ingredients_list = []
        if hasattr(db_menu, "menu_ingredients") and db_menu.menu_ingredients:
            for mi in db_menu.menu_ingredients:
                if mi.ingredient:
                    ingredients_list.append({
                        "i_id": mi.ingredient.i_id,
                        "i_name": mi.ingredient.i_name
                    })

        # 3. 옵션 그룹 및 하위 옵션 배열 조립 (og_id, op_id 계열 규칙 전체 반영)
        option_groups_list = []
        if hasattr(db_menu, "option_groups") and db_menu.option_groups:
            for og in db_menu.option_groups:
                
                # 하위 옵션 리스트 생성
                options_list = []
                if hasattr(og, "options") and og.options:
                    for op in og.options:
                        options_list.append({
                            "op_id": op.op_id,
                            "op_name": op.op_name,
                            "op_price": op.op_price,
                            "og_id": op.og_id
                        })
                
                option_groups_list.append({
                    "og_id": og.og_id,
                    "og_name": og.og_name,
                    "og_required": og.og_required,
                    "og_min": og.og_min,
                    "og_max": og.og_max,
                    "options": options_list  # 내포된 Array 매칭
                })

        # 최종 Response 조립 (모두 소문자 두 글자 규칙으로 통일)
        return {
            "m_id": db_menu.m_id,
            "m_name": db_menu.m_name,
            "m_price": db_menu.m_price,
            "m_description": db_menu.m_description,
            "allergies": allergies_list,
            "ingredients": ingredients_list,
            "option_groups": option_groups_list
        }