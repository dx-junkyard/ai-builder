# AI Builder

AI Builder は YAML テンプレートからエージェントを生成し、評価・デプロイを自動化するメタエージェントフレームワークです。LLM の設定や利用可能なツールを宣言的に記述することで、再利用可能なエージェントを素早く構築できます。

## 特徴
- **テンプレート駆動のエージェント生成**: `templates/` 以下の YAML を読み込み、`Agent` クラスを動的に組み立てます。
- **LangGraph オーケストレーション**: 生成 → 評価 → デプロイのワークフローを状態遷移グラフとして表現します。
- **自動評価スイート**: 合成テストを実行し、基準を満たした場合のみ次のステージへ遷移します。
- **Docker ランタイムサンドボックス**: エージェントを隔離環境で実行し、依存関係を簡潔に保ちます。
- **観測性と CI/CD**: Prometheus と GitHub Actions により運用を可視化し、自動テスト・デプロイを行います。

## ディレクトリ構成
```
ai-builder/
├─ templates/          # エージェント定義 YAML
│  └─ faq_bot.yaml
├─ ai_builder/         # ライブラリ本体
│  ├─ orchestrator.py  # LangGraph ワークフロー
│  ├─ generator.py     # テンプレート → エージェント
│  ├─ evaluator.py     # 自動評価
│  └─ runtime_pool.py  # Docker デプロイ
├─ docker/             # ランタイム用 Dockerfile & Compose
├─ .github/workflows/  # CI/CD 定義
└─ README.md
```

## インストール
Python 3.11 と Docker が必要です。

```bash
pip install -e .
```

`OPENAI_API_KEY` 環境変数を設定してください。

## 使い方
1. `templates/` に YAML テンプレートを追加します。
2. オーケストレーターを通じてエージェントを生成・評価・デプロイします。

```python
from ai_builder.orchestrator import build_graph

graph = build_graph()
result = graph.invoke({"template_id": "faq_bot_v1"})
print(result)
```

Docker 環境での実行は以下のコマンドで行えます。

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

## 開発とテスト

```bash
pip install -e .
pytest
docker compose -f docker/docker-compose.yml config
```

## ライセンス

このプロジェクトは MIT ライセンスの下で提供されます。
