import os
import json
import tempfile
import asyncio
import time
from astrbot.api.all import *
from astrbot.api.message_components import Image, Plain
from astrbot.api.event.filter import event_message_type, EventMessageType
from .game_engine import SessionManager
from .image_renderer import render_game_state

try:
    from astrbot.api import AstrBotConfig
except ImportError:
    AstrBotConfig = dict

@register("arknights_dle", "Opencode", "明日方舟猜干员极致版", "7.7.0")
class ArknightsDlePlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig = None):
        super().__init__(context)
        self.current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()

        self.config = config if config is not None else {}

        defaults = {
            "auto_timeout_seconds": 300,
            "max_guesses": 8,
            "atk_red_threshold": 500,
            "star_6_probability": 50,
            "star_5_probability": 35,
            "custom_bg_image": [],
            "bg_opacity": 0.5,
            "hidden_columns": []  # 🔥 年份列已完全释放
        }
        for key, value in defaults.items():
            self.config.setdefault(key, value)

        data_path = os.path.join(self.current_dir, "operator_data.json")
        self.operators_data = self.load_data(data_path)

        self.session_manager = SessionManager(self.operators_data, self.config)
        self.all_operator_names = {op["name"] for op in self.operators_data}

    def load_data(self, path: str) -> list:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.context.logger.error(f"加载干员数据失败: {e}")
            return []

    def start_timeout_task(self, event: AstrMessageEvent, session_id: str):
        timeout = self.config.get("auto_timeout_seconds", 300)
        if timeout <= 0:
            return
        asyncio.create_task(self._timeout_loop(event, session_id, timeout))

    async def _timeout_loop(self, event: AstrMessageEvent, session_id: str, timeout: int):
        while True:
            await asyncio.sleep(10)
            session = self.session_manager.sessions.get(session_id)
            if not session or not session.is_active:
                break

            elapsed = time.time() - session.last_active_time
            if elapsed >= timeout:
                self.session_manager.give_up(session_id)
                msg = f"⏳ 游戏超过 {timeout} 秒无操作，已自动结束。"
                try:
                    # 🔥 修复报错：直接使用 Plain，移除废弃的 MessageChain
                    await event.send(Plain(msg))
                except Exception:
                    pass
                break

    @command("arkdle")
    async def start_game(self, event: AstrMessageEvent, mode: str = "简单"):
        if not self.operators_data:
            yield event.plain_result("❌ 无法读取数据库。")
            return

        if mode not in ["简单", "困难", "6星"]:
            mode = "简单"

        session_id = str(event.session_id)
        self.session_manager.config = self.config
        text_reply = self.session_manager.start_game(session_id, mode=mode)

        if "猜干员游戏开始" in text_reply:
            self.start_timeout_task(event, session_id)

        yield event.plain_result(text_reply)

    @command("add", alias=["添加别名", "别名"])
    async def add_alias_command(self, event: AstrMessageEvent, alias: str, real_name: str):
        reply = self.session_manager.add_alias(alias, real_name)
        yield event.plain_result(reply)

    async def _handle_guess_and_reply(self, event: AstrMessageEvent, session_id: str, operator_name: str):
        text_reply = self.session_manager.handle_guess(session_id, operator_name)

        if "❌" in text_reply or "⚠️" in text_reply or "⏳" in text_reply:
            yield event.plain_result(text_reply)
            return

        session = self.session_manager.sessions.get(session_id)
        if session:
            sys_temp_dir = tempfile.gettempdir()
            safe_img_path = os.path.join(sys_temp_dir, f"arkdle_guess_{session_id}.png")
            final_img_path = render_game_state(session, safe_img_path, self.config)
            yield event.chain_result([Image.fromFileSystem(final_img_path)])
        else:
            yield event.plain_result(text_reply)

    @command("cc")
    async def guess_command(self, event: AstrMessageEvent, operator_name: str):
        session_id = str(event.session_id)
        async for result in self._handle_guess_and_reply(event, session_id, operator_name):
            yield result

    @command("gu", alias=["giveup", "放弃", "认输"])
    async def giveup_command(self, event: AstrMessageEvent):
        session_id = str(event.session_id)
        reply = self.session_manager.give_up(session_id)
        yield event.plain_result(reply)

    @event_message_type(EventMessageType.ALL)
    async def on_raw_message(self, event: AstrMessageEvent):
        session_id = str(event.session_id)
        if not self.session_manager.has_active_game(session_id):
            return

        message_str = event.message_obj.message_str.strip()
        if message_str in self.all_operator_names or message_str in self.session_manager.alias_dict:
            async for result in self._handle_guess_and_reply(event, session_id, message_str):
                yield result
            event.stop_event()