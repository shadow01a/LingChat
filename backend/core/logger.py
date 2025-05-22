# logger.py
import logging
import sys
import time
import threading
from datetime import datetime
import os
import re  # Import re for ANSI stripping
import itertools
import traceback
from typing import Optional, Dict, List, Any, Union, Callable

# 日志配置
ENABLE_FILE_LOGGING = True  # 是否启用文件日志记录
LOG_FILE_DIRECTORY = "run_logs"  # 日志文件存储的相对目录

# 注意，若环境变量DEBUG_MODE = True/false时，会覆盖LOG_FILE_LEVEL的设置
LOG_FILE_LEVEL = logging.DEBUG  # 可以设置为 logging.DEBUG，logging.INFO, logging.WARNING, logging.ERROR

# 控制台时间戳显示开关，可通过环境变量 CONSOLE_SHOW_TIMESTAMP 控制
# 获取环境变量的值，默认为true
def get_console_timestamp_setting():
    """获取控制台时间戳显示设置"""
    console_timestamp_env = os.environ.get("CONSOLE_SHOW_TIMESTAMP", "false")
    # 调试时可取消注释下行
    # print(f"CONSOLE_SHOW_TIMESTAMP环境变量值: '{console_timestamp_env}'")
    return console_timestamp_env.lower() == "true"

# 初始化默认设置
CONSOLE_SHOW_TIMESTAMP = get_console_timestamp_setting()
# print(f"初始CONSOLE_SHOW_TIMESTAMP解析后的值: {CONSOLE_SHOW_TIMESTAMP}")

ANIMATION_STYLES = {
    'braille': ['⢿', '⣻', '⣽', '⣾', '⣷', '⣯', '⣟', '⡿'],
    'spinner': ['-', '\\', '|', '/'],
    'dots': ['.  ', '.. ', '...', ' ..', '  .', '   '],
    'arrows': ['←', '↖', '↑', '↗', '→', '↘', '↓', '↙'],
    'moon': ['🌑', '🌒', '🌓', '🌔', '🌕', '🌖', '🌗', '🌘'],
    'clock': ['🕛', '🕐', '🕑', '🕒', '🕓', '🕔', '🕕', '🕖', '🕗', '🕘', '🕙', '🕚'],
    'directional_arrows_unicode': ['⬆️', '↗️', '➡️', '↘️', '⬇️', '↙️', '⬅️', '↖️'],
    'traffic_lights': ['🔴', '🟡', '🟢'],
    'growth_emoji': ['🌱', '🌿', '🌳'],
    'weather_icons': ['☀️', '☁️', '🌧️', '⚡️'],
    'heartbeat': ['♡', '♥'],
}

_ansi_escape_regex = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def _strip_ansi_codes(text):
    """Removes ANSI escape codes from a string."""
    return _ansi_escape_regex.sub('', text)

sys.stderr.flush()

def wcswidth(s):
    """回退 wcswidth, 将非 ASCII 字符视为宽度2。应在剥离ANSI码后使用。"""
    if not isinstance(s, str):
        return len(s) if s else 0
    length = 0
    for char_ in s:  # Assumes s is already stripped of ANSI codes
        if ord(char_) < 128:
            length += 1
        else:
            length += 2
    return length

