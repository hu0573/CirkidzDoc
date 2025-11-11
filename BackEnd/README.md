# CirkidzDoc 后端服务

该目录包含基于 FastAPI 实现的文档模板填充与转换服务。当前阶段实现了基础骨架、模板元数据加载与健康检查接口。

## 快速开始

```bash
uv sync
uv run fastapi dev app/main.py --reload
```

默认情况下，服务监听 `http://127.0.0.1:8000`，可通过 `http://127.0.0.1:8000/health` 检查健康状态。

## 模板目录

模板位于 `BackEnd/templates/` 目录，后端通过 `metadata.json` 描述模板信息。可通过环境变量 `BACKEND_TEMPLATE_ROOT` 覆盖模板根目录。

## 常用命令

请参阅 `Makefile` 获取 `uv` 同步、运行开发服务以及调用通用健康检查脚本的示例命令。

