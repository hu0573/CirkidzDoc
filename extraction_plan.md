# 文档模板填充功能提取项目计划

## 目标
从参考项目 docassemble 中提炼文档模板填充能力，构建一个前后端分离的 Web 应用，实现：
- 前端：React + TypeScript + Tailwind（已初始化），提供模板选择、字段填写、输出格式选择与结果下载体验。
- 后端：Python 技术栈（推荐 FastAPI）提供模板解析、数据填充、格式转换 API；服务需独立于 docassemble 运行。
- 支持模板类型 `.docx`、`.pdf` 等，输出涵盖 docassemble 现有能力（DOCX、PDF、HTML、RTF、TeX、Markdown 等）。

## 开发阶段任务板
- [x] **任务组 1：文档与规划**
  - [x] 汇总 docassemble 模板/格式能力，形成依赖矩阵草稿。
  - [x] 定义模板元数据结构、字段类型映射与校验规则。
  - [x] 编写《需求规格说明.md》，存档至 `docs/`.
  - [x] 编写《技术调研报告.md》，覆盖 docassemble 依赖安装方式、版本对齐策略与调试指南。
  - [x] 制定《系统设计蓝图.md》，总结整体架构与关键决策。
- [x] **任务组 2：镜像构建与环境对齐**
  - [x] 明确 docassemble 同源容器镜像的构建计划与 PoC，沉淀镜像组件清单。
  - [x] 编写与 ReferenceProjects/docassemble 对齐的多阶段 Dockerfile，并完成基础镜像构建与版本校验。
  - [x] 配置 `docker-compose.yml` / Dev Container，集成 `make render-sample`、`make healthcheck` 等脚本验证 Pandoc、LibreOffice、ImageMagick 可用性。
  - [x] 撰写《镜像使用与调试手册.md》，记录依赖版本、构建流程与常见问题排查。
  - [x] 2025-11-11 于本地执行 `make healthcheck` 与 `make render-sample`，确认镜像构建、依赖探测与渲染链路可用。
- [ ] **任务组 3：后端基础设施**
  - [ ] 初始化 FastAPI 项目骨架，配置 Pydantic 模型与路由框架。
  - [ ] 建立模板目录结构与加载缓存机制，提供示例模板元数据。
  - [ ] 引入 `uv` 管理 Python 依赖，生成锁文件并制定依赖更新流程。
  - [ ] 配置 Makefile/justfile，固化开发环境并复用镜像健康检查脚本。
  - [ ] 引入配置管理、日志基线，完成《后端环境配置说明.md》。
- [ ] **任务组 4：后端渲染与转换能力**
  - [ ] 实现 DOCX 渲染服务，覆盖图片、条件逻辑等场景。
  - [ ] 实现 PDF 表单填充与导出，处理扁平化、PDF/A 选项。
  - [ ] 构建 `ConversionPipeline`，串联 docx → pdf → {html, rtf, tex, md} 转换。
  - [ ] 集成 Pandoc/LibreOffice 等外部工具健康检查与降级策略。
  - [ ] 为渲染与转换核心模块编写单元测试，记录至《后端渲染测试说明.md》。
- [ ] **任务组 5：后端任务编排与接口**
  - [ ] 设计并迁移数据库表结构（templates、tasks、task_results 等）。
  - [ ] 实现任务创建、进度更新、状态查询 API，支持 BackgroundTasks 抽象。
  - [ ] 完成结果文件归档、过期清理、下载 token 管理。
  - [ ] 提供格式与高级选项查询、模板详情等接口。
  - [ ] 写作《后端 API 使用说明.md》，涵盖接口约定、错误码与示例。
- [ ] **任务组 6：前端实现与交互**
  - [ ] 封装 Axios API 客户端，处理错误拦截、文件下载与通用请求配置。
  - [ ] 构建模板列表、预览与说明界面，串联后端模板接口。
  - [ ] 实现元数据驱动的动态表单，支持多字段类型与校验提示。
  - [ ] 实现输出格式与高级选项配置组件，联动任务提交。
  - [ ] 构建任务状态、下载管理与错误重试体验。
  - [ ] 整理《前端组件与状态管理指南.md》，沉淀复用规范。
- [ ] **任务组 7：综合验证与交付**
  - [ ] 执行前后端单元、集成、E2E 测试，生成《测试报告.md》。
  - [ ] 完成 K6/JMeter 性能压测与监控验证，形成《性能基线报告.md》。
  - [ ] 完成兼容性与大文件场景验证，记录异常案例与解决方案。
  - [ ] 完成部署资产（Docker Compose、Helm Chart 等）并撰写 `deploy/README.md`。
  - [ ] 组织内部验收与知识分享，记录《交付复盘纪要.md》，列出后续迭代清单。

