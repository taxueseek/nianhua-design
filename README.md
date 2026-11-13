# nianhua-design

年画缩样 × 80s 先锋译丛封面提示词 skill。基于平面现代主义（Graphic Modernism）与年画三重历史功能规律，把「年画缩样」与「80s 先锋译丛」两条细分风格拆成一套 MECE 正交词库，输出高可控的中文生图提示词与无字底图，并把括号原标题与坐标参考从提示词正文中彻底剥离。

版本：v0.0.1。

## 它解决什么

给 AI 生图模型写中文封面提示词时，常见问题是要么泛泛堆砌风格词，要么把内部术语、HEX 色值、坐标参数直接写进正文，导致出图不可控。本 skill 把风格、断代、载体、字区、排布、配色、字形拆成可组合的正交维度，由脚本统一拼装，正文只留纯正、连续、可直接绘形的中文视觉指令。

## 两大细分风格

- **`nianhua-suoyang`（年画缩样 · 传统至现代集大成）**：1950s–90s 美术出版社内部订货缩样与画集封面体系。工笔开光、民间剪纸锯齿线刻、套色木刻、篆刻方印与毛笔题签，和田字格色块切割、大留白、摄影拼贴与手绘非标变形美术字并存。
- **`pioneer-book-series`（80s 先锋译丛 · 现代主义装帧）**：1980 年代文艺丛书、美学译丛与思想画册装帧路线。吸收包豪斯与俄国构成主义，靠大留白、正圆与三角与实心条带硬边切割、低饱和书卷套印与建筑梁柱般的手工几何书名建立秩序。

叠加年画三重历史功能（`--function`：节庆装饰 / 民间信仰表达 / 大众视觉传播）、真实历史断代（`--decade`：1950s-60s / 1970s / 1980s / 1990s）与三种同代风味变体（`--flavor`：几何东方构成 / 三分线框丛书 / 双专色孔版叠印）。

## 安装

把本仓整体复制到你的 skills 目录，例如：

```bash
git clone https://github.com/taxueseek/nianhua-design.git ~/.agents/skills/nianhua-design
```

## 用法

```bash
# 年画缩样路线（支持断代与三重功能）
python3 scripts/compose_prompt.py \
  --style nianhua-suoyang --decade 1980s --flavor ikko-geometric --title "年画缩样" --year "2026"

# 80s 先锋译丛路线（搭配三分线框与副标）
python3 scripts/compose_prompt.py \
  --style pioneer-book-series --flavor marber-grid --title "美学译丛" --subtitle "现代构成导论"

# 回归自检（验证零括号与零黑话残留）
python3 scripts/compose_prompt.py --self-test
```

需纯无字底图方便后期精排时加 `--no-text`；需原味年代民俗题材时加 `--era-mode vintage`。

贴出 AI 生成初稿或参考封面请求修改时，按 `references/design-principles.md` 第四节的看图复诊协议处理：先观测再诊断，再给局部改图指令与重抽升级提示词。

## 目录结构

- `SKILL.md`：技能主文件（美学母体、正交维度、两条工作流）。
- `assets/blueprints.json`：双细分风格、断代语法、下沉字区、跨轴约束与词库真源。
- `assets/examples.md`：双细分风格、三变体、历史功能与无字底图范例。
- `references/design-principles.md`：第一性原理、年画三重历史功能、断代规范、MECE 矩阵与看图复诊协议。
- `scripts/compose_prompt.py`：零依赖提示词组合器（含 `--self-test` 回归校验）。

## 许可

MIT，见 [LICENSE](LICENSE)。
