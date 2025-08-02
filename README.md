# AIBuilder ― Codex 向け実装ガイド
> **目的**  
> 本ドキュメントは「AI エージェントを自動生成するメタ-エージェント（AIBuilder）」を **Codex** に実装させるための指示書です。  
> – 手順は *上から順に* 実行できるよう並べています。  
> – コード片はそのままターミナル／エディタに貼り付けて OK です。  
> – 必要に応じて `TODO:` コメントを付けているので、実案件に合わせて編集してください。

---

## 0. 前提ソフトウェア
| 種別 | バージョン例 | 備考 |
|------|-------------|------|
| Python | 3.11 | `pyenv` 推奨 |
| OpenAI Python SDK | ^1.24.0 | Agents SDK/Responses API 対応版 |
| LangChain | ^0.2.0 | LangGraph 同梱 |
| LangGraph | ^0.0.39 | 状態遷移グラフ |
| Docker / Docker Compose | Engine 25 以上 | Firecracker or Kata でも可 |
| node | 20 (任意) | Streamlit UI 不要なら省略 |

```bash
# one-liner (例)
pip install "openai>=1.24,<2" langchain langgraph python-dotenv pyyaml
```

---

## 1. ディレクトリ構成

```
ai-builder/
├─ templates/          # YAML テンプレート群
│  └─ faq_bot.yaml
├─ ai_builder/         # Python パッケージ
│  ├─ __init__.py
│  ├─ orchestrator.py  # LangGraph 実装
│  ├─ generator.py     # テンプレート → Agent 定義
│  ├─ evaluator.py     # 自動評価スイート
│  └─ runtime_pool.py  # Docker Sandboxing API
├─ docker/
│  ├─ runtime.Dockerfile
│  └─ docker-compose.yml
├─ .github/
│  └─ workflows/
│     └─ ci-cd.yaml
└─ README.md           # ← 今ココ
```

---

## 2. テンプレート定義 (YAML)

```yaml
# templates/faq_bot.yaml
id: faq_bot_v1
description: "社内 FAQ 回答エージェント"
llm:
  model: gpt-4o
  temperature: 0.2
tools:
  - name: web_search
  - name: file_search
system_prompt: |
  あなたは社内 FAQ を即答するアシスタントです。
  禁止事項: 個人情報・機密情報の開示
success_criteria:
  - keyword_match: ["解決", "参考になりました"]
  - latency_ms: 2000
```

### Codex への指示
1. `templates/` 内の全 YAML を読み込み  
2. `id` をキーに辞書化  
3. 後続ステップで `system_prompt` と `llm` 設定を利用して `Agent` クラスを生成

---

## 3. Orchestrator ― LangGraph 実装

```python
# ai_builder/orchestrator.py
from langgraph import StateGraph, END
from ai_builder import generator, evaluator, runtime_pool

def build_graph():
    g = StateGraph()
    g.add_node("Generate", generator.build_agent)
    g.add_node("Evaluate", evaluator.run_suite)
    g.add_node("Deploy", runtime_pool.deploy)

    g.set_entry("Generate")
    g.connect("Generate", "Evaluate")
    g.connect("Evaluate", condition=lambda score: score >= 0.8, true="Deploy", false="Generate")
    g.set_termination("Deploy", END)
    return g.compile()
```

#### Codex ポイント
- **目的関数の引数と戻り値**を必ず型ヒントする  
- 失敗時に `next_state="Generate"` へ戻す再帰ループを実装

---

## 4. 自動評価スイート

```python
# ai_builder/evaluator.py
import openai, json, time
from tenacity import retry, wait_random_exponential

@retry(wait=wait_random_exponential(min=1, max=60))
def run_suite(agent_def, n_tests: int = 5) -> float:
    passed = 0
    for case in make_synthetic_tests(agent_def):
        res = agent_def.invoke(case["input"])
        if validate(res, case):
            passed += 1
    return passed / n_tests
```

- `make_synthetic_tests()` は Few-Shot から自動生成  
- `validate()` はキーワード一致 + OpenAI Moderation API スコアを採用

---

## 5. ランタイムサンドボックス (Docker)

```Dockerfile
# docker/runtime.Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY runner.py .
CMD ["python", "runner.py"]
```

```yaml
# docker/docker-compose.yml
version: "3.9"
services:
  agent-runtime:
    build:
      context: ./docker
      dockerfile: runtime.Dockerfile
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./logs:/logs
    deploy:
      resources:
        limits:
          cpus: "1"
          memory: 1g
```

---

## 6. Observability & Safety

1. **LangSmith / OpenAI トレーシング**  
   ```python
   from openai import OpenAI
   client = OpenAI(tracing="on")
   ```
2. **Prometheus Exporter** を `runtime_pool` 内に組み込み  
3. Slack / Discord にアラート通知 (失敗率 >5 % で発火)

---

## 7. CI / CD (GitHub Actions)

```yaml
# .github/workflows/ci-cd.yaml
name: CI-CD
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.11"}
      - run: pip install -e .
      - run: pytest
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - run: docker compose -f docker/docker-compose.yml up -d --build
```

---

## 8. Codex への最終プロンプト例

```text
### Instruction
You are ChatGPT-Codex. Implement the AIBuilder system described below.
Follow directory conventions. Write idiomatic Python 3.11.
Add type hints, docstrings (Google style), and TODO markers where clarification is needed.

### Specification
<README 内容を貼り付け>
```

---

## 9. 完了チェックリスト

- [ ] `pip install -e .` で import エラーが無い  
- [ ] `pytest` 5 件すべて合格 (初期値)  
- [ ] `docker compose up` で `/healthz` が 200 を返す  
- [ ] LangSmith ダッシュボードにトレースが表示される  

---

**以上で Codex への指示書は完了です。**  
不足点や環境に応じて `TODO:` を検索して追記してください。
