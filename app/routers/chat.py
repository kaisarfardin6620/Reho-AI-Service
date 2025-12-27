import asyncio
import json
from typing import List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from app.utils.security import verify_token_ws
from app.db import queries as db_queries
from app.ai import prompt_builder
from openai import AsyncOpenAI
from app.core.config import settings
from loguru import logger
from app.utils.retry import retry_openai
from app.utils.metrics import track_openai_metrics, ACTIVE_USERS, add_active_user, remove_active_user

router = APIRouter(prefix="/chat", tags=["Chat"])

aclient = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


@retry_openai(max_retries=3)
@track_openai_metrics()
async def get_openai_full_response(messages_for_api: list):
    response = await aclient.chat.completions.create(
        model="gpt-4o",
        messages=messages_for_api,
        temperature=0.7
    )
    return response.choices[0].message.content


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    token = websocket.query_params.get("token")
    try:
        user_id = verify_token_ws(token)
        add_active_user(user_id)
    except ValueError as e:
        logger.error(f"WebSocket Authentication failed: {e}")
        await websocket.send_json({"error": f"Authentication failed: {e}"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    conversation_id = f"fixed_convo_{user_id}"

    try:
        financial_summary = await db_queries.get_user_financial_summary(user_id) 
        
        initial_history = await db_queries.get_conversation_history(conversation_id)

        if initial_history:
            await websocket.send_json({"type": "initial_history", "data": initial_history})
            
        else:
            user_name = financial_summary.get('name', 'there')
            welcome_message = f"Hello {user_name}! I'm Reho, your personal AI financial assistant. I see you're new here! You can start by asking me to analyze your financial condition or ask for tips to save money. How can I help you today? 😊"
            
            await websocket.send_json({"type": "full_response", "data": welcome_message})
            
            await db_queries.save_chat_message(user_id, conversation_id, "assistant", welcome_message)
            
            initial_history = [{"role": "assistant", "content": welcome_message}]
        
        personalized_system_prompt = prompt_builder.build_contextual_system_prompt(financial_summary)
        messages_for_api = [{"role": "system", "content": personalized_system_prompt}, *initial_history]

        while True:
            raw_data = await websocket.receive_text()
            
            try:
                user_data = json.loads(raw_data) 
                user_message = user_data.get("message", "").strip() 
            except json.JSONDecodeError:
                logger.warning(f"Received non-JSON message from client: {raw_data}")
                user_message = raw_data.strip()
            
            if not user_message:
                continue
            
            await db_queries.save_chat_message(user_id, conversation_id, "user", user_message)
            messages_for_api.append({"role": "user", "content": user_message})
            
            full_reply = await get_openai_full_response(messages_for_api)
            
            await websocket.send_json({"type": "full_response", "data": full_reply})
            await websocket.send_json({"type": "status", "data": "done"})
            
            await db_queries.save_chat_message(user_id, conversation_id, "assistant", full_reply)
            messages_for_api.append({"role": "assistant", "content": full_reply})

    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {user_id}")
        remove_active_user(user_id)

    except Exception as e:
        logger.exception(f"Unexpected error for user {user_id}: {e}")
        remove_active_user(user_id)
        try:
            await websocket.send_json({"error": f"Internal server error: {str(e)}"})
        except Exception:
            pass
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)