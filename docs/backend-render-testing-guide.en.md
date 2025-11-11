# Backend Rendering Test Guide

## Objectives
- Verify that the DOCX rendering service handles dynamic fields, date formatting, and embedded images correctly.
- Verify that the PDF rendering service populates text fields and checkboxes, and degrades gracefully when dependencies are missing.
- Validate the control flow in `ConversionPipeline` for DOCX → PDF/Pandoc multi-format conversions.
- Ensure the health check endpoint reflects external dependency status and switches to `degraded` when dependencies are unavailable.

## Test Layers
- **Unit tests**: Located under `BackEnd/tests/`, executed with `pytest`. They minimize dependencies and use MonkeyPatch to stub external tools.
- **Dependency simulation**: Commands such as Pandoc, LibreOffice, qpdf, and Ghostscript are intercepted with `DummyRunner` or MonkeyPatch so tests run even when the binaries are not installed locally.
- **Data fabrication**: Tests generate DOCX templates and sample images dynamically, keeping them independent from the actual template repository.

## Coverage
- `test_docx_renderer.py`
  - Render string and date fields, then assert the output text.
  - Inject a logo via the image descriptor protocol (`{"__type": "image"}`) and confirm the `InlineImage` output.
- `test_pdf_renderer.py`
  - Populate text fields and toggle checkboxes, ensuring `/V` and `/AS` are assigned correctly.
  - Confirm `NeedAppearances` is enabled automatically so PDF readers render appearances properly.
- `test_conversion_pipeline.py`
  - Request `docx`, `pdf`, `html`, and `markdown` outputs simultaneously, validating command invocation order and output paths.
  - Raise `ConversionError` for unsupported formats (for example, `pptx`).
- `test_health_api.py`
  - Simulate missing dependencies to assert the `degraded` status and dependency matrix content.

## Execution
```bash
cd BackEnd
uv sync --extra dev      # Run on first setup or when dependencies change
uv run pytest            # Or use .venv/bin/pytest
```

## Future Enhancements
- Add integration tests once real Pandoc/LibreOffice environments are available to cover end-to-end DOCX → PDF → HTML conversions.
- After the task orchestrator is ready, write contract tests for the background task APIs to verify result archiving and download workflows.


