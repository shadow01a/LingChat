import os
from fastapi import APIRouter, Body, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from core.logger import logger
import shutil

router = APIRouter(prefix="/api/v1/chat/background", tags=["Chat Character"])

BACKGROUND_DIR = Path(os.path.join("game_data","backgrounds"))
ALLOWED_EXTENSIONS = {'.jpg', '.png', '.webp', '.bmp', '.svg', '.tif', '.gif'}

@router.get("/background_file/{background_file}")
async def get_specific_avatar(background_file: str):
    file_path = os.path.join("game_data", "backgrounds", background_file)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Background not found")
    
    return FileResponse(file_path)

@router.get("/list")
async def list_all_backgrounds():
    try:
        backgrounds_dir = os.path.join("game_data", "backgrounds")
        if not os.path.exists(backgrounds_dir):
            return {"data": [], "message": "背景图片的目录没有找到"}
        
        background_files = []
        for filename in os.listdir(backgrounds_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                file_path = os.path.join(backgrounds_dir, filename)
                stat = os.stat(file_path)
                
                title = os.path.splitext(filename)[0]
                
                background_files.append({
                    "image_path": filename,
                    "title": title,
                    "modified_time": stat.st_mtime
                })
        
        background_files.sort(key=lambda x: x["modified_time"], reverse=True)

        if not background_files:
            return {"data": [], "message": "背景图片一个都没找到"}

        return {"data": background_files}

    except Exception as e:
        logger.error(f"获取背景列表失败: {str(e)}")
        return JSONResponse(status_code=500, content={"message": "获取背景列表失败"})
    
@router.post("/upload")
async def upload_music(file: UploadFile, name: str = None):
    """
    上传一个背景图片文件到服务器
    """
    try:
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="无效文件类型")
        
        BACKGROUND_DIR.mkdir(parents=True, exist_ok=True)
        
        filename = name if name else file.filename
        save_path = BACKGROUND_DIR / filename
        
        with save_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return JSONResponse(
            status_code=200,
            content={"message": "背景图片上传成功"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"未能上传背景图片: {str(e)}")