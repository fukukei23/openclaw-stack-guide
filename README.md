# OpenClaw Stack Guide

> AIエージェントプラットフォーム OpenClaw Stack の構築・運用を初心者向けに完全解説するモバイル最適化ガイドサイト

**サイト**: [https://fukukei23.github.io/openclaw-stack-guide/](https://fukukei23.github.io/openclaw-stack-guide/)

## 章構成（11章）

| 章 | タイトル | 内容 |
|---|---|---|
| 00 | 早見表 | コマンド・ポート・ファイル一覧チートシート |
| 01 | OpenClaw Stackとは | AIエージェントプラットフォームの概要と2つの環境 |
| 02 | アーキテクチャ | Docker・Caddy・Gatewayのシステム構成 |
| 03 | ネットワーク | ポート・UFW・トラフィック経路 |
| 04 | なぜセキュリティが必要か | 4層防御を初心者向けに解説 |
| 05 | AIの8つの安全装置 | PIIマスキング・RBAC・サンドボックス等を例えで解説 |
| 06 | セキュリティ設計 | 技術的な多層防御設計と環境別比較 |
| 07 | デプロイ手順 | VPSへのデプロイ手順 |
| 08 | ローカル環境構築 | Linuxマシンでのローカル開発環境構築 |
| 09 | 運用手順 | ヘルスチェック・ログ・トラブルシューティング |
| 10 | チェックリスト | デプロイ前後の確認項目一覧 |

## 特徴

- モバイルファースト レスポンシブデザイン（360px〜）
- ダーク/ライトテーマ切替
- Mermaid図によるアーキテクチャ・セキュリティの視覚化
- 目次（TOC）自動生成
- コードブロックのコピーボタン
- ページ内検索
- OGP/Twitter Card対応

## 技術構成

| 要素 | 技術 |
|---|---|
| 変換 | `convert.py`（Python: markdown-it-py + jinja2） |
| スタイリング | CSS Custom Properties（ダーク/ライト対応） |
| 図解 | Mermaid.js（CDN） |
| テスト | pytest 34テスト |
| CI/CD | GitHub Actions → GitHub Pages |

## ローカル開発

```bash
# 依存インストール
pip install markdown-it-py jinja2 pytest

# テスト実行
python3 -m pytest test_convert.py -v

# HTML生成
python3 convert.py

# 確認
open docs/index.html
```

## 関連リポジトリ

- [openclaw-stack](https://github.com/fukukei23/openclaw-stack) — 元となるインフラ構成管理リポジトリ
- [claude-code-guide](https://github.com/fukukei23/claude-code-guide) — 同パターンのClaude Codeガイド

## ライセンス

MIT License
