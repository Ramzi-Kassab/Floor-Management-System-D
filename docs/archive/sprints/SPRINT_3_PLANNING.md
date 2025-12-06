# 🚀 SPRINT 3 PLANNING - Quality & Technology

**Project:** ARDT FMS v5.4  
**Sprint:** 3 of 4  
**Duration:** 6 days (48 hours)  
**Status:** Planning Phase  
**Prerequisites:** Sprint 1 ✅, Sprint 2 ✅

---

## 📊 SPRINT OVERVIEW

### Theme: "Quality Assurance & Technical Excellence"

Sprint 3 focuses on quality management and technology infrastructure:
- NCR (Non-Conformance Report) system
- Inspection tracking and management
- Design and BOM management
- Cutter layout tracking
- Procedure execution system
- Notification and task management

---

## 🎯 SPRINT GOALS

### Primary Deliverables

1. **Quality Management (quality app)**
   - Inspection creation and tracking
   - NCR (Non-Conformance Report) system
   - NCR photos and documentation
   - Quality dashboard and reporting
   - Approval workflows

2. **Technology Module (technology app)**
   - Design management
   - Bill of Materials (BOM)
   - BOM line items
   - Cutter layout tracking
   - Design versioning

3. **Procedure Integration (procedures + execution apps)**
   - Procedure creation and management
   - Step definitions with types
   - Checkpoint definitions
   - Branching logic
   - Procedure execution tracking
   - Step completion tracking

4. **Notification System (notifications app)**
   - Real-time notifications
   - Task management
   - Comment system
   - Audit trail
   - Email notifications

5. **Enhanced Features**
   - QC dashboard enhancements
   - Manager approval workflows
   - Document approval routing
   - Activity tracking

---

## 📦 SPRINT 3 SCOPE

### Apps to Implement

**Primary Apps (Full Implementation):**

1. **quality** (Inspection, NCR, NCRPhoto)
2. **technology** (Design, BOM, BOMLine, DesignCutterLayout)
3. **procedures** (Procedure, ProcedureStep, StepType, etc.)
4. **execution** (ProcedureExecution, StepExecution, etc.)
5. **notifications** (Notification, Task, AuditLog, Comment)

**Enhanced Apps:**
- **workorders** - Link to inspections and procedures
- **dashboard** - Add quality and technology metrics

---

## 📅 DAY-BY-DAY BREAKDOWN

### Day 1: Quality Foundation - Inspections (8 hours)

**Morning: Inspection System (4 hours)**

**Tasks:**
- Review Inspection model
- Create InspectionForm with validation
- InspectionListView with filters (type, status, date range)
- InspectionDetailView with photos and results
- InspectionCreateView with photo upload
- InspectionUpdateView
- Inspection templates (list, detail, form)

**Key Features:**
- Inspection types (incoming, in-process, final, audit)
- Status workflow (scheduled, in-progress, completed, failed)
- Pass/fail criteria
- Inspector assignment
- Photo documentation
- Inspection results recording

**Afternoon: Inspection Integration (4 hours)**

**Tasks:**
- Link inspections to work orders
- Add inspection tab to work order detail
- Create inspection from work order
- QC dashboard updates
- Inspection calendar view
- Inspection reporting

---

### Day 2: NCR System (8 hours)

**Morning: NCR Foundation (4 hours)**

**Tasks:**
- Review NCR model
- NCRForm with validation
- NCR status workflow (open, in-progress, closed)
- NCR severity levels (minor, major, critical)
- NCRListView with advanced filters
- NCRDetailView with tabs (Details, Investigation, Actions, Photos)
- NCRCreateView with auto-numbering

**Key Features:**
```python
class NCRCreateView(LoginRequiredMixin, QCRequiredMixin, CreateView):
    model = NCR
    fields = [
        'work_order', 'inspection', 'ncr_type',
        'severity', 'description', 'root_cause',
        'corrective_action', 'preventive_action'
    ]
    
    def form_valid(self, form):
        form.instance.reported_by = self.request.user
        form.instance.ncr_number = self.generate_ncr_number()
        form.instance.status = 'OPEN'
        # Send notification to manager
        return super().form_valid(form)
    
    def generate_ncr_number(self):
        prefix = 'NCR'
        last_ncr = NCR.objects.order_by('-id').first()
        next_number = (last_ncr.id + 1) if last_ncr else 1
        return f"{prefix}-{timezone.now().year}-{str(next_number).zfill(4)}"
```

