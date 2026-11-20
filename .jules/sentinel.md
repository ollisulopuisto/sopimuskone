## 2026-11-16 - User-supplied contract data rendered as unescaped markup
**Vulnerability:** Contract text entered by the user (names, addresses, free-form conditions) is interpolated directly into HTML rendered by the live preview and into reportlab Paragraph markup for PDF export without output encoding. Markup characters are interpreted as structure, so contract content can be visually spoofed or silently mangled.
**Learning:** Both QTextEdit.setHtml() and reportlab Paragraph re-parse developer-built HTML/XML markup, so encoding must happen at the render layer, immediately before interpolation — not on input storage.
**Prevention:** Escape all user-controlled values with html.escape() right before embedding them in HTML/markup, and convert newlines to `<br/>` only after escaping. Keep raw data in the data model and in conditional logic.

## 2026-11-19 - Untrusted contract JSON aborts the app on type mismatch
**Vulnerability:** Contract JSON files are read from local directories and their values are passed straight into Qt setters and string operations without type validation. A field of the wrong type (number, list, null) raises a TypeError inside a Qt signal slot; PyQt treats an unhandled slot exception as fatal and aborts the process, so a single malformed file can prevent the app from starting.
**Learning:** Loaded JSON is untrusted input even in a local desktop app, and PyQt does not surface slot exceptions as catchable Python errors - they terminate the process. Checking only that keys are present (`_is_contract_file`) does not validate their values.
**Prevention:** Coerce/validate deserialized data to its expected types at the load boundary, before it reaches UI code, and fail secure with safe defaults instead of trusting the file's shape.

## 2026-11-19 - Correct types are not enough: comparability and decoder depth
**Vulnerability:** Even after contract fields were type-coerced, single malformed files still aborted startup: ISO timestamps that mix timezone-aware and naive forms raise TypeError when the contract list is sorted, and pathologically nested JSON raises RecursionError while decoding rather than a JSONDecodeError.
**Learning:** "The value has the expected Python type" is weaker than "every downstream operation on the value is total". Ordering comparisons and decoder resource limits are separate failure modes that input type checks do not cover.
**Prevention:** Normalize parsed values into one comparable representation at the load boundary (for example, convert timestamps to a single timezone before sorting), and treat decoder resource errors such as RecursionError alongside malformed-syntax errors when skipping untrusted files.
