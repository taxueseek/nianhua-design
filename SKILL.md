---
name: nianhua-design
description: 基于「平面现代主义（Graphic Modernism）」与年画三重历史功能规律（节庆装饰、民间信仰表达、大众视觉传播），拆分为「年画缩样（传统至现代集大成）」与「80s 先锋译丛（现代主义装帧）」两大细分风格，各自兼容三种同代平面风味变体（几何东方构成/三分线框丛书/双专色孔版叠印）与真实历史断代语法（1950s-60s/1970s/1980s/1990s），吸收版画剪纸工艺、出版饰件、三四色面积比与手工非标字骨，将括号原标题与坐标参考从提示词正文中彻底剥离，生成高可控中文生图提示词及无字底图，并支持看图复诊闭环。触发词：年画缩样风格、复古画册封面、80年代先锋装帧、美学译丛封面、80年代美术字海报、老宣传画风格、年历设计提示词、nianhua-design。
---

# nianhua-design（v0.0.1）

## 美学母体：双细分风格 × 年画三重历史功能

1. **两大细分风格（`--style`）**：
   - **`nianhua-suoyang`（年画缩样 · 传统至现代集大成）**：1950s–90s 美术出版社内部订货缩样与画集封面体系。它不是单一民俗画，而是当时封面设计的集大成者——包罗万象，既能用工笔开光、民间剪纸锯齿线刻、套色木刻、篆刻方印与毛笔题签立住传统气韵，也能用田字格色块切割、大留白、摄影拼贴与突破当代印刷体框死的手绘非标变形美术字展现超前现代感。
   - **`pioneer-book-series`（80s 先锋译丛 · 现代主义装帧）**：1980 年代文艺丛书、美学译丛与思想画册装帧路线。吸收包豪斯与俄国构成主义，依靠大留白、正圆/三角/实心条带硬边切割、低饱和书卷套印与建筑梁柱般的手工几何书名建立秩序。
2. **年画三重历史功能规律（`--function`）**：年画曾经同时承担三个功能——**节庆装饰**（`festive-ornament`）、**民间信仰表达**（`folk-belief`）、**大众视觉传播**（`mass-visual`）。这一规律解释了缩样封面为何天然兼具喜庆图形张力、对称仪式秩序与远距一眼识别的巨型年份及手绘招牌大字。
3. **三种同代同源风味变体（`--flavor`，默认 `none`）**：`ikko-geometric`（几何东方构成）| `marber-grid`（三分线框丛书）| `riso-overprint`（双专色孔版叠印）。两大细分风格均可按自身语义适配这三种变体。

## 正交维度与断代语法（真源：`assets/blueprints.json`）

- **真实历史断代（`decade`）**：`1950s-60s`（素纸铅印、老宋楷隶、禁拼音饰带）| `1970s`（红光亮高饱和专色、粗黑/描边字、禁低饱和书卷色与烫金）| `1980s`（默认最高权重，集大成期，兼容工笔缩样与先锋译丛）| `1990s`（铜版胶印、胶片拼贴与高对比撞色、禁传统花边）。
- **载体与绑定字区骨架（`format` × `skeleton`）**：`cover` / `calendar` / `poster` / `pattern-book` / `book-series` × `block-cut` / `window-frame` / `grid-minimal` / `bleed-poster`（每条具体 `layout` 均绑定专属 `title_zone`、`year_zone` 与 `sub_zone`）。
- **排布与咬合（`cjk_grid` × `tactic`）**：8 类汉字排布网格（带横/竖/斜方向校验，防止极扁宽字强行竖排）× 6 类字图手法（格子版式自动避让斜向冲突）。
- **隐喻、媒介、饰件与色字**：`metaphor` × `medium` × `accent`（细双线框 / 阴文篆刻方印 / 全大写拼音饰带 / 二方连续回纹窄边 / 局部哑光烫金 / 暗纹织锦纸）× `palette`（3–4 色面积占比）× `typo`（非标手绘字骨）。

## 工作流 A：出词、剥离括号参考与分区锁字

1. **剥离原则**：所有括号原标题（如「东亚排版网格法则」「主从分区」「#D8432C」与坐标参数）一律剥离出提示词正文，移入独立的 `【设计参考与锁字简报】`；提示词正文只保留纯正、连续、可直接绘形的中文视觉指令。
2. **调用 `scripts/compose_prompt.py` 生成**：
   ```bash
   # 年画缩样路线（支持断代与三重功能）
   python3 scripts/compose_prompt.py \
     --style nianhua-suoyang --decade 1980s --flavor ikko-geometric --title "年画缩样" --year "2026"

   # 80s 先锋译丛路线（搭配三分线框与副标）
   python3 scripts/compose_prompt.py \
     --style pioneer-book-series --flavor marber-grid --title "美学译丛" --subtitle "现代构成导论"

   # 回归自检（验证零括号与零黑话残留）
   python3 .agents/skills/nianhua-cover-prompt/scripts/compose_prompt.py --self-test
   ```
   - 需纯无字底图方便后期精排时加 `--no-text`；需原味年代民俗题材时加 `--era-mode vintage`。
3. **核对输出**：确认正文无括号元标签与 HEX 字符，并在 `【设计参考与锁字简报】` 核对书名、年份与副标落位。

## 工作流 B：看图复诊与针对性调整

当用户贴出 AI 生成初稿或参考封面请求修改时，执行 [references/design-principles.md](references/design-principles.md) 第四节协议：
1. **先观测再诊断（What I See → Main Diagnosis）**：先陈述真实画面比例、色数、每个汉字/数字的完整度与字图遮挡，再锁定 1–3 个 `Must-fix` 病灶。
2. **双轨输出**：给出锁定完好区块不变的**局部改图指令**，以及调整 `--style` / `--decade` / `--flavor` / `--cjk-grid` 后的**重抽升级提示词**。

## 目录结构

- `assets/blueprints.json`：v5.1 双细分风格、断代语法、下沉字区、跨轴约束与词库真源。
- `assets/examples.md`：双细分风格、三变体、历史功能与无字底图范例（正文已剥离括号参考）。
- `references/design-principles.md`：第一性原理、年画三重历史功能、断代规范、MECE 矩阵与看图复诊协议。
- `scripts/compose_prompt.py`：v5.1 零依赖提示词组合器（含 `--self-test` 回归校验）。
