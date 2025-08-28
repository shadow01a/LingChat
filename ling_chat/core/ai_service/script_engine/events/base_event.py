from abc import ABC, abstractmethod
from ling_chat.core.ai_service.script_engine.type import GameContext

class BaseEvent(ABC):
    """事件基类"""
    
    def __init__(self, event_data: dict, game_context: GameContext):
        self.event_data = event_data
        self.game_context = game_context
    
    @abstractmethod
    async def execute(self):
        """执行事件"""
        pass
    
    @classmethod
    def can_handle(cls, event_type: str) -> bool:
        """判断是否能处理指定类型的事件"""
        return False