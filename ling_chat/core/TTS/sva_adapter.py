import aiohttp
from ling_chat.core.TTS.base_adapter import TTSBaseAdapter
from ling_chat.core.logger import logger


class SVAAdapter(TTSBaseAdapter):
    def __init__(self, api_url: str, speaker_id: int=4, 
                 audio_format: str="wav", lang: str="ja"):
        
        self.api_url = api_url
        self.params: dict[str, str|int|float] = {
            "id": speaker_id,
            "format": audio_format,   # 可用wav,ogg,silk,mp3,flac
            "lang": lang,    # 可用auto,mix,zh,ja
            "text": "",
            #"length": 1.0,   # 音频长度
            #"noise": 0.0,    # 噪声
            #"noisew": 0.0,   # SDP噪声
            #"segment_size": 0,  # 分段大小
            #"streaming": False
        }

    async def generate_voice(self, text: str) -> bytes :
        params = self.params
        params["text"] = text
        logger.debug("发送到SVA的请求:"+ str(params))

        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.api_url, 
                params=params
            ) as response:
                response.raise_for_status()
                return await response.read()

    def get_params(self):
        return self.params.copy()
