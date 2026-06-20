"""convert.py のテスト — 個人情報除去・リンク書き換え・セクションフィルタリング."""

import re

import pytest

from convert import (
    CHAPTER_MAP,
    CHAPTER_TEMPLATE,
    INDEX_TEMPLATE,
    filter_sections,
    inject_mermaid,
    rewrite_links,
    convert_md_to_html,
    enhance_html,
    MERMAID_DIAGRAMS,
    OUTPUT_DIR,
)


# === 1. 個人情報サニタイズ ===

PERSONAL_PATTERNS = [
    "fopenclaw.com",
    "fukukei23",
    "yn4416",
    "フクロウ",
    "よつば",
    "openclaw-workspace",
    "/home/op/",
]


class TestNoPersonalInfoInOutput:
    """生成済みHTMLに個人情報が含まれないことを検証."""

    @pytest.fixture(autouse=True)
    def _generate(self):
        main = __import__("convert", fromlist=["main"]).main
        main()

    @pytest.mark.parametrize("pattern", PERSONAL_PATTERNS)
    def test_no_personal_info_in_chapters(self, pattern):
        for html_file in sorted((OUTPUT_DIR / "chapters").glob("*.html")):
            content = html_file.read_text(encoding="utf-8")
            body = re.sub(r'<footer.*?</footer>', '', content, flags=re.DOTALL)
            body = re.sub(r'<meta property="og:.*?">', '', body)
            body = re.sub(r'<a href="https://github\.com/[^"]*">', '', body)
            assert pattern not in body, (
                f"{pattern} found in {html_file.name}"
            )

    @pytest.mark.parametrize("pattern", PERSONAL_PATTERNS)
    def test_no_personal_info_in_index(self, pattern):
        index = OUTPUT_DIR / "index.html"
        if not index.exists():
            pytest.skip("index.html not found")
        content = index.read_text(encoding="utf-8")
        body = re.sub(r'<footer.*?</footer>', '', content, flags=re.DOTALL)
        body = re.sub(r'<meta property="og:.*?">', '', body)
        body = re.sub(r'<a href="https://github\.com/[^"]*">', '', body)
        assert pattern not in body, f"{pattern} found in index.html"


# === 2. セクションフィルタリング ===

class TestFilterSections:
    """filter_sections() の単体テスト."""

    def test_removes_kanren_section(self):
        md = "## 本文\nhello\n## 関連\n- [link](x.md)\n## 次セクション\nok"
        result = filter_sections(md)
        assert "## 関連" not in result
        assert "[link](x.md)" not in result
        assert "## 次セクション" in result

    def test_sanitizes_domain(self):
        result = filter_sections("curl https://fopenclaw.com/status")
        assert "fopenclaw.com" not in result
        assert "example.com" in result

    def test_sanitizes_username(self):
        result = filter_sections("user: fukukei23")
        assert "fukukei23" not in result

    def test_sanitizes_codenames(self):
        result = filter_sections("フクロウ環境でのデプロイ")
        assert "フクロウ" not in result
        result2 = filter_sections("よつば環境でのビルド")
        assert "よつば" not in result2

    def test_sanitizes_internal_paths(self):
        result = filter_sections("cd /home/op/openclaw-stack")
        assert "/home/op/" not in result

    def test_sanitizes_workspace_ref(self):
        result = filter_sections("openclaw-workspaceリポジトリ")
        assert "openclaw-workspace" not in result

    def test_preserves_normal_content(self):
        md = "## コマンド一覧\n`docker compose up -d`\n### 使い方\n説明"
        result = filter_sections(md)
        assert "## コマンド一覧" in result
        assert "`docker compose up -d`" in result
        assert "### 使い方" in result


# === 3. リンク書き換え ===

class TestRewriteLinks:
    """rewrite_links() の単体テスト."""

    def test_md_links_to_html(self):
        html = '<a href="01_基礎概念.md">link</a>'
        result = rewrite_links(html)
        assert 'href="01-basics.html"' in result
        assert ".md" not in result

    def test_md_link_with_anchor(self):
        html = '<a href="02_アーキテクチャ.md#overview">link</a>'
        result = rewrite_links(html)
        assert 'href="02-architecture.html#overview"' in result

    def test_unknown_md_links_to_hash(self):
        html = '<a href="unknown_file.md">link</a>'
        result = rewrite_links(html)
        assert 'href="#"' in result

    def test_removes_relative_links(self):
        html = '<a href="../other/file.md">link</a>'
        result = rewrite_links(html)
        assert 'href="#"' in result

    def test_all_chapter_slugs_valid(self):
        html = "".join(f'<a href="{f}"></a>' for f in CHAPTER_MAP)
        result = rewrite_links(html)
        for info in CHAPTER_MAP.values():
            assert f'{info["slug"]}.html' in result


