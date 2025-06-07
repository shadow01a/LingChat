from fastapi import APIRouter, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

router = APIRouter()

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
frontend_dir = os.path.join(root_dir, 'frontend', 'public')

# ✅ 自定义 StaticFiles（禁用缓存）
class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

# ✅ 托管所有静态资源（保持原有路径结构）
# 注意：这里改为返回 StaticFiles 实例，由上层 app.mount() 调用
def get_static_files():
    return NoCacheStaticFiles(directory=frontend_dir)

# ✅ 保持原有HTML路由
def get_file_response(file_path: str) -> FileResponse:
    response = FileResponse(file_path)
    response.headers.update({
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    })
    return response

@router.get("/")
async def index():
    return get_file_response(os.path.join(frontend_dir, "pages", "index.html"))

@router.get("/about")
async def about():
    return get_file_response(os.path.join(frontend_dir, "pages", "about.html"))