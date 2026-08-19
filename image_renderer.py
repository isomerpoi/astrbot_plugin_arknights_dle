import os
from PIL import Image, ImageDraw, ImageFont

# =====================================================================
# 罗德岛终端 UI 核心颜色配置
# =====================================================================
BG = "#080C10"
PANEL = "#10171D"
HEADER = "#151F26"
GRID = "#26343C"
TEXT = "#D7E1E5"
TEXT_TITLE = "#E8F1F4"
TEXT_SECONDARY = "#71858E"
CYAN = "#65D6D1"

MATCH_COLOR = ("#65C7B9", "#397D76", "#16302F")
WRONG_COLOR = ("#C96870", "#733E46", "#321D22")
COMPARE_COLOR = ("#D09A5B", "#715535", "#30271D")
DEFAULT_COLOR = (TEXT, GRID, PANEL)

def get_chinese_font(size):
    current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
    for file in os.listdir(current_dir):
        if file.lower().endswith(('.ttf', '.ttc')):
            font_path = os.path.join(current_dir, file)
            return ImageFont.truetype(font_path, size)
    raise FileNotFoundError(f"❌ 找不到字体文件！请把字体上传到: {current_dir}")

def render_game_state(session, output_path: str, config: dict):
    current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
    
    bg_opacity = config.get("bg_opacity", 0.5)
    atk_threshold = config.get("atk_red_threshold", 500)
    
    bg_config = config.get("custom_bg_image", [])
    bg_path = ""
    if isinstance(bg_config, list) and len(bg_config) > 0:
        item = bg_config[0]
        bg_path = str(item.get("path", item)) if isinstance(item, dict) else str(item)
    elif isinstance(bg_config, str) and bg_config.strip():
        bg_path = bg_config.strip()
        
    final_bg_path = None
    if bg_path:
        if os.path.isabs(bg_path) and os.path.exists(bg_path):
            final_bg_path = bg_path
        else:
            path_root = os.path.join(os.getcwd(), bg_path)
            path_plugin = os.path.join(current_dir, bg_path)
            if os.path.exists(path_root):
                final_bg_path = path_root
            elif os.path.exists(path_plugin):
                final_bg_path = path_plugin

    MARGIN_X, TOP_AREA_H, HEADER_H, ROW_H, GAP, RADIUS = 48, 100, 52, 68, 6, 4
    
    # 🔥 彻底废弃隐藏列逻辑，无条件强制渲染全部 12 列 🔥
    COLUMNS = [
        {"name": "干员", "key": "name", "width": 210, "type": "name"},
        {"name": "职业", "key": "class", "width": 120, "type": "str"},
        {"name": "分支", "key": "sub_class", "width": 180, "type": "str"},
        {"name": "阵营", "key": "faction", "width": 250, "type": "str"}, 
        {"name": "星级", "key": "rarity", "width": 105, "type": "num_star"},
        {"name": "生命", "key": "hp", "width": 150, "type": "num"},
        {"name": "攻击", "key": "atk", "width": 140, "type": "num"},
        {"name": "防御", "key": "defense", "width": 140, "type": "num"},
        {"name": "法抗", "key": "res", "width": 120, "type": "num"},
        {"name": "费用", "key": "cost", "width": 110, "type": "num"},
        {"name": "阻挡", "key": "block", "width": 110, "type": "num"},
        {"name": "年份", "key": "year", "width": 140, "type": "num_year"},
    ]
    
    total_col_width = sum(col["width"] for col in COLUMNS)
    WIDTH = MARGIN_X * 2 + total_col_width + (len(COLUMNS) - 1) * GAP
    
    history_count = len(session.history)
    grid_h = max(1, history_count) * (ROW_H + GAP)
    HEIGHT = TOP_AREA_H + HEADER_H + GAP + grid_h + (90 if not session.is_active else 30)

    if final_bg_path:
        try:
            base_img = Image.open(final_bg_path).convert("RGBA")
            img = Image.new("RGBA", (WIDTH, HEIGHT), BG)
            img.paste(base_img, (0, 0), mask=base_img if base_img.mode == 'RGBA' else None)
            img = img.crop((0, 0, WIDTH, HEIGHT))
            
            overlay_alpha = int((1.0 - max(0.0, min(1.0, float(bg_opacity)))) * 255)
            overlay = Image.new("RGBA", (WIDTH, HEIGHT), (8, 12, 16, overlay_alpha))
            img.paste(overlay, (0, 0), mask=overlay)
            img = img.convert("RGB")
        except Exception:
            img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    else:
        img = Image.new("RGB", (WIDTH, HEIGHT), BG)

    draw = ImageDraw.Draw(img)
    font_title = get_chinese_font(32)
    font_sub = get_chinese_font(18)
    font_header = get_chinese_font(18)
    font_normal = get_chinese_font(22)
    font_arrow = get_chinese_font(18)

    draw.text((MARGIN_X, 22), "SYSTEM COMMANDS //", font=font_sub, fill=CYAN)
    cmd_hints = "开局: /arkdle [6星/困难]  |  猜: /cc 名字  |  认输: /gu  |  加别名: /add 外号 真名"
    draw.text((MARGIN_X, 48), cmd_hints, font=font_sub, fill=TEXT_SECONDARY)
    
    title_text = "Arkdle (舟兜)"
    try:
        bbox = draw.textbbox((0, 0), title_text, font=font_title)
        tw = bbox[2] - bbox[0]
    except AttributeError:
        tw, _ = draw.textsize(title_text, font=font_title)
    draw.text(((WIDTH - tw)/2, 35), title_text, font=font_title, fill=TEXT_TITLE)
    
    draw.text((WIDTH - MARGIN_X - 120, 22), "SYNC : ONLINE", font=font_sub, fill=CYAN)
    progress = f"MATCH RATE  {history_count:02d} / {session.max_guesses:02d}"
    draw.text((WIDTH - MARGIN_X - 180, 48), progress, font=font_sub, fill=TEXT_SECONDARY)
    draw.line([(MARGIN_X, 90), (WIDTH - MARGIN_X, 90)], fill=GRID, width=1)

    current_y, current_x = TOP_AREA_H, MARGIN_X
    for col in COLUMNS:
        w = col["width"]
        draw.rounded_rectangle([current_x, current_y, current_x + w, current_y + HEADER_H], radius=RADIUS, fill=HEADER, outline=GRID, width=1)
        try:
            bbox = draw.textbbox((0, 0), col["name"], font=font_header)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            tw, th = draw.textsize(col["name"], font=font_header)
        draw.text((current_x + (w-tw)/2, current_y + (HEADER_H-th)/2 - 2), col["name"], font=font_header, fill=TEXT_SECONDARY)
        current_x += w + GAP
    current_y += HEADER_H + GAP

    def draw_cell(x, y, w, text_main, color_tuple, arrow_text="", is_name=False):
        txt_color, border_color, bg_color = color_tuple
        draw.rounded_rectangle([x, y, x + w, y + ROW_H], radius=RADIUS, fill=bg_color, outline=border_color, width=1)
        
        full_text = str(text_main) + (f" {arrow_text}" if arrow_text else "")
        try:
            bbox = draw.textbbox((0, 0), full_text, font=font_normal)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            tw, th = draw.textsize(full_text, font=font_normal)
            
        avatar_drawn = False
        if is_name:
            avatar_path = os.path.join(current_dir, "avatars", f"{text_main}.png")
            if os.path.exists(avatar_path):
                try:
                    ava_img = Image.open(avatar_path).convert("RGBA")
                    ava_size = ROW_H - 14
                    ava_img = ava_img.resize((ava_size, ava_size))
                    mask = Image.new("L", (ava_size, ava_size), 0)
                    ImageDraw.Draw(mask).rounded_rectangle((0, 0, ava_size, ava_size), radius=4, fill=255)
                    img.paste(ava_img, (int(x + 8), int(y + 7)), mask=mask)
                    draw.text((x + 8 + ava_size + 14, y + (ROW_H-th)/2 - 3), str(text_main), font=font_normal, fill=txt_color)
                    avatar_drawn = True
                except: pass
                    
        if not avatar_drawn:
            text_x, text_y = x + (w-tw)/2, y + (ROW_H-th)/2 - 3
            draw.text((text_x, text_y), str(text_main), font=font_normal, fill=txt_color)
            if arrow_text:
                try:
                    m_tw = draw.textbbox((0, 0), str(text_main), font=font_normal)[2]
                except AttributeError:
                    m_tw, _ = draw.textsize(str(text_main), font=font_normal)
                draw.text((text_x + m_tw + 6, text_y + 4), arrow_text, font=font_arrow, fill=txt_color)

    target = session.target_operator
    for guess in session.history:
        current_x = MARGIN_X
        for col in COLUMNS:
            val, t_val = guess.get(col["key"], 0), target.get(col["key"], 0)
            w, ctype = col["width"], col["type"]
            c_style, text, arrow, is_name_col = DEFAULT_COLOR, str(val), "", False
            
            if ctype == "name":
                c_style, is_name_col = (TEXT_TITLE, GRID, PANEL), True
            elif ctype in ["str", "str_short"]:
                c_style = MATCH_COLOR if val == t_val else WRONG_COLOR
            elif ctype == "num":
                if val == t_val: 
                    c_style = MATCH_COLOR
                else: 
                    c_style, arrow = COMPARE_COLOR, "↑" if t_val > val else "↓"
                    if col["key"] == "atk" and abs(int(val) - int(t_val)) >= atk_threshold:
                        c_style = WRONG_COLOR
            elif ctype == "num_star":
                if val == t_val:
                    c_style, text = MATCH_COLOR, f"{val}★"
                else:
                    c_style = WRONG_COLOR if abs(int(val) - int(t_val)) >= 2 else COMPARE_COLOR
                    text, arrow = f"{val}★", "↑" if t_val > val else "↓"
            elif ctype == "num_year":
                if getattr(session, "mode", "简单") == "困难":
                    c_style, text = DEFAULT_COLOR, "????"
                else:
                    if val == t_val: c_style = MATCH_COLOR
                    else: c_style, arrow = COMPARE_COLOR, "↑" if t_val > val else "↓"

            draw_cell(current_x, current_y, w, text, c_style, arrow, is_name=is_name_col)
            current_x += w + GAP
        current_y += ROW_H + GAP

    if not session.is_active:
        current_y += 10
        is_win = (session.guesses_left >= 0 and session.history[-1]["name"] == target["name"])
        banner_style = MATCH_COLOR if is_win else WRONG_COLOR
        draw.rounded_rectangle([MARGIN_X, current_y, WIDTH - MARGIN_X, current_y + 60], radius=RADIUS, fill=banner_style[2], outline=banner_style[1], width=1)
        msg = f">> 猜对啦，你是超大杯，目标干员确认【{target['name']}】 <<" if is_win else f">> 次数耗尽，中杯~正确干员为【{target['name']}】 <<"
        try:
            bbox = draw.textbbox((0, 0), msg, font=font_normal)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            tw, th = draw.textsize(msg, font=font_normal)
        draw.text((MARGIN_X + (WIDTH - 2*MARGIN_X - tw)/2, current_y + (60 - th)/2 - 3), msg, font=font_normal, fill=banner_style[0])

    img.save(output_path, format="PNG")
    return output_path