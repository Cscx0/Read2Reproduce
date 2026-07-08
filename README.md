# Read2Reproduce

Read2Reproduce 是一个面向本科生科研入门的论文阅读与实验复现辅助平台。用户上传论文 PDF 后，系统会解析论文文本、检测 GitHub / GitLab / HuggingFace / 项目页等资源，并围绕“从论文到复现”生成结构化总结、实验设置、方法流程、关键公式解释和复现 checklist。

## 功能列表

- 上传 PDF 并用 PyMuPDF 解析全文、分页文本、标题、摘要和章节标题。
- 分析前会识别文档类型与学科领域，用户也可以手动选择计算机、物理、数学、医学等大类方向；非论文、扫描件或恶搞文本会返回诊断和下一步建议，而不是套用论文模板。
- 正则与关键词规则检测 GitHub、GitLab、HuggingFace、项目主页、代码可用性和补充材料线索。
- 支持用户选择只分析论文、结合检测到的仓库资源分析，或上传补充资料分析。
- 补充资料支持 `.txt`、`.md`、`.pdf`、`.zip`；MVP 阶段 zip 先保存不解压。
- GitHub 资源分析会尝试读取 README、默认分支、文件树、依赖文件和配置文件；网络失败时自动降级。
- LLM 调用集中封装在 `backend/app/services/llm_client.py`，没有 API Key 时返回完整 mock 结果。
- 前端用 dashboard 展示结构化总结、方法流程图、关键公式、实验设置、实体表格、相关工作图、复现 checklist 和仓库阅读辅助。

## 技术栈

- 前端：React + Vite + TypeScript
- 后端：Python 3.11 + FastAPI
- PDF 解析：PyMuPDF
- 数据结构：Pydantic
- 网络请求：httpx
- UI 图标：lucide-react

## 后端启动

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

也可以使用脚本：

```bash
./scripts/start_backend.sh
```

健康检查：

```bash
curl http://127.0.0.1:8000/api/health
```

LLM 配置检查：

```bash
curl "http://127.0.0.1:8000/api/llm-health"
curl "http://127.0.0.1:8000/api/llm-health?check_remote=true"
```

## 前端启动

```bash
cd frontend
npm install
npm run dev
```

也可以使用脚本：

```bash
./scripts/start_frontend.sh
```

默认访问地址：

```text
http://127.0.0.1:5173
```

Vite 已配置 `/api` 代理到 `http://127.0.0.1:8000`。

## 环境变量

后端环境变量位于 `backend/.env`，可以从示例文件复制：

```bash
cp backend/.env.example backend/.env
```

可配置项：

```text
OPENAI_API_KEY=
COMPATIBLE_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
COMPATIBLE_BASE_URL=
LLM_MODEL=gpt-4o-mini
LLM_TIMEOUT_SECONDS=90
LLM_MOCK_FALLBACK=true
LLM_RESPONSE_FORMAT_JSON=true
GITHUB_TOKEN=
```

`OPENAI_BASE_URL` 或 `COMPATIBLE_BASE_URL` 可以填写 OpenAI-compatible base URL，例如 `https://api.openai.com/v1`，也可以直接填写完整的 `/chat/completions` endpoint。`LLM_MOCK_FALLBACK=false` 时，真实 API 调用失败或模型输出不符合 schema 会直接抛错，便于排查配置问题。

不要把 API Key 写入代码或提交到仓库。

## Mock 模式

如果 `OPENAI_API_KEY` 和 `COMPATIBLE_API_KEY` 都为空，后端会自动使用 mock 模式。mock 数据覆盖所有前端展示区域，因此本地没有模型服务也能完整演示：

1. 上传任意论文 PDF。
2. 查看资源检测结果。
3. 选择分析模式。
4. 进入完整 dashboard。

如果配置了真实 API Key，`llm_client.py` 会调用兼容 OpenAI Chat Completions 的接口；当 `LLM_MOCK_FALLBACK=true` 时，调用失败会降级为 mock，保证演示流程不中断。

## 项目结构

```text
Read2Reproduce/
  backend/
    app/
      main.py
      config.py
      schemas.py
      services/
        pdf_parser.py
        resource_detector.py
        github_analyzer.py
        paper_analyzer.py
        llm_client.py
      storage/
        uploads/
    requirements.txt
    .env.example
  frontend/
    src/
      App.tsx
      main.tsx
      api.ts
      styles.css
      components/
        UploadPanel.tsx
        ResourceDecisionPanel.tsx
        AnalysisDashboard.tsx
        SummaryCard.tsx
        FormulaCard.tsx
        ExperimentTable.tsx
        ChecklistView.tsx
        MethodFlowView.tsx
        RelatedWorkGraph.tsx
        RepoGuideView.tsx
    package.json
    vite.config.ts
    tsconfig.json
  scripts/
    start_backend.sh
    start_frontend.sh
  README.md
```

## 后续计划

- 把内存态 `PAPERS` 替换为 SQLite / PostgreSQL，并保存分析历史。
- 增加论文分块、向量检索和按章节的 RAG 分析。
- 完善公式、表格、图注和参考文献解析。
- 支持用户手动输入仓库 URL，并可选择 clone 到沙盒做更深入的静态分析。
- 为 checklist 增加导出 Markdown / PDF / 实验日志功能。
- 增加登录、项目空间和团队协作能力。
