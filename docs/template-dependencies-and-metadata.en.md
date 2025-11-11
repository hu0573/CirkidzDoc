## Template Dependencies and Metadata Specification

### Background
To ensure templates migrated from docassemble remain reusable in the new backend service, this specification catalogues the core components required for existing docassemble template and output workflows. It also defines a unified metadata schema and validation rules to guide implementation and testing.

### Template Capabilities & Dependency Matrix
| Template Type | Rendering Pipeline | Supported Outputs | Key Dependencies | Notes |
| --- | --- | --- | --- | --- |
| DOCX (`docx_template_file`) | Jinja2 → docxtpl → python-docx → docxcompose | docx, pdf, html, rtf, tex, markdown | `docxtpl`, `python-docx`, `docxcompose`, LibreOffice (`soffice`), Pandoc, ImageMagick | DOCX is the base artifact. LibreOffice creates PDFs, Pandoc generates HTML/Markdown/TeX/RTF, and ImageMagick handles image processing. |
| PDF (`pdf_template_file`) | XFDF generation → pdftk/pikepdf → qpdf | pdf (optional flattening, PDF/A, encryption) | `xfdfgen`, `pdftk`, `pikepdf`, `qpdf`, `ghostscript` | `pdftk` fills forms and flattens output; `pikepdf` writes fields; `ghostscript` produces PDF/A; `qpdf` encrypts. |
| RTF (`rtf_template_file`) | Template merge → LibreOffice conversion | rtf, docx, pdf, html | LibreOffice, Pandoc | RTF output usually needs converting to DOCX/HTML; style compatibility is critical. |
| Attachment (`attachment`) | Direct bundling | Any | File storage | Ships static files without rendering or conversion. |

#### Advanced Features & Dependencies
- PDF/A: `ghostscript`, `qpdf`
- Flattening: `pdftk` (`flatten`) or `ghostscript`
- Image embedding: `docxtpl`, `Pillow`
- Hyperlink/style refresh: `python-docx`, `docxcompose`
- Sub-template merging: `docxcompose`, `jinja2`

### Template Metadata Structure
Templates reside under `templates/<template_id>/` with main files, assets, sample data, and preview images. Metadata is stored in `metadata.json` with the following fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | string | Yes | Unique identifier (kebab-case). |
| `name` | string | Yes | Display name; supports localization. |
| `description` | string | Yes | Template description; Markdown-friendly. |
| `version` | string | Yes | Semantic version used for caching and rollback decisions. |
| `entry` | string | Yes | Relative path to the main template file. |
| `preview` | string | No | Preview image path (PNG recommended). |
| `tags` | string[] | No | Business tags such as industry or document type. |
| `fields` | FieldSchema[] | Yes | Field definitions (see below). |
| `options` | object | Yes | Rendering and output options. |
| `examples` | array | No | Example payloads for integration tests. |
| `created_at` | string | No | ISO8601 creation timestamp. |
| `updated_at` | string | No | ISO8601 update timestamp. |

Recommended `options` shape:
```json
{
  "allowed_outputs": ["docx", "pdf", "html", "markdown"],
  "pdf": {
    "allow_flatten": true,
    "allow_pdfa": true,
    "allow_password": true,
    "default_flatten": false
  },
  "docx": {
    "update_reference_fields": true
  }
}
```

### Field Type Mapping & Validation
`FieldSchema` structure:
```json
{
  "name": "party_a_name",
  "label": "Party A Name",
  "type": "string",
  "required": true,
  "placeholder": "Enter company name",
  "default": "",
  "validation": {
    "pattern": "^[\\u4e00-\\u9fa5A-Za-z0-9（）()]{2,60}$",
    "message": "Name must be 2-60 characters and can include Chinese brackets"
  },
  "options": {
    "enum": ["option_a", "option_b"]
  },
  "depends_on": {
    "field": "need_extra_clause",
    "value": true
  }
}
```

Field type to component mapping:

| `type` | UI Component | Validation | Notes |
| --- | --- | --- | --- |
| `string` | Single-line text input | `minLength`, `maxLength`, `pattern` | UTF-8 by default; allow casing helpers. |
| `textarea` / `richtext` | Multi-line text / rich text editor | Length checks, rich-text whitelist | Sanitize rich text server-side. |
| `number` | Numeric input | `minimum`, `maximum`, `multipleOf` | Support integers/floats; use `input[type=number]`. |
| `boolean` | Toggle or checkbox | - | Respect defaults and disabled state. |
| `date` | Date picker | ISO8601 validation | Extend to `date_range` as needed. |
| `enum` | Select / radio group | Enum membership | Use `enumLabels` for display strings. |
| `file` | File upload | MIME and size constraints | Document allowed types and max size. |

Common validation rules:
- Server-side validation: Re-run all checks in the backend with Pydantic plus custom logic to prevent bypasses.
- Dependencies: `depends_on` supports simple boolean expressions; extend with a DSL for complex logic later.
- Defaults: When `default` is absent, fall back to empty string, `false`, `null`, or `[]` depending on type.
- Internationalization: `label`, `placeholder`, and `validation.message` can use `{ "zh-CN": "...", "en-US": "..." }`.

### Conclusions & Next Steps
1. Use this dependency matrix to build installation scripts that align CLI tool versions with docassemble.
2. Validate `metadata.json` through JSON Schema in the backend to enforce consistent field definitions.
3. Feed `FieldSchema` directly into the frontend dynamic-form engine; integrate React Hook Form with Zod/JSON Schema generators for unified validation.


