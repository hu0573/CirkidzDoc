## Transformation Goals Overview
- Clean up the current template structure, remove preview assets, and streamline metadata fields.
- Support user uploads of custom templates and generate initial metadata configuration automatically.
- Remove explicit configuration for template conversion options so that all capabilities are enabled by default.

## Template Directory Adjustments (`BackEnd/templates`)
- **Remove preview assets**: Traverse each template directory, delete preview images and related references, and confirm the frontend no longer depends on them.
- **Streamline field definitions**: Update `metadata.json` so that each field only retains `name` and `type`. Remove redundant attributes such as `label`, `description`, and `required`; treat all fields as required by default during generation.
- **Metadata format specification**: Standardize template metadata to include only `id`, `name`, `description`, `entry`, and `fields`. Inside `fields`, each field should keep only `name` and `type`. Remove legacy properties like `version`, `label`, `required`, and `options` to avoid confusion.
- **Structural validation**: Validate the new parsing logic to ensure templates load without `KeyError` when optional fields are missing, and verify that frontend rendering and form binding still work correctly.
- **Documentation sync**: Update existing documentation to describe the new metadata format and constraints.

## Template Upload Feature
- **Backend endpoint**: Design an upload endpoint that accepts a template file and automatically creates `BackEnd/templates/<new-template>/` based on the filename.
- **Template initialization**:
  - Save the uploaded document as the template entry file.
  - Generate a base `metadata.json`, pre-filling `id`, `name`, and `entry`; keep `description` empty by default. Build the `fields` array by parsing placeholders, initially setting every field `type` to `string` so users can adjust later.
  - Placeholder extraction: Reuse the current template syntax to detect variables like `{{placeholder}}`. Allow repeated occurrences but de-duplicate at the metadata level.
- **Guided response**: Return the creation result along with follow-up guidance (e.g., where to edit metadata next).
- **Validation & conflicts**: Enforce file type and size limits, handle naming collisions, and ensure safe folder creation.
- **Default output capabilities**: New templates should immediately leverage the full system output format list without extra `options` configuration.

## Metadata Editing Experience
- **Frontend interaction**:
  - Add a dedicated "Field Configuration" section in the template detail view that lists fields from `metadata.json`.
  - Expose only `name` and `type` columns for each field. Provide a dropdown for `type` (e.g., `string`, `number`, `date`), defaulting to `string`.
  - When the document contains placeholders not yet registered in metadata, display a notification (e.g., "New placeholders detected") with a one-click action to add them.
  - Remove UI elements that relied on `label`, `description`, `required`, `validation`, and `placeholder`. Use the field `name` as the display label.
- **Backend persistence**: Implement an update endpoint so that field ordering and types remain consistent after saving and reloading.
- **Validation logic**: Validate that each field `name` is non-empty and that `type` belongs to the allowed list before saving.

## Options Cleanup and Frontend Simplification
- **Backend**: Remove parsing and usage of `metadata.json` `options` fields. Always enable the system-supported output formats.
- **Frontend**:
  - Delete any `TemplateDetailPanel` dependencies on `metadata.options`, including PDF-specific settings (`__pdf_flatten`, `__pdf_pdfa`, `__pdf_password`). Use `name` and `type` only when collecting field values.
  - Remove version badges (`template.version`) and allowed output format tags (`template.allowed_outputs`) from `TemplateList`.
  - Update `OutputFormatSelector` to rely on the system default format catalog, eliminating checklists driven by `metadata.options.allowed_outputs`.
- **Testing & regression**: Ensure default capabilities cover existing use cases without regressions.

## Verification & Release
- **Testing**: Add or update unit and integration tests for template loading, upload, and editing flows.
- **Regression checks**: Perform end-to-end validation with both existing templates and newly uploaded ones.
- **Documentation**: Document the upload workflow, metadata field rules, and new behavior without `options` in the `docs/` directory.
- **Release plan**: Prepare canary or beta rollout. Confirm that legacy templates migrate cleanly to the new structure before full release.
