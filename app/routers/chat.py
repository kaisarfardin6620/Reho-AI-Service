import asyncio
from typing import List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, Depends, HTTPException, Response
from app.utils.security import verify_token_ws, get_user_id_from_token
from app.db import queries as db_queries
from app.ai import prompt_builder
import openai
from app.core.config import settings
from loguru import logger
from app.utils.retry import retry_openai
from app.utils.metrics import track_openai_metrics, ACTIVE_USERS, add_active_user, remove_active_user

router = APIRouter(prefix="/chat", tags=["Chat"])
openai.api_key = settings.OPENAI_API_KEY

@retry_openai(max_retries=3)
@track_openai_metrics()
async def generate_and_save_title(user_id: str, conversation_id: str, first_message: str, websocket: WebSocket):
    logger.info(f"Skipping title generation for fixed conversation: {conversation_id}")
    return

@retry_openai(max_retries=3)
@track_openai_metrics()
async def stream_openai_response(messages_for_api: list):
    return openai.chat.completions.create(
        model="gpt-4o", 
        messages=messages_for_api, 
        stream=True
    )


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
    is_new_conversation = False 
    
    try:
        financial_summary = await db_queries.get_user_financial_summary(user_id) 
        personalized_system_prompt = prompt_builder.build_contextual_system_prompt(financial_summary)

        while True:
            message = await websocket.receive_text()
            
            await db_queries.save_chat_message(user_id, conversation_id, "user", message)
            
            history = await db_queries.get_conversation_history(conversation_id)

            messages_for_api = [{"role": "system", "content": personalized_system_prompt}, *history]
            
            stream = await stream_openai_response(messages_for_api) 
            
            full_reply = ""
            for chunk in stream:
                content = chunk.choices[0].delta.content or ""
                if content:
                    full_reply += content
                    await websocket.send_json({"type": "stream", "data": content})
            
            await websocket.send_json({"type": "status", "data": "done"})

            if full_reply:
                await db_queries.save_chat_message(
                    user_id, conversation_id, "assistant", full_reply
                )

    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {user_id}")
        remove_active_user(user_id)
    except Exception as e:
        logger.exception(f"An unexpected error occurred for user {user_id}: {e}")
        remove_active_user(user_id)
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