# === 3.5 XSS回帰テスト（autoescape + html:False） ===

class TestConvertMdToHtml:

    def test_raw_html_is_escaped_not_rendered(self):
        """source の生 HTML は出力でエスケープされ、要素として解釈されない."""
        html = convert_md_to_html("<script>alert(1)</script>")
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_inline_html_in_text_is_escaped(self):
        html = convert_md_to_html("本文 <iframe src=x> 末尾")
        assert "<iframe" not in html
        assert "&lt;iframe" in html


class TestTemplateAutoEscape:

    def _chapter_payload(self):
        return {
            "title": "<script>alert(1)</script>",
            "slug": "00-x",
            "current_slug": "00-x",
            "content": "<p>OK</p>",
            "chapters": [
                {
                    "slug": "00-x",
                    "number": "00",
                    "title": "<b>t</b>",
                    "icon": "🎵",
                    "desc": "<img src=x onerror=alert(1)>",
                    "filename": "00.md",
                }
            ],
            "prev_ch": None,
            "next_ch": None,
            "version": "1",
            "build_date": "2026.01.01",
        }

    def test_chapter_template_escapes_title_and_desc(self):
        out = CHAPTER_TEMPLATE.render(**self._chapter_payload())
        assert "<script>alert(1)</script>" not in out
        assert "<img src=x onerror=alert(1)>" not in out
        assert "&lt;script&gt;" in out

    def test_chapter_template_keeps_safe_content_html(self):
        out = CHAPTER_TEMPLATE.render(**self._chapter_payload())
        assert "<p>OK</p>" in out

    def test_index_template_escapes_desc(self):
        out = INDEX_TEMPLATE.render(
            chapters=self._chapter_payload()["chapters"],
            version="1",
            build_date="2026.01.01",
        )
        assert "<img src=x onerror=alert(1)>" not in out
        assert "&lt;img" in out


# === 4. Mermaid注入 ===

class TestMermaidInjection:
    """inject_mermaid() の単体テスト."""

    def test_injects_diagram(self):
        html = "<h2>2つの構成環境</h2><p>text</p>"
        result = inject_mermaid(html, "01_基礎概念.md")
        assert "mermaid-wrapper" in result
        assert "graph LR" in result

    def test_no_injection_for_unknown_file(self):
        html = "<h2>Test</h2>"
        result = inject_mermaid(html, "99_存在しない.md")
        assert "mermaid-wrapper" not in result

    def test_mermaid_no_personal_info(self):
        for filename, diagrams in MERMAID_DIAGRAMS.items():
            for heading, code in diagrams:
                for pattern in ["fopenclaw", "fukukei", "フクロウ", "よつば"]:
                    assert pattern not in code, (
                        f"{pattern} found in Mermaid diagram for {filename}"
                    )


# === 5. HTML生成の整合性 ===

class TestBuildIntegrity:
    """生成されたHTMLの構造チェック."""

    @pytest.fixture(autouse=True)
    def _generate(self):
        main = __import__("convert", fromlist=["main"]).main

    def test_all_chapters_generated(self):
        for info in CHAPTER_MAP.values():
            assert (OUTPUT_DIR / "chapters" / f'{info["slug"]}.html').exists()

    def test_index_generated(self):
        assert (OUTPUT_DIR / "index.html").exists()

    def test_all_chapters_have_nav(self):
        for html_file in (OUTPUT_DIR / "chapters").glob("*.html"):
            content = html_file.read_text(encoding="utf-8")
            assert "chapter-nav-bottom" in content
            assert "sidebar" in content

    def test_no_broken_md_links(self):
        for html_file in (OUTPUT_DIR / "chapters").glob("*.html"):
            content = html_file.read_text(encoding="utf-8")
            md_links = re.findall(r'href="[^"]*\.md[^"]*"', content)
            assert len(md_links) == 0, (
                f".md href links found in {html_file.name}: {md_links}"
            )

    def test_mermaid_rendered(self):
        files_with_diagrams = set(MERMAID_DIAGRAMS.keys())
        for md_name in files_with_diagrams:
            slug = CHAPTER_MAP[md_name]["slug"]
            html_file = OUTPUT_DIR / "chapters" / f"{slug}.html"
            if html_file.exists():
                content = html_file.read_text(encoding="utf-8")
                assert "mermaid" in content.lower()