## docassemble 现有能力
- 模板类型：`docx_template_file`、`pdf_template_file`、`rtf_template_file` 等。
- 数据填充：
  - DOCX：`docxtpl` 渲染 Jinja2 模板，支持图片、子模板、条件逻辑。
  - PDF：基于 `AcroForm` 写入文本、复选框、签名图像；可配置导出值。
- 格式输出：
  - DOCX 模板可输出 `docx`、`pdf`、`rtf`、`rtf to docx`、`tex`、`html`、`md` 等。
  - PDF 模板输出 `pdf`，可选扁平化、PDF/A、加密。
  - 手动附件可输出任意扩展名文件。
- 高级特性：PDF/A 转换、扁平化、密码保护、DOCX 引用更新、超链接样式、子模板合并、图像嵌入等。

## 需求范围
### 前端（React + TS + Tailwind）
- **模板选择**：
  - 内置 DOCX 模板列表供用户选择（显示示例名称、预览/说明）。
  - 后续可扩展自定义上传。
- **字段填写**：
  - 根据模板字段定义生成表单（文本、数字、布尔、日期、文件上传等）。
  - 提供 JSON 查看/编辑模式（可选）。
- **输出格式选择**：
  - 列出后端支持的格式（DOCX、PDF、HTML、RTF、TeX、Markdown 等），允许多选。
  - 展示高级选项（如 PDF/A、扁平化、加密等）。
- **生成与下载**：
  - 触发生成任务，展示进度/状态。
  - 生成完成后提供下载按钮，可一次下载多种格式（组合打包或单个）。
  - 提供错误提示与重试机制。
- **鉴权说明**：
  - 本阶段不引入任何鉴权或安全策略，所有接口假设在受信网络内部使用。

### 后端（Python, 推荐 FastAPI）
- 接收模板标识与字段 JSON，调度 DOCX/PDF 填充流程。
- 支持格式转换链，输出 Docassemble 覆盖的各类格式。
- 管理任务状态、临时文件、日志；提供结果下载接口。
- 处理高级选项（PDF/A、扁平化、密码、附加文档等）。

## 技术路径
- **前端实现**：
  - 组件：模板库、字段表单、输出格式选择器、任务状态展示、下载列表、设置面板、错误提示。
  - 状态管理：首阶段使用 React Query + 本地状态；若业务复杂度提升，再引入 Zustand。表单状态需与任务状态分离，避免重复请求。
  - API 对接：使用 Axios 封装统一客户端，集中处理错误拦截、文件上传（multipart/form-data）与结果下载（Blob + FileSaver）。
  - UI 规范：Tailwind + Headless UI 构建组件，预置主题、暗色模式、响应式布局；输出格式、多选列表、进度条等组件可复用。
  - 可扩展性：预留国际化（i18n）与可访问性（a11y）钩子，所有文案集中管理，表单控件符合键盘可达要求。
- **后端实现**：
  - 框架：FastAPI + Pydantic v2 数据模型，运行于 Uvicorn/Gunicorn；按功能拆分 Router，提供 OpenAPI 文档。
  - 核心依赖：与 ReferenceProjects/docassemble 环境保持一致，包含 `docxtpl`、`python-docx`、`docxcompose`、`pikepdf`、`xfdfgen`、`pdftk`、`qpdf`、ImageMagick、Pandoc、LibreOffice、`unoconv` 等全量组件。
  - 模板管理：模板目录结构为 `templates/<template_id>/`，包含主模板、静态资源与 `metadata.json`；后端通过缓存服务（如 `functools.lru_cache` 或 Redis）提升读取效率。
  - 转换流程：构建 `ConversionPipeline`，支持 docx → pdf → {html, rtf, tex, md} 链路；根据目标格式动态组合 Pandoc、LibreOffice、ImageMagick 调用，统一错误处理。
  - 外部依赖监测：在服务启动与定期巡检中检测 Pandoc/LibreOffice 等命令可用性，提供降级策略（例如仅返回原始 DOCX）与报警机制。
  - 文件处理：使用 `tempfile` 创建任务级别临时目录，任务完成后将产物归档至 `results/<task_id>/`；定时清理过期目录，必要时接入对象存储。
  - 异步任务：MVP 使用 FastAPI BackgroundTasks；若任务耗时超过阈值（例如 10 秒），升级为 Celery + Redis，抽象任务执行接口以便切换实现。
  - 监控与日志：引入结构化日志（`loguru` 或 `structlog`），记录模板 ID、格式、耗时、错误堆栈；预留 Prometheus 指标导出端点。

