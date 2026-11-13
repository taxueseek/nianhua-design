#!/usr/bin/env python3
"""1950s—90s 中国美术出版物（年画缩样 × 80s 先锋译丛）MECE 提示词组合器（v5.1）。

特性：
1. 拆分两大细分风格：年画缩样（传统至现代集大成）与 80s 先锋译丛（现代主义装帧），均兼容三种同代风味变体；
2. 引入真实历史断代语法（1950s-60s / 1970s / 1980s / 1990s）与年画三重历史功能（节庆装饰 / 民间信仰表达 / 大众视觉传播）；
3. 吸收工艺细节、出版饰件、三色/四色面积占比与手工非标字骨，同时建立跨轴互斥约束；
4. 彻底从提示词正文中剥离所有括号原标题与抽象元标签，移入独立的「设计参考与锁字简报」区块。
"""
from __future__ import annotations

import argparse
import json
import random
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

BLUEPRINTS_PATH = Path(__file__).resolve().parent.parent / "assets" / "blueprints.json"

BANNED_PROMPT_TERMS = (
    "东亚排版网格法则",
    "版面锁字分区",
    "核心视觉隐喻",
    "主从分区",
    "字中有画",
    "阶梯错位",
    "负空间双关",
    "压缩重复字带",
    "MECE",
)
HEX_PATTERN = re.compile(r"#[0-9A-Fa-f]{6}")
PAREN_PATTERN = re.compile(r"[（）()]")


def load_blueprints() -> dict[str, Any]:
    with BLUEPRINTS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


@dataclass
class Recipe:
    style: str
    style_name: str
    historical_function: str
    historical_function_name: str
    era_mode: str
    format_type: str
    format_name: str
    decade: str
    skeleton: str
    skeleton_name: str
    layout_id: str
    cjk_grid: str
    cjk_grid_name: str
    tactic: str
    tactic_name: str
    flavor: str
    flavor_name: str
    metaphor: str
    metaphor_name: str
    medium: str
    medium_name: str
    palette: str
    palette_name: str
    palette_hexes: list[str]
    typo: str
    typo_name: str
    accent: str
    accent_name: str
    presentation: str
    aspect_ratio: str
    no_text: bool
    subject: str
    title: str
    year_text: str
    subtitle: str
    frozen_brief: str
    design_reference: str
    prompt: str
    overlay_guide: str


def strip_hex_parens(text: str) -> tuple[str, list[str]]:
    """剥离色板描述中的（#XXXXXX）以保持正文洁净，同时返回提取出的 HEX 列表供参考区使用。"""
    hexes = HEX_PATTERN.findall(text)
    cleaned = re.sub(r"（#[0-9A-Fa-f]{6}）", "", text)
    cleaned = re.sub(r"\(#[0-9A-Fa-f]{6}\)", "", cleaned)
    return cleaned, hexes


def resolve_style_and_format(
    bp: dict[str, Any],
    style_key: str | None,
    format_key: str | None,
    rng: random.Random,
) -> tuple[str, str]:
    styles = bp["styles"]
    if style_key in styles:
        chosen_style = style_key
    elif format_key == "book-series":
        chosen_style = "pioneer-book-series"
    else:
        chosen_style = "nianhua-suoyang"

    allowed_fmts = styles[chosen_style]["allowed_formats"]
    if format_key in allowed_fmts:
        chosen_fmt = format_key
    elif chosen_style == "pioneer-book-series":
        chosen_fmt = "book-series"
    else:
        chosen_fmt = "cover" if format_key not in bp["formats"] else rng.choice(allowed_fmts)
    return chosen_style, chosen_fmt


def pick_decade(
    bp: dict[str, Any],
    style_key: str,
    decade_key: str | None,
    rng: random.Random,
) -> str:
    allowed = bp["styles"][style_key]["allowed_decades"]
    if decade_key in allowed:
        return decade_key
    weights = [bp["decades"][d]["weight"] for d in allowed]
    return rng.choices(allowed, weights=weights, k=1)[0]


