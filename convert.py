#!/usr/bin/env python3
"""OpenClaw Stack Guide: Markdown → モバイル最適化HTML変換スクリプト."""

import re
from pathlib import Path

from jinja2 import Template
from markdown_it import MarkdownIt

# --- 設定 ---

SOURCE_DIR = Path(__file__).parent / "source"
OUTPUT_DIR = Path(__file__).parent / "docs"

CHAPTER_MAP = {
    "00_早見表.md": {"slug": "00-cheatsheet", "title": "早見表", "icon": "📋", "desc": "コマンド・ポート・ファイル一覧チートシート"},
    "01_基礎概念.md": {"slug": "01-basics", "title": "OpenClaw Stackとは", "icon": "🤖", "desc": "AIエージェントプラットフォームの概要と2つの環境"},
    "02_アーキテクチャ.md": {"slug": "02-architecture", "title": "アーキテクチャ", "icon": "🏗️", "desc": "Docker・Caddy・Gatewayのシステム構成"},
    "03_ネットワーク.md": {"slug": "03-network", "title": "ネットワーク", "icon": "🌐", "desc": "ポート・ドメイン・ファイアウォール設定"},
    "04_なぜセキュリティが必要か.md": {"slug": "04-security-why", "title": "なぜセキュリティが必要か", "icon": "🔒", "desc": "4層防御を初心者向けに解説"},
    "05_AIの8つの安全装置.md": {"slug": "05-security-ai", "title": "AIの8つの安全装置", "icon": "🛡️", "desc": "PIIマスキング・RBAC・サンドボックス等を例えで解説"},
    "06_セキュリティ設計.md": {"slug": "06-security-portfolio", "title": "セキュリティ設計", "icon": "🔐", "desc": "技術的なセキュリティ設計と環境別比較"},
    "07_デプロイ手順.md": {"slug": "07-deployment", "title": "デプロイ手順", "icon": "🚀", "desc": "VPSへのデプロイ手順（Docker・Caddy・初期設定）"},
    "08_ローカル環境構築.md": {"slug": "08-local-setup", "title": "ローカル環境構築", "icon": "💻", "desc": "Surface Go等でのローカル開発環境構築"},
    "09_運用手順.md": {"slug": "09-operations", "title": "運用手順", "icon": "🔧", "desc": "ヘルスチェック・ログ・トラブルシューティング"},
    "10_チェックリスト.md": {"slug": "10-checklist", "title": "チェックリスト", "icon": "✅", "desc": "デプロイ前後の確認項目一覧"},
}

REMOVE_SECTIONS = [
    "## 関連",
    "## 関連ドキュメント",
    "## 次の章",
]

INLINE_REPLACEMENTS = [
    # 個人情報 → 汎用化
    (r"fopenclaw\.com", "example.com"),
    (r"fukukei23", "<USERNAME>"),
    (r"yn4416", "<USER>"),
    (r"フクロウ", "VPS環境"),
    (r"よつば", "ローカル環境"),
    (r"/home/op/openclaw-stack", "/opt/openclaw"),
    (r"/home/op/", "/home/<USER>/"),
    (r"Surface Go 第1世代 / Pentium 4415Y / RAM 8GB", "お好みのLinuxマシン"),
    (r"Surface Go（Ubuntu 24\.04 LTS）", "Linuxマシン（Ubuntu 24.04 LTS）"),
    (r"Surface GoのWi-Fiチップ（ath10k）が定期的にエラーを起こしSSHが切断される。", "一部の環境でWi-Fiが不安定になる場合がある。"),
    (r"根本解決にはUSB-C有線LANアダプターを推奨。", "USB有線LANアダプターの使用を推奨。"),
    (r"Surface Go の Tailscale IP で外出先からSSH接続可能。", "TailscaleのIPアドレスで外出先からSSH接続可能。"),
    # 内部参照パス → 除去
    (r"\[yotsuba/handover/README_HANDOVER\.md\]\([^)]+\)", "関連ドキュメント"),
    (r"正本: \[.*?\]\(.*?\)", ""),
    (r"openclaw-workspace", "<WORKSPACE_REPO>"),
    (r"openclaw-stack", "<STACK_REPO>"),
]