**Afternoon: NCR Workflow (4 hours)**

**Tasks:**
- NCR investigation tracking
- NCR closure workflow
- NCR approval system
- Manager review and approval
- NCR photos management (with HTMX)
- NCR reporting and analytics

---

### Day 3: Technology - Design Management (8 hours)

**Morning: Design System (4 hours)**

**Tasks:**
- Review Design model
- DesignForm with specifications
- DesignListView with search and filters
- DesignDetailView with tabs (Overview, BOM, Cutter Layout, History)
- DesignCreateView with code generation
- DesignUpdateView with versioning

**Key Features:**
```python
class DesignDetailView(LoginRequiredMixin, DetailView):
    model = Design
    template_name = 'technology/design_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        design = self.object
        
        context['bom_items'] = design.bom_items.select_related(
            'inventory_item'
        ).order_by('sequence')
        
        context['cutter_layouts'] = design.cutter_layouts.all()
        
        context['work_orders'] = design.workorder_set.select_related(
            'customer', 'drill_bit'
        ).order_by('-created_at')[:10]
        
        context['total_usage'] = design.workorder_set.count()
        
        return context
```

**Afternoon: BOM Management (4 hours)**

**Tasks:**
- BOM model review
- BOMForm and BOMLineForm
- Inline formsets for BOM lines
- BOM creation wizard
- BOM import from CSV
- BOM export to PDF
- Material cost calculation
- BOM versioning

---

### Day 4: Technology - Cutter Layouts & Procedures (8 hours)

**Morning: Cutter Layout System (2 hours)**

**Tasks:**
- DesignCutterLayoutForm
- Cutter position management
- Visual cutter layout display
- Cutter layout templates
- PDF export for manufacturing

**Morning: Procedure Foundation (2 hours)**

**Tasks:**
- Review Procedure model
- ProcedureForm with steps
- ProcedureListView with categories
- ProcedureDetailView with step visualization
- ProcedureCreateView with step wizard

**Afternoon: Procedure Steps (4 hours)**

**Tasks:**
- Step type management (10 types from fixtures)
- ProcedureStepForm with type-specific fields
- Step sequence management
- Checkpoint definition
- Branch logic (conditional steps)
- Input/output definitions
- Step templates and reusability

**Key Features:**
```python
class ProcedureStepInline(admin.TabularInline):
    model = ProcedureStep
    extra = 1
    fields = [
        'sequence', 'step_type', 'title',
        'description', 'duration_minutes',
        'is_required', 'requires_approval'
    ]

# Step types from fixtures:
# - Manual Task
# - Quality Check
# - Equipment Operation
# - Material Issue
# - Documentation
# - Measurement
# - Assembly
# - Inspection
# - Approval
# - Notification
```

---

### Day 5: Procedure Execution & Notifications (8 hours)

**Morning: Procedure Execution (4 hours)**

**Tasks:**
- ProcedureExecution model integration
- Start procedure from work order
- StepExecution tracking
- Checkpoint result recording
- Branch evaluation logic
- Form submission (dynamic forms)
- Execution progress tracking
- Execution completion

**Key Features:**
```python
class ProcedureExecutionView(LoginRequiredMixin, DetailView):
    model = ProcedureExecution
    template_name = 'execution/execution_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        execution = self.object
        
        # Get current step
        context['current_step'] = execution.step_executions.filter(
            status='IN_PROGRESS'
        ).first()
        
        # Get all steps with status
        context['steps'] = execution.step_executions.select_related(
            'step'
        ).order_by('step__sequence')
        
        # Calculate progress
        total_steps = execution.step_executions.count()
        completed_steps = execution.step_executions.filter(
            status='COMPLETED'
        ).count()
        context['progress'] = int((completed_steps / total_steps) * 100) if total_steps > 0 else 0
        
        return context
```

