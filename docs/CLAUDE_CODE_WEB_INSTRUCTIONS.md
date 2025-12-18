# 🚀 SPRINT 9 INSTRUCTIONS FOR CLAUDE CODE WEB

**Date:** December 6, 2024
**Task:** Complete all 6 incomplete apps with full UI implementation
**Branch:** claude/review-django-project-structure-015ULfqKNF5FbLdx8vnsd9fg

---

## 📋 READ THESE DOCUMENTS FIRST

**Before starting, read these 3 documents in order:**

1. **FINAL_TRIPLE_CHECKED_VERIFICATION.md** - Complete verification of all 6 apps
2. **SPRINT_9_COMPLETE_ALL_5_APPS.md** - Detailed requirements for each app (title says 5 but corrected to 6)
3. **VERIFIED_5_INCOMPLETE_APPS.md** - Additional verification details

All documents are in the `docs/` folder.

---

## 🎯 YOUR TASK

Build complete views, templates, and working URLs for **6 apps**:

1. apps/hr/ (16 models)
2. apps/forms_engine/ (5 models) - P1 CRITICAL
3. apps/scancodes/ (2 models)
4. apps/dispatch/ (4 models)
5. apps/hsse/ (3 models)
6. apps/organization/ (3 models)

**Total:** 33 models, ~60+ views, ~70+ templates

---

## 📊 PREVIOUS COMMITS (For Reference)

Your previous work on this project:

- **Commit adae5b8:** "feat: Add view tests and user guides (Day 5)"
- **Commit 6f939a4:** "feat: Implement role-based permissions and N+1 query optimization"
- **Commit 62ac929:** "fix: Remove incomplete apps from URL routing" (claimed, but URLs still active)

**Current State:**
- URLs are NOT commented out (still need fixing or completion)
- All 6 apps return 404 errors
- User wants complete implementation, not commenting out

---

## ✅ AFTER COMPLETION

1. Uncomment these 6 lines in `ardt_fms/urls.py`:
   ```python
   path('organization/', include('apps.organization.urls', namespace='organization')),  # Line 48
   path('forms/', include('apps.forms_engine.urls', namespace='forms_engine')),  # Line 60
   path('scan/', include('apps.scancodes.urls', namespace='scancodes')),  # Line 70
   path('dispatch/', include('apps.dispatch.urls', namespace='dispatch')),  # Line 83
   path('hr/', include('apps.hr.urls', namespace='hr')),  # Line 84
   path('hsse/', include('apps.hsse.urls', namespace='hsse')),  # Line 85
   ```

2. Run tests: `pytest`

3. Commit: "feat: Complete Sprint 9 - All 6 apps fully implemented"

---

## 🔑 KEY REQUIREMENTS

- Use existing patterns from apps/workorders/, apps/quality/, etc.
- Use Tailwind CSS, HTMX, Alpine.js (already in system)
- Implement role-based permissions (already have framework from commit 6f939a4)
- Write view tests for all new views
- Follow 8-day implementation plan in SPRINT_9_COMPLETE_ALL_5_APPS.md

---

## 📝 ESTIMATED TIME

**Day 1-2:** Forms Engine (P1 CRITICAL)
**Day 3-4:** HR Module
**Day 5:** Scancodes
**Day 6:** Organization
**Day 7:** Dispatch
**Day 8:** HSSE

**Total:** 7-8 days

---

**All detailed requirements are in SPRINT_9_COMPLETE_ALL_5_APPS.md**

**Start when ready!** 🚀
