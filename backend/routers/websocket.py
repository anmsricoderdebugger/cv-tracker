import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.task_manager import get_progress

router = APIRouter(tags=["websocket"])


@router.websocket("/api/v1/ws/progress/{task_id}")
async def ws_progress(websocket: WebSocket, task_id: str):
    await websocket.accept()
    try:
        while True:
            progress = get_progress(task_id)
            if progress:
                await websocket.send_json(progress)
                if progress.get("status") == "completed":
                    break
            else:
                await websocket.send_json({"status": "unknown"})
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass
