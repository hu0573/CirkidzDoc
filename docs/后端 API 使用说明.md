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
    "entry": "template.docx",
    "field_count": 4
  }
]
```

### 2. 获取模板详情
- **Endpoint**：`GET /api/templates/{template_id}`
- **说明**：返回指定模板的完整元数据信息。元数据现仅包含模板标识、入口文件、描述以及精简后的 `fields` 列表（每个字段仅含 `name` 与 `type`）。
- **响应示例**
```json
{
  "template": {
    "id": "example_contract",
    "name": "示例合同",
    "description": "基础合同模板",
    "entry": "template.docx",
    "fields": [
      { "name": "party_a_name", "type": "string" },
      { "name": "party_b_name", "type": "string" },
      { "name": "sign_date", "type": "date" }
    ]
  }
}
```

### 3. 上传模板
- **Endpoint**：`POST /api/templates/upload`
- **说明**：接收 DOCX 模板文件，创建模板目录并根据 `{{placeholder}}` 自动生成基础 `metadata.json`。
- **请求格式**：`multipart/form-data`，包含一个 `file` 字段（仅支持 `.docx`，大小不超过 20MB）。
- **响应示例**
```json
{
  "template": {
    "id": "partner-contract",
    "name": "Partner Contract",
    "description": "",
    "entry": "Partner Contract.docx",
    "fields": [
      { "name": "client_name", "type": "string" },
      { "name": "sign_date", "type": "string" }
    ]
  },
  "metadata_path": "partner-contract/metadata.json",
  "message": "模板已创建，请编辑 metadata.json 确认字段类型。"
}
```
- **备注**
  - 模板 ID 根据文件名自动转换为 kebab-case，如已存在同名目录会自动追加数字后缀。
  - 默认将所有占位符生成为 `string` 类型，可以手动编辑生成的 `metadata.json` 调整类型（例如日期或数字）。
  - 新模板默认启用系统维护的全部输出能力，无需再配置 `options`。

### 4. 查询支持的输出格式
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

### 5. 提交渲染任务
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

### 6. 查询任务状态
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

### 7. 下载任务结果
- **Endpoint**：`GET /api/templates/tasks/{task_id}/files/{format}?token=<download_token>`
- **说明**：基于任务 ID、目标格式与下载 token 获取文件。
- **返回**：二进制流，默认 `application/octet-stream`。
- **错误码**
  - `404`：任务不存在、token 无效或文件已过期。

## 任务生命周期与清理
- 任务默认有效期由 `