import random
import os
import json
import time
from typing import Dict, Optional, Tuple, List

def string_distance(s1: str, s2: str) -> int:
    if len(s1) < len(s2): return string_distance(s2, s1)
    if len(s2) == 0: return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

class GameSession:
    def __init__(self, target_operator: dict, config: dict, mode: str = "简单"):
        self.target_operator = target_operator
        self.max_guesses = config.get("max_guesses", 8)
        self.guesses_left = self.max_guesses
        self.is_active = True
        self.guessed_names = set()
        self.mode = mode
        self.history = []
        
        # 记录超时与数值配置
        self.last_active_time = time.time()
        self.timeout_seconds = config.get("auto_timeout_seconds", 300)
        self.atk_red_threshold = config.get("atk_red_threshold", 500)

    def compare_num(self, guess_val: int, target_val: int) -> str:
        if guess_val == target_val: return "🟩"
        return "⬆️" if target_val > guess_val else "⬇️"

    def compare_str(self, guess_str: str, target_str: str) -> str:
        return "🟩" if guess_str == target_str else "🟥"

    def process_guess(self, guess_op: dict, input_name: str = "") -> Tuple[bool, str]:
        if not self.is_active:
            return False, "当前没有进行中的游戏。"

        # 刷新活跃时间
        self.last_active_time = time.time()

        guess_name = guess_op["name"]
        correction_msg = ""
        if input_name and input_name.lower() != guess_name.lower():
            correction_msg = f"*(已自动纠正: {input_name} -> {guess_name})*\n"

        if guess_name in self.guessed_names:
            return False, f"{correction_msg}⚠️ 【{guess_name}】已经被猜过了！"

        self.guesses_left -= 1
        self.guessed_names.add(guess_name)
        self.history.append(guess_op)
        
        t = self.target_operator
        is_win = (guess_name == t["name"])
        
        result_text = correction_msg + f"成功录入数据：{guess_name}"

        if is_win:
            self.is_active = False
            result_text = correction_msg + f"🎉 恭喜猜中！目标干员就是【{t['name']}】！"
        elif self.guesses_left <= 0:
            self.is_active = False
            result_text = correction_msg + f"💀 次数用尽，游戏结束！\n正确答案是：【{t['name']}】。"

        return is_win, result_text


