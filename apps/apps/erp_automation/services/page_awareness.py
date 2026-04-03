"""
D365 Page Awareness — "Look → Act → Verify"

Reads D365 page state via Playwright JS evaluation without modifying anything.
Used by the executor to:
1. Log what field has focus before every step
2. Verify values were set correctly after fill/type actions
3. Count grid rows before/after "New" clicks
4. Provide page context to the debug UI
"""
import logging

logger = logging.getLogger(__name__)


class D365PageReader:
    """Read D365 page state without modifying anything.

    All methods are safe (read-only JS evaluation) and wrapped in
    try/except so a failed read never breaks the automation flow.
    """

    def __init__(self, page):
        self.page = page

    # ── FOCUSED ELEMENT ──────────────────────────────────────────

    def get_focused_field(self) -> dict:
        """What field currently has keyboard focus?

        Returns dict with: tag, type, id, name, label, value, placeholder,
        dyn_control (D365 data-dyn-controlname from ancestor).
        Returns empty dict on failure.
        """
        try:
            result = self.page.evaluate("""() => {
                const el = document.activeElement;
                if (!el || el === document.body) return {tag: 'BODY', name: null, value: null};

                // Walk up to find D365 control name
                let dynControl = null;
                let ancestor = el;
                for (let i = 0; i < 5 && ancestor; i++) {
                    const dcn = ancestor.getAttribute && ancestor.getAttribute('data-dyn-controlname');
                    if (dcn) { dynControl = dcn; break; }
                    ancestor = ancestor.parentElement;
                }

                return {
                    tag: el.tagName,
                    type: el.getAttribute('type') || '',
                    id: el.id || '',
                    name: el.getAttribute('name') || '',
                    label: el.getAttribute('aria-label') || '',
                    value: (el.value !== undefined ? el.value : (el.innerText || '')).substring(0, 200),
                    placeholder: el.getAttribute('placeholder') || '',
                    dyn_control: dynControl || '',
                    role: el.getAttribute('role') || '',
                    class_name: (el.className || '').substring(0, 100),
                };
            }""")
            return result or {}
        except Exception as e:
            logger.debug(f"[PageReader] get_focused_field failed: {e}")
            return {}

    # ── FIELD VALUE READING ──────────────────────────────────────

    def get_field_value(self, field_name: str) -> str | None:
        """Read a specific field's current value by name attribute.

        Searches main page and all iframes (D365 uses iframes).
        Returns the value string or None if not found.
        """
        try:
            result = self.page.evaluate("""(fieldName) => {
                function findInDoc(doc) {
                    // Try by name attribute first
                    let el = doc.querySelector('input[name="' + fieldName + '"]');
                    if (!el) el = doc.querySelector('textarea[name="' + fieldName + '"]');
                    if (!el) el = doc.querySelector('select[name="' + fieldName + '"]');
                    // Fallback: data-dyn-controlname
                    if (!el) {
                        const ctrl = doc.querySelector('[data-dyn-controlname="' + fieldName + '"]');
                        if (ctrl) el = ctrl.querySelector('input, textarea, select');
                    }
                    if (el) return el.value !== undefined ? el.value : (el.innerText || '');
                    return null;
                }
                // Search main document
                let val = findInDoc(document);
                if (val !== null) return val;
                // Search iframes
                const frames = document.querySelectorAll('iframe');
                for (const frame of frames) {
                    try {
                        val = findInDoc(frame.contentDocument || frame.contentWindow.document);
                        if (val !== null) return val;
                    } catch(e) {}
                }
                return null;
            }""", field_name)
            return result
        except Exception as e:
            logger.debug(f"[PageReader] get_field_value('{field_name}') failed: {e}")
            return None

    def get_field_value_by_element(self, element) -> str | None:
        """Read value from a Playwright Locator/ElementHandle."""
        try:
            return element.input_value(timeout=2000)
        except Exception:
            try:
                return element.inner_text(timeout=2000)
            except Exception:
                try:
                    return element.evaluate("el => el.value || el.innerText || ''")
                except Exception:
                    return None

    # ── GRID STATE ───────────────────────────────────────────────

    def count_grid_rows(self) -> int:
        """Count visible data rows in the active D365 grid.

        Excludes header rows and empty placeholder rows.
        Returns 0 on failure.
        """
        try:
            count = self.page.evaluate("""() => {
                function countInDoc(doc) {
                    // D365 FixedDataTable or standard grid
                    const rows = doc.querySelectorAll(
                        '[role="grid"] [role="row"], ' +
                        'table[role="grid"] tbody tr, ' +
                        '.fixedDataTableLayout_body [role="row"]'
                    );
                    let dataRows = 0;
                    for (const row of rows) {
                        // Skip header rows
                        if (row.closest('thead') || row.closest('[role="rowgroup"][aria-label*="header"]'))
                            continue;
                        // Skip empty/placeholder rows
                        const text = (row.textContent || '').trim();
                        if (text.length < 2) continue;
                        dataRows++;
                    }
                    return dataRows;
                }
                let total = countInDoc(document);
                const frames = document.querySelectorAll('iframe');
                for (const frame of frames) {
                    try {
                        total += countInDoc(frame.contentDocument || frame.contentWindow.document);
                    } catch(e) {}
                }
                return total;
            }""")
            return count or 0
        except Exception as e:
            logger.debug(f"[PageReader] count_grid_rows failed: {e}")
            return 0

    def count_selected_grid_rows(self, grid_scope: str = "") -> dict:
        """Count selected vs total data rows in a D365 grid.

        Args:
            grid_scope: Optional CSS/ID scope for a specific grid
                        (e.g. 'BOMTable' to search within that container).

        Returns dict: {total: int, selected: int, all_selected: bool,
                       checkbox_state: str ('true'|'false'|'mixed'|'unknown')}.
        """
        try:
            result = self.page.evaluate("""(gridScope) => {
                function checkInDoc(doc) {
                    // Find grid container — if gridScope given, narrow search
                    let root = doc;
                    if (gridScope) {
                        const scoped = doc.querySelector(
                            '[id*="' + gridScope + '"], [data-dyn-controlname*="' + gridScope + '"]'
                        );
                        if (scoped) root = scoped;
                    }

                    // Count total data rows (body rows, not headers)
                    const bodyRows = root.querySelectorAll(
                        '.fixedDataTableLayout_body [role="row"], ' +
                        '[role="rowgroup"]:not([aria-label*="header"]) [role="row"]'
                    );
                    let total = 0;
                    let selected = 0;
                    for (const row of bodyRows) {
                        // Skip header rows that might leak in
                        if (row.closest('.fixedDataTableLayout_header') ||
                            row.closest('thead') ||
                            row.closest('[role="rowgroup"][aria-label*="header"]'))
                            continue;
                        const text = (row.textContent || '').trim();
                        if (text.length < 2) continue;
                        total++;
                        // Check selection: D365 uses aria-selected or dyn-marked class
                        if (row.getAttribute('aria-selected') === 'true' ||
                            row.classList.contains('dyn-marked') ||
                            row.querySelector('.dyn-marked, [aria-checked="true"]')) {
                            selected++;
                        }
                    }

                    // Check the header "select all" checkbox state
                    let checkboxState = 'unknown';
                    const headerCb = root.querySelector(
                        '.fixedDataTableLayout_header [role="checkbox"][title*="Select"],' +
                        '.fixedDataTableLayout_header [aria-checked]'
                    );
                    if (headerCb) {
                        checkboxState = headerCb.getAttribute('aria-checked') || 'unknown';
                    }

                    return {total, selected, checkboxState};
                }

                // Try main document
                let res = checkInDoc(document);
                if (res.total > 0) return res;

                // Try iframes
                const frames = document.querySelectorAll('iframe');
                for (const frame of frames) {
                    try {
                        res = checkInDoc(frame.contentDocument || frame.contentWindow.document);
                        if (res.total > 0) return res;
                    } catch(e) {}
                }
                return {total: 0, selected: 0, checkboxState: 'unknown'};
            }""", grid_scope)
            if result:
                result["all_selected"] = (
                    result["total"] > 0 and result["selected"] >= result["total"]
                ) or result.get("checkboxState") == "true"
                return result
            return {"total": 0, "selected": 0, "all_selected": False, "checkboxState": "unknown"}
        except Exception as e:
            logger.debug(f"[PageReader] count_selected_grid_rows failed: {e}")
            return {"total": 0, "selected": 0, "all_selected": False, "checkboxState": "unknown"}

    def get_grid_row_values(self, max_rows: int = 20) -> list:
        """Read visible grid rows as a list of cell-value lists.

        Returns [["cell1", "cell2", ...], ...] for each visible row.
        Useful for verifying BOM lines were added correctly.
        """
        try:
            rows = self.page.evaluate("""(maxRows) => {
                function readGrid(doc) {
                    const result = [];
                    const rows = doc.querySelectorAll(
                        '[role="grid"] [role="row"], table[role="grid"] tbody tr'
                    );
                    for (const row of rows) {
                        if (row.closest('thead')) continue;
                        const cells = row.querySelectorAll('td, [role="gridcell"]');
                        if (cells.length === 0) continue;
                        const cellValues = [];
                        for (const cell of cells) {
                            const input = cell.querySelector('input, select');
                            const val = input ? (input.value || '') : (cell.textContent || '').trim();
                            cellValues.push(val.substring(0, 100));
                        }
                        if (cellValues.some(v => v.length > 0)) {
                            result.push(cellValues);
                        }
                        if (result.length >= maxRows) break;
                    }
                    return result;
                }
                let all = readGrid(document);
                const frames = document.querySelectorAll('iframe');
                for (const frame of frames) {
                    try {
                        const r = readGrid(frame.contentDocument || frame.contentWindow.document);
                        all = all.concat(r);
                    } catch(e) {}
                }
                return all.slice(0, maxRows);
            }""", max_rows)
            return rows or []
        except Exception as e:
            logger.debug(f"[PageReader] get_grid_row_values failed: {e}")
            return []

    # ── PAGE CONTEXT ─────────────────────────────────────────────

    def get_page_context(self) -> dict:
        """Read D365 page context: title, form name, breadcrumb.

        Returns dict with: title, form_name, breadcrumb, has_unsaved_changes.
        """
        try:
            result = self.page.evaluate("""() => {
                // Page title
                const title = document.title || '';

                // D365 form name from data attribute
                const formEl = document.querySelector('[data-dyn-formname]');
                const formName = formEl ? formEl.getAttribute('data-dyn-formname') : '';

                // Breadcrumb / navigation path
                const breadcrumbs = [];
                document.querySelectorAll('.breadcrumb-item, [data-dyn-role="BreadCrumb"] span').forEach(el => {
                    const t = (el.textContent || '').trim();
                    if (t) breadcrumbs.push(t);
                });

                // Check for unsaved changes indicator
                const hasUnsaved = !!document.querySelector(
                    '[data-dyn-haschanges="true"], .modifiedIndicator'
                );

                // Active tab
                const activeTab = document.querySelector(
                    '[role="tab"][aria-selected="true"], .tab-active'
                );
                const activeTabName = activeTab ? (activeTab.textContent || '').trim() : '';

                return {
                    title: title.substring(0, 200),
                    form_name: formName,
                    breadcrumb: breadcrumbs.join(' > '),
                    has_unsaved: hasUnsaved,
                    active_tab: activeTabName,
                };
            }""")
            return result or {}
        except Exception as e:
            logger.debug(f"[PageReader] get_page_context failed: {e}")
            return {}

    # ── ERROR DETECTION ──────────────────────────────────────────

    def get_error_messages(self) -> list:
        """Read any D365 error/warning messages currently visible.

        Returns list of {type: 'error'|'warning'|'info', text: '...'}.
        """
        try:
            messages = self.page.evaluate("""() => {
                const msgs = [];
                // D365 message bars
                document.querySelectorAll('.messageBar-error, .messageBar-critical, .messageBar-warning, .messageBar-info').forEach(el => {
                    const text = (el.textContent || '').trim();
                    if (text) {
                        const type = el.className.includes('error') || el.className.includes('critical')
                            ? 'error' : el.className.includes('warning') ? 'warning' : 'info';
                        msgs.push({type, text: text.substring(0, 300)});
                    }
                });
                // Generic alerts
                document.querySelectorAll('[role="alert"]').forEach(el => {
                    const text = (el.textContent || '').trim();
                    if (text && !msgs.some(m => m.text === text)) {
                        msgs.push({type: 'alert', text: text.substring(0, 300)});
                    }
                });
                return msgs;
            }""")
            return messages or []
        except Exception as e:
            logger.debug(f"[PageReader] get_error_messages failed: {e}")
            return []

    # ── CONVENIENCE: FULL STATE SNAPSHOT ─────────────────────────

    def snapshot(self) -> dict:
        """Capture complete page state for debug UI.

        Returns a dict safe for JSON serialization.
        """
        return {
            "focused": self.get_focused_field(),
            "grid_rows": self.count_grid_rows(),
            "page": self.get_page_context(),
            "errors": self.get_error_messages(),
        }

    def snapshot_short(self) -> str:
        """One-line summary of current page state for logging."""
        f = self.get_focused_field()
        field_name = f.get("name") or f.get("label") or f.get("dyn_control") or f.get("tag", "?")
        field_val = f.get("value", "")
        if len(field_val) > 30:
            field_val = field_val[:30] + "..."
        grid = self.count_grid_rows()
        return f"focus={field_name}('{field_val}') grid_rows={grid}"
