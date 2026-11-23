#!/usr/bin/env python3
"""
Render the profile README's cards as animated SVGs into cards/.

Design: "Three Worlds" (paper, ink, and one colour per world:
BUILD blue, BRAND red, LEARN yellow; Instrument Serif, Geist, Geist Mono).

Every card is a standalone SVG shown through <img>, so it can only use what GitHub
allows there: inline CSS animations, SMIL and fonts embedded as data URIs (no JS,
no external requests). Fonts are subset WOFFs in fonts/ (SIL OFL).

Live numbers come from data/contributions.json (fetch_contributions.py).
Run by .github/workflows/update-profile-art.yml after fetch_contributions.py.
"""
import base64
import datetime
import json
import os
import random
import re
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data", "contributions.json")
OUT = os.path.join(ROOT, "cards")
FONTS = os.path.join(ROOT, "fonts")
PORTRAIT = os.path.join(OUT, "portrait.png")

# ---- Personalization Tokens (Pranjal Karan) ---------------------------------
FIRST_NAME = "Pranjal"
LAST_NAME = "Karan"
ROLE_BADGE = "FULLSTACK ENGINEER · HEALTH INFORMATICS"
TAGLINE_LINES = [
    "Building scalable healthcare platforms, real-time IoT,",
    "and intelligent LLM systems for modern software."
]
WEBSITE_DISPLAY = "github.com/Pranjal-k22"

# World Metrics
BUILD_NUMBER = "3+"
BUILD_LABEL = "platforms"
BUILD_DESC = "HealthPulse, HealConnect (real-time IoT), and ReconAI (FinTech)."

BRAND_NUMBER = "1.3K+"
BRAND_LABEL = "contributions"
BRAND_DESC = "Year-round open source shipping across web, AI and healthcare systems."

LEARN_NUMBER = "2027"
LEARN_LABEL = "class"
LEARN_DESC = "B.Tech CSE in Health Informatics · Open to SDE Internships 2026/27."

# Pinned Repositories: (repo_slug, description, language, accent_color)
REPOS = [
    ("Healthcare-app-manager", "HealthPulse: Clinical appointments and management platform with AI summaries.", "TypeScript", "#2f55ff"),
    ("AstroSync", "AI compatibility analysis with multi-model fallback and serverless functions.", "TypeScript", "#ef3b2d"),
    ("Pranjal-k22", "Interactive animated Three Worlds GitHub profile with daily data refresh.", "Python", "#ffc81a"),
]

# ---- Brand Tokens -----------------------------------------------------------
PAPER = "#f3f3f1"
PAPER_DEEP = "#e2e2de"
INK = "#111111"
INK_SOFT = "#3a3a3c"
MUTED = "#6e6e73"
RULE = "#dcdcd7"
TECH = "#2f55ff"        # BUILD Blue
STUDIO = "#ef3b2d"      # BRAND Red
LEARN_COLOR = "#ffc81a" # LEARN Yellow
W = 880                 # Full card width (GitHub's README max column width)

SERIF = "'Instrument Serif', Georgia, serif"
SANS = "Geist, system-ui, -apple-system, sans-serif"
MONO = "'Geist Mono', ui-monospace, SFMono-Regular, Menlo, monospace"

FONT_FILES = {
    "serif": ("Instrument Serif", "normal", 400, "serif-400.woff"),
    "serif-i": ("Instrument Serif", "italic", 400, "serif-italic.woff"),
    "sans": ("Geist", "normal", 400, "geist-400.woff"),
    "sans-b": ("Geist", "normal", 600, "geist-600.woff"),
    "mono": ("Geist Mono", "normal", 400, "geistmono-400.woff"),
}

