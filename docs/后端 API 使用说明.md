# 后端 API 使用说明

本文档介绍当前 FastAPI 后端提供的公开接口、请求示例及注意事项，便于前端或第三方服务集成调试。

## 基础信息
- 服务地址：`http://<host>:<port>`
- OpenAPI 文档：`/docs`（Swagger UI）、`/redoc`
- 所有接口均返回 JSON，除文件下载接口外。

## 鉴权
目前处于内网 MVP 阶段，未启用鉴权。后续如需引入 Token/Session，请在接口层统一加装。

## 接口列表

### 1. 获取模板列表
- **Endpoint**：`GET /api/templates`
- **说明**：返回所有可用模板的概要信息。
- **响应示例**
```json
[
  {
    "id": "example_contract",
    "name": "示例合同",
    "description": "基础合同模板",
    "version": "1.0.0",
    "preview": "preview.png",
    "field_count": 6,
    "allowed_outputs": ["docx", "pdf", "html", "markdown"]
  }
]
```

### 2. 获取模板详情
- **Endpoint**：`GET /api/templates/{template_id}`
- **说明**：返回指定模板的完整元数据（字段定义、输出选项等）。

### 3. 查询支持的输出格式
- **Endpoint**：`GET /api/formats`
- **说明**：列出 DOCX 转换流水线支持的目标格式及 PDF 高级选项能力。
- **响应示例**
```json
{
  "formats": [
    { "id": "docx", "label": "DOCX", "description": "DOCX 模板可导出格式" },
    { "id": "html", "label": "HTML", "description": "DOCX 模板可导出格式" }
  ],
  "advanced_options": {
    "pdf": {
      "allow_flatten": true,
      "allow_pdfa": true,
      "allow_password": true,
      "description": "PDF 渲染支持扁平化、PDF/A、密码保护"
    }
  }
}
```

### 4. 提交渲染任务
- **Endpoint**：`POST /api/templates/render`
- **状态码**：`202 Accepted`
- **说明**：创建一个异步渲染任务，后台执行后在数据库中记录结果。
- **请求体**
```json
{
  "template_id": "example_contract",
  "data": {
    "party_a_name": "甲方科技",
    "party_b_name": "乙方合作",
    "sign_date": "2025-11-11"
  },
  "formats": ["docx", "pdf"],
  "options": {
    "pdf": {
      "flatten": true,
      "password": "Secret123"
    }
  }
}
```
- **响应体**
```json
{
  "task_id": "4df5c4a0f5f34e64af3f2b6f1a4e2c51",
  "status": "queued",
  "expires_at": "2025-11-11T14:30:00Z"
}
```
- **错误说明**
  - `404`：模板不存在。
  - `422`：请求参数校验失败。

### 5. 查询任务状态
- **Endpoint**：`GET /api/templates/tasks/{task_id}`
- **说明**：返回任务状态、进度及生成结果列表。
- **响应示例**
```json
{
  "task_id": "4df5c4a0f5f34e64af3f2b6f1a4e2c51",
  "status": "succeeded",
  "progress": 100,
  "error": null,
  "results": [
    {
      "format": "docx",
      "download_url": "/api/templates/tasks/4df5c4a0f5f34e64af3f2b6f1a4e2c51/files/docx?token=af2db4f5...",
      "file_size": 143256,
      "checksum": "8f5d3d...",
      "expires_at": "2025-11-11T15:30:00Z"
    }
  ]
}
```
- **状态枚举**
  - `queued`：已入队等待执行。
  - `processing`：正在渲染/转换。
  - `succeeded`：全部结果生成完成。
  - `failed`：任务失败，`error` 字段包含失败原因。

### 6. 下载任务结果
- **Endpoint**：`GET /api/templates/tasks/{task_id}/files/{format}?token=<download_token>`
- **说明**：基于任务 ID、目标格式与下载 token 获取文件。
- **返回**：二进制流，默认 `application/octet-stream`。
- **错误码**
  - `404`：任务不存在、token 无效或文件已过期。

## 任务生命周期与清理
- 任务默认有效期由 `BACKEND_TASK_EXPIRY_MINUTES` 控制（默认 60 分钟）。
- 创建任务时会自动清理已过期任务及其磁盘文件。
- 结果文件存放于 `results/<task_id>/` 目录，可通过 `BACKEND_RESULTS_ROOT_RELATIVE` 覆盖。

## 数据库存储
- 默认使用 SQLite（路径：`BackEnd/data/backend.db`），可通过 `BACKEND_DATABASE_URL` 切换到 PostgreSQL 等数据库。
- 首次启动会自动创建 `templates`、`tasks`、`task_results` 三张表。

## 调试建议
- 启动后访问 `/docs` 验证 OpenAPI 定义。
- 使用 `uv run pytest` 运行内置测试确保渲染、转换链路正常。
- 若外部依赖缺失，可调用 `/health/deps`（待实现）或查看日志定位失败命令。