## 架构设计
- **整体架构**：前端 Vite + React SPA 部署于静态托管（Vercel/S3 + CloudFront）；后端 FastAPI 服务部署在容器环境，通过 HTTPS 提供 API。必要时引入 API 网关与对象存储。
- **模块划分**：
  - Web 前端：页面路由、视图组件、表单引擎、任务中心、下载管理。
  - API 层：模板管理、渲染任务、文件下载、系统配置接口。
  - 渲染引擎：封装 DOCX/PDF 渲染逻辑，提供统一 `RenderService`。
  - 转换服务：对外提供 `convert(input_path, target_format, options)`，内部调用 Pandoc/LibreOffice。
  - 存储层：模板仓库、任务元数据（SQLite/Postgres）、结果文件存放（本地或对象存储）。
  - 任务调度：背景任务执行器（BackgroundTasks/Celery），负责并发控制、重试、超时。
- **部署形态**：
  - 本地开发：Docker Compose（FastAPI、前端、Redis、LibreOffice/Pandoc 镜像）。
  - 测试环境：CI/CD 自动部署，使用持久化卷存储模板与日志。
  - 生产环境：Kubernetes 或容器服务，配合水平扩展、健康检查、集中日志。

## 模板与字段建模
- **模板元数据结构**（`templates/<id>/metadata.json`）示例：
  ```json
  {
    "id": "example_contract",
    "name": "示例合同",
    "description": "基础合同模板，包含当事人信息与条款",
    "version": "1.0.0",
    "entry": "template.docx",
    "preview": "preview.png",
    "fields": [
      {
        "name": "party_a_name",
        "label": "甲方名称",
        "type": "string",
        "required": true,
        "placeholder": "请输入公司名称"
      },
      {
        "name": "sign_date",
        "label": "签署日期",
        "type": "date",
        "required": true
      }
    ],
    "options": {
      "allowed_outputs": ["docx", "pdf", "html", "markdown"],
      "pdf": {
        "allow_flatten": true,
        "allow_pdfa": true,
        "allow_password": true
      }
    }
  }
  ```
- **字段类型映射**：`string`、`number`、`boolean`、`date`、`enum`、`file`、`textarea/richtext`；支持正则、最值、长度等校验规则。
- **高级配置**：字段分组（steps/sections）、条件显示（依赖表达式）、默认值计算（表达式），后续可与 JSON Schema/自定义 DSL 融合。

## 核心业务流程
1. 用户进入前端，选择模板，加载字段定义、预览、支持输出格式。
2. 前端基于字段元数据生成动态表单，展示高级选项（PDF/A、加密等）。
3. 用户填写数据后提交：
   - 前端执行校验，构建 `RenderRequest`，调用 `POST /api/templates/render`。
   - 后端校验字段与选项，创建任务记录，写入持久化存储，返回 `task_id`。
4. 任务执行：
   - 渲染引擎按模板类型加载并填充数据（DOCX → `docxtpl`，PDF → `xfdfgen/pdfrw`）。
   - 生成基础文件后调用转换服务，按请求格式输出结果。
   - 生成结果文件元数据，写入 `task_results`。
5. 前端根据 `task_id` 轮询 `GET /api/templates/{task_id}` 或使用 SSE/WebSocket 接收进度更新。
6. 任务完成后，用户在下载列表中选择单个文件或批量打包（Zip）下载。

### 错误处理与重试
- 输入校验失败返回 422，并包含详细字段错误信息。
- 渲染或转换失败：记录错误日志，通知监控，返回 500 与 error_code；支持后台重试一次。
- 外部工具超时：设置 120 秒超时与资源限制，超时后中止进程并提示用户重试。
- 结果存储失败：回滚任务状态并推送告警。

## 数据模型与接口契约
- **数据库表**（以 Postgres 为例）：
  - `templates`：`id`, `name`, `description`, `version`, `entry`, `config_hash`, `status`, `created_at`, `updated_at`.
  - `template_files`：`id`, `template_id`, `filename`, `file_type`, `checksum`, `path`.
  - `tasks`：`id`, `template_id`, `status`, `requested_formats`, `options`, `requested_by`, `progress`, `error_code`, `created_at`, `updated_at`, `expires_at`.
  - `task_results`：`id`, `task_id`, `format`, `file_path`, `file_size`, `checksum`, `download_token`, `expires_at`（默认保留 7 天，可通过配置延长，配合定期清理任务）。
  - `task_logs`：`id`, `task_id`, `level`, `message`, `payload`, `created_at`.
- **Pydantic 模型**：
  - `TemplateSummary`: `id`, `name`, `description`, `version`, `fields`, `allowed_outputs`, `preview_url`.
  - `FieldSchema`: `name`, `label`, `type`, `required`, `default`, `placeholder`, `options`, `validation`.
  - `RenderRequest`: `template_id`, `data`, `formats`, `options`, `attachments`.
  - `RenderResponse`: `task_id`, `status`, `expires_at`.
  - `TaskStatus`: `task_id`, `status`（`queued/processing/succeeded/failed`）, `progress`（0-100）, `results`, `error`.
  - `ResultFile`: `format`, `download_url`, `file_size`, `checksum`, `expires_at`.

