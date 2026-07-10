import httpx
import logging
from app.core.settings import settings
from app.ai.client.request import LLMRequest, SessionStateRequest
from app.ai.client.response import LLMResponse

logger = logging.getLogger(__name__)


async def call_llm_aiClient(
    se_id: str,
    query: str,
    fsm_state: str = None,
    order_type: str = None,
    order_item: dict = None,
    cart: list = None,
) -> LLMResponse:
    """AI 서버 LLM 엔드포인트 호출 → LLMResponse 반환"""

    request = LLMRequest(
        session=SessionStateRequest(
            se_id=se_id,
            fsm_state=fsm_state,
            order_type=order_type,
            order_item=order_item,
            cart=cart,
        ),
        query=query,
    )

    url = f"{settings.ai_server_url}/api/v1/llm"
    logger.info(f"AI 서버 호출 | url: {url} | se_id: {se_id} | query: {query}")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(url, json=request.model_dump())
            res.raise_for_status()
            result = LLMResponse(**res.json())
            logger.info(f"AI 서버 응답 완료 | events: {len(result.events)}개")
            return result

    except httpx.TimeoutException:
        logger.error(f"AI 서버 타임아웃 | url: {url}")
        raise

    except httpx.HTTPStatusError as e:
        logger.error(f"AI 서버 HTTP 오류: {e.response.status_code} | {e.response.text}")
        raise

    except Exception as e:
        logger.error(f"AI 서버 호출 오류: {str(e)}")
        raise