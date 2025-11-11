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
Templates live under `templates/<template_id>/`, each with a main template file and metadata. `metadata.json` now contains the following minimal fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | string | Yes | Unique identifier (kebab-case), derived from the uploaded filename. |
| `name` | string | Yes | Display name; defaults to a title-cased version of the filename. |
| `description` | string | No | Optional description; defaults to an empty string. |
| `entry` | string | Yes | Relative path to the main template file (usually `.docx`). |
| `fields` | FieldSchema[] | Yes | Field definitions, each limited to `name` and `type`. |

> Legacy metadata fields—`version`, `preview`, `options`, tag collections, etc.—have been removed. The renderer exposes the full set of supported output formats automatically; no per-template `allowed_outputs` section is required.

Uploading a template performs the following steps:
1. Normalise the filename to kebab-case to produce the template directory and `id`. Conflicts are resolved by appending a numeric suffix.
2. Save the uploaded DOCX as the template entry file, preserving the original filename.
3. Scan all `{{placeholder}}` occurrences inside the DOCX, de-duplicate them, and populate the `fields` array. Every field defaults to type `string`; adjust the generated `metadata.json` to promote types (e.g. `date`, `number`).

### Field Schema
`FieldSchema` structure:
```json
{
  "name": "party_a_name",
  "type": "string"
}
```

Allowed `type` values and the suggested UI mapping:

| `type` | UI Component | Notes |
| --- | --- | --- |
| `string` | Single-line text input | Default type; the frontend uses the field `name` as the label. |
| `textarea` / `richtext` | Multi-line text / rich text editor | `richtext` still requires sanitation. |
| `number` | Numeric input | Supports integers and floats. |
| `boolean` | Toggle or checkbox | |
| `date` | Date picker | Expect ISO8601 strings in payloads. |
| `enum` | Select / radio group | Combine with static options in the template. |
| `file` | File upload | Values are Base64-encoded content. |

### Conclusions & Next Steps
1. Continue aligning installation scripts with docassemble’s dependency versions for the DOCX/PDF toolchain.
2. Provide JSON Schema validation for the simplified `metadata.json` to guarantee valid uploads.
3. Feed the streamlined `FieldSchema` into the frontend form renderer, adding UI affordances to edit field types or add/remove entries as needed.