## API 设计初稿
- `GET /api/templates`：返回模板列表（含字段概要、预览信息）。
- `GET /api/templates/{template_id}`：返回指定模板详情及字段定义。
- `POST /api/templates/render`：提交模板 ID、字段 JSON、输出格式、高级选项，返回任务 ID。
- `GET /api/templates/{task_id}`：查询任务状态、进度、结果文件列表。
- `GET /api/templates/{task_id}/files/{format}`：下载指定格式结果。
- `GET /api/formats`：列出支持的输出格式及高级选项说明。
- `POST /api/templates/validate`（可选）：仅校验字段数据不生成文件，用于前端预检。

## 环境与工具链
- **开发环境**：Python 3.11、Node.js 20、pnpm；提供 Dev Container 或 `Makefile/justfile` 简化命令。
- **Python 依赖管理**：采用 `uv` 统一创建虚拟环境与锁定依赖，配套 `uv pip sync` 与 `uv lock --upgrade` 流程。
- **容器镜像策略**：
  - 使用与 ReferenceProjects/docassemble 同源的 Ubuntu 基础镜像与依赖安装脚本，确保 Pandoc、LibreOffice、ImageMagick、`unoconv`、`pdftk` 等工具版本一致。
  - 通过多阶段 Dockerfile 构建，将重量级依赖安装与应用代码分层缓存；基础镜像在构建阶段完成全部 docassemble 依赖安装并清理缓存。
  - 提供 `docker-compose.yml`，聚合 FastAPI、前端、Redis（如需）及渲染依赖服务，一键启动开发环境；配套 `make build`、`make up`、`make render-sample` 等脚本做健康检查。
  - 在容器启动脚本中执行 `pandoc --version`、`soffice --headless --version` 等探测，并暴露 `/health/deps` 接口，支持故障排查。
- **本地调试指引**：
  - `docs/技术调研报告.md` 集中记录 docassemble 依赖栈的安装流程、版本比对、常见问题及与 ReferenceProjects/docassemble 的对齐矩阵。
  - 通过预置 `make render-sample`、`make healthcheck` 等脚本验证 Pandoc、LibreOffice、ImageMagick 可用性，确保本地行为与 docassemble 实例一致。
- **CI/CD**：GitHub Actions/GitLab CI，包含 lint、测试、构建、集成测试、镜像推送等流程。
- **质量保障**：
  - 前端：ESLint、Prettier、Stylelint、Vitest、React Testing Library。
  - 后端：Ruff、Mypy、Pytest、Coverage、Bandit。
  - 依赖更新：Dependabot 定期检查版本。

## 流程管理与协作
- 使用看板工具（Jira/Linear）跟踪需求、任务、缺陷；每周例会同步进展与风险。
- 维护 ADR（Architecture Decision Record），记录关键技术决策与取舍。
- 模板上线流程：提交模板包（模板文件 + metadata + 示例数据 + 预览图），通过代码评审与自动校验后合并。

## 测试与验收
- **测试分层**：
  - 单元测试：渲染函数、转换适配器、表单校验。
  - 集成测试：结合真实模板与示例数据，验证 API 与文件输出正确性。
  - E2E：模拟用户生成与下载流程，涵盖错误提示与重试。
  - 回归测试：确保新增模板不会破坏既有模板；引入快照对比（DOCX/HTML 结构）。
- **验收标准**：
  - 至少 3 个 DOCX、1 个 PDF 模板通过全流程验证。
  - 支持 DOCX、PDF、HTML、Markdown 输出，格式与内容正确。
  - 任务失败时返回明确错误码与追踪 ID，前端展示友好提示。
  - 提供完备的部署脚本、使用手册、模板编写规范。

## 风险与缓解
- **依赖与部署复杂度**：通过容器化、初始化脚本封装安装，区分基础/高级功能路径。
- **模板兼容性**：提供模板校验工具，覆盖常见场景；引入示例库进行回归测试。
- **性能瓶颈**：任务调度引入并发控制、限流、缓存；必要时拆分渲染与转换阶段，并明确吞吐量/时延指标用于验收。
- **资源限制**：对 Pandoc、LibreOffice 等外部命令设置容器 CPU/内存配额与执行超时，结合监控报警防止资源耗尽。
- **前端字段配置**：建立模板字段验证流程，结合自动化测试与人工校验。

## 后续工作
- 支持自定义模板上传与版本管理，提供在线模板预览（高优先级，依赖模板校验能力完备）。
- 引入字段映射可视化工具，帮助业务方编辑模板（中优先级，需要完善字段 DSL）。
- 集成对象存储（S3/OSS/MinIO）与消息队列提升扩展性。
- 规划多语言界面、本地化输出支持。
- 持续调研替代库（`borb`, `pdfplumber`, `docx2pdf` 等）优化性能与依赖。