class TermColors:
    GREY = '\033[90m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    WHITE = '\033[97m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    LIGHT_BLUE = '\033[94m'  # Actually same as BLUE in this list, but kept for intent
    ORANGE = '\033[38;5;208m'

_logger = None
_animation_thread = None
_stop_animation_event = threading.Event()

_is_animating = False
_current_animation_line_width = 0
_animation_state_lock = threading.Lock()

DEFAULT_ANIMATION_STYLE_KEY = 'braille'
DEFAULT_ANIMATION_COLOR = TermColors.WHITE  # Default color for animation if not specified

class AnimationAwareStreamHandler(logging.StreamHandler):
    def emit(self, record):
        global _is_animating, _current_animation_line_width, _animation_state_lock

        if hasattr(record, 'is_animation_control') and record.is_animation_control:
            super().emit(record)
            return

        current_animation_active_locally = False
        current_width_to_clear_locally = 0

        with _animation_state_lock:
            current_animation_active_locally = _is_animating
            current_width_to_clear_locally = _current_animation_line_width

        if current_animation_active_locally and current_width_to_clear_locally > 0:
            self.acquire()
            try:
                self.flush()
                # Ensure the full line is cleared, then cursor to start
                self.stream.write("\r" + " " * current_width_to_clear_locally + "\r")
                self.stream.flush()
            finally:
                self.release()

        super().emit(record)

class ColoredFormatter(logging.Formatter):
    DATE_FORMAT = "%Y-%m-%d-%H:%M:%S"

    def __init__(self, show_timestamp=None):
        super().__init__(datefmt=self.DATE_FORMAT)
        # 如果未指定，则使用全局设置
        self.show_timestamp = CONSOLE_SHOW_TIMESTAMP if show_timestamp is None else show_timestamp

    def format(self, record):
        if hasattr(record, 'is_animation_control') and record.is_animation_control:
            return record.getMessage()

        timestamp_part = ""
        if self.show_timestamp:
            timestamp_str = self.formatTime(record, self.DATE_FORMAT)
            timestamp_part = f"{timestamp_str} "

        message_content = record.getMessage()
        level_name = record.levelname
        level_prefix_text = f"[{level_name}]: "

        if record.levelno == logging.DEBUG:
            return f"{TermColors.GREY}{timestamp_part}{level_prefix_text}{message_content}{TermColors.RESET}"

        level_color = ""
        if record.levelno == logging.INFO:
            level_color = TermColors.GREEN
        elif record.levelno == logging.WARNING:
            level_color = TermColors.YELLOW
        elif record.levelno == logging.ERROR:
            level_color = TermColors.RED

        colored_level_prefix = f"{level_color}{level_prefix_text}{TermColors.RESET}"
        return f"{timestamp_part}{colored_level_prefix}{message_content}"


def _animate(message="Loading", animation_chars=None, color_code=DEFAULT_ANIMATION_COLOR):
    global _is_animating, _current_animation_line_width, _animation_state_lock, _stop_animation_event

    if animation_chars is None:
        animation_chars = ANIMATION_STYLES[DEFAULT_ANIMATION_STYLE_KEY]

    idx = 0
    last_char_for_clear = animation_chars[0]

    while not _stop_animation_event.is_set():
        char = animation_chars[idx % len(animation_chars)]
        last_char_for_clear = char

        full_animation_line_with_ansi = f"{color_code}{message} {char}{TermColors.RESET} "

        stripped_line_for_width = _strip_ansi_codes(full_animation_line_with_ansi)
        current_visible_width = wcswidth(stripped_line_for_width)

        with _animation_state_lock:
            _current_animation_line_width = current_visible_width

        sys.stdout.write(f"\r{full_animation_line_with_ansi}")
        sys.stdout.flush()

        idx += 1
        time.sleep(0.12)

    final_animation_line_to_clear_ansi = f"{color_code}{message} {last_char_for_clear}{TermColors.RESET} "
    stripped_final_line = _strip_ansi_codes(final_animation_line_to_clear_ansi)
    width_to_clear = wcswidth(stripped_final_line)

    sys.stdout.write("\r" + " " * width_to_clear + "\r")
    sys.stdout.flush()

    with _animation_state_lock:
        _is_animating = False
        _current_animation_line_width = 0


def start_loading_animation(message="Processing",
                            animation_style_key=DEFAULT_ANIMATION_STYLE_KEY,
                            animation_color=DEFAULT_ANIMATION_COLOR):
    global _animation_thread, _stop_animation_event, _is_animating, _current_animation_line_width, _animation_state_lock

    with _animation_state_lock:
        if _is_animating:
            log_debug("Animation already running, not starting another one.")
            return

        _stop_animation_event.clear()
        selected_chars = ANIMATION_STYLES.get(animation_style_key, ANIMATION_STYLES[DEFAULT_ANIMATION_STYLE_KEY])

        initial_char = selected_chars[0]
        initial_full_line_ansi = f"{animation_color}{message} {initial_char}{TermColors.RESET} "
        stripped_initial_line = _strip_ansi_codes(initial_full_line_ansi)
        initial_width = wcswidth(stripped_initial_line)

        _is_animating = True
        _current_animation_line_width = initial_width

        _animation_thread = threading.Thread(target=_animate,
                                             args=(message, selected_chars, animation_color),
                                             daemon=True)
        _animation_thread.start()


def stop_loading_animation(success=True, final_message=None):
    global _animation_thread, _stop_animation_event, _is_animating, _animation_state_lock

    was_animating_when_called = False
    with _animation_state_lock:
        if _is_animating or _animation_thread is not None:
            was_animating_when_called = True
            _stop_animation_event.set()

    if not was_animating_when_called:
        if final_message:
            if success:
                log_info(f"{TermColors.GREEN}✔{TermColors.RESET} {final_message}")
            else:
                log_error(f"{TermColors.RED}✖{TermColors.RESET} {final_message}")
        return

    current_thread_ref = _animation_thread
    if current_thread_ref and current_thread_ref.is_alive():
        current_thread_ref.join(timeout=2)

    with _animation_state_lock:
        _is_animating = False
        _current_animation_line_width = 0
        _animation_thread = None

    if final_message:
        if success:
            log_info(f"{TermColors.GREEN}✔{TermColors.RESET} {final_message}")
        else:
            log_error(f"{TermColors.RED}✖{TermColors.RESET} {final_message}")

def initialize_logger(app_name="AppLogger", config_debug_mode=True, show_timestamp=None):
    global _logger, CONSOLE_SHOW_TIMESTAMP
    
    # 每次初始化时重新读取环境变量
    CONSOLE_SHOW_TIMESTAMP = get_console_timestamp_setting()
    
    _logger = logging.getLogger(app_name)
    _logger.propagate = False

    if config_debug_mode:
        _logger.setLevel(logging.DEBUG)
    else:
        _logger.setLevel(logging.INFO)

    if _logger.hasHandlers():
        for handler in _logger.handlers[:]:
            handler.close()
            _logger.removeHandler(handler)

    console_handler = AnimationAwareStreamHandler(sys.stdout)
    # 如果未指定，则使用全局设置
    show_timestamp = CONSOLE_SHOW_TIMESTAMP if show_timestamp is None else show_timestamp
    console_formatter = ColoredFormatter(show_timestamp=show_timestamp)
    console_handler.setFormatter(console_formatter)
    _logger.addHandler(console_handler)

    if ENABLE_FILE_LOGGING:
        try:
            if not os.path.exists(LOG_FILE_DIRECTORY):
                os.makedirs(LOG_FILE_DIRECTORY, exist_ok=True)

            log_filename = datetime.now().strftime(f"{app_name}_%Y-%m-%d_%H-%M-%S.log")
            log_filepath = os.path.join(LOG_FILE_DIRECTORY, log_filename)

            file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt=ColoredFormatter.DATE_FORMAT
            )
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(LOG_FILE_LEVEL)
            _logger.addHandler(file_handler)
        except Exception as e:
            sys.stderr.write(
                f"{TermColors.RED}错误: 初始化文件日志记录失败: {e}{TermColors.RESET}\n"
            )
            sys.stderr.flush()
    return _logger

