from ling_chat.core.ai_service.script_engine.events.base_event import BaseEvent
from ling_chat.core.messaging.broker import message_broker
from ling_chat.core.logger import logger
from ling_chat.core.schemas.response_models import ResponseFactory

class NarrationEvent(BaseEvent):
    """处理对话事件"""
    
    async def execute(self):
        text = self.event_data.get('text', '')
        
        logger.info(f"显示对话: 旁白Narration - {text}")
        
        # 在实际实现中，这里会更新游戏状态和UI
        self.game_context.dialogue.append({
            'character': 'narration',
            'text': text,
        })
        
        event_response = ResponseFactory.create_narration(text)
        await message_broker.publish("1", 
            event_response.model_dump()
        )
    
    @classmethod
    def can_handle(cls, event_type: str) -> bool:
        return event_type == 'narration'