def pick_layout_and_skeleton(
    bp: dict[str, Any],
    style_key: str,
    fmt_key: str,
    skeleton_key: str | None,
    flavor_key: str,
    rng: random.Random,
) -> tuple[str, dict[str, Any]]:
    skeletons = bp["skeletons"]
    if skeleton_key in skeletons:
        skel_candidates = [skeleton_key]
    elif style_key == "pioneer-book-series":
        skel_candidates = ["block-cut", "grid-minimal", "window-frame"]
    elif fmt_key == "pattern-book":
        skel_candidates = ["block-cut", "window-frame", "grid-minimal"]
    elif fmt_key == "poster":
        skel_candidates = ["bleed-poster", "block-cut"]
    else:
        skel_candidates = list(skeletons.keys())

    if flavor_key == "marber-grid":
        marber_skels = [
            s for s in skel_candidates
            if any("marber-grid" in l["compatible_flavors"] for l in skeletons[s]["layouts"])
        ]
        if marber_skels:
            skel_candidates = marber_skels

    chosen_skel = rng.choice(skel_candidates)
    layouts = skeletons[chosen_skel]["layouts"]
    compat_layouts = [l for l in layouts if flavor_key in l["compatible_flavors"]]
    chosen_layout = rng.choice(compat_layouts or layouts)
    return chosen_skel, chosen_layout


def pick_cjk_grid(
    bp: dict[str, Any],
    layout_obj: dict[str, Any],
    cjk_grid_key: str | None,
    tactic_key: str,
    rng: random.Random,
) -> str:
    grids = bp["cjk_grids"]
    if cjk_grid_key in grids:
        return cjk_grid_key
    if tactic_key == "stepped-stagger":
        return rng.choices(["contour-stagger", "asymmetric-tension"], weights=[0.6, 0.4], k=1)[0]
    preferred = [g for g in layout_obj.get("preferred_grids", []) if g in grids]
    if preferred:
        return rng.choice(preferred)
    return rng.choice(list(grids.keys()))


def pick_tactic(
    skeleton_key: str,
    layout_obj: dict[str, Any],
    tactic_key: str | None,
    no_text: bool,
    bp: dict[str, Any],
    rng: random.Random,
) -> str:
    tactics = bp["tactics"]
    grid_locked_layouts = {"quad-reversal", "archive-grid-cells", "ticket-double-frame", "rounded-arch-frame"}
    if tactic_key in tactics:
        chosen = tactic_key
    elif no_text:
        chosen = rng.choices(["standard", "negative-space"], weights=[0.7, 0.3], k=1)[0]
    elif layout_obj["id"] in grid_locked_layouts or skeleton_key == "window-frame":
        chosen = rng.choices(["standard", "type-overlap", "type-mask"], weights=[0.65, 0.2, 0.15], k=1)[0]
    elif skeleton_key == "grid-minimal":
        chosen = rng.choices(["standard", "negative-space", "stepped-stagger"], weights=[0.55, 0.25, 0.2], k=1)[0]
    else:
        chosen = rng.choices(
            ["standard", "type-mask", "type-overlap", "stepped-stagger", "negative-space", "repeat-band"],
            weights=[0.35, 0.16, 0.16, 0.13, 0.12, 0.08],
            k=1,
        )[0]

    if no_text and chosen in ("type-mask", "type-overlap", "stepped-stagger", "repeat-band"):
        return "standard"
    return chosen