class SessionManager:
    def __init__(self, operators_data: List[dict], config: dict):
        self.operators_data = operators_data
        self.config = config
        self.sessions: Dict[str, GameSession] = {}
        
        self.star_6_pool = [op for op in self.operators_data if op.get("rarity") == 6]
        self.star_5_pool = [op for op in self.operators_data if op.get("rarity") == 5]
        self.star_others_pool = [op for op in self.operators_data if op.get("rarity") < 5]
        
        self.deck_6 = []
        self.deck_5 = []
        self.deck_others = []
        
        self.alias_dict = {
            "水陈": "假日威龙陈", "异德": "缄默德克萨斯", "翼德": "缄默德克萨斯",
            "异刀": "麒麟R夜刀", "双刀": "麒麟R夜刀", "麒麟r夜刀": "麒麟R夜刀", "麒麟x夜刀": "麒麟R夜刀",
            "耀骑士": "耀骑士临光", "耀光": "耀骑士临光", "红蒂": "浊心斯卡蒂",
            "归鲨": "归溟幽灵鲨", "令姐": "令", "老陈": "陈",
            "粉毛": "澄闪", "小羊": "艾雅法拉", "纯艾": "纯烬艾雅法拉",
            "异客": "异客", "神": "异客", "小火龙": "伊芙利特",
            "塞爹": "塞雷娅", "洁哥": "安洁莉娜", "煌喵": "煌",
            "叔叔": "玛恩纳", "42": "史尔特尔", "42姐": "史尔特尔"
        }
        
        current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
        self.custom_alias_file = os.path.join(current_dir, "custom_aliases.json")
        if os.path.exists(self.custom_alias_file):
            try:
                with open(self.custom_alias_file, 'r', encoding='utf-8') as f:
                    self.alias_dict.update(json.load(f))
            except: pass

    def add_alias(self, arg1: str, arg2: str) -> str:
        op1 = next((op for op in self.operators_data if op["name"] == arg1), None)
        op2 = next((op for op in self.operators_data if op["name"] == arg2), None)
        
        if op2 and not op1:
            real_name, alias = op2["name"], arg1
        elif op1 and not op2:
            real_name, alias = op1["name"], arg2
        else:
            fuzzy_op2 = self.fuzzy_match_operator(arg2)
            if fuzzy_op2:
                real_name, alias = fuzzy_op2["name"], arg1
            else:
                fuzzy_op1 = self.fuzzy_match_operator(arg1)
                if fuzzy_op1:
                    real_name, alias = fuzzy_op1["name"], arg2
                else:
                    return f"❌ 无法识别真名，请提供至少一个标准干员名！"

        self.alias_dict[alias] = real_name
        
        custom = {}
        if os.path.exists(self.custom_alias_file):
            try:
                with open(self.custom_alias_file, 'r', encoding='utf-8') as f:
                    custom = json.load(f)
            except: pass
        custom[alias] = real_name
        with open(self.custom_alias_file, 'w', encoding='utf-8') as f:
            json.dump(custom, f, ensure_ascii=False, indent=2)
            
        return f"✅ 添加成功！输入【{alias}】将自动识别为【{real_name}】。"

    def _draw_operator(self, mode: str) -> dict:
        if mode == "6星":
            if not self.deck_6:
                self.deck_6 = self.star_6_pool.copy()
                random.shuffle(self.deck_6)
            return self.deck_6.pop()

        roll = random.randint(1, 100)
        prob_6 = self.config.get("star_6_probability", 50)
        prob_5 = self.config.get("star_5_probability", 35)
        
        if roll <= prob_6:
            if not self.deck_6:
                self.deck_6 = self.star_6_pool.copy()
                random.shuffle(self.deck_6)
            return self.deck_6.pop()
        elif roll <= prob_6 + prob_5:
            if not self.deck_5:
                self.deck_5 = self.star_5_pool.copy()
                random.shuffle(self.deck_5)
            return self.deck_5.pop()
        else:
            if not self.deck_others:
                self.deck_others = self.star_others_pool.copy()
                random.shuffle(self.deck_others)
            return self.deck_others.pop()

    def fuzzy_match_operator(self, input_name: str) -> Optional[dict]:
        input_name = input_name.strip()
        if input_name in self.alias_dict:
            input_name = self.alias_dict[input_name]

        for op in self.operators_data:
            if op["name"].lower() == input_name.lower():
                return op
                
        best_match = None
        min_dist = 999
        for op in self.operators_data:
            real_name = op["name"]
            if input_name in real_name and len(input_name) >= 2:
                return op
            dist = string_distance(input_name, real_name)
            allowed_dist = 1 if len(real_name) <= 3 else 2
            if abs(len(input_name) - len(real_name)) > allowed_dist:
                continue
            if dist <= allowed_dist and dist < min_dist:
                min_dist = dist
                best_match = op
        return best_match

    def has_active_game(self, session_id: str) -> bool:
        return session_id in self.sessions and self.sessions[session_id].is_active

    def start_game(self, session_id: str, mode: str = "简单") -> str:
        if self.has_active_game(session_id):
            return "⚠️ 当前已有进行中的游戏！请继续 /cc 猜测，或发送 /gu 放弃。"
            
        target_operator = self._draw_operator(mode)
        # 传入配置项创建对局
        self.sessions[session_id] = GameSession(target_operator, config=self.config, mode=mode)
        
        mode_str = {"简单": "简单模式", "困难": "困难模式", "6星": "✨6星专属模式"}.get(mode, "简单模式")
        max_g = self.config.get("max_guesses", 8)
        return f"🎲 猜干员开始！[{mode_str}]\n共有 {max_g} 次机会。使用 `/cc 干员名` 猜测。"

    def handle_guess(self, session_id: str, operator_name: str) -> str:
        if not self.has_active_game(session_id):
            return "❌ 没有进行中的游戏。发送 `/arkdle` 开始。"
            
        session = self.sessions[session_id]
        
        # 被动超时检测
        if session.timeout_seconds > 0 and (time.time() - session.last_active_time) > session.timeout_seconds:
            self.give_up(session_id)
            return f"⏳ 上局游戏因超过 {session.timeout_seconds} 秒无操作已自动结束。请重新发送 `/arkdle` 开始新游戏。"

        guess_op = self.fuzzy_match_operator(operator_name)
        if not guess_op:
            return f"❌ 找不到与【{operator_name}】相近的干员，请检查错别字。"
            
        _, response_text = session.process_guess(guess_op, input_name=operator_name)
        return response_text

    def give_up(self, session_id: str) -> str:
        if not self.has_active_game(session_id):
            return "❌ 当前没有进行中的游戏。"
        session = self.sessions[session_id]
        session.is_active = False
        target_name = session.target_operator["name"]
        return f"🏳️ 游戏结束。\n正确答案是：【{target_name}】。"