BASE_CSS = """
@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes pop{0%{opacity:0;transform:scale(.3)}70%{opacity:1;transform:scale(1.15)}100%{opacity:1;transform:none}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}
@keyframes nudge{0%,100%{transform:none}50%{transform:translateX(4px)}}
@keyframes nudgeup{0%,100%{transform:none}50%{transform:translate(3px,-3px)}}
.r{opacity:0;animation:rise .8s cubic-bezier(.2,.7,.2,1) both;transform-box:fill-box}
.f{opacity:0;animation:fade .9s ease-out both}
.g{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow .8s cubic-bezier(.2,.7,.2,1) both}
.p{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .4s ease-out both}
.live{animation:pulse 1.6s ease-in-out infinite}
.n{transform-box:fill-box;animation:nudge 1.8s ease-in-out infinite}
.nu{transform-box:fill-box;animation:nudgeup 1.8s ease-in-out infinite}
@keyframes tilein{0%{opacity:0;transform:translateY(90px) scale(.6) rotate(-9deg)}55%{opacity:1;transform:translateY(-10px) scale(1.05) rotate(2deg)}75%{transform:translateY(3px) scale(.98) rotate(-.8deg)}90%{transform:translateY(-1px) scale(1.01) rotate(.2deg)}100%{opacity:1;transform:none}}
@keyframes slidein{from{opacity:0;transform:translateX(-26px)}to{opacity:1;transform:none}}
@keyframes arrowin{0%{opacity:0;transform:translateX(-30px)}60%{opacity:1;transform:translateX(6px)}100%{opacity:1;transform:none}}
@keyframes roll{from{transform:translateY(60px)}to{transform:none}}
@keyframes sheen{0%{transform:translateX(-260px) skewX(-20deg)}22%,100%{transform:translateX(420px) skewX(-20deg)}}
@keyframes ring{0%{opacity:.7;transform:scale(.2)}100%{opacity:0;transform:scale(2.4)}}
.ti{opacity:0;transform-box:fill-box;transform-origin:50% 60%;animation:tilein 1.1s cubic-bezier(.2,.8,.2,1) both}
.sl{opacity:0;transform-box:fill-box;animation:slidein .6s cubic-bezier(.2,.7,.2,1) both}
.ai{opacity:0;transform-box:fill-box;animation:arrowin .7s cubic-bezier(.2,.7,.2,1) both}
.ro{transform-box:fill-box;animation:roll .8s cubic-bezier(.15,.8,.2,1) both}
.sh{animation:sheen 5s ease-in-out infinite}
.rg{opacity:0;transform-box:fill-box;transform-origin:center;animation:ring 1s ease-out both}
@media (prefers-reduced-motion: reduce){.r,.f,.g,.p,.live,.n,.nu,.ti,.sl,.ai,.ro,.rg{animation:none!important;opacity:1!important;transform:none!important}.sh,.rg{display:none}}
"""


def font_face(keys):
    """Embed requested subset WOFF font files as base64 data URIs."""
    out = []
    for k in keys:
        fam, style, weight, fn = FONT_FILES[k]
        font_path = os.path.join(FONTS, fn)
        if os.path.exists(font_path):
            b64 = base64.b64encode(open(font_path, "rb").read()).decode()
            out.append(
                f"@font-face{{font-family:'{fam}';font-style:{style};font-weight:{weight};"
                f"src:url(data:font/woff;base64,{b64}) format('woff')}}"
            )
    return "".join(out)


GAP = 12          # 12px gap between cards
BOTTOM = 12       # 12px bottom padding
COL = W / 3       # Each column in a row of three is 293.333px


def svg(w, h, body, fonts, label, extra_css="", left=0, right=0, bottom=BOTTOM):
    """Draw a card with dimensions (w x h) inside a padded viewport for perfect grid tiling."""
    if left:
        body = f'<g transform="translate({left:.3f} 0)">{body}</g>'
    w_total, h_total = w + left + right, h + bottom
    css = font_face(fonts) + BASE_CSS + extra_css
    if os.environ.get("STATIC"):
        css += ".r,.f,.g,.p,.live,.n,.nu,.ti,.sl,.ai,.ro{animation:none!important;opacity:1!important;transform:none!important}.sh,.rg{display:none}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w_total:.3f}" height="{h_total}" viewBox="0 0 {w_total:.3f} {h_total}" '
        f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
        f"<style>{css}</style>{body}</svg>"
    )


def write(name, content):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"wrote cards/{name} ({len(content) // 1024} KB)")


def d(s):
    return f'style="animation-delay:{s:.2f}s"'


def wrap(text, n):
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > n:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line] if line else lines


def text_lines(x, y, lines, lh, attrs):
    return "".join(
        f'<text x="{x}" y="{y + i * lh}" {attrs}>{escape(l)}</text>' for i, l in enumerate(lines)
    )