MERMAID_DIAGRAMS = {
    "01_基礎概念.md": [
        (
            "## 2つの構成環境",
            """graph LR
    subgraph "VPS（本番）"
        V_INTERNET["🌐 インターネット"]
        V_UFW["🧱 UFW ファイアウォール"]
        V_CADDY["🔑 Caddy<br/>TLS + BasicAuth"]
        V_GW["🤖 OpenClaw Gateway<br/>:18789"]
        V_API["☁️ LLM API"]
        V_INTERNET --> V_UFW --> V_CADDY --> V_GW --> V_API
    end""",
        ),
    ],
    "02_アーキテクチャ.md": [
        (
            "## 責任境界",
            """graph TD
    Client["👤 クライアント"] --> Caddy["🔑 Caddy<br/>TLS終端 + BasicAuth"]
    Caddy -->|"127.0.0.1:18789"| GW["🤖 OpenClaw Gateway<br/>トークン認証 + デバイスペアリング"]
    GW --> Agent["🤖 エージェント<br/>ワークフロー実行"]
    Agent -->|"HTTPS"| API["☁️ LLM API<br/>テキスト生成"]""",
        ),
    ],
    "03_ネットワーク.md": [
        (
            "## トラフィック経路",
            """graph TD
    subgraph "公開ポート"
        P80["Port 80<br/>HTTP → HTTPSリダイレクト"]
        P443["Port 443<br/>HTTPS（TLS終端）"]
    end
    subgraph "内部のみ"
        G18789["Port 18789<br/>Gateway（ループバックのみ）"]
    end
    P80 -->|"リダイレクト"| P443
    P443 -->|"プロキシ"| G18789""",
        ),
    ],
    "04_なぜセキュリティが必要か.md": [
        (
            "## 4層防御の全体像",
            """graph TD
    L1["🧱 レイヤー1: UFW ファイアウォール<br/>80/443のみ公開"]
    L2["🔐 レイヤー2: TLS/HTTPS<br/>通信暗号化"]
    L3["🔑 レイヤー3: BasicAuth<br/>ID/パスワード認証"]
    L4["🎫 レイヤー4: Token + ペアリング<br/>Gateway認証"]
    L1 --> L2 --> L3 --> L4
    style L1 fill:#e3f2fd
    style L2 fill:#e8f5e9
    style L3 fill:#fff3e0
    style L4 fill:#fce4ec""",
        ),
    ],
    "06_セキュリティ設計.md": [
        (
            "## アーキテクチャ図",
            """graph TD
    INET["🌐 インターネット"] --> UFW["🧱 UFW<br/>80/443のみ許可"]
    UFW --> CADDY_TLS["🔐 Caddy<br/>TLS終端 + Auto HTTPS"]
    CADDY_TLS --> CADDY_AUTH["🔑 Caddy<br/>BasicAuth認証"]
    CADDY_AUTH --> NET["📦 Docker Network<br/>172.30.0.0/24"]
    NET --> GW["🤖 OpenClaw Gateway<br/>Token + デバイスペアリング"]
    GW --> LLM["☁️ LLM API"]""",
        ),
    ],
    "08_ローカル環境構築.md": [
        (
            "## 構築の流れ",
            """graph LR
    A["📋 テンプレート<br/>コピー"] --> B["⚙️ 設定ファイル<br/>編集"]
    B --> C["🐳 Docker<br/>ビルド"]
    C --> D["▶️ コンテナ<br/>起動"]
    D --> E["✅ 動作確認"]""",
        ),
    ],
}

# --- HTMLテンプレート ---

CHAPTER_TEMPLATE = Template("""\
<!DOCTYPE html>
<html lang="ja" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} — OpenClaw Stack Guide</title>
    <meta name="description" content="OpenClaw Stack {{ title }}の解説 — AIエージェントプラットフォーム構築ガイド">
    <meta property="og:title" content="{{ title }} — OpenClaw Stack Guide">
    <meta property="og:description" content="OpenClaw Stack {{ title }}の解説">
    <meta property="og:type" content="article">
    <meta property="og:image" content="https://fukukei23.github.io/openclaw-stack-guide/assets/ogp.png">
    <meta name="twitter:card" content="summary_large_image">
    <link rel="stylesheet" href="../assets/style.css">
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🤖</text></svg>">
</head>
<body>
    <header class="site-header">
        <button class="menu-toggle" aria-label="メニュー" id="menuToggle">
            <span></span><span></span><span></span>
        </button>
        <a href="../index.html" class="site-title">🤖 OpenClaw Stack Guide</a>
        <button class="theme-toggle" id="themeToggle" aria-label="テーマ切替">
            <span class="icon-light">☀️</span>
            <span class="icon-dark">🌙</span>
        </button>
    </header>

    <nav class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <a href="../index.html">🏠 ホーム</a>
        </div>
        {% for ch in chapters %}
        <a href="{{ ch.slug }}.html"
           class="sidebar-link{{ ' active' if ch.slug == current_slug }}">
            <span class="sidebar-icon">{{ ch.icon }}</span>
            {{ ch.title }}
        </a>
        {% endfor %}
    </nav>
    <div class="sidebar-overlay" id="sidebarOverlay"></div>

    <main class="content">
        <div class="chapter-nav-top">
            {% if prev_ch %}
            <a href="{{ prev_ch.slug }}.html" class="nav-prev">← {{ prev_ch.title }}</a>
            {% endif %}
            {% if next_ch %}
            <a href="{{ next_ch.slug }}.html" class="nav-next">{{ next_ch.title }} →</a>
            {% endif %}
        </div>

        <article class="chapter-body">
            {{ content|safe }}
        </article>

        <nav class="chapter-nav-bottom">
            {% if prev_ch %}
            <a href="{{ prev_ch.slug }}.html" class="nav-card prev">
                <span class="nav-label">← 前の章</span>
                <span class="nav-title">{{ prev_ch.icon }} {{ prev_ch.title }}</span>
            </a>
            {% endif %}
            {% if next_ch %}
            <a href="{{ next_ch.slug }}.html" class="nav-card next">
                <span class="nav-label">次の章 →</span>
                <span class="nav-title">{{ next_ch.icon }} {{ next_ch.title }}</span>
            </a>
            {% endif %}
        </nav>
    </main>

    <script src="../assets/script.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({
            startOnLoad: true,
            theme: document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'default',
            themeVariables: { fontSize: '14px' }
        });
    </script>
</body>
</html>
""", autoescape=True)