def pick_medium(
    bp: dict[str, Any],
    style_key: str,
    fmt_key: str,
    decade_key: str,
    skeleton_key: str,
    flavor_key: str,
    medium_key: str | None,
    rng: random.Random,
) -> str:
    mediums = bp["mediums"]
    dec_allowed = bp["decades"][decade_key]["allowed_mediums"]
    forbidden = set(bp["constraints"]["flavor_forbidden_mediums"].get(flavor_key, []))

    pool = [m for m in dec_allowed if m not in forbidden]
    if not pool:
        pool = [m for m in mediums if m not in forbidden]

    if medium_key in mediums and medium_key not in forbidden:
        return medium_key

    if style_key == "pioneer-book-series":
        pref = [m for m in ("geometry-symbol", "monoline-print", "gongbi-watercolor") if m in pool]
        if pref:
            return rng.choice(pref)
    if fmt_key == "pattern-book":
        pref = [m for m in ("monoline-print", "geometry-symbol") if m in pool]
        if pref:
            return rng.choice(pref)
    if skeleton_key == "grid-minimal":
        pref = [m for m in ("geometry-symbol", "monoline-print", "gongbi-watercolor") if m in pool]
        if pref:
            return rng.choice(pref)
    return rng.choice(pool)


def pick_palette(
    bp: dict[str, Any],
    style_key: str,
    decade_key: str,
    flavor_key: str,
    palette_key: str | None,
    rng: random.Random,
) -> str:
    palettes = bp["palettes"]
    dec_allowed = bp["decades"][decade_key]["allowed_palettes"]
    forbidden = set(bp["constraints"]["flavor_forbidden_palettes"].get(flavor_key, []))
    pool = [p for p in dec_allowed if p not in forbidden]
    if not pool:
        pool = [p for p in palettes if p not in forbidden]

    if palette_key in palettes and palette_key in pool:
        return palette_key
    if palette_key in palettes and palette_key not in forbidden and style_key == "pioneer-book-series":
        return palette_key

    if style_key == "pioneer-book-series":
        pref = [p for p in bp["constraints"]["style_preferred_palettes"]["pioneer-book-series"] if p in pool]
        if pref:
            weights = [0.5 if p == "literary-muted" else 0.25 if p == "paper-ink" else 0.125 for p in pref]
            return rng.choices(pref, weights=weights, k=1)[0]

    return rng.choice(pool)


def pick_typo_and_title_desc(
    bp: dict[str, Any],
    style_key: str,
    decade_key: str,
    cjk_grid_key: str,
    typo_key: str | None,
    rng: random.Random,
) -> tuple[str, str, str]:
    typos = bp["typos"]
    dec_allowed = bp["decades"][decade_key]["allowed_typos"]
    if typo_key in typos and typo_key in dec_allowed:
        chosen_typo = typo_key
    elif style_key == "pioneer-book-series":
        pref = [t for t in bp["constraints"]["style_preferred_typos"]["pioneer-book-series"] if t in dec_allowed]
        chosen_typo = rng.choice(pref or dec_allowed)
    else:
        chosen_typo = rng.choice(dec_allowed)

    direction = bp["cjk_grids"][cjk_grid_key]["text_direction"]
    t_obj = typos[chosen_typo]
    compat_titles = [c["desc"] for c in t_obj["title_choices"] if direction in c["directions"]]
    if not compat_titles:
        compat_titles = [c["desc"] for c in t_obj["title_choices"]]
    return chosen_typo, rng.choice(compat_titles), rng.choice(t_obj["number_choices"])


def pick_accent(
    bp: dict[str, Any],
    style_key: str,
    decade_key: str,
    skeleton_key: str,
    flavor_key: str,
    accent_key: str | None,
    rng: random.Random,
) -> str:
    accents = bp["accents"]
    forbidden = set(bp["decades"][decade_key].get("forbidden_accents", []))
    forbidden |= set(bp["constraints"]["skeleton_forbidden_accents"].get(skeleton_key, []))
    if style_key == "pioneer-book-series":
        forbidden |= {"traditional-border", "damask-paper"}
    if flavor_key == "marber-grid":
        forbidden |= {"double-hairline"}

    if accent_key in accents and accent_key not in forbidden:
        return accent_key

    pool = [a for a in accents if a not in forbidden]
    if style_key == "pioneer-book-series":
        pref = [a for a in ("none", "seal-stamp", "pinyin-band", "double-hairline") if a in pool]
        return rng.choices(pref or pool, weights=[0.5 if a == "none" else 0.2 for a in (pref or pool)], k=1)[0]
    return rng.choices(pool, weights=[0.35 if a == "none" else 0.15 for a in pool], k=1)[0]


