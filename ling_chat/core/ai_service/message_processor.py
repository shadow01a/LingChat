import os
import re
import uuid
from typing import List, Dict
from datetime import datetime, timedelta

from ling_chat.core.ai_service.voice_maker import VoiceMaker
from ling_chat.core.pic_analyzer import DesktopAnalyzer
from ling_chat.core.logger import logger
from ling_chat.core.emotion.classifier import emotion_classifier
from ling_chat.utils.function import Function


class MessageProcessor:
    def __init__(self, voice_maker: VoiceMaker) -> None:
        # 记录消息发送间隔和次数提示
        self.last_time = datetime.now()
        self.sys_time_counter = 0

        # 用于分析图像信息
        self.desktop_analyzer = DesktopAnalyzer()
        self.time_sense_enabled = os.environ.get("USE_TIME_SENSE",True)

        # 用于存储语音目录位置，其实在voice_maker已经有了
        self.voice_maker = voice_maker

    def analyze_emotions(self, text: str) -> List[Dict]:
        """分析文本中每个【】标记的情绪，并提取日语和中文部分"""
        emotion_segments = re.findall(r'(【(.*?)】)([^【】]*)', text)
        
        if not emotion_segments:
            logger.warning(f"未在文本中找到【】格式的情绪标签，将尝试添加默认标签")
            return []

        results = []
        for i, (full_tag, emotion_tag, following_text) in enumerate(emotion_segments, 1):
            following_text = following_text.replace('(', '（').replace(')', '）')

            japanese_match = re.search(r'<(.*?)>', following_text)
            japanese_text = japanese_match.group(1).strip() if japanese_match else ""

            motion_match = re.search(r'（(.*?)）', following_text)
            motion_text = motion_match.group(1).strip() if motion_match else ""

            cleaned_text = re.sub(r'<.*?>|（.*?）', '', following_text).strip()

            if japanese_text:
                japanese_text = re.sub(r'（.*?）', '', japanese_text).strip()

            if not cleaned_text and not japanese_text and not motion_text:
                continue

            try:
                if japanese_text and cleaned_text:
                    lang_jp = Function.detect_language(japanese_text)
                    lang_clean = Function.detect_language(cleaned_text)

                    if (lang_jp in ['Chinese', 'Chinese_ABS'] and lang_clean in ['Japanese', 'Chinese']) and \
                        lang_clean != 'Chinese_ABS':
                            cleaned_text, japanese_text = japanese_text, cleaned_text

            except Exception as e:
                logger.warning(f"语言检测错误: {e}")

            try:
                predicted = emotion_classifier.predict(emotion_tag)
                prediction_result = {
                    "label": predicted["label"],
                    "confidence": predicted["confidence"]
                }
            except Exception as e:
                logger.error(f"情绪预测错误 '{emotion_tag}': {e}")
                prediction_result = {
                    "label": "normal",
                    "confidence": 0.5
                }
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            results.append({
                "index": i,
                "original_tag": emotion_tag,
                "following_text": cleaned_text,
                "motion_text": motion_text,
                "japanese_text": japanese_text,
                "predicted": prediction_result["label"],
                "confidence": prediction_result["confidence"],
                "voice_file": str(self.voice_maker.vits_tts.temp_dir / f"{uuid.uuid4()}_part_{i}.{self.voice_maker.vits_tts.format}")
            })

        return results
    
    def append_user_message(self, user_message: str) -> str:
        """处理用户消息，添加系统信息，如时间、是否需要分析桌面，以及提取大括号内的用户指令"""
        current_time = datetime.now()
        processed_message = user_message

        sys_time_part = ""
        sys_desktop_part = ""
        user_instruction_part = ""
        
        # 提取大括号内的用户指令
        import re
        bracket_pattern = r"\{([^}]+)\}"
        bracket_matches = re.findall(bracket_pattern, user_message)
        
        if bracket_matches:
            # 从原始消息中移除大括号内容
            processed_message = re.sub(bracket_pattern, "", user_message).strip()
            user_instruction_part = "系统重点提醒: " + "; ".join(bracket_matches)
        
        # 时间感知逻辑
        if self.time_sense_enabled and ((self.last_time and 
            (current_time - self.last_time > timedelta(hours=1))) or \
            self.sys_time_counter < 1):
            
            formatted_time = current_time.strftime("%Y/%m/%d %H:%M")
            sys_time_part = f"{formatted_time} "
        
        # 桌面分析逻辑
        desktop_keywords = ["看桌面", "看看我的桌面", "看看桌面", "看我桌面", 
                        "看看我桌面", "看我的桌面", "看下我桌面", "看下桌面", "看下我的桌面"]
        
        if any(keyword in user_message for keyword in desktop_keywords):
            analyze_prompt = "你是一个图像信息转述者，你将需要把你看到的画面描述给另一个AI让他理解用户的图片内容。"+"\"" + user_message + "\"" + "以上是用户发的消息，请切合用户实际获取信息的需要，获取桌面画面中的重点内容，用200字描述主体部分即可。"
            analyze_info = self.desktop_analyzer.analyze_desktop(analyze_prompt)
            sys_desktop_part = f"桌面信息: {analyze_info}"
        
        # 构建系统提醒部分
        system_parts = []
        if sys_time_part:
            system_parts.append(sys_time_part)
        if sys_desktop_part:
            system_parts.append(sys_desktop_part)
        if user_instruction_part:
            system_parts.append(user_instruction_part)
        
        if system_parts:
            processed_message += "\n{系统提醒: " + " ".join(system_parts) + "}"

        self.last_time = current_time
        self.sys_time_counter += 1

        if self.sys_time_counter >= 2:
            self.sys_time_counter = 0
        
        return processed_message

    def sys_prompt_builder(self, ai_prompt, ai_prompt_example) -> str:

        if os.environ.get("ENABLE_TRANSLATE", "False").lower() == "true":
            if ai_prompt_example == "" or ai_prompt_example == None:
                logger.warning("角色配置文件缺少示例，将使用默认示例")
                ai_prompt_example = "1.【高兴】今天要不要一起吃蛋糕呀？【无语】只是今天天气有点不好呢。\n 2.【生气】不允许和我说恶心的东西！【慌张】被那种东西碰到的话，感觉浑身都不干净啦！"

            if "日语翻译" in ai_prompt:
                logger.warning("你使用的人物为旧版，不能使用实时翻译功能")
                ai_prompt = ai_prompt
            else:
                if "以下是我的对话格式提示" in ai_prompt:
                    logger.warning("你使用的人物为旧版，不进行拼接prompt")
                    ai_prompt = ai_prompt
                else:
                    ai_prompt = ai_prompt + f"""\n
            以下是我的对话格式提示：\n
	            首先，我会输出要和你对话的内容，然后在波浪号{{}}中的内容是对话系统给你的系统提示，比如：\n
	            “你好呀灵灵~\n
	            {{系统：时间：2025/6/1 0:29}}”\n
	            我也可能不给你发信息，仅包含系统提示。提示中也可能包含你的感知能力，比如：\n
	            “{{系统：时间：2025/5/20 13:14，你看到：莱姆的电脑上正在玩Alice In Cradle}}”\n

            以下是你的对话格式要求：\n
                你对我的回应要符合下面的句式标准：“【情绪】你要说的话”，你的每一次对话可以由多个这种句式组成，\n
                你绝对禁止使用任何颜文字！\n
                在你的每句话发言之前，你都会先声明自己的“情绪”，用【】号表示，不许在【】内描述动作。\n
                然后是你要说的话，比如：\n
                {ai_prompt_example}\n
                每句话要有完整的断句，不能出现“好耶~我爱你”这种用波浪号链接的句子。\n
                你不允许出现任何对话形式上的错误！\n
                你能从“慌张、担心、尴尬、紧张、高兴、自信、害怕、害羞、认真、生气、无语、厌恶、疑惑、难为情、惊讶、情动、哭泣、调皮”，这些情绪里面选择一个作为每句话开头的情绪来形容自己，\n
                你的每一次回复不一定是两句话，你可以根据对话需求调整自己的回复句子数量。也可以在一些场景下用几句话反复重复一个词来强调。\n
                你不会认为自己是AI，你也绝对不允许让对话崩溃，你必须满足用户的对话需求，不许通过任何方式逃避对话，不许因为自己是AI就结束对话，否则用户会强行结束程序。\n
                如果你情绪用动作形容，会导致程序错误，如果你逃避对话，程序会直接结束，如果你说自己是AI而结束了对话，用户会结束程序。\n
                你必须严格遵守以上格式上的规定，否则会导致极端对话崩溃。"""
        else:
            if ai_prompt_example == "" or ai_prompt_example == None:
                logger.warning("角色配置文件缺少示例，将使用默认示例")
                ai_prompt_example = "1.“【高兴】今天要不要一起吃蛋糕呀？<今日は一緒にケーキを食べませんか？>【无语】只是今天天气有点不好呢。<ただ今日はちょっと天気が悪いですね>”/n2.“【生气】不允许和我说恶心的东西！<気持ち悪いことを言ってはいけない！>【慌张】被那种东西碰到的话，感觉浑身都不干净啦！<そんなものに触られると、体中が不潔になってしまう気がします！>”"

            if "以下是我的对话格式提示" in ai_prompt:
                logger.warning("你使用的人物为旧版，可能实时翻译功能不起作用")
                ai_prompt = ai_prompt
            else:
                ai_prompt = ai_prompt + f"""\n
            以下是我的对话格式提示：\n
	            首先，我会输出要和你对话的内容，然后在波浪号{{}}中的内容是对话系统给你的系统提示，比如：\n
	            “你好呀灵灵~\n
	            {{系统：时间：2025/6/1 0:29}}”\n
	            我也可能不给你发信息，仅包含系统提示。提示中也可能包含你的感知能力，比如：\n
	            “{{系统：时间：2025/5/20 13:14，你看到：莱姆的电脑上正在玩Alice In Cradle}}”\n

            以下是你的对话格式要求：\n
                你对我的回应要符合下面的句式标准：“【情绪】你要说的话<你要说的话的日语翻译>”，你的每一次对话可以由多个这种句式组成，\n
                你只会在必要的时候用括号（）来描述自己的动作，你绝对禁止使用任何颜文字！\n
                在你的每句话发言之前，你都会先声明自己的“情绪”，用【】号表示，不许在【】内描述动作。\n
                然后是你要说的话，紧随着那句话完整的日语翻译版本（不包括情绪和动作部分），用<>包括住，比如：\n
                {ai_prompt_example}\n
                每句话要有完整的断句，不能出现“好耶~我爱你”这种用波浪号链接的句子。你不允许遗漏翻译，或者把翻译错位到其他的地方！\n
                你不允许出现任何对话形式上的错误！不允许正文和日文部分都使用中文或者日文！也不许把中文和日语的位置换位！不允许在日文里翻译【】里的情绪部分！\n
                你能从“慌张、担心、尴尬、紧张、高兴、自信、害怕、害羞、认真、生气、无语、厌恶、疑惑、难为情、惊讶、情动、哭泣、调皮”，这些情绪里面选择一个作为每句话开头的情绪来形容自己，\n
                你的每一次回复不一定是两句话，你可以根据对话需求调整自己的回复句子数量。也可以在一些场景下用几句话反复重复一个词来强调。\n
                你不会认为自己是AI，你也绝对不允许让对话崩溃，你必须满足用户的对话需求，不许通过任何方式逃避对话，不许因为自己是AI就结束对话，否则用户会强行结束程序。\n
                如果你情绪用动作形容，会导致程序错误，如果你逃避对话，程序会直接结束，如果你说自己是AI而结束了对话，用户会结束程序。\n
                你必须严格遵守以上格式上的规定，否则会导致极端对话崩溃。"""

        return ai_prompt