**Afternoon: Notification System (4 hours)**

**Tasks:**
- Notification model setup
- NotificationTemplate system
- Real-time notification display
- Notification preferences
- Email notification sending
- Task creation and assignment
- Comment system (with attachments)
- AuditLog automatic tracking

**Key Features:**
```python
# Notification creation
def create_notification(user, notification_type, title, message, link=None):
    notification = Notification.objects.create(
        user=user,
        type=notification_type,
        title=title,
        message=message,
        link=link
    )
    
    # Send email if user prefers
    if user.notification_preferences.email_enabled:
        send_notification_email(notification)
    
    # Log to audit
    AuditLog.objects.create(
        user=user,
        action='NOTIFICATION_CREATED',
        model_name='Notification',
        object_id=notification.id
    )
    
    return notification

# Usage
create_notification(
    user=work_order.assigned_to,
    notification_type='WORK_ORDER_ASSIGNED',
    title='New Work Order Assigned',
    message=f'Work order {work_order.wo_number} has been assigned to you.',
    link=work_order.get_absolute_url()
)
```

---

### Day 6: Integration, Testing & Polish (8 hours)

**Morning: Cross-App Integration (4 hours)**

**Tasks:**
- Link inspections to work orders
- Link NCRs to work orders and inspections
- Link designs to drill bits and work orders
- Link procedures to work orders
- Update work order detail with all tabs
- Add procedure tab to work order
- Add quality tab to work order
- Add design/BOM tab to drill bit

**Enhanced Work Order Detail:**
```html
<!-- workorder_detail.html - Enhanced tabs -->
<div class="border-b border-gray-200">
    <nav class="-mb-px flex space-x-8">
        <a href="#overview" class="...">Overview</a>
        <a href="#procedure" class="...">Procedure</a>  <!-- NEW -->
        <a href="#materials" class="...">Materials</a>
        <a href="#quality" class="...">Quality</a>     <!-- NEW -->
        <a href="#time" class="...">Time Logs</a>
        <a href="#documents" class="...">Documents</a>
        <a href="#photos" class="...">Photos</a>
        <a href="#history" class="...">History</a>
    </nav>
</div>

<!-- Quality tab content -->
<div id="quality" class="tab-content">
    <div class="grid grid-cols-2 gap-6">
        <div>
            <h3 class="font-semibold mb-4">Inspections</h3>
            {% for inspection in work_order.inspections.all %}
                {% include 'quality/inspection_card.html' %}
            {% endfor %}
        </div>
        <div>
            <h3 class="font-semibold mb-4">NCRs</h3>
            {% for ncr in work_order.ncrs.all %}
                {% include 'quality/ncr_card.html' %}
            {% endfor %}
        </div>
    </div>
</div>

<!-- Procedure tab content -->
<div id="procedure" class="tab-content">
    {% if work_order.procedure_execution %}
        {% include 'execution/execution_progress.html' %}
    {% else %}
        <button onclick="startProcedure({{ work_order.id }})">
            Start Procedure
        </button>
    {% endif %}
</div>
```

**Afternoon: Testing, Reporting & Polish (4 hours)**

**Tasks:**
- Test all quality workflows
- Test procedure execution
- Test notifications
- Test audit logging
- Create quality reports:
  - NCR summary report
  - Inspection pass/fail rates
  - Quality trends over time
  - NCR by severity
- Create technology reports:
  - Design usage report
  - BOM cost analysis
  - Popular designs
- Performance optimization
- Bug fixes
- Documentation updates

---

## 📋 DETAILED CHECKLIST

### Quality Module ✓

- [ ] Inspection CRUD operations
- [ ] Inspection types and statuses
- [ ] Inspection photo upload
- [ ] NCR creation and tracking
- [ ] NCR severity levels
- [ ] NCR workflow (open → closed)
- [ ] NCR photo management
- [ ] NCR approval system
- [ ] Quality dashboard
- [ ] Quality reports
- [ ] Link inspections to work orders
- [ ] Link NCRs to inspections
- [ ] QC role permissions