def pick_aspect(
    bp: dict[str, Any],
    fmt_key: str,
    medium_key: str,
    presentation_key: str,
    override: str | None,
    rng: random.Random,
) -> str:
    if override:
        return override
    if presentation_key == "white-table-mockup":
        return rng.choice(["4:3", "1:1"])
    if medium_key in ("retro-film", "gouache-poster"):
        return rng.choice(["3:4", "2:3"])
    return rng.choice(bp["formats"][fmt_key]["default_aspects"])


def build_clean_text_block(
    no_text: bool,
    title: str,
    year_text: str,
    subtitle: str,
    title_desc: str,
    number_desc: str,
    layout_obj: dict[str, Any],
    grid_obj: dict[str, Any],
    tactic_key: str,
    tactic_obj: dict[str, Any],
) -> tuple[str, str, str]:
    """生成不含任何括号元标签或抽象黑话的纯视觉锁字句，并分离输出参考简报。"""
    title_zone = layout_obj["title_zone"]
    year_zone = layout_obj["year_zone"]
    sub_zone = layout_obj["sub_zone"]

    if no_text:
        text_block = (
            f"在{title_zone}与{year_zone}保留完整干净的纯色负空间以便后期排字，"
            "画面内不出现任何汉字、数字、英文或乱码符号。"
        )
        sub_part = f" / 副标（{sub_zone}）：「{subtitle}」" if subtitle else ""
        overlay_guide = (
            f"后期叠字建议：标题（{title_zone}）用{title_desc}排入「{title}」"
            f" / 年份（{year_zone}）用{number_desc}排入「{year_text}」{sub_part}。"
        )
        frozen_brief = f"无字底图模式 | 预留标题区={title_zone} | 预留年份区={year_zone}"
        return text_block, overlay_guide, frozen_brief

    tactic_clause = f"{tactic_obj['rule']}；" if tactic_key != "standard" and tactic_obj["rule"] else ""
    sub_clause = f"，并在{sub_zone}用细瘦手工宋体单行小字精确呈现\"{subtitle}\"" if subtitle else ""
    text_block = (
        f"文字编排上，{grid_obj['rule']}；{tactic_clause}"
        f"在{title_zone}以{title_desc}的字骨清晰完整地渲染汉字\"{title}\"，"
        f"在{year_zone}以视觉分量极大的{number_desc}渲染年份\"{year_text}\""
        f"{sub_clause}。"
        "除上述指定文字外不出现任何其他多余文字、水印或签名。"
    )
    brief_sub = f' / "{subtitle}" ({sub_zone})' if subtitle else ""
    frozen_brief = f'"{title}" ({title_zone}) / "{year_text}" ({year_zone}){brief_sub}'
    return text_block, "", frozen_brief