INDEX_TEMPLATE = Template("""\
<!DOCTYPE html>
<html lang="ja" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenClaw Stack ガイド</title>
    <meta name="description" content="AIエージェントプラットフォーム OpenClaw Stack の構築・運用を初心者向けに完全解説">
    <meta property="og:title" content="OpenClaw Stack ガイド">
    <meta property="og:description" content="AIエージェントプラットフォーム OpenClaw Stack の構築・運用を初心者向けに完全解説">
    <meta property="og:type" content="website">
    <meta property="og:image" content="https://fukukei23.github.io/openclaw-stack-guide/assets/ogp.png">
    <meta name="twitter:card" content="summary_large_image">
    <link rel="stylesheet" href="assets/style.css">
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🤖</text></svg>">
</head>
<body class="index-page">
    <header class="site-header">
        <span class="site-title">🤖 OpenClaw Stack Guide</span>
        <button class="theme-toggle" id="themeToggle" aria-label="テーマ切替">
            <span class="icon-light">☀️</span>
            <span class="icon-dark">🌙</span>
        </button>
    </header>

    <main class="content">
        <section class="hero">
            <h1>OpenClaw Stack ガイド</h1>
            <p>AIエージェントプラットフォーム OpenClaw Stack の<br>構築・運用を初心者向けに完全解説</p>
        </section>

        <section class="chapter-grid">
            {% for ch in chapters %}
            <a href="chapters/{{ ch.slug }}.html" class="chapter-card">
                <div class="card-icon">{{ ch.icon }}</div>
                <div class="card-number">第{{ ch.number }}章</div>
                <h2 class="card-title">{{ ch.title }}</h2>
                <p class="card-desc">{{ ch.desc }}</p>
            </a>
            {% endfor %}
        </section>

        <section class="features">
            <h2>📖 このガイドの特徴</h2>
            <div class="feature-grid">
                <div class="feature-item">
                    <span class="feature-icon">🎯</span>
                    <h3>初心者向け</h3>
                    <p>専門用語は初出時に説明。前提知識不要</p>
                </div>
                <div class="feature-item">
                    <span class="feature-icon">📊</span>
                    <h3>図解付き</h3>
                    <p>アーキテクチャやセキュリティを図で視覚化</p>
                </div>
                <div class="feature-item">
                    <span class="feature-icon">📱</span>
                    <h3>モバイル対応</h3>
                    <p>スマホからいつでも見返せるレスポンシブデザイン</p>
                </div>
                <div class="feature-item">
                    <span class="feature-icon">🌙</span>
                    <h3>ダークモード</h3>
                    <p>目に優しいテーマ切替対応</p>
                </div>
            </div>
        </section>
    </main>

    <footer class="site-footer">
        <p>OpenClaw Stack Guide — <a href="https://github.com/fukukei23/openclaw-stack-guide">GitHub</a></p>
    </footer>

    <script src="assets/script.js"></script>
</body>
</html>
""", autoescape=True)


# --- フィルタリング ---

def filter_sections(text: str) -> str:
    """個人情報・環境固有セクションを除去."""
    lines = text.split("\n")
    result = []
    skip = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("## ") and any(stripped.startswith(s) for s in REMOVE_SECTIONS):
            skip = True
            continue

        if skip and stripped.startswith("## ") and not any(stripped.startswith(s) for s in REMOVE_SECTIONS):
            skip = False

        if not skip:
            result.append(line)

    text = "\n".join(result)

    # インライン個人情報のサニタイズ
    for pattern, replacement in INLINE_REPLACEMENTS:
        text = re.sub(pattern, replacement, text)

    return text


# --- Markdown → HTML変換 ---

def convert_md_to_html(md_text: str) -> str:
    """MarkdownをHTMLに変換."""
    md = MarkdownIt("commonmark", {"html": False}).enable("table")
    return md.render(md_text)


