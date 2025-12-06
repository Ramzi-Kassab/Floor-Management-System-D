# 🚀 SPRINT 9: COMPLETE ALL 6 INCOMPLETE APPS
## CRITICAL INSTRUCTION FOR CLAUDE CODE WEB

**Date:** December 6, 2024
**Priority:** HIGH
**Estimated Time:** 5-7 days
**Decision:** User wants ALL 6 apps completed, NOT commented out
**Update:** Corrected to 6 apps (organization was missing from original count)

---

## 📋 EXECUTIVE SUMMARY

**PREVIOUS ACTION (Commit 62ac929):**
- ⚠️ You CLAIMED to comment out apps from URLs
- ⚠️ BUT URLs are STILL ACTIVE in current file
- ⚠️ 6 apps (not 5) will return 404 errors

**NEW INSTRUCTION:**
- 🔴 **User wants these apps COMPLETED, not hidden**
- 🔴 **Build views, templates, and working URLs for all 6 apps**
- 🔴 **This is Sprint 9 - the true finale**
- 🔴 **See FINAL_TRIPLE_CHECKED_VERIFICATION.md for accurate details**

---

## 🎯 YOUR MISSION

**Build complete, working UI for these 6 apps:**

1. ✅ **apps/hr/** (16 models) - Employee management system
2. ✅ **apps/forms_engine/** (5 models) - Dynamic form builder (P1 CRITICAL)
3. ✅ **apps/scancodes/** (2 models) - Central QR/barcode registry
4. ✅ **apps/dispatch/** (4 models) - Fleet & dispatch management
5. ✅ **apps/hsse/** (3 models) - Safety & compliance
6. ✅ **apps/organization/** (3 models) - Department & position management

**Total:** 33 models need views, templates, and functional URLs

---

## 📊 DETAILED REQUIREMENTS - APP BY APP

### **1. apps/hr/ - HR & Workforce Management** (PRIORITY: HIGH)

**Status:** 16 models exist, 0 views exist
**Time Estimate:** 2-3 days
**Complexity:** HIGH (most models)

#### **Models to Implement (16 models):**
1. Employee (70+ fields - extended profile)
2. EmployeeDocument (document management)
3. EmergencyContact (emergency contacts)
4. BankAccount (payroll banking details)
5. PerformanceReview (performance evaluations)
6. Goal (objectives tracking)
7. SkillMatrix (competencies & skills)
8. DisciplinaryAction (disciplinary records)
9. ShiftSchedule (work schedules)
10. TimeEntry (time tracking)
11. LeaveRequest (leave management)
12. PayrollPeriod (payroll periods)
13. Attendance (attendance tracking)
14. AttendancePunch (clock in/out)
15. LeaveType (leave type definitions)
16. OvertimeRequest (overtime management)

#### **Required Views:**

**Employee Management:**
```python
# apps/hr/views.py

# Employee Views
- EmployeeListView (list all employees, with search/filter)
- EmployeeDetailView (employee profile page)
- EmployeeCreateView (add new employee)
- EmployeeUpdateView (edit employee)
- EmployeeDeleteView (archive employee)

# Performance Management
- PerformanceReviewListView (all reviews)
- PerformanceReviewCreateView (new review)
- PerformanceReviewDetailView (review details)
- GoalListView (objectives)
- GoalCreateView (create goal)

# Leave Management
- LeaveRequestListView (all leave requests)
- LeaveRequestCreateView (submit leave)
- LeaveRequestApproveView (approve/reject)
- LeaveBalanceView (leave balance dashboard)

# Attendance & Time
- AttendanceListView (attendance records)
- AttendancePunchView (clock in/out)
- TimeEntryListView (timesheet)
- TimeEntryCreateView (log time)

# Shift Scheduling
- ShiftScheduleListView (schedules)
- ShiftScheduleCreateView (create schedule)
- ShiftScheduleCalendarView (calendar view)

# Skills & Training
- SkillMatrixView (employee skills)
- SkillGapAnalysisView (skill gaps)
```

#### **Required Templates:**

```
apps/hr/templates/hr/
├── employee/
│   ├── employee_list.html (list view with search/filter/pagination)
│   ├── employee_detail.html (profile page)
│   ├── employee_form.html (create/edit form)
│   └── employee_confirm_delete.html
│
├── performance/
│   ├── review_list.html
│   ├── review_detail.html
│   ├── review_form.html
│   ├── goal_list.html
│   └── goal_form.html
│
├── leave/
│   ├── leave_request_list.html
│   ├── leave_request_form.html
│   ├── leave_approve.html
│   └── leave_balance.html
│
├── attendance/
│   ├── attendance_list.html
│   ├── attendance_punch.html
│   ├── timeentry_list.html
│   └── timeentry_form.html
│
├── schedule/
│   ├── shift_schedule_list.html
│   ├── shift_schedule_form.html
│   └── shift_calendar.html
│
└── skills/
    ├── skill_matrix.html
    └── skill_gap_analysis.html
```

#### **Required URLs:**

```python
# apps/hr/urls.py

app_name = "hr"

urlpatterns = [
    # Employee Management
    path('employees/', EmployeeListView.as_view(), name='employee-list'),
    path('employees/<int:pk>/', EmployeeDetailView.as_view(), name='employee-detail'),
    path('employees/create/', EmployeeCreateView.as_view(), name='employee-create'),
    path('employees/<int:pk>/edit/', EmployeeUpdateView.as_view(), name='employee-update'),
    path('employees/<int:pk>/delete/', EmployeeDeleteView.as_view(), name='employee-delete'),

    # Performance
    path('reviews/', PerformanceReviewListView.as_view(), name='review-list'),
    path('reviews/create/', PerformanceReviewCreateView.as_view(), name='review-create'),
    path('reviews/<int:pk>/', PerformanceReviewDetailView.as_view(), name='review-detail'),
    path('goals/', GoalListView.as_view(), name='goal-list'),
    path('goals/create/', GoalCreateView.as_view(), name='goal-create'),

    # Leave Management
    path('leave/', LeaveRequestListView.as_view(), name='leave-list'),
    path('leave/request/', LeaveRequestCreateView.as_view(), name='leave-request'),
    path('leave/<int:pk>/approve/', LeaveRequestApproveView.as_view(), name='leave-approve'),
    path('leave/balance/', LeaveBalanceView.as_view(), name='leave-balance'),

    # Attendance & Time
    path('attendance/', AttendanceListView.as_view(), name='attendance-list'),
    path('attendance/punch/', AttendancePunchView.as_view(), name='attendance-punch'),
    path('time/', TimeEntryListView.as_view(), name='time-list'),
    path('time/entry/', TimeEntryCreateView.as_view(), name='time-entry'),

    # Schedules
    path('schedules/', ShiftScheduleListView.as_view(), name='schedule-list'),
    path('schedules/create/', ShiftScheduleCreateView.as_view(), name='schedule-create'),
    path('schedules/calendar/', ShiftScheduleCalendarView.as_view(), name='schedule-calendar'),

    # Skills
    path('skills/', SkillMatrixView.as_view(), name='skill-matrix'),
    path('skills/gaps/', SkillGapAnalysisView.as_view(), name='skill-gaps'),
]
```

#### **Key Features to Implement:**

1. **Employee Profile Page** - Complete employee information dashboard
2. **Leave Request Workflow** - Submit → Manager Approval → HR Approval
3. **Performance Review Cycle** - Create review → Add goals → Submit → Archive
4. **Attendance Tracking** - Clock in/out with GPS location
5. **Shift Scheduling** - Calendar view, drag-and-drop scheduling
6. **Skills Matrix** - Visual skill assessment, gap analysis

#### **Integration Points:**

- Link employees to `apps.accounts.User` (already has FK)
- Link attendance to `apps.organization.Department`
- Show employee assignments in other apps (workorders, fieldservices)

---

### **2. apps/forms_engine/ - Dynamic Form Builder** (PRIORITY: CRITICAL - P1)

**Status:** 5 models exist, 0 views exist
**Time Estimate:** 1-2 days
**Complexity:** HIGH (form builder UI is complex)
**CRITICAL:** Already integrated with `apps.procedures` - this is P1 core feature!

#### **Models to Implement (5 models):**
1. FormTemplate (form definitions)
2. FormSection (form sections)
3. FieldType (field type definitions - CharField, IntegerField, etc.)
4. FormField (individual fields)
5. FormTemplateVersion (versioning system)

#### **Required Views:**

```python
# apps/forms_engine/views.py

# Form Template Management
- FormTemplateListView (list all form templates)
- FormTemplateDetailView (view form template)
- FormTemplateCreateView (create new template)
- FormTemplateUpdateView (edit template)
- FormTemplateDeleteView (archive template)
- FormTemplateBuilderView (drag-and-drop builder UI) ⭐ CRITICAL

# Form Section Management
- FormSectionCreateView (add section to form)
- FormSectionUpdateView (edit section)
- FormSectionDeleteView (remove section)

# Form Field Management
- FormFieldCreateView (add field to section)
- FormFieldUpdateView (edit field)
- FormFieldDeleteView (remove field)

# Form Rendering
- FormRenderView (render form for filling out)
- FormSubmitView (handle form submission)
- FormResponseListView (view submitted forms)
- FormResponseDetailView (view form response)
```

#### **Required Templates:**

```
apps/forms_engine/templates/forms_engine/
├── template/
│   ├── template_list.html (list all templates)
│   ├── template_detail.html (view template structure)
│   ├── template_form.html (create/edit template)
│   ├── template_builder.html ⭐ (drag-and-drop form builder)
│   └── template_confirm_delete.html
│
├── section/
│   ├── section_form.html (add/edit section)
│   └── section_inline.html (inline section editor)
│
├── field/
│   ├── field_form.html (add/edit field)
│   ├── field_inline.html (inline field editor)
│   └── field_preview.html (preview field rendering)
│
└── render/
    ├── form_render.html (render form for user)
    ├── form_response_list.html (submitted forms)
    └── form_response_detail.html (view response)
```

#### **Required URLs:**

```python
# apps/forms_engine/urls.py

app_name = "forms_engine"

urlpatterns = [
    # Template Management
    path('', FormTemplateListView.as_view(), name='template-list'),
    path('<int:pk>/', FormTemplateDetailView.as_view(), name='template-detail'),
    path('create/', FormTemplateCreateView.as_view(), name='template-create'),
    path('<int:pk>/edit/', FormTemplateUpdateView.as_view(), name='template-update'),
    path('<int:pk>/delete/', FormTemplateDeleteView.as_view(), name='template-delete'),
    path('<int:pk>/builder/', FormTemplateBuilderView.as_view(), name='template-builder'),

    # Section Management
    path('<int:template_pk>/section/create/', FormSectionCreateView.as_view(), name='section-create'),
    path('section/<int:pk>/edit/', FormSectionUpdateView.as_view(), name='section-update'),
    path('section/<int:pk>/delete/', FormSectionDeleteView.as_view(), name='section-delete'),

    # Field Management
    path('section/<int:section_pk>/field/create/', FormFieldCreateView.as_view(), name='field-create'),
    path('field/<int:pk>/edit/', FormFieldUpdateView.as_view(), name='field-update'),
    path('field/<int:pk>/delete/', FormFieldDeleteView.as_view(), name='field-delete'),

    # Form Rendering
    path('<int:pk>/render/', FormRenderView.as_view(), name='form-render'),
    path('<int:pk>/submit/', FormSubmitView.as_view(), name='form-submit'),
    path('<int:pk>/responses/', FormResponseListView.as_view(), name='response-list'),
    path('response/<int:pk>/', FormResponseDetailView.as_view(), name='response-detail'),
]
```

#### **Key Features to Implement:**

1. **Form Builder UI** ⭐ MOST IMPORTANT
   - Drag-and-drop interface (use Alpine.js or HTMX)
   - Add sections, add fields
   - Reorder sections/fields
   - Field type selector (text, number, date, dropdown, checkbox, etc.)
   - Field validation settings
   - Save and preview

2. **Form Rendering Engine**
   - Render FormTemplate dynamically based on structure
   - Handle all field types
   - Client-side validation
   - Submit to database

3. **Integration with Procedures**
   - Show "Attach Form" option in procedure step editor
   - Render attached forms in procedure execution
   - Save form responses with procedure execution data

#### **Integration Points:**

- ✅ Already integrated with `apps.procedures.ProcedureStep` (FK exists)
- Show forms in procedure execution workflow
- Link form responses to procedure executions

---

### **3. apps/scancodes/ - Central QR/Barcode Registry** (PRIORITY: MEDIUM)

**Status:** 2 models exist, 0 views exist
**Time Estimate:** 1 day
**Complexity:** MEDIUM
**Note:** QR codes already work in workorders, this adds central registry

#### **Models to Implement (2 models):**
1. ScanCode (QR/barcode registry)
2. ScanLog (scan history tracking)

#### **Required Views:**

```python
# apps/scancodes/views.py

# ScanCode Management
- ScanCodeListView (list all registered codes)
- ScanCodeDetailView (code details & history)
- ScanCodeCreateView (register new code)
- ScanCodeUpdateView (edit code)
- ScanCodeDeleteView (archive code)

# Scanning Interface
- ScanView (mobile scanning interface)
- ScanLogListView (scan history)
- ScanLogDetailView (scan details)

# Reporting
- ScanReportView (scan analytics)
- ScanActivityView (recent scans dashboard)
```

#### **Required Templates:**

```
apps/scancodes/templates/scancodes/
├── scancode/
│   ├── scancode_list.html (all registered codes)
│   ├── scancode_detail.html (code details + scan history)
│   ├── scancode_form.html (create/edit code)
│   └── scancode_confirm_delete.html
│
├── scan/
│   ├── scan_interface.html (mobile scan UI - camera)
│   ├── scan_success.html (scan recorded)
│   └── scan_log_list.html (scan history)
│
└── reports/
    ├── scan_report.html (analytics)
    └── scan_activity.html (dashboard)
```

#### **Required URLs:**

```python
# apps/scancodes/urls.py

app_name = "scancodes"

urlpatterns = [
    # ScanCode Management
    path('', ScanCodeListView.as_view(), name='scancode-list'),
    path('<int:pk>/', ScanCodeDetailView.as_view(), name='scancode-detail'),
    path('create/', ScanCodeCreateView.as_view(), name='scancode-create'),
    path('<int:pk>/edit/', ScanCodeUpdateView.as_view(), name='scancode-update'),
    path('<int:pk>/delete/', ScanCodeDeleteView.as_view(), name='scancode-delete'),

    # Scanning
    path('scan/', ScanView.as_view(), name='scan'),
    path('scan/log/', ScanLogListView.as_view(), name='scan-log-list'),
    path('scan/log/<int:pk>/', ScanLogDetailView.as_view(), name='scan-log-detail'),

    # Reports
    path('reports/', ScanReportView.as_view(), name='scan-report'),
    path('activity/', ScanActivityView.as_view(), name='scan-activity'),
]
```

#### **Key Features to Implement:**

1. **Mobile Scan Interface**
   - Camera access for QR scanning
   - Manual code entry option
   - GPS location capture
   - Offline capability (save scans locally, sync later)

2. **Central Registry**
   - Register all QR codes (ARDT-generated, supplier, ARAMCO, external)
   - Track what each code represents
   - Link to assets (drill bits, equipment, inventory)

3. **Scan Logging**
   - Who scanned, when, where (GPS)
   - What action was performed
   - History timeline

#### **Integration Points:**

- Integrate with `apps.workorders.DrillBit` (QR codes already exist there)
- Link to inventory items
- Link to equipment tracking

---

### **4. apps/dispatch/ - Fleet & Dispatch Management** (PRIORITY: LOW - P3)

**Status:** 4 models exist, 0 views exist
**Time Estimate:** 1-2 days
**Complexity:** MEDIUM
**Note:** This is P3 (Phase 3) - future feature

#### **Models to Implement (4 models):**
1. Vehicle (fleet vehicles)
2. Dispatch (dispatch requests/deliveries)
3. DispatchItem (items being dispatched)
4. InventoryReservation (inventory reservations for dispatch)

#### **Required Views:**

```python
# apps/dispatch/views.py

# Vehicle Management
- VehicleListView (fleet list)
- VehicleDetailView (vehicle details)
- VehicleCreateView (add vehicle)
- VehicleUpdateView (edit vehicle)
- VehicleDeleteView (archive vehicle)

# Dispatch Management
- DispatchListView (all dispatches)
- DispatchDetailView (dispatch details)
- DispatchCreateView (create dispatch)
- DispatchUpdateView (edit dispatch)
- DispatchDeleteView (cancel dispatch)
- DispatchAssignView (assign to vehicle)

# Dispatch Items
- DispatchItemCreateView (add items to dispatch)
- DispatchItemUpdateView (edit dispatch item)

# Reporting
- DispatchDashboardView (dispatch dashboard)
- DispatchMapView (map view of active dispatches)
```

#### **Required Templates:**

```
apps/dispatch/templates/dispatch/
├── vehicle/
│   ├── vehicle_list.html
│   ├── vehicle_detail.html
│   ├── vehicle_form.html
│   └── vehicle_confirm_delete.html
│
├── dispatch/
│   ├── dispatch_list.html
│   ├── dispatch_detail.html
│   ├── dispatch_form.html
│   ├── dispatch_assign.html
│   └── dispatch_confirm_delete.html
│
├── item/
│   ├── item_form.html
│   └── item_inline.html
│
└── dashboard/
    ├── dispatch_dashboard.html
    └── dispatch_map.html
```

#### **Required URLs:**

```python
# apps/dispatch/urls.py

app_name = "dispatch"

urlpatterns = [
    # Vehicles
    path('vehicles/', VehicleListView.as_view(), name='vehicle-list'),
    path('vehicles/<int:pk>/', VehicleDetailView.as_view(), name='vehicle-detail'),
    path('vehicles/create/', VehicleCreateView.as_view(), name='vehicle-create'),
    path('vehicles/<int:pk>/edit/', VehicleUpdateView.as_view(), name='vehicle-update'),
    path('vehicles/<int:pk>/delete/', VehicleDeleteView.as_view(), name='vehicle-delete'),

    # Dispatches
    path('', DispatchListView.as_view(), name='dispatch-list'),
    path('<int:pk>/', DispatchDetailView.as_view(), name='dispatch-detail'),
    path('create/', DispatchCreateView.as_view(), name='dispatch-create'),
    path('<int:pk>/edit/', DispatchUpdateView.as_view(), name='dispatch-update'),
    path('<int:pk>/delete/', DispatchDeleteView.as_view(), name='dispatch-delete'),
    path('<int:pk>/assign/', DispatchAssignView.as_view(), name='dispatch-assign'),

    # Items
    path('<int:dispatch_pk>/item/create/', DispatchItemCreateView.as_view(), name='item-create'),
    path('item/<int:pk>/edit/', DispatchItemUpdateView.as_view(), name='item-update'),

    # Dashboard
    path('dashboard/', DispatchDashboardView.as_view(), name='dashboard'),
    path('map/', DispatchMapView.as_view(), name='map'),
]
```

---

### **5. apps/hsse/ - Health, Safety, Security, Environment** (PRIORITY: LOW - P4)

**Status:** 3 models exist, 0 views exist
**Time Estimate:** 1 day
**Complexity:** LOW
**Note:** This is P4 (Phase 4) - lowest priority

#### **Models to Implement (3 models):**
1. HOCReport (Hazard Observation Cards)
2. Incident (safety incidents)
3. Journey (journey management)

#### **Required Views:**

```python
# apps/hsse/views.py

# HOC Reports
- HOCReportListView (all hazard observations)
- HOCReportDetailView (HOC details)
- HOCReportCreateView (submit HOC)
- HOCReportUpdateView (edit HOC)
- HOCReportDeleteView (archive HOC)

# Incidents
- IncidentListView (all incidents)
- IncidentDetailView (incident details)
- IncidentCreateView (report incident)
- IncidentUpdateView (edit incident)
- IncidentDeleteView (archive incident)

# Journey Management
- JourneyListView (all journeys)
- JourneyDetailView (journey details)
- JourneyCreateView (plan journey)
- JourneyUpdateView (edit journey)
- JourneyDeleteView (cancel journey)

# Dashboards
- HSSEDashboardView (safety dashboard)
- IncidentAnalyticsView (incident analytics)
```

#### **Required Templates:**

```
apps/hsse/templates/hsse/
├── hoc/
│   ├── hoc_list.html
│   ├── hoc_detail.html
│   ├── hoc_form.html
│   └── hoc_confirm_delete.html
│
├── incident/
│   ├── incident_list.html
│   ├── incident_detail.html
│   ├── incident_form.html
│   └── incident_confirm_delete.html
│
├── journey/
│   ├── journey_list.html
│   ├── journey_detail.html
│   ├── journey_form.html
│   └── journey_confirm_delete.html
│
└── dashboard/
    ├── hsse_dashboard.html
    └── incident_analytics.html
```

#### **Required URLs:**

```python
# apps/hsse/urls.py

app_name = "hsse"

urlpatterns = [
    # HOC Reports
    path('hoc/', HOCReportListView.as_view(), name='hoc-list'),
    path('hoc/<int:pk>/', HOCReportDetailView.as_view(), name='hoc-detail'),
    path('hoc/create/', HOCReportCreateView.as_view(), name='hoc-create'),
    path('hoc/<int:pk>/edit/', HOCReportUpdateView.as_view(), name='hoc-update'),
    path('hoc/<int:pk>/delete/', HOCReportDeleteView.as_view(), name='hoc-delete'),

    # Incidents
    path('incident/', IncidentListView.as_view(), name='incident-list'),
    path('incident/<int:pk>/', IncidentDetailView.as_view(), name='incident-detail'),
    path('incident/create/', IncidentCreateView.as_view(), name='incident-create'),
    path('incident/<int:pk>/edit/', IncidentUpdateView.as_view(), name='incident-update'),
    path('incident/<int:pk>/delete/', IncidentDeleteView.as_view(), name='incident-delete'),

    # Journeys
    path('journey/', JourneyListView.as_view(), name='journey-list'),
    path('journey/<int:pk>/', JourneyDetailView.as_view(), name='journey-detail'),
    path('journey/create/', JourneyCreateView.as_view(), name='journey-create'),
    path('journey/<int:pk>/edit/', JourneyUpdateView.as_view(), name='journey-update'),
    path('journey/<int:pk>/delete/', JourneyDeleteView.as_view(), name='journey-delete'),

    # Dashboard
    path('', HSSEDashboardView.as_view(), name='dashboard'),
    path('analytics/', IncidentAnalyticsView.as_view(), name='analytics'),
]
```

---

### **6. apps/organization/ - Department & Position Management** (PRIORITY: LOW)

**Status:** 3 models exist, 0 views exist
**Time Estimate:** 1 day
**Complexity:** LOW
**Note:** Reference data, admin-only may be sufficient, but in URLs so needs UI

#### **Models to Implement (3 models):**
1. Department (organizational departments)
2. Position (job positions/titles)
3. Theme (UI theme preferences - for users)

#### **Required Views:**

```python
# apps/organization/views.py

# Department Management
- DepartmentListView (all departments)
- DepartmentDetailView (department details)
- DepartmentCreateView (create department)
- DepartmentUpdateView (edit department)
- DepartmentDeleteView (archive department)

# Position Management
- PositionListView (all positions)
- PositionDetailView (position details)
- PositionCreateView (create position)
- PositionUpdateView (edit position)
- PositionDeleteView (archive position)

# Theme Management (User Preferences)
- ThemeListView (available themes)
- ThemeSelectView (user selects theme)
```

#### **Required Templates:**

```
apps/organization/templates/organization/
├── department/
│   ├── department_list.html
│   ├── department_detail.html
│   ├── department_form.html
│   └── department_confirm_delete.html
│
├── position/
│   ├── position_list.html
│   ├── position_detail.html
│   ├── position_form.html
│   └── position_confirm_delete.html
│
└── theme/
    ├── theme_list.html
    └── theme_select.html
```

#### **Required URLs:**

```python
# apps/organization/urls.py

app_name = "organization"

urlpatterns = [
    # Departments
    path('departments/', DepartmentListView.as_view(), name='department-list'),
    path('departments/<int:pk>/', DepartmentDetailView.as_view(), name='department-detail'),
    path('departments/create/', DepartmentCreateView.as_view(), name='department-create'),
    path('departments/<int:pk>/edit/', DepartmentUpdateView.as_view(), name='department-update'),
    path('departments/<int:pk>/delete/', DepartmentDeleteView.as_view(), name='department-delete'),

    # Positions
    path('positions/', PositionListView.as_view(), name='position-list'),
    path('positions/<int:pk>/', PositionDetailView.as_view(), name='position-detail'),
    path('positions/create/', PositionCreateView.as_view(), name='position-create'),
    path('positions/<int:pk>/edit/', PositionUpdateView.as_view(), name='position-update'),
    path('positions/<int:pk>/delete/', PositionDeleteView.as_view(), name='position-delete'),

    # Themes
    path('themes/', ThemeListView.as_view(), name='theme-list'),
    path('themes/select/', ThemeSelectView.as_view(), name='theme-select'),
]
```

#### **Key Features:**

1. **Department Management** - Organizational hierarchy
2. **Position Management** - Job titles and roles
3. **Theme Selection** - User can choose UI theme

#### **Integration Points:**

- ✅ Already used by `apps.accounts.User` (has FK to Department, Position, Theme)
- Show department employees count
- Show position assignments
- Apply selected theme to user's UI

---

## 🎨 DESIGN & UI REQUIREMENTS

### **Use Existing System Patterns:**

All templates should follow the existing ARDT FMS design:

1. **Use the same base template:**
   ```html
   {% extends "base.html" %}
   ```

2. **Use existing CSS/JS stack:**
   - Tailwind CSS (already in system)
   - HTMX (already in system)
   - Alpine.js (already in system)
   - Lucide Icons (already in system)

3. **Follow existing patterns:**
   - Look at `apps/workorders/templates/` for reference
   - Use same list/detail/form patterns
   - Use same navigation structure
   - Match existing color scheme and layout

4. **Responsive Design:**
   - Mobile-first (especially for scanning, attendance punch)
   - Desktop dashboard views
   - Tablet-friendly forms

---

## 🔐 PERMISSIONS & SECURITY

### **Implement Role-Based Access:**

You already implemented permissions (commit 6f939a4). Use them:

```python
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

# Example:
class EmployeeListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    permission_required = 'hr.view_employee'
    model = Employee
```

### **Permission Requirements:**

- **HR:** Only managers and HR staff
- **Forms Engine:** All authenticated users (form builders: admins only)
- **Scancodes:** Field technicians and warehouse staff
- **Dispatch:** Logistics coordinators and drivers
- **HSSE:** All employees (for reporting), safety officers (for management)

---

## ✅ TESTING REQUIREMENTS

### **For Each App, Create:**

1. **Model Tests** (already exist ✅)
2. **View Tests** ⭐ CRITICAL (create these)
3. **Form Tests** (create these)
4. **Integration Tests** (optional but recommended)

### **View Test Example:**

```python
# apps/hr/tests/test_views.py

import pytest
from django.urls import reverse

@pytest.mark.django_db
class TestEmployeeViews:

    def test_employee_list_requires_login(self, client):
        response = client.get(reverse('hr:employee-list'))
        assert response.status_code == 302  # Redirect to login

    def test_employee_list_accessible_by_authenticated_user(self, client, auth_user):
        client.force_login(auth_user)
        response = client.get(reverse('hr:employee-list'))
        assert response.status_code == 200
        assert 'employee' in response.context

    def test_employee_create_view(self, client, auth_user):
        client.force_login(auth_user)
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'employee_id': 'EMP001',
            'department': 1,
        }
        response = client.post(reverse('hr:employee-create'), data)
        assert response.status_code == 302  # Redirect on success
        assert Employee.objects.filter(employee_id='EMP001').exists()
```

---

## 📝 AFTER COMPLETION CHECKLIST

### **For Each App:**

- [ ] All models have views (list, detail, create, update, delete)
- [ ] All views have templates (functional, not beautiful initially)
- [ ] All URLs work (no 404 errors)
- [ ] Forms validate correctly
- [ ] Permissions applied
- [ ] View tests written and passing
- [ ] Integration with existing apps working
- [ ] Documentation updated

### **Final Steps:**

1. ✅ Uncomment 6 URLs in `ardt_fms/urls.py` (lines 48, 60, 70, 83-85)
2. ✅ Run full test suite (`pytest`)
3. ✅ Manual testing of all features
4. ✅ Update docs/README.md to show "All apps complete"
5. ✅ Commit with message: "feat: Complete Sprint 9 - All 6 apps fully implemented"

---

## 🚀 IMPLEMENTATION STRATEGY

### **Recommended Order:**

**Day 1-2: Forms Engine** (P1 CRITICAL)
- This is already integrated, highest priority
- Build form builder UI
- Test with procedures integration

**Day 3-4: HR Module** (Sprint 8 finale)
- Most models, most complexity
- Employee management first
- Leave and attendance next
- Performance reviews last

**Day 5: Scancodes** (P1, simpler)
- Mobile scanning interface
- Central registry
- Quick wins

**Day 6: Dispatch** (P3, future)
- Vehicle management
- Dispatch assignment
- Lower priority, simpler

**Day 6: Organization** (Reference data)
- Department management
- Position management
- Theme selection
- Quick, simple

**Day 7: Dispatch** (P3, future)
- Vehicle management
- Dispatch assignment
- Lower priority

**Day 8: HSSE** (P4, future)
- Incident reporting
- HOC cards
- Lowest priority

---

## 💬 FINAL NOTES

### **Quality Over Speed:**

- Take time to do this right
- Follow existing patterns
- Don't rush - 7-8 days is realistic
- Ask if you need clarification

### **What Success Looks Like:**

**After Sprint 9:**
- ✅ All 21 apps fully functional
- ✅ 173 models with complete UI
- ✅ Zero 404 errors
- ✅ Professional, cohesive system
- ✅ Ready for production
- ✅ TRUE "100% complete"

### **Reference Documents:**

- Read: `docs/VERIFIED_5_INCOMPLETE_APPS.md` (accurate verification)
- Read: `docs/SKELETON_APPS_ROOT_CAUSE_ANALYSIS.md` (root cause analysis)
- Read: Existing app code in `apps/workorders/`, `apps/quality/`, etc.

---

## 🎯 YOUR TASK - CRYSTAL CLEAR

**Build views, templates, and working URLs for:**
1. apps/hr/ (16 models)
2. apps/forms_engine/ (5 models)
3. apps/scancodes/ (2 models)
4. apps/dispatch/ (4 models)
5. apps/hsse/ (3 models)
6. apps/organization/ (3 models)

**Then uncomment these 6 lines in ardt_fms/urls.py:**
```python
# Line 48:
path('organization/', include('apps.organization.urls', namespace='organization')),

# Line 60:
path('forms/', include('apps.forms_engine.urls', namespace='forms_engine')),

# Line 70:
path('scan/', include('apps.scancodes.urls', namespace='scancodes')),

# Lines 83-85:
path('dispatch/', include('apps.dispatch.urls', namespace='dispatch')),
path('hr/', include('apps.hr.urls', namespace='hr')),
path('hsse/', include('apps.hsse.urls', namespace='hsse')),
```

**Test everything works. No 404 errors. Complete system.**

---

## 🎊 LET'S FINISH THIS!

**You already completed Sprints 1-7 brilliantly.**
**You fixed permissions, N+1 queries, and view tests.**
**Now complete Sprint 9 - the TRUE finale.**

**Make all 6 apps fully functional.**
**This is the final push to 100% complete!**

🚀 **Ready when you are!**

---

**END OF SPRINT 9 INSTRUCTIONS**
