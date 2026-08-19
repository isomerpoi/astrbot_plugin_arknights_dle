# 📦 astrbot_plugin_arknights_dle (舟兜 - Arkdle)

[![AstrBot](https://img.shields.io/badge/AstrBot-Plugin-blue.svg)](https://github.com/Soulter/AstrBot)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

基于 [AstrBot](https://github.com/Soulter/AstrBot) 框架开发的**明日方舟干员竞猜小游戏 (Arknights Wordle/Loldle)**。
通过极致的“罗德岛战术终端”风格图片渲染，为你和群友提供沉浸式的硬核数据推理体验。
---

## ✨ 核心特性

- 🎨 **顶级视觉渲染**：纯本地 Pillow 动态绘图，自动排版适配。内置极客赛博工业风 UI，支持 WebUI 一键上传自定义底图与调节透明度。
- 📊 **十二维硬核数据**：比对干员的 职业、分支、阵营、星级、生命、攻击、防御、法抗、费用、阻挡、实装年份！
- 🤖 **智能防连抽发牌**：内置 50% 极高六星爆率，并通过“洗牌堆”算法彻底杜绝短期内连续抽到同一名干员。
- 🧠 **超级模糊匹配**：
  - **外号识别**：支持“水陈”、“叔叔”、“红蒂”等几十种常用外号。
  - **群友调教**：支持群内使用 `/add 外号 真名` 指令，让机器人越用越聪明！
  - **错别字容错**：采用莱文斯坦距离算法，打错字也能瞬间精确锁定干员。
- ⚡ **开箱即用**：**自带开源中文字体**，完美兼容 Linux / Docker 环境，告别中文方块字烦恼！渲染零网络 I/O 阻塞，毫秒级出图。
-⚙️ **AstrBot 完美对接**：全面支持 AstrBot 网页控制台，无需重启即可热更新猜测次数、超时时间、隐藏指定列等配置。

---

## 🛠️ 安装与配置

### 1. 下载插件
在 AstrBot 的 `data/plugins/` 目录下，克隆本仓库：
```bash
git clone https://github.com/你的GitHub用户名/astrbot_plugin_arknights_dle.git
