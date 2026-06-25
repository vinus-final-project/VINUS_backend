from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.crud.menus import CrudMenus

class ServicesMenus:
    @staticmethod
    async def get_menu_list_by_category(c_id: int, db: AsyncSession):
        # [메뉴 조회 API 로직]
        db_menus = await CrudMenus.get_menus_by_category(db, category_id=c_id)
        
        response_menus = []
        for m in db_menus:
            # 명세서에서 m_description 필드가 제외되었으므로 깔끔하게 필요한 데이터만 정제
            response_menus.append({
                "m_id": m.menu_id,
                "c_id": m.category_id,
                "m_name": m.menu_name,
                "m_price": m.menu_price
            })
            
        return {"menus": response_menus}

    @staticmethod
    async def get_single_menu_detail(m_id: int, db: AsyncSession):
        # [메뉴 상세 조회 API 로직]
        db_menu = await CrudMenus.get_menu_detail(db, menu_id=m_id)
        
        if not db_menu:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="해당 메뉴를 찾을 수 없습니다."
            )
            
        # 1. 알레르기 배열 조립
        allergies_list = []
        if hasattr(db_menu, "menu_allergies") and db_menu.menu_allergies:
            for ma in db_menu.menu_allergies:
                if ma.allergy:
                    allergies_list.append({
                        "a_id": ma.allergy.allergy_id,
                        "a_name": ma.allergy.allergy_name
                    })

        # 2. 성분 배열 조립
        ingredients_list = []
        if hasattr(db_menu, "menu_ingredients") and db_menu.menu_ingredients:
            for mi in db_menu.menu_ingredients:
                if mi.ingredient:
                    ingredients_list.append({
                        "i_id": mi.ingredient.ingredient_id,
                        "i_name": mi.ingredient.ingredient_name
                    })

        # 3. 옵션 그룹 및 하위 옵션 배열 조립
        option_groups_list = []
        if hasattr(db_menu, "option_groups") and db_menu.option_groups:
            for og in db_menu.option_groups:
                # 하위 옵션 리스트 생성
                options_list = []
                if hasattr(og, "options") and og.options:
                    for op in og.options:
                        options_list.append({
                            "op_id": op.option_id,
                            "op_name": op.option_name,
                            "op_price": op.option_price,
                            "og_id": op.option_group_id
                        })
                
                option_groups_list.append({
                    "og_id": og.option_group_id,
                    "og_name": og.option_group_name,
                    "og_required": og.option_group_required,
                    "og_min": og.option_group_min,
                    "og_max": og.option_group_max,
                    "options": options_list  # 내포된 Array 매칭
                })

        # 명세서의 Response 필드와 완벽하게 1:1 매칭된 최종 결과물 리턴
        return {
            "m_id": db_menu.menu_id,
            "m_name": db_menu.menu_name,
            "m_price": db_menu.menu_price,
            "m_description": db_menu.menu_description,
            "allergies": allergies_list,
            "ingredients": ingredients_list,
            "option_groups": option_groups_list
        }