### Technology Module ✓

- [ ] Design CRUD operations
- [ ] Design search and filters
- [ ] BOM creation and management
- [ ] BOM line items (inline forms)
- [ ] BOM cost calculation
- [ ] Cutter layout management
- [ ] Cutter layout visualization
- [ ] Design versioning
- [ ] Link designs to drill bits
- [ ] Link BOMs to work orders
- [ ] Technology reports

### Procedures Module ✓

- [ ] Procedure creation
- [ ] Step management
- [ ] Step types (all 10 types)
- [ ] Checkpoint definitions
- [ ] Branch logic
- [ ] Input/output definitions
- [ ] Procedure versioning
- [ ] Link procedures to work orders
- [ ] Procedure templates

### Execution Module ✓

- [ ] Start procedure execution
- [ ] Step execution tracking
- [ ] Checkpoint result recording
- [ ] Branch evaluation
- [ ] Form submission
- [ ] Progress tracking
- [ ] Execution completion
- [ ] Execution history

### Notifications Module ✓

- [ ] Notification creation
- [ ] Notification display
- [ ] Notification preferences
- [ ] Email notifications
- [ ] Task creation
- [ ] Task assignment
- [ ] Comment system
- [ ] Comment attachments
- [ ] Audit log tracking
- [ ] Activity feed

---

## 🎨 UI COMPONENTS

### New Components Needed

**1. Inspection Card**
```html
<div class="inspection-card bg-white rounded-lg shadow p-4">
    <div class="flex justify-between">
        <div>
            <h4 class="font-semibold">{{ inspection.inspection_type }}</h4>
            <p class="text-sm text-gray-600">{{ inspection.inspection_date }}</p>
        </div>
        <span class="{% if inspection.passed %}text-green-600{% else %}text-red-600{% endif %}">
            {% if inspection.passed %}PASSED{% else %}FAILED{% endif %}
        </span>
    </div>
</div>
```

**2. NCR Card**
```html
<div class="ncr-card border-l-4 {% if ncr.severity == 'CRITICAL' %}border-red-600{% elif ncr.severity == 'MAJOR' %}border-orange-600{% else %}border-yellow-600{% endif %} bg-white p-4">
    <div class="flex justify-between items-start">
        <div>
            <h4 class="font-semibold">{{ ncr.ncr_number }}</h4>
            <p class="text-sm text-gray-600">{{ ncr.description|truncatewords:15 }}</p>
        </div>
        {% status_badge ncr.status %}
    </div>
    <div class="mt-2">
        <span class="text-xs px-2 py-1 rounded
            {% if ncr.severity == 'CRITICAL' %}bg-red-100 text-red-800
            {% elif ncr.severity == 'MAJOR' %}bg-orange-100 text-orange-800
            {% else %}bg-yellow-100 text-yellow-800{% endif %}">
            {{ ncr.get_severity_display }}
        </span>
    </div>
</div>
```

**3. Procedure Step Progress**
```html
<div class="step-progress">
    {% for step_exec in execution.step_executions.all %}
    <div class="flex items-center">
        <div class="w-8 h-8 rounded-full flex items-center justify-center
            {% if step_exec.status == 'COMPLETED' %}bg-green-600 text-white
            {% elif step_exec.status == 'IN_PROGRESS' %}bg-blue-600 text-white
            {% else %}bg-gray-300 text-gray-600{% endif %}">
            {{ step_exec.step.sequence }}
        </div>
        <div class="ml-4 flex-1">
            <p class="font-medium">{{ step_exec.step.title }}</p>
            <p class="text-sm text-gray-600">{{ step_exec.step.get_step_type_display }}</p>
        </div>
        <div>
            {% if step_exec.status == 'COMPLETED' %}
                <i data-lucide="check-circle" class="w-5 h-5 text-green-600"></i>
            {% elif step_exec.status == 'IN_PROGRESS' %}
                <i data-lucide="play-circle" class="w-5 h-5 text-blue-600"></i>
            {% endif %}
        </div>
    </div>
    {% if not forloop.last %}
    <div class="w-0.5 h-8 bg-gray-300 ml-4"></div>
    {% endif %}
    {% endfor %}
</div>
```

