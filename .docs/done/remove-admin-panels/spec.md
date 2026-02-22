# Spec: Remove Admin Panels

### Requirement: Remove Panel Commands
The CLI SHALL no longer expose admin panel commands.

#### Scenario: CLI command listing
- GIVEN the digest CLI
- WHEN command help is displayed
- THEN `admin`, `admin-streamlit`, and `admin-streamlit-prototype` are not available

### Requirement: Remove Panel Code
The codebase SHALL not contain HTTP/Streamlit admin panel modules.

#### Scenario: Source tree inspection
- GIVEN the source tree under `src/digest`
- WHEN admin-panel modules are inspected
- THEN `src/digest/admin/` and `src/digest/admin_streamlit/` are absent

### Requirement: Preserve Ops via CLI + Telegram
Operational workflows SHALL continue via existing non-panel paths.

#### Scenario: Test suite verification
- GIVEN the repository test suite
- WHEN tests are executed
- THEN runtime, source ops, render, and Telegram admin command tests pass