def build_prompt(
    bp: dict[str, Any],
    style_key: str | None = None,
    function_key: str | None = None,
    era_mode: str = "contemporary",
    format_key: str | None = None,
    decade_key: str | None = None,
    skeleton_key: str | None = None,
    cjk_grid_key: str | None = None,
    tactic_key: str | None = None,
    flavor_key: str = "none",
    metaphor_key: str | None = None,
    medium_key: str | None = None,
    palette_key: str | None = None,
    typo_key: str | None = None,
    accent_key: str | None = None,
    presentation_key: str | None = None,
    aspect: str | None = None,
    no_text: bool = False,
    custom_palette: str | None = None,
    custom_layout: str | None = None,
    subject: str | None = None,
    title: str | None = None,
    year_text: str | None = None,
    subtitle: str | None = None,
    seed: int | None = None,
) -> Recipe:
    rng = random.Random(seed)
    chosen_style, chosen_fmt = resolve_style_and_format(bp, style_key, format_key, rng)
    chosen_decade = pick_decade(bp, chosen_style, decade_key, rng)

    funcs = bp["historical_functions"]
    if function_key in funcs:
        chosen_func = function_key
    elif chosen_style == "pioneer-book-series":
        chosen_func = "mass-visual"
    else:
        chosen_func = rng.choice(list(funcs.keys()))

    chosen_flavor = flavor_key if flavor_key in bp["flavors"] else "none"
    chosen_skel, layout_obj = pick_layout_and_skeleton(bp, chosen_style, chosen_fmt, skeleton_key, chosen_flavor, rng)
    chosen_tactic = pick_tactic(chosen_skel, layout_obj, tactic_key, no_text, bp, rng)
    chosen_cjk_grid = pick_cjk_grid(bp, layout_obj, cjk_grid_key, chosen_tactic, rng)

    metaphors = bp["metaphors"]
    if metaphor_key in metaphors:
        chosen_metaphor = metaphor_key
    elif chosen_fmt == "pattern-book":
        chosen_metaphor = rng.choices(["grid-archive", "single-object", "nested-frame"], weights=[0.55, 0.3, 0.15], k=1)[0]
    else:
        chosen_metaphor = rng.choices(["single-object", "dual-contrast", "nested-frame", "grid-archive"], weights=[0.5, 0.2, 0.2, 0.1], k=1)[0]

    chosen_med = pick_medium(bp, chosen_style, chosen_fmt, chosen_decade, chosen_skel, chosen_flavor, medium_key, rng)
    chosen_pal = pick_palette(bp, chosen_style, chosen_decade, chosen_flavor, palette_key, rng)
    chosen_typo, chosen_title_desc, chosen_number_desc = pick_typo_and_title_desc(
        bp, chosen_style, chosen_decade, chosen_cjk_grid, typo_key, rng
    )
    chosen_accent = pick_accent(bp, chosen_style, chosen_decade, chosen_skel, chosen_flavor, accent_key, rng)
    chosen_pres = presentation_key if presentation_key in bp["presentations"] else "clean-fullbleed"
    chosen_aspect = pick_aspect(bp, chosen_fmt, chosen_med, chosen_pres, aspect, rng)

    style_obj = bp["styles"][chosen_style]
    func_obj = funcs[chosen_func]
    fmt_obj = bp["formats"][chosen_fmt]
    dec_obj = bp["decades"][chosen_decade]
    skel_obj = bp["skeletons"][chosen_skel]
    grid_obj = bp["cjk_grids"][chosen_cjk_grid]
    tactic_obj = bp["tactics"][chosen_tactic]
    flavor_obj = bp["flavors"][chosen_flavor]
    metaphor_obj = metaphors[chosen_metaphor]
    med_obj = bp["mediums"][chosen_med]
    pal_obj = bp["palettes"][chosen_pal]
    typo_obj = bp["typos"][chosen_typo]
    accent_obj = bp["accents"][chosen_accent]

    raw_palette_desc = custom_palette or rng.choice(pal_obj["choices"])
    clean_palette_desc, palette_hexes = strip_hex_parens(raw_palette_desc)

    if subject:
        chosen_subject = subject
    elif chosen_style == "pioneer-book-series" and era_mode == "contemporary":
        chosen_subject = med_obj.get("default_book_series", med_obj["default_contemporary"])
    elif era_mode == "vintage":
        chosen_subject = med_obj["default_vintage"]
    else:
        chosen_subject = med_obj["default_contemporary"]

    if title:
        chosen_title = title
    elif chosen_style == "pioneer-book-series":
        chosen_title = rng.choice(["美学译丛", "文艺丛书", "现代构成", "形式导论", "视觉语法"])
    elif era_mode == "vintage":
        title_map = {
            "cover": ["年画缩样", "风物画集", "山海缩样"],
            "calendar": ["瑞岁年历", "春风挂历", "岁时画历"],
            "poster": ["时代新风", "建设纪元", "百花齐放"],
            "pattern-book": ["装饰图案集", "报头题图集", "民间纹样集"],
            "book-series": ["美学译丛", "文艺丛书", "现代画册"],
        }
        chosen_title = rng.choice(title_map[chosen_fmt])
    else:
        chosen_title = rng.choice(["算力纪元", "城市漫游", "街头手冲", "夜行巴士", "未来缩样"])

    vintage_years = {
        "1950s-60s": ["1958", "1960", "1965"],
        "1970s": ["1973", "1977", "1979"],
        "1980s": ["1981", "1984", "'89"],
        "1990s": ["1990", "'91", "'93"],
    }
    chosen_year = year_text or (
        rng.choice(vintage_years[chosen_decade])
        if era_mode == "vintage"
        else ("'26" if chosen_decade == "1990s" else "2026")
    )
    chosen_sub = (subtitle or "").strip()

    layout_sentence = custom_layout or layout_obj["desc"]
    flavor_sentence = (
        f"{style_obj['flavor_adaptation'][chosen_flavor]}。"
        if chosen_flavor != "none"
        else ""
    )
    accent_sentence = f"{accent_obj['rule']}。" if accent_obj["rule"] else ""
    paper_sentence = (
        "全新铜版纸胶印质感，微暖胶片色调"
        if chosen_med == "retro-film"
        else dec_obj["paper_rule"]
    )
    func_sentence = func_obj["visual_cue"] if chosen_style == "nianhua-suoyang" else ""
    func_clause = f"{func_sentence}，" if func_sentence else ""

    text_block, overlay_guide, frozen_brief = build_clean_text_block(
        no_text=no_text,
        title=chosen_title,
        year_text=chosen_year,
        subtitle=chosen_sub,
        title_desc=chosen_title_desc,
        number_desc=chosen_number_desc,
        layout_obj=layout_obj,
        grid_obj=grid_obj,
        tactic_key=chosen_tactic,
        tactic_obj=tactic_obj,
    )

    # 正文完全剥离括号原标题与内部黑话，只保留可画、连续的中文视觉指令
    # 同时去掉无意义的连续逗号或重复标点
    raw_prompt = (
        f"{chosen_aspect} 比例，中国{dec_obj['label']}的{fmt_obj['prompt_label']}。"
        f"{bp['presentations'][chosen_pres]}，{paper_sentence}。"
        f"{flavor_sentence}"
        f"{clean_palette_desc}。"
        f"{layout_sentence}。"
        f"{text_block}"
        f"主体画面聚焦{chosen_subject}，{metaphor_obj['visual_hint']}，{med_obj['prompt_rule']}，{func_clause}"
        f"{accent_sentence}"
        "构图克制大留白，绝不堆砌无关传统花纹，纯平面高清印刷设计稿，拒绝现代电脑标准黑体字库，禁止 3D 立体光影、塑料高光、影视体积光与现代霓虹渐变。"
    )
    prompt = re.sub(r"。。+", "。", raw_prompt)

    hex_info = " ".join(palette_hexes) if palette_hexes else "自定义"
    design_reference = (
        f"细分风格：{style_obj['name']} | 历史功能：{func_obj['name']} | 断代：{chosen_decade} | 载体：{fmt_obj['name']}\n"
        f"坐标明细：{skel_obj['name']}（{layout_obj['id']}）· {grid_obj['name']} + {tactic_obj['name']} | "
        f"风味={flavor_obj['name']} | 隐喻={metaphor_obj['name']} | 媒介={med_obj['name']} | "
        f"色系={pal_obj['name']}（{hex_info}）| 字形={typo_obj['name']} | 饰件={accent_obj['name']}\n"
        f"锁字简报：{frozen_brief}"
    )

    return Recipe(
        style=chosen_style,
        style_name=style_obj["name"],
        historical_function=chosen_func,
        historical_function_name=func_obj["name"],
        era_mode=era_mode,
        format_type=chosen_fmt,
        format_name=fmt_obj["name"],
        decade=chosen_decade,
        skeleton=chosen_skel,
        skeleton_name=skel_obj["name"],
        layout_id=layout_obj["id"],
        cjk_grid=chosen_cjk_grid,
        cjk_grid_name=grid_obj["name"],
        tactic=chosen_tactic,
        tactic_name=tactic_obj["name"],
        flavor=chosen_flavor,
        flavor_name=flavor_obj["name"],
        metaphor=chosen_metaphor,
        metaphor_name=metaphor_obj["name"],
        medium=chosen_med,
        medium_name=med_obj["name"],
        palette=chosen_pal,
        palette_name=pal_obj["name"],
        palette_hexes=palette_hexes,
        typo=chosen_typo,
        typo_name=typo_obj["name"],
        accent=chosen_accent,
        accent_name=accent_obj["name"],
        presentation=chosen_pres,
        aspect_ratio=chosen_aspect,
        no_text=no_text,
        subject=chosen_subject,
        title=chosen_title,
        year_text=chosen_year,
        subtitle=chosen_sub,
        frozen_brief=frozen_brief,
        design_reference=design_reference,
        prompt=prompt,
        overlay_guide=overlay_guide,
    )