def inject_mermaid(html: str, filename: str) -> str:
    """Mermaid図を指定位置に挿入."""
    diagrams = MERMAID_DIAGRAMS.get(filename, [])
    if not diagrams:
        return html

    for heading, diagram_code in diagrams:
        heading_text = heading.replace("## ", "").strip()
        mermaid_block = (
            f'<div class="mermaid-wrapper">'
            f'<div class="mermaid">\n{diagram_code}\n</div>'
            f'</div>'
        )

        pattern = f"(<h2>(?:<a[^>]*></a>)?{re.escape(heading_text)}</h2>)"
        if re.search(pattern, html):
            html = re.sub(pattern, mermaid_block + r"\1", html, count=1)

    return html


def rewrite_links(html: str) -> str:
    """内部リンクをHTML URLに書き換え."""
    from urllib.parse import quote, unquote

    for filename, info in CHAPTER_MAP.items():
        html = html.replace(f'href="{filename}', f'href="{info["slug"]}.html')
        html = re.sub(
            rf'href="{re.escape(filename)}#',
            f'href="{info["slug"]}.html#',
            html,
        )

        encoded_name = quote(filename, safe='')
        if encoded_name != filename:
            html = html.replace(f'href="{encoded_name}', f'href="{info["slug"]}.html')
            html = re.sub(
                rf'href="{re.escape(encoded_name)}#',
                f'href="{info["slug"]}.html#',
                html,
            )

    def replace_md_link(match):
        href = match.group(1)
        for filename, info in CHAPTER_MAP.items():
            decoded = unquote(href)
            if filename in decoded or filename in href:
                anchor = ""
                if "#" in href:
                    anchor = "#" + href.split("#", 1)[1]
                elif "#" in decoded:
                    anchor = "#" + decoded.split("#", 1)[1]
                return f'href="{info["slug"]}.html{anchor}"'
        return f'href="#"'

    html = re.sub(r'href="([^"]*\.md[^"]*)"', replace_md_link, html)

    html = re.sub(r'href="\.\./[^"]*"', 'href="#"', html)

    return html


def enhance_html(html: str) -> str:
    """HTMLに装飾を追加（テーブルラップ・コールアウト等）."""
    html = re.sub(
        r"(<table[^>]*>.*?</table>)",
        r'<div class="table-wrapper">\1</div>',
        html,
        flags=re.DOTALL,
    )

    def callout_replace(match):
        content = match.group(1)
        if "注意" in content or "⚠" in content:
            return f'<div class="callout callout-warn"><p>{content}</p></div>'
        if "重要" in content:
            return f'<div class="callout callout-danger"><p>{content}</p></div>'
        if "Tip" in content or "💡" in content:
            return f'<div class="callout callout-tip"><p>{content}</p></div>'
        return f'<div class="callout callout-info"><p>{content}</p></div>'

    html = re.sub(r"<blockquote>\s*<p>(.*?)</p>\s*</blockquote>", callout_replace, html, flags=re.DOTALL)

    return html


# --- メイン ---

def main():
    chapters_dir = OUTPUT_DIR / "chapters"
    assets_dir = OUTPUT_DIR / "assets"
    chapters_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    chapters = []
    for filename, info in sorted(CHAPTER_MAP.items()):
        chapters.append({
            "number": info["slug"][:2],
            "slug": info["slug"],
            "title": info["title"],
            "icon": info["icon"],
            "desc": info["desc"],
            "filename": filename,
        })

    for i, ch in enumerate(chapters):
        src = SOURCE_DIR / ch["filename"]
        if not src.exists():
            print(f"SKIP: {ch['filename']} not found")
            continue

        md_text = src.read_text(encoding="utf-8")
        md_text = filter_sections(md_text)
        html_body = convert_md_to_html(md_text)
        html_body = inject_mermaid(html_body, ch["filename"])
        html_body = rewrite_links(html_body)
        html_body = enhance_html(html_body)

        prev_ch = chapters[i - 1] if i > 0 else None
        next_ch = chapters[i + 1] if i < len(chapters) - 1 else None

        full_html = CHAPTER_TEMPLATE.render(
            title=ch["title"],
            slug=ch["slug"],
            current_slug=ch["slug"],
            content=html_body,
            chapters=chapters,
            prev_ch=prev_ch,
            next_ch=next_ch,
        )

        out = chapters_dir / f"{ch['slug']}.html"
        out.write_text(full_html, encoding="utf-8")
        print(f"OK: {ch['slug']}.html")

    index_html = INDEX_TEMPLATE.render(chapters=chapters)
    (OUTPUT_DIR / "index.html").write_text(index_html, encoding="utf-8")
    print("OK: index.html")

    print(f"\n完了: {len(chapters)}章 + index → {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