def get_logger():
    global _logger
    if _logger is None:
        # 直接初始化，不发出警告
        _logger = initialize_logger()
        # 使用logger实例直接记录debug消息，避免循环调用
        if _logger:
            _logger.debug("日志记录器在显式初始化之前被访问，已使用默认值进行初始化")
    return _logger

def log_debug(message, exc_info=False):
    """记录调试级别日志"""
    if _logger is None:
        print(f"{TermColors.GREY}[DEBUG]: {message}{TermColors.RESET}")
    else:
        _logger.debug(message, exc_info=exc_info)

def log_info(message, exc_info=False):
    """记录信息级别日志"""
    if _logger is None:
        print(f"[INFO]: {message}")
    else:
        _logger.info(message, exc_info=exc_info)

def log_warning(message, exc_info=False):
    """记录警告级别日志"""
    if _logger is None:
        print(f"{TermColors.YELLOW}[WARNING]: {message}{TermColors.RESET}")
    else:
        _logger.warning(message, exc_info=exc_info)

def log_error(message, exc_info=False):
    """记录错误级别日志"""
    if _logger is None:
        print(f"{TermColors.RED}[ERROR]: {message}{TermColors.RESET}")
        if exc_info:
            traceback.print_exc()
    else:
        _logger.error(message, exc_info=exc_info)

def log_critical(message: str, exc_info: bool = False) -> None:
    """记录严重错误级别日志"""
    if _logger is None:
        print(f"{TermColors.RED}{TermColors.BOLD}[CRITICAL]: {message}{TermColors.RESET}")
        if exc_info:
            traceback.print_exc()
    else:
        _logger.critical(message, exc_info=exc_info)

def log_info_color(message: str, color: str = TermColors.GREEN, exc_info: bool = False) -> None:
    """使用自定义颜色输出信息"""
    if _logger is None:
        print(f"{color}[INFO]: {message}{TermColors.RESET}")
        if exc_info:
            traceback.print_exc()
    else:
        # 由于logger不支持ANSI颜色代码，使用print并模仿日志格式
        print(f"{color}[INFO]: {message}{TermColors.RESET}")
        if exc_info:
            traceback.print_exc()

