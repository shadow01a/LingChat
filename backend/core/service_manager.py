from .ai_service import AIService
from .logger import logger
import os

class ServiceManager:
    _instance = None
    
    def __init__(self):
        self.ai_service = AIService()
        logger.info(f"🧠🧠🧠 ai_service 初始化，进程 ID: {os.getpid()}")
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

service_manager = ServiceManager.get_instance()