# ---- 1 · Hero Card (Modern Editorial Layout with Transparent Cutout) ---------
def hero():
    h = 420
    portrait_svg = ""
    if os.path.exists(PORTRAIT):
        with open(PORTRAIT, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode("ascii")
        portrait_svg = f"""
<!-- Right Column: Illustrated Cutout Portrait -->
<g class="r" {d(0.35)}>
  <image x="535" y="20" width="280" height="385"
         href="data:image/png;base64,{b64_data}"
         xlink:href="data:image/png;base64,{b64_data}"
         preserveAspectRatio="xMidYMid meet"/>
</g>"""
    else:
        # Fallback terminal box if portrait image is not found
        portrait_svg = f"""
<g class="r" {d(0.4)} transform="translate(510, 48)">
  <rect width="322" height="324" rx="12" fill="{PAPER_DEEP}" stroke="{RULE}" stroke-width="1"/>
  <circle cx="20" cy="22" r="4.5" fill="#ff5f56"/>
  <circle cx="36" cy="22" r="4.5" fill="#ffbd2e"/>
  <circle cx="52" cy="22" r="4.5" fill="#27c93f"/>
  <text x="161" y="26" text-anchor="middle" font-family="{MONO}" font-size="11" fill="{MUTED}">profile.config.ts</text>
  <line x1="0" y1="42" x2="322" y2="42" stroke="{RULE}" stroke-width="1"/>
  <g font-family="{MONO}" font-size="12">
    <text x="20" y="74" fill="{MUTED}">const <tspan fill="{TECH}">developer</tspan> = &#123;</text>
    <text x="36" y="104" fill="{MUTED}">focus: <tspan fill="{INK}">"Health &amp; AI Systems"</tspan>,</text>
    <text x="36" y="134" fill="{MUTED}">stack: [<tspan fill="{STUDIO}">"Next.js"</tspan>, <tspan fill="{TECH}">"FastAPI"</tspan>, <tspan fill="{INK}">"Node"</tspan>],</text>
    <text x="36" y="164" fill="{MUTED}">status: <tspan fill="{TECH}">"Internships 26/27"</tspan>,</text>
    <text x="36" y="194" fill="{MUTED}">class: <tspan fill="{INK}">"B.Tech CSE '27"</tspan></text>
    <text x="20" y="224" fill="{MUTED}">&#125;;</text>
  </g>
  <g class="f" {d(0.9)} transform="translate(20, 252)">
    <rect width="282" height="48" rx="8" fill="{PAPER}" stroke="{RULE}" stroke-width="1"/>
    <circle class="live" cx="20" cy="24" r="4" fill="{TECH}"/>
    <text x="36" y="28" font-family="{MONO}" font-size="11" fill="{INK_SOFT}">Shipping healthcare &amp; AI products</text>
  </g>
</g>"""

    body = f"""
<defs>
  <linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="600" y2="0">
    <stop offset="0" stop-color="{INK}"/><stop offset=".42" stop-color="{INK}"/>
    <stop offset=".5" stop-color="{TECH}"/><stop offset=".58" stop-color="{INK}"/>
    <stop offset="1" stop-color="{INK}"/>
    <animateTransform attributeName="gradientTransform" type="translate" values="-600 0;600 0;600 0"
      keyTimes="0;.45;1" dur="7s" begin="1.6s" repeatCount="indefinite"/>
  </linearGradient>
</defs>
<rect width="{W}" height="{h}" rx="14" fill="{PAPER}"/>

<!-- Left Column: Editorial Headline & Bio -->
<g class="f" {d(0)}>
  <rect class="live" x="48" y="49" width="8" height="8" rx="2" fill="{TECH}"/>
  <text x="66" y="57" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MUTED}">{ROLE_BADGE}</text>
</g>
<text class="r" {d(0.15)} x="44" y="190" font-family="{SERIF}" font-size="116" letter-spacing="-2.5" fill="{INK}">{FIRST_NAME}</text>
<text class="r" {d(0.3)} x="44" y="290" font-family="{SERIF}" font-style="italic" font-size="116" letter-spacing="-2.5" fill="url(#shine)">{LAST_NAME}</text>
<g class="r" {d(0.55)}>
  {text_lines(48, 338, TAGLINE_LINES, 27, f'font-family="{SANS}" font-size="18" fill="{INK_SOFT}"')}
</g>
<g class="f" {d(0.8)}>
  <text x="48" y="396" font-family="{MONO}" font-size="13" fill="{INK}">{WEBSITE_DISPLAY}</text>
  <text class="nu" x="224" y="396" font-family="{MONO}" font-size="13" fill="{TECH}">&#8599;</text>
</g>

{portrait_svg}
"""
    write("hero.svg", svg(W, h, body, ["serif", "serif-i", "sans", "mono"],
                          f"{FIRST_NAME} {LAST_NAME} - {ROLE_BADGE}"))


# ---- 2 · World Tiles (BUILD, BRAND, LEARN) -----------------------------------
TILE_W, TILE_H = 880 / 3 - 8, 210  # 285.33px card width, two 12px gaps across 880px


def count_up(num, word, x, y, attrs, begin, dur=1.1, frames=18):
    """Number counts up from 0 using SMIL <set> opacity toggles (runs in GitHub <img>)."""
    m = re.match(r"([\d.]+)(.*)", num)
    val, suf = float(m.group(1)), m.group(2) if m else ("", "")
    dec = len(m.group(1).split(".")[1]) if m and "." in m.group(1) else 0
    tail = f' <tspan font-style="italic">{escape(word)}</tspan>'
    if os.environ.get("STATIC"):
        return f'<text x="{x}" y="{y}" {attrs}>{escape(num)}{tail}</text>'
    out = []
    for i in range(frames + 1):
        e = 1 - (1 - i / frames) ** 3
        txt = num if i == frames else f"{val * e:.{dec}f}{suf}"
        on = begin + dur * i / frames
        off = "" if i == frames else f'<set attributeName="opacity" to="0" begin="{begin + dur * (i + 1) / frames:.3f}s"/>'
        out.append(f'<text x="{x}" y="{y}" {attrs} opacity="0">{escape(txt)}{tail}'
                   f'<set attributeName="opacity" to="1" begin="{on:.3f}s"/>{off}</text>')
    return "".join(out)


def tile(name, label, color, on, num, word, blurb, delay, pos):
    lines = wrap(blurb, 34)
    blurb_svg = "".join(
        f'<text class="r" {d(delay + 0.75 + i * 0.1)} x="24" y="{150 + i * 20}" font-family="{SANS}" '
        f'font-size="14" fill="{on}" opacity=".92">{escape(l)}</text>'
        for i, l in enumerate(lines)
    )
    body = f"""
<defs>
  <clipPath id="card"><rect width="{TILE_W}" height="{TILE_H}" rx="14"/></clipPath>
  <clipPath id="slot"><rect x="0" y="62" width="{TILE_W}" height="62"/></clipPath>
  <linearGradient id="gl" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>
    <stop offset=".5" stop-color="#fff" stop-opacity=".35"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
</defs>
<g class="ti" {d(delay)}>
  <g clip-path="url(#card)">
    <rect width="{TILE_W}" height="{TILE_H}" fill="{color}"/>
    <circle class="rg" {d(delay + 0.5)} cx="{TILE_W - 40}" cy="{TILE_H - 40}" r="60" fill="none" stroke="{on}" stroke-opacity=".5" stroke-width="2"/>
    <rect class="sh" style="animation-delay:{delay + 1.4:.2f}s" x="0" y="-20" width="90" height="{TILE_H + 40}" fill="url(#gl)" transform="translate(-260 0)"/>
  </g>
  <text class="sl" {d(delay + 0.35)} x="24" y="38" font-family="{MONO}" font-size="12" letter-spacing="1.2" fill="{on}">{label}</text>
  <g class="ai" {d(delay + 0.5)}><text class="n" style="animation-delay:{delay + 1.3:.2f}s" x="250" y="38" font-family="{MONO}" font-size="14" fill="{on}">&#8594;</text></g>
  <g clip-path="url(#slot)"><g class="ro" {d(delay + 0.45)}>
    {count_up(num, word, 22, 112, f'font-family="{SERIF}" font-size="44" fill="{on}"', delay + 0.45)}
  </g></g>
  {blurb_svg}
</g>
"""
    write(f"{name}.svg", svg(TILE_W, TILE_H, body, ["serif", "serif-i", "sans", "mono"],
                             f"{label}: {num} {word}. {blurb}", left=4 * pos, right=8 - 4 * pos))


# ---- 3 · Activity Card (12 Monthly Bars + Streak Stats) ----------------------
def activity(data):
    h = 340
    monthly = data["monthly"][-12:]
    best = max(monthly[:-1] or monthly, key=lambda m: m["total"])
    top = best["total"]
    x0, x1, base, maxh, gap = 40, 600, 292, 140, 10
    bw = (x1 - x0 - gap * (len(monthly) - 1)) / len(monthly)
    bars = []
    for i, m in enumerate(monthly):
        partial = i == len(monthly) - 1
        is_best = m is best
        bh = max(4, round(m["total"] / top * maxh)) if top else 4
        x = x0 + i * (bw + gap)
        fill = TECH if is_best else ("#c9c9c4" if partial else INK)
        label = datetime.date.fromisoformat(m["month"] + "-01").strftime("%b")
        bars.append(
            f'<rect class="g" style="animation-delay:{2.2 + i * 0.07:.2f}s" x="{x:.1f}" y="{base - bh}" '
            f'width="{bw:.1f}" height="{bh}" rx="4" fill="{fill}"><title>{label}: {m["total"]:,}</title></rect>'
            f'<text class="f" style="animation-delay:{2.2 + i * 0.07:.2f}s" x="{x + bw / 2:.1f}" y="{base + 22}" '
            f'text-anchor="middle" font-family="{MONO}" font-size="11" fill="{MUTED}">{label}</text>'
        )
        if is_best:
            bars.append(
                f'<text class="p" style="animation-delay:3.2s" x="{x + bw / 2:.1f}" y="{base - bh - 10}" '
                f'text-anchor="middle" font-family="{MONO}" font-size="11" fill="{TECH}">{m["total"]:,}</text>'
            )
    cs = data["current_streak"]["length"]
    ls = data["longest_streak"]["length"]
    streak_note = "current streak, and the longest" if cs >= ls else f"current streak, longest {ls}"
    total_days = len(data["days"])
    stats = [
        (f'{cs} <tspan font-style="italic">days</tspan>', streak_note),
        (f'{data["active_days"]}<tspan fill="#8e8e93"> / {total_days}</tspan>', "days with a commit"),
        (f'{data["best_day"]["count"]}', "on the busiest day"),
    ]
    side = []
    for i, (big, small) in enumerate(stats):
        y = 104 + i * 92
        side.append(
            f'<g class="r" {d(2.6 + i * 0.15)}>'
            f'<text x="650" y="{y}" font-family="{SERIF}" font-size="40" fill="{INK}">{big}</text>'
            f'<text x="650" y="{y + 24}" font-family="{SANS}" font-size="13" fill="{MUTED}">{small}</text></g>'
        )
        if i < 2:
            side.append(f'<rect class="f" {d(2.6)} x="650" y="{y + 44}" width="190" height="1" fill="{RULE}"/>')
    body = f"""
<rect width="{W}" height="{h}" rx="14" fill="{PAPER}"/>
<text class="f" {d(1.9)} x="40" y="58" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MUTED}">THE LAST 12 MONTHS ON GITHUB</text>
<text class="r" {d(2.0)} x="38" y="114" font-family="{SERIF}" font-size="52" fill="{INK}">{data["total_contributions"]:,} <tspan font-style="italic">contributions</tspan></text>
{''.join(bars)}
{''.join(side)}
"""
    write("activity.svg", svg(W, h, body, ["serif", "serif-i", "sans", "mono"],
                              f'{data["total_contributions"]:,} contributions in the last year, {cs}-day streak'))


# ---- 4 · Pinned Repository Cards --------------------------------------------
REPO_W, REPO_H = 880 / 3 - 8, 176


def repo_card(i, name, desc, lang, color, stars):
    delay = 4.6 + i * 0.12
    meta = f"{lang}  ·  ★ {stars}" if stars else f"{lang}  ·  live"
    body = f"""
<rect width="{REPO_W}" height="{REPO_H}" rx="14" fill="{PAPER}"/>
<g class="r" {d(delay)}>
  <rect x="24" y="30" width="8" height="8" rx="2" fill="{color}"/>
  <text x="40" y="39" font-family="{SANS}" font-weight="600" font-size="18" fill="{INK}">{escape(name)}</text>
  {text_lines(24, 72, wrap(desc, 34), 21, f'font-family="{SANS}" font-size="14" fill="{INK_SOFT}"')}
  <text x="24" y="{REPO_H - 24}" font-family="{MONO}" font-size="12" fill="{MUTED}">{escape(meta)}</text>
</g>
"""
    write(f"repo-{name}.svg", svg(REPO_W, REPO_H, body, ["sans", "sans-b", "mono"], f"{name}: {desc}",
                                  left=4 * i, right=8 - 4 * i))


def section_title(text, italic, theme):
    fg = "#e6edf3" if theme == "dark" else INK
    body = (
        f'<text class="r" {d(4.4)} x="2" y="46" font-family="{SERIF}" font-size="34" fill="{fg}">{escape(text)} '
        f'<tspan font-style="italic">{escape(italic)}</tspan></text>'
    )
    write(f"title-coding-{theme}.svg", svg(W, 64, body, ["serif", "serif-i"], f"{text} {italic}", bottom=0))


# ---- 5 · Blue Contribution Heatmap ------------------------------------------
BLUE = [PAPER_DEEP, "#c8d3ff", "#94a8ff", "#6280ff", TECH, "#1a3be0"]


def level_for(c):
    return 0 if c == 0 else 1 if c <= 5 else 2 if c <= 15 else 3 if c <= 30 else 4 if c <= 50 else 5


def build_snake_route(ncols, nrows, active, seed=42):
    """
    Generate an organic, lifelike snake route with natural zig-zags,
    coils, and dynamic S-curves covering the contribution calendar.
    Every step is exactly 1 unit (15px) for strictly uniform speed.
    """
    rng = random.Random(seed)
    route = []
    c, r = 0, 0
    route.append((c, r))
    visited = {(c, r)}

    # Forward pass: organic vertical/diagonal zig-zag across columns 0 -> ncols - 1
    col = 0
    going_down = True

    while col < ncols:
        target_r = nrows - 1 if going_down else 0
        dr = 1 if target_r > r else -1

        while r != target_r:
            r += dr
            route.append((col, r))
            visited.add((col, r))

            # Organic twist: side-step into adjacent active column or random detour
            if rng.random() < 0.22 and 0 < col < ncols - 1:
                side_c = col + (1 if (col + 1, r) in active or rng.random() < 0.55 else -1)
                if 0 <= side_c < ncols:
                    route.append((side_c, r))
                    visited.add((side_c, r))
                    if 0 <= r + dr < nrows:
                        r += dr
                        route.append((side_c, r))
                        visited.add((side_c, r))
                    route.append((col, r))

        # Advance column
        if col < ncols - 1:
            step_cols = 1 if (col + 1, r) in active or rng.random() < 0.8 else 2
            for _ in range(min(step_cols, ncols - 1 - col)):
                col += 1
                route.append((col, r))
                visited.add((col, r))
            going_down = not going_down
        else:
            break

    # Return pass: loop smoothly back from ncols - 1 to 0 with counter-curves
    target_return_r = 0 if r > nrows // 2 else nrows - 1
    dr = 1 if target_return_r > r else -1
    while r != target_return_r:
        r += dr
        route.append((col, r))
        visited.add((col, r))

    while col > 0:
        col -= 1
        route.append((col, r))
        visited.add((col, r))
        if rng.random() < 0.18 and 0 < r < nrows - 1:
            r += 1 if rng.random() < 0.5 else -1
            route.append((col, r))
            visited.add((col, r))

    while r != 0:
        r += -1 if r > 0 else 1
        route.append((col, r))

    return route


def heatmap(data):
    days = data["days"]
    first = datetime.date.fromisoformat(days[0]["date"])
    lead = (first.weekday() + 1) % 7  # sunday = 0
    cell, step, gx, gy = 12, 15, 44, 96
    ncols = (len(days) + lead + 6) // 7
    right = gx + ncols * step - 3
    h = gy + 7 * step + 44
    is_static = bool(os.environ.get("STATIC"))

    # Map active contribution cells (food targets for the snake)
    active_cells = set()
    for i, day in enumerate(days):
        k = i + lead
        col, row = divmod(k, 7)
        if day["count"] > 0:
            active_cells.add((col, row))

    # --- 1. Build organic serpentine (zig-zag + random) path ---
    route = build_snake_route(ncols, 7, active_cells, seed=42)
    pixel_route = [
        (gx + c * step + cell / 2, gy + r * step + cell / 2) for c, r in route
    ]
    path_d = f"M {pixel_route[0][0]:.1f} {pixel_route[0][1]:.1f} " + " ".join(
        f"L {x:.1f} {y:.1f}" for x, y in pixel_route[1:]
    )

    pos_to_idx = {}
    for idx, cell_pt in enumerate(route):
        if cell_pt not in pos_to_idx:
            pos_to_idx[cell_pt] = idx

    # --- 2. Synchronized timing constants (slower, natural snake speed) ---
    total_steps = len(route) - 1
    dt_cell = 0.11                      # 0.11s per cell (~9 cells/sec: smooth, visible pace)
    t_run = total_steps * dt_cell       # time for head to complete the sweep
    t_tail = 5 * dt_cell                # time for last body segment to finish
    t_reset = t_tail + 2.5              # tail exit + respawn fade + brief pause
    t_total = t_run + t_reset

    f_respawn_start = (t_run + t_tail + 0.35) / t_total
    f_respawn_end = (t_total - 0.45) / t_total

    # --- 3. Render contribution cells with synchronized eat & respawn SMIL ---
    cells, months, seen = [], [], set()
    for i, day in enumerate(days):
        k = i + lead
        col, row = divmod(k, 7)
        date = datetime.date.fromisoformat(day["date"])
        if date.day <= 7 and (date.year, date.month) not in seen and row == 0:
            seen.add((date.year, date.month))
            months.append((col, date.strftime("%b")))

        c = day["count"]
        orig_fill = BLUE[level_for(c)]
        eat_anim = ""

        if c > 0 and not is_static and (col, row) in pos_to_idx:
            idx = pos_to_idx[(col, row)]
            t_hit = idx * dt_cell
            f_hit = max(0.0001, t_hit / t_total)
            f_eat = min((t_hit + 0.05) / t_total, f_respawn_start - 0.0005)
            eat_anim = (
                f'<animate attributeName="fill" '
                f'values="{orig_fill};{orig_fill};{PAPER_DEEP};{PAPER_DEEP};{orig_fill};{orig_fill}" '
                f'keyTimes="0;{f_hit:.5f};{f_eat:.5f};{f_respawn_start:.5f};{f_respawn_end:.5f};1" '
                f'dur="{t_total:.3f}s" repeatCount="indefinite"/>'
            )

        cells.append(
            f'<rect x="{gx + col * step}" y="{gy + row * step}" '
            f'width="{cell}" height="{cell}" rx="3" fill="{orig_fill}">'
            f'<title>{day["date"]}: {c} contribution{"s" if c != 1 else ""}</title>'
            f'{eat_anim}</rect>'
        )

    # --- 4. Render forward-facing snake (head leads, 5 body segments trail) ---
    snake_svg = ""
    if not is_static:
        body_colors = ["#2f55ff", "#5b7bff", "#829cff", "#a8bcff", "#c8d3ff"]
        segments = []

        # Draw tail -> neck first so the head always renders on top
        for s in range(len(body_colors), 0, -1):
            lag = s * dt_cell
            f_start = lag / t_total
            f_end = (t_run + lag) / t_total
            f_vis = min(f_start + 0.001, f_end - 0.001)
            f_hide = min(f_end + 0.001, 0.9999)
            size = max(7, cell - s * 0.7)
            half = size / 2
            segments.append(
                f'<g opacity="0">'
                f'<rect x="{-half:.1f}" y="{-half:.1f}" width="{size:.1f}" height="{size:.1f}" '
                f'rx="3" fill="{body_colors[s - 1]}"/>'
                f'<animateMotion path="{path_d}" dur="{t_total:.3f}s" calcMode="linear" '
                f'keyPoints="0;0;1;1" keyTimes="0;{f_start:.5f};{f_end:.5f};1" '
                f'rotate="auto" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values="0;0;1;1;0;0" '
                f'keyTimes="0;{f_start:.5f};{f_vis:.5f};{f_end:.5f};{f_hide:.5f};1" '
                f'dur="{t_total:.3f}s" repeatCount="indefinite"/>'
                f'</g>'
            )

        # Head: drawn facing RIGHT (+X) so rotate="auto" always points forward
        f_head_end = t_run / t_total
        f_head_hide = min(f_head_end + 0.001, 0.9999)
        head = (
            f'<g opacity="1">'
            # Flicking red tongue extending forward (+X)
            f'<path d="M 6 0 L 10.5 0 M 9 0 L 11.5 -2 M 9 0 L 11.5 2" '
            f'stroke="{STUDIO}" stroke-width="1.2" stroke-linecap="round" fill="none">'
            f'<animate attributeName="opacity" values="1;0;1" dur="0.45s" repeatCount="indefinite"/>'
            f'</path>'
            # Head block
            f'<rect x="-6.5" y="-6.5" width="13" height="13" rx="3.5" fill="#1a3be0"/>'
            # Eyes on the front (+X) side
            f'<circle cx="2.6" cy="-2.8" r="1.7" fill="#ffffff"/>'
            f'<circle cx="2.6" cy="2.8" r="1.7" fill="#ffffff"/>'
            f'<circle cx="3.2" cy="-2.8" r="0.85" fill="{INK}"/>'
            f'<circle cx="3.2" cy="2.8" r="0.85" fill="{INK}"/>'
            f'<animateMotion path="{path_d}" dur="{t_total:.3f}s" calcMode="linear" '
            f'keyPoints="0;1;1" keyTimes="0;{f_head_end:.5f};1" '
            f'rotate="auto" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="1;1;0;0" '
            f'keyTimes="0;{f_head_end:.5f};{f_head_hide:.5f};1" '
            f'dur="{t_total:.3f}s" repeatCount="indefinite"/>'
            f'</g>'
        )
        snake_svg = f'<g class="snake-layer">{"".join(segments)}{head}</g>'

    # --- 5. Month labels & legend ---
    labels = "".join(
        f'<text x="{gx + col * step}" y="{gy + 7 * step + 16}" font-family="{MONO}" font-size="11" fill="{MUTED}">{m}</text>'
        for col, m in months if col < ncols - 12
    )
    legend_x = right - len(BLUE) * 14
    legend = "".join(
        f'<rect x="{legend_x + i * 14}" y="{gy + 7 * step + 6}" width="11" height="11" rx="2.5" fill="{c}"/>'
        for i, c in enumerate(BLUE)
    )

    extra_css = "@media (prefers-reduced-motion: reduce){.snake-layer{display:none}}"

    body = f"""
<rect width="{W}" height="{h}" rx="14" fill="{PAPER}"/>
<text class="r" {d(0.8)} x="42" y="62" font-family="{SERIF}" font-size="34" fill="{INK}">Every day, <tspan font-style="italic" fill="{TECH}">in blue</tspan></text>
<text class="f" {d(0.8)} x="{right}" y="60" text-anchor="end" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MUTED}">SNAKE RUN · REFRESHED DAILY</text>
{''.join(cells)}
{snake_svg}
<g class="f" {d(2.4)}>{labels}
<text x="{legend_x - 8}" y="{gy + 7 * step + 16}" text-anchor="end" font-family="{MONO}" font-size="11" fill="{MUTED}">less</text>{legend}
<text x="{legend_x + len(BLUE) * 14 + 2}" y="{gy + 7 * step + 16}" font-family="{MONO}" font-size="11" fill="{MUTED}">more</text></g>
"""
    write(
        "heatmap.svg",
        svg(
            W, h, body, ["serif", "serif-i", "mono"],
            f'Contribution graph: {data["total_contributions"]:,} contributions in the last year',
            extra_css=extra_css,
        ),
    )


def repo_stars(username):
    """Fetch live star counts from GitHub REST API (gracefully fallback if offline)."""
    stars = {}
    try:
        import requests
        for name, *_ in REPOS:
            r = requests.get(f"https://api.github.com/repos/{username}/{name}", timeout=10)
            if r.ok:
                stars[name] = r.json().get("stargazers_count", 0)
    except Exception as e:
        print(f"stars API unavailable ({e}); proceeding with defaults")
    return stars


if __name__ == "__main__":
    if not os.path.exists(DATA):
        print(f"Data file not found at {DATA}. Run fetch_contributions.py first.")
        exit(1)
    data = json.load(open(DATA, encoding="utf-8"))
    username = data.get("username", "Pranjal-k22")

    hero()
    tile("build", "BUILD", TECH, "#ffffff", BUILD_NUMBER, BUILD_LABEL, BUILD_DESC, 3.1, 0)
    tile("brand", "BRAND", STUDIO, "#ffffff", BRAND_NUMBER, BRAND_LABEL, BRAND_DESC, 3.35, 1)
    tile("learn", "LEARN", LEARN_COLOR, INK, LEARN_NUMBER, LEARN_LABEL, LEARN_DESC, 3.6, 2)
    activity(data)

    stars = repo_stars(username)
    for i, (name, desc, lang, color) in enumerate(REPOS):
        repo_card(i, name, desc, lang, color, stars.get(name, 0))

    section_title("What I'm", "coding", "dark")
    section_title("What I'm", "coding", "light")
    heatmap(data)
    print("All README cards successfully rendered into cards/")