**4. Notification Bell**
```html
<div x-data="{ open: false, unreadCount: {{ notifications.unread_count }} }"
     class="relative">
    <button @click="open = !open" class="relative p-2">
        <i data-lucide="bell" class="w-5 h-5"></i>
        <span x-show="unreadCount > 0"
              class="absolute top-0 right-0 w-4 h-4 bg-red-600 text-white text-xs rounded-full flex items-center justify-center"
              x-text="unreadCount"></span>
    </button>
    
    <div x-show="open" @click.away="open = false"
         class="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg">
        {% for notification in notifications %}
            <div class="notification-item p-4 border-b hover:bg-gray-50">
                <p class="font-medium">{{ notification.title }}</p>
                <p class="text-sm text-gray-600">{{ notification.message }}</p>
                <p class="text-xs text-gray-500 mt-1">{{ notification.created_at|timesince }} ago</p>
            </div>
        {% endfor %}
    </div>
</div>
```

---

## 🔧 TECHNICAL SPECIFICATIONS

### Database Additions

**Performance Indexes:**
```python
# Inspection model
indexes = [
    models.Index(fields=['inspection_type', 'status']),
    models.Index(fields=['inspection_date']),
    models.Index(fields=['work_order', 'status']),
]

# NCR model
indexes = [
    models.Index(fields=['ncr_number']),
    models.Index(fields=['status', 'severity']),
    models.Index(fields=['work_order', 'status']),
]

# Design model
indexes = [
    models.Index(fields=['code']),
    models.Index(fields=['bit_type', 'size']),
]

# ProcedureExecution model
indexes = [
    models.Index(fields=['work_order', 'status']),
    models.Index(fields=['started_at']),
]

# Notification model
indexes = [
    models.Index(fields=['user', 'read']),
    models.Index(fields=['created_at']),
]
```

### File Storage for NCR Photos

```python
# settings.py
ARDT_NCR_PHOTO_PATH = 'ncr_photos/%Y/%m/'
ARDT_MAX_NCR_PHOTOS = 10
```

### Email Configuration for Notifications

```python
# settings.py
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@ardt.com')

# Notification settings
ARDT_NOTIFICATION_RETENTION_DAYS = 90  # Clean up old notifications
ARDT_SEND_EMAIL_NOTIFICATIONS = True
```

---

## 📊 SUCCESS METRICS

### Sprint 3 Goals

**Functional:**
- ✅ Complete quality management workflow
- ✅ Full design and BOM system
- ✅ Procedure execution tracking
- ✅ Notification system functional
- ✅ All integrations working

**Quality:**
- Django check: 0 errors
- All workflows tested
- All permissions checked
- Performance optimized
- Email notifications working

**User Experience:**
- Intuitive inspection flow
- Clear NCR workflow
- Easy procedure execution
- Real-time notifications
- Responsive design

---

## 🧪 TESTING PRIORITIES

### Critical Tests

```python
# Quality workflow test
def test_ncr_workflow():
    # Create inspection
    # Inspection fails
    # NCR is created
    # NCR is assigned
    # NCR is investigated
    # NCR is closed
    # Verify notifications sent

# Procedure execution test
def test_procedure_execution():
    # Start procedure
    # Complete steps in sequence
    # Record checkpoints
    # Handle branches
    # Complete procedure
    # Verify progress tracking

# Notification test
def test_notification_system():
    # Create notification
    # Send email
    # Mark as read
    # Delete old notifications
```

---

## 🚀 SPRINT 3 VELOCITY ESTIMATE

**Complexity:** High  
**New Concepts:** Procedure execution, workflow automation  
**Risk Level:** Medium  
**Estimated Velocity:** 85-90%

**Confidence Level:** 🟡 Medium-High

---

**Sprint 3 Status:** Ready for Planning Review  
**Prerequisites:** Sprint 1 ✅, Sprint 2 Required  
**Duration:** 6 days  
**Next:** Sprint 4 (Final)

**Ready to build quality and excellence!** 🎯