def log_warning_color(message: str, color: str = TermColors.YELLOW, exc_info: bool = False) -> None:
    """使用自定义颜色输出警告"""
    if _logger is None:
        print(f"{color}[WARNING]: {message}{TermColors.RESET}")
        if exc_info:
            traceback.print_exc()
    else:
        print(f"{color}[WARNING]: {message}{TermColors.RESET}")
        if exc_info:
            traceback.print_exc()

def log_error_color(message: str, color: str = TermColors.RED, exc_info: bool = False) -> None:
    """使用自定义颜色输出错误"""
    if _logger is None:
        print(f"{color}[ERROR]: {message}{TermColors.RESET}")
        if exc_info:
            traceback.print_exc()
    else:
        print(f"{color}[ERROR]: {message}{TermColors.RESET}")
        if exc_info:
            traceback.print_exc()

def log_rag_output(message, *args, **kwargs):  # Example of a domain-specific logger
    get_logger().info(f"{TermColors.BLUE}{message}{TermColors.RESET}", *args, **kwargs)

# 添加log_text函数，用于直接输出未格式化的文本
def log_text(message, *args, **kwargs):
    """直接输出未格式化的文本，不添加日志级别和时间戳"""
    print(message, *args, **kwargs)

if __name__ == "__main__":
    # 1. Initialize logger - app_name will be part of the log file name
    initialize_logger(app_name="演示应用", config_debug_mode=True, show_timestamp=True)
    log_info("=============== 炫彩日志与加载动画演示开始 ===============")
    log_debug("这是一个调试消息：日志系统已成功初始化。")
    if not ENABLE_FILE_LOGGING:
        log_warning("文件日志记录已禁用。如需启用，请设置 ENABLE_FILE_LOGGING = True")
    else:
        log_info(f"文件日志已启用，日志将存储在 '{LOG_FILE_DIRECTORY}' 目录下。")

    # 2. Basic log levels demo
    log_info("演示2.1: log_info是一条 INFO 信息。")
    log_warning("演示2.2: log_warning是一条警告 WARNING 信息。")
    log_error("演示2.3: log_error是一条错误 ERROR 信息。")
    log_debug("演示2.4: log_debug是一条调试 DEBUG 信息。DEBUG信息（包括对应时间戳）全部保持灰色")

    log_info_color("演示2.5: log_info_color的 INFO 信息默认带有醒目的绿色。")
    log_info_color("当然，你也可以自定义log_info_color的颜色", TermColors.MAGENTA)
    log_warning_color("演示2.6: log_warning_color的 WARNING 信息默认带有醒目的黄色。")
    log_warning_color("当然你也可以改成蓝的", TermColors.BLUE)
    log_error_color("演示2.7: log_error_color的 ERROR 信息默认带有醒目的红色。")
    log_error_color("一个绿色的ERROR?", TermColors.GREEN)

    # 示例：使用log_text
    log_text("演示2.8: log_text直接输出文本，不添加日志级别和时间戳")
    log_text("这是一行直接输出的文本")
    log_text("这是第二行直接输出的文本")

    # 3. Loading animation demo
    log_info("演示3.1: 默认加载动画 (braille样式, 默认白色)")
    # Pass message without internal colors, use animation_color for the whole line
    start_loading_animation(message="任务A处理中")
    time.sleep(2)
    stop_loading_animation(success=True, final_message="任务A成功完成!")

    log_info("演示3.2: 自定义动画样式 (spinner样式, 默认白色)")
    start_loading_animation(message="任务B执行中", animation_style_key='spinner')
    time.sleep(2)
    stop_loading_animation(success=True, final_message="任务B (spinner) 执行完毕!")

    log_info("演示3.3: 自定义动画颜色 (默认braille样式, 青色)")
    start_loading_animation(message="任务C加载中", animation_color=TermColors.CYAN)
    time.sleep(2)
    stop_loading_animation(success=True, final_message="任务C (青色) 加载完成!")

    log_info("演示3.4: 传递本身带颜色的消息给动画")
    # This shows that message can carry its own colors, and animation_color is an outer wrapper
    # animation_color (default WHITE) wraps (MAGENTA "Task D" RESET) + char + RESET
    start_loading_animation(
        message=f"{TermColors.MAGENTA}任务D(本身品红){TermColors.RESET}进行中",
        animation_style_key='arrows',
        animation_color=TermColors.YELLOW  # Yellow wrapper
    )
    time.sleep(2.5)
    stop_loading_animation(success=True, final_message="任务D (品红内容，黄色包装) 完成!")

    log_info("演示3.5: 其他动画样式 (moon样式, 浅蓝色)")
    start_loading_animation(message="月相观察", animation_style_key='moon', animation_color=TermColors.LIGHT_BLUE)
    time.sleep(2.5)
    stop_loading_animation(success=True, final_message="月相观察完毕!")

    log_info("演示3.6: 动画期间进行日志记录 (dots样式, 橙色)")
    start_loading_animation(message="橙色点点任务", animation_style_key='dots', animation_color=TermColors.ORANGE)
    log_info("动画已启动，现在记录一条 INFO 消息，动画会自动避让。")
    time.sleep(1)
    log_warning("这是一条警告 WARNING 消息，动画仍在后台继续。")
    time.sleep(1)
    log_debug("一条调试 DEBUG 消息，动画即将停止并模拟失败。")
    time.sleep(1)
    stop_loading_animation(success=False, final_message="橙色点点任务模拟失败。")

    log_info("演示3.7: 停止动画时不显示最终消息")
    start_loading_animation(message="短暂处理")
    time.sleep(1.5)
    stop_loading_animation()  # No final_message
    log_info("动画已停止，不提供 final_message。")

    # 4. Special color log functions
    log_info("演示4.1: 使用 log_info_color 输出自定义颜色 INFO (例如紫红色)")
    log_info_color("这是一条紫红色的 INFO 信息。", TermColors.MAGENTA)

    log_info("演示4.2: 使用 log_rag_output 输出特定格式 INFO")
    log_rag_output("这是一个RAG 模型输出内容 (蓝色)")

    # 5. Re-initialize logger: turn off console timestamp
    log_info("演示5: 重新初始化日志，关闭控制台时间戳 (文件日志不受影响)")
    initialize_logger(app_name="演示应用-无时间戳", config_debug_mode=True, show_timestamp=False)
    log_info("这条 INFO 信息在控制台不显示时间戳。")
    log_debug("这条 DEBUG 信息在控制台也不显示时间戳。")
    start_loading_animation(message="无时间戳任务执行")
    time.sleep(1.5)
    stop_loading_animation(final_message="无时间戳任务完成。")

    # 6. 全局时间戳设置演示
    log_info("演示6: 全局时间戳设置演示")
    # 备份当前设置
    original_setting = CONSOLE_SHOW_TIMESTAMP
    
    # 临时修改全局设置
    globals()['CONSOLE_SHOW_TIMESTAMP'] = not CONSOLE_SHOW_TIMESTAMP
    initialize_logger(app_name="演示应用-全局时间戳", config_debug_mode=True)
    log_info(f"已修改全局时间戳设置为: {CONSOLE_SHOW_TIMESTAMP}")
    log_debug("此时所有日志默认使用新的全局时间戳设置")
    
    # 恢复原始设置
    globals()['CONSOLE_SHOW_TIMESTAMP'] = original_setting
    initialize_logger(app_name="演示应用", config_debug_mode=True)
    log_info("已恢复原始全局时间戳设置")
    
    # 7. 测试print() 交互
    log_info("演示7: 恢复时间戳并测试动画与普通 print() 语句的交互")
    initialize_logger(app_name="演示应用", config_debug_mode=True, show_timestamp=True)  # Restore default
    log_info("日志时间戳已恢复。")

    print(f"{TermColors.YELLOW}这是一条普通的 print() 语句，在动画开始前。{TermColors.RESET}")
    start_loading_animation(message="测试与print交互")
    time.sleep(1)
    # Standard print() is not intercepted by the logger's handler.
    # It will likely mess up the animation line.
    print(f"{TermColors.RED}警告: 下面这条 print() 语句会打断当前动画行。{TermColors.RESET}")
    time.sleep(1)
    log_info("这条日志消息在 print() 之后，会由 AnimationAwareStreamHandler 正确处理。")
    time.sleep(1)
    stop_loading_animation(final_message="动画与 print() 交互测试结束。")
    print(f"{TermColors.GREEN}动画结束后的另一条 print() 语句。{TermColors.RESET}")

    # 8. End
    if ENABLE_FILE_LOGGING:
        log_info(f"所有演示已完成。请检查 '{LOG_FILE_DIRECTORY}' 目录中的日志文件。")
    else:
        log_info("所有演示已完成。文件日志记录当前已禁用。")
    log_info("=============== 演示结束 ===============")