# Frontend Components and State Management Guide

## Overview

This document explains the frontend implementation of the Document Template Console, helping developers understand component responsibilities, state flow, and future extension principles. The frontend is built with React 19, TypeScript, and TailwindCSS, and uses React Query, React Hook Form, and Axios for data fetching and form handling.

The UI is divided into three primary areas that follow the flow of “list selection → dynamic form → task center”. The key components are:

- `TemplateList`: Displays the template catalog and handles selection.
- `TemplateDetailPanel`: Dynamically renders forms, output format configuration, and advanced options based on template metadata.
- `TaskCenter`: Shows the current task (with polling) and history, providing download and retry capabilities.

## Data Fetching and Caching

- `src/lib/apiClient.ts` defines the Axios instance, configuring `baseURL`, timeout, error interception, and helper functions for file downloads. The download helper assembles relative or absolute URLs returned by the backend and extracts filenames from the `Content-Disposition` header.
- `src/lib/api.ts` wraps template, format, and render-task APIs. All calls return strongly typed objects so components get immediate type hints.
- React Query is registered in `src/main.tsx` via `QueryClientProvider`, with window-refetch disabled and a single retry configured. This strikes a balance between request volume and resilience under poor network conditions.
- Queries used in `App`:
  - `['templates']`: Fetch the template list and auto-select the first entry on initial load.
  - `['template', templateId]`: Fetch details for the selected template. Switching selections only refreshes the relevant data instead of reloading everything.
  - `['formats']`: Retrieve supported output formats and advanced PDF capabilities.
  - `['taskStatus', taskId]`: Poll current task status every two seconds, stopping automatically when the task transitions to `succeeded` or `failed`.

## Form Construction and Validation

- `TemplateDetailPanel` renders input controls dynamically using `FieldSchema`, supporting `string`, `number`, `boolean`, `date`, `enum`, `textarea`, and `file` types.
- React Hook Form manages field values, validation, and errors. `ValidationRule` definitions (required, length, range, regex, etc.) are transformed into form validation logic automatically.
- File fields are encoded as Base64 strings before being submitted with the JSON payload. Files are capped at 20 MB by default; adjust the limit inside the component as needed. Switch to chunked uploads or multipart forms by replacing this logic with an upload endpoint that returns a file token.
- Output formats are configured via `OutputFormatSelector`, which surfaces descriptions provided by the backend. At least one format must be selected before submission, otherwise the user gets a validation error.
- When PDF output is selected, the component reads PDF capability flags from template metadata and conditionally renders options such as flattening, PDF/A, and password protection. Only enabled options are forwarded to the backend.

## Task Status and Download Management

- `TaskCenter` is split into **Current Task** and **History**:
  - Current Task: Displays task ID, real-time progress bar, status badge, failure reason, and generated results. Failed tasks can be retried with one click.
  - History: Keeps the latest 10 entries in reverse chronological order. Users can quickly download specific formats and retry failed tasks.
- Retry logic: `App` caches every task’s `RenderRequestPayload`. When a user clicks **Retry** in the task center, the original payload is reused. If the payload is missing (for example, after clearing history), the user is prompted to re-fill the form.
- Downloads: The `downloadFile` helper triggers browser downloads and works with both relative and absolute URLs from the backend. Any request or network error bubbles up to the global alert banner.

## Error Handling and Messaging

- API failures, polling errors, or task failures are converted to readable messages by `pickErrorMessage` and shown in the red banner at the top of the page.
- Template detail failures render an error card beside the template list so other content remains accessible.
- Field-level errors (including file validation) show under inputs with red text so users can spot issues quickly.
- The **Clear History** button in the task center removes past entries and dismisses alerts, making it easier to run new tests.

## Component Responsibilities and Extension Tips

| Component | Responsibility | Extension Ideas |
| --- | --- | --- |
| `TemplateList` | Display template summaries and handle selection | Add search, tag filters, or pagination |
| `TemplateDetailPanel` | Dynamic form, format configuration, and advanced options | Extract the field renderer into a `FieldRenderer` sub-component for complex layouts; integrate a rich-text editor if needed |
| `TaskCenter` | Task polling, downloads, and retries | Adopt WebSocket/SSE to reduce polling; add bulk downloads (ZIP) when required |
| `apiClient` | Axios setup and download helpers | Inject authentication tokens and handle 401 responses when auth is introduced |

## State Management Conventions

1. Global data (templates, task status, etc.) is managed by React Query to keep requests and caching consistent.
2. Short-lived state (selected template, alerts, task history) lives in the `App` component; lift it into Context if multiple descendants need access.
3. Form state and validation stay inside `TemplateDetailPanel`. Submissions bubble up through `RenderRequestPayload`, keeping the component cohesive.
4. All async operations use `async/await` plus the shared error-display helper so UI feedback remains consistent when failures occur.

## Suggested Enhancements

- **Task notifications**: Add browser notifications or audio alerts when tasks finish to improve UX for long-running jobs.
- **Form draft storage**: Provide local drafts for complex templates to prevent accidental data loss.
- **Internationalization & accessibility**: Externalize copy with libraries like `i18next` and improve keyboard/screen reader support.
- **Component tests**: Use React Testing Library to cover core interactions such as template switching, validation, and task polling.

These conventions keep the frontend understandable and evolvable, allowing future iterations to focus on business demands without compromising structure.


