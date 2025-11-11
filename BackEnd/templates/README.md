# 模板目录说明

所有模板按照 `templates/<template_id>/` 组织，每个模板目录至少包含：

- `metadata.json`：模板元数据，定义字段、输出格式与高级选项。
- 实际模板文件（如 `template.docx` 或 `form.pdf`），名称由 `metadata.json` 中的 `entry` 指定。
- 可选静态资源（预览图、附件）用于前端展示或渲染附带。

当模板目录发生变更后，可执行 `make refresh-templates` 刷新缓存。