def run_self_test(bp: dict[str, Any]) -> None:
    """跨风格 × 三风味 × 断代 × 无字模式的回归自检。"""
    cases: list[dict[str, Any]] = []
    for i in range(60):
        style = "nianhua-suoyang" if i % 2 == 0 else "pioneer-book-series"
        flavor = ["none", "ikko-geometric", "marber-grid", "riso-overprint"][i % 4]
        no_text = (i % 7 == 0)
        cases.append({"seed": i + 1, "style_key": style, "flavor_key": flavor, "no_text": no_text})
    for dec in ("1950s-60s", "1970s", "1980s", "1990s"):
        cases.append({"seed": 100, "style_key": "nianhua-suoyang", "decade_key": dec, "flavor_key": "none"})
    for fl in ("ikko-geometric", "marber-grid", "riso-overprint"):
        cases.append({"seed": 200, "style_key": "pioneer-book-series", "flavor_key": fl})

    for idx, kw in enumerate(cases):
        r = build_prompt(bp=bp, **kw)
        assert not PAREN_PATTERN.search(r.prompt), f"case {idx} 提示词正文出现括号残留: {r.prompt}"
        assert not HEX_PATTERN.search(r.prompt), f"case {idx} 提示词正文出现 HEX 残留: {r.prompt}"
        for term in BANNED_PROMPT_TERMS:
            assert term not in r.prompt, f"case {idx} 提示词正文残留内部术语 {term}: {r.prompt}"
        if r.decade in ("1950s-60s", "1970s"):
            assert r.palette != "literary-muted", f"case {idx} 断代越界: {r.decade} 配了 literary-muted"
        if r.flavor == "ikko-geometric":
            assert r.medium not in ("retro-film", "gongbi-watercolor"), f"case {idx} 风味冲突: {r.flavor} + {r.medium}"
        if r.cjk_grid == "vertical-cjk-cross":
            assert "极扁宽" not in r.prompt, f"case {idx} 竖排冲突: vertical-cjk-cross 配了极扁宽字形"
        if r.no_text:
            assert r.overlay_guide, f"case {idx} 无字模式缺后期叠字建议"
            assert r.title not in r.prompt and r.year_text not in r.prompt, f"case {idx} 无字模式泄漏文字"

    print(f"self-test passed: {len(cases)}/{len(cases)} cases clean.")


def main() -> None:
    bp = load_blueprints()
    parser = argparse.ArgumentParser(description="1950s—90s 中国美术出版物（年画缩样 × 80s 先锋译丛）提示词组合器（v5.1）")
    parser.add_argument("--style", choices=list(bp["styles"].keys()), help="细分风格：nianhua-suoyang / pioneer-book-series")
    parser.add_argument("--function", dest="func_type", choices=list(bp["historical_functions"].keys()), help="年画历史功能：festive-ornament / folk-belief / mass-visual")
    parser.add_argument("--mode", choices=["random", "custom"], default="random", help="random=随机或半锁定；custom=全自定义")
    parser.add_argument("--era-mode", choices=["contemporary", "vintage"], default="contemporary", help="contemporary=当代主题转译（默认）；vintage=年代原味复刻")
    parser.add_argument("--format", dest="format_type", choices=list(bp["formats"].keys()), help="出版物品类")
    parser.add_argument("--decade", choices=list(bp["decades"].keys()), help="历史断代基调")
    parser.add_argument("--skeleton", choices=list(bp["skeletons"].keys()), help="主构成骨架")
    parser.add_argument("--cjk-grid", choices=list(bp["cjk_grids"].keys()), help="汉字排布网格")
    parser.add_argument("--tactic", choices=list(bp["tactics"].keys()), help="字图空间手法")
    parser.add_argument("--flavor", choices=list(bp["flavors"].keys()), default="none", help="三种同代风味变体")
    parser.add_argument("--metaphor", choices=list(bp["metaphors"].keys()), help="视觉隐喻")
    parser.add_argument("--medium", choices=list(bp["mediums"].keys()), help="图形媒介")
    parser.add_argument("--palette", choices=list(bp["palettes"].keys()), help="专色油墨系")
    parser.add_argument("--typo", choices=list(bp["typos"].keys()), help="手工字形")
    parser.add_argument("--accent", choices=list(bp["accents"].keys()), help="年代工艺与出版饰件")
    parser.add_argument("--presentation", choices=list(bp["presentations"].keys()), help="默认 clean-fullbleed")
    parser.add_argument("--aspect", help="画幅比例，如 3:4、4:3、1:1、2:3、16:9")
    parser.add_argument("--no-text", action="store_true", help="生成纯无字视觉底图，并附后期叠字建议")
    parser.add_argument("--custom-palette", help="自定义配色描写")
    parser.add_argument("--custom-layout", help="自定义版式描写")
    parser.add_argument("--subject", help="自定义主体内容")
    parser.add_argument("--title", help="自定义主标题（建议 2–6 字）")
    parser.add_argument("--year", help="自定义年份或编号（建议 4 字符内）")
    parser.add_argument("--subtitle", help="可选辅文短标/社名/期号")
    parser.add_argument("--count", type=int, default=1, help="生成方案数量")
    parser.add_argument("--seed", type=int, help="随机种子")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    parser.add_argument("--self-test", action="store_true", help="运行回归自检")
    args = parser.parse_args()

    if args.self_test:
        run_self_test(bp)
        return

    results = []
    for i in range(max(1, args.count)):
        cur_seed = (args.seed + i) if args.seed is not None else None
        recipe = build_prompt(
            bp=bp,
            style_key=args.style,
            function_key=args.func_type,
            era_mode=args.era_mode,
            format_key=args.format_type,
            decade_key=args.decade,
            skeleton_key=args.skeleton,
            cjk_grid_key=args.cjk_grid,
            tactic_key=args.tactic,
            flavor_key=args.flavor,
            metaphor_key=args.metaphor,
            medium_key=args.medium,
            palette_key=args.palette,
            typo_key=args.typo,
            accent_key=args.accent,
            presentation_key=args.presentation,
            aspect=args.aspect,
            no_text=args.no_text,
            custom_palette=args.custom_palette,
            custom_layout=args.custom_layout,
            subject=args.subject,
            title=args.title,
            year_text=args.year,
            subtitle=args.subtitle,
            seed=cur_seed,
        )
        results.append(asdict(recipe))

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    for idx, item in enumerate(results, start=1):
        mode_tag = "无字底图" if item["no_text"] else item["era_mode"]
        flavor_tag = f" · {item['flavor_name']}" if item["flavor"] != "none" else ""
        print(f"=== 方案 {idx} [{item['style_name']} · {mode_tag} · {item['decade']}{flavor_tag}] ===")
        print(f"画幅呈现：{item['aspect_ratio']} · {item['presentation']}")
        print(f"【提示词正文（{len(item['prompt'])} 字 · 已剥离括号与参考元标签）】\n{item['prompt']}\n")
        print(f"【设计参考与锁字简报】\n{item['design_reference']}")
        if item["overlay_guide"]:
            print(f"{item['overlay_guide']}")
        print()


if __name__ == "__main__":
    main()
