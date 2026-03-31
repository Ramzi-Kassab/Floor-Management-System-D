"""
APPEND this block to apps/hr/views.py
(or create apps/hr/views_competency.py and import in urls.py)

Also add these URL patterns to apps/hr/urls.py:

    from . import views_competency  # or from .views import ...

    path('competency/', views_competency.CompetencyMatrixView.as_view(), name='competency_matrix'),
    path('competency/save/', views_competency.api_competency_save, name='competency_matrix_save'),
    path('competency/gaps/', views_competency.CompetencyGapReportView.as_view(), name='competency_matrix_gaps'),
    path('competency/export/', views_competency.competency_matrix_export, name='competency_matrix_export'),
"""

import json
from itertools import groupby

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import TemplateView

from apps.accounts.mixins import RoleRequiredMixin
from apps.hr.models import Employee, ProcessCompetencyMatrix
from apps.workorders.models import MasterProcess


class CompetencyMatrixView(RoleRequiredMixin, TemplateView):
    """
    Main competency matrix grid view.
    Shows all employees × all processes with current authorization levels.
    Only supervisors, managers, and admins can access.
    """
    template_name = 'hr/competency_matrix.html'
    required_roles = ['ADMIN', 'OPS_MANAGER', 'PDC_SUPERVISOR', 'RC_SUPERVISOR', 'GM']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # All active processes, grouped by category
        processes = MasterProcess.objects.filter(
            is_default_included=True
        ).select_related('parent_process').order_by('category', 'sort_order')

        # Group processes by category
        grouped = []
        for cat_code, proc_group in groupby(processes, key=lambda p: p.category):
            proc_list = list(proc_group)
            cat_label = dict(MasterProcess.Category.choices).get(cat_code, cat_code)
            grouped.append((cat_code, cat_label, proc_list))

        context['grouped_processes'] = grouped
        context['process_categories'] = MasterProcess.Category.choices

        # All active employees with their competency data
        employees = Employee.objects.filter(
            employment_status='ACTIVE'
        ).select_related('user', 'position').order_by('department', 'job_title')

        # Build a flat competency lookup: {(employee_id, process_id): competency}
        all_competencies = {
            (c.employee_id, c.master_process_id): c
            for c in ProcessCompetencyMatrix.objects.select_related('master_process')
        }

        # Build rows
        flat_processes = [p for _, _, pl in grouped for p in pl]

        employee_rows = []
        for emp in employees:
            cells = []
            for proc in flat_processes:
                comp = all_competencies.get((emp.pk, proc.pk))
                cells.append({
                    'process_pk': proc.pk,
                    'process_name': proc.name,
                    'level': comp.level if comp else 'NONE',
                    'level_display': comp.get_level_display() if comp else 'Not Authorized',
                    'expiry': comp.expiry_date.strftime('%Y-%m-%d') if comp and comp.expiry_date else '',
                    'cert_ref': comp.certificate_reference if comp else '',
                    'is_expired': comp.is_expired if comp else False,
                })
            employee_rows.append({
                'employee': emp,
                'dept_code': emp.user.department.code if emp.user.department else '',
                'cells': cells,
            })

        context['employee_rows'] = employee_rows

        # Departments for filter
        from apps.organization.models import Department
        context['departments'] = Department.objects.filter(is_active=True).order_by('name')

        return context


@login_required
def api_competency_save(request):
    """
    POST: Save or update a single competency record.
    Body: { employee_pk, process_pk, level, expiry_date, certified_date,
            certificate_reference }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    if not request.user.has_any_role(['ADMIN', 'OPS_MANAGER', 'PDC_SUPERVISOR',
                                       'RC_SUPERVISOR', 'GM']):
        return JsonResponse({'error': 'Permission denied'}, status=403)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    employee = get_object_or_404(Employee, pk=body.get('employee_pk'))
    process = get_object_or_404(MasterProcess, pk=body.get('process_pk'))
    level = body.get('level', 'NONE')

    if level not in [c[0] for c in ProcessCompetencyMatrix.CompetencyLevel.choices]:
        return JsonResponse({'error': f'Invalid level: {level}'}, status=400)

    comp, created = ProcessCompetencyMatrix.objects.get_or_create(
        employee=employee,
        master_process=process,
        defaults={'created_by': request.user}
    )

    comp.level = level
    comp.certificate_reference = body.get('certificate_reference', '')

    if body.get('expiry_date'):
        try:
            from datetime import date
            comp.expiry_date = date.fromisoformat(body['expiry_date'])
        except (ValueError, TypeError):
            pass
    else:
        comp.expiry_date = None

    if body.get('certified_date'):
        try:
            from datetime import date
            comp.certified_date = date.fromisoformat(body['certified_date'])
        except (ValueError, TypeError):
            pass

    if level in ('CERTIFIED', 'TRAINER') and not comp.certified_date:
        comp.certified_date = timezone.now().date()

    comp.save()

    return JsonResponse({
        'success': True,
        'created': created,
        'level': comp.level,
        'level_display': comp.get_level_display(),
    })


class CompetencyGapReportView(RoleRequiredMixin, TemplateView):
    """
    Shows all employees who have NOT_AUTHORIZED or TRAINEE level
    for processes required by their position.
    """
    template_name = 'hr/competency_gap_report.html'
    required_roles = ['ADMIN', 'OPS_MANAGER', 'PDC_SUPERVISOR', 'RC_SUPERVISOR', 'GM']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        gaps = ProcessCompetencyMatrix.objects.filter(
            level__in=['NONE', 'TRAINEE'],
            employee__employment_status='ACTIVE',
        ).select_related(
            'employee__user', 'employee__position', 'master_process'
        ).order_by('employee__user__last_name', 'master_process__category')

        expired = ProcessCompetencyMatrix.objects.filter(
            expiry_date__lt=timezone.now().date(),
            employee__employment_status='ACTIVE',
        ).exclude(level='NONE').select_related(
            'employee__user', 'employee__position', 'master_process'
        )

        context['gaps'] = gaps
        context['expired'] = expired
        context['gap_count'] = gaps.count()
        context['expired_count'] = expired.count()
        return context


@login_required
def competency_matrix_export(request):
    """Export the competency matrix as CSV."""
    import csv

    if not request.user.has_any_role(['ADMIN', 'OPS_MANAGER', 'PDC_SUPERVISOR', 'GM']):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="competency_matrix_{timezone.now().strftime("%Y%m%d")}.csv"'
    )

    writer = csv.writer(response)

    processes = MasterProcess.objects.filter(
        is_default_included=True
    ).order_by('category', 'sort_order')

    # Header
    writer.writerow(
        ['Employee No.', 'Name', 'Position', 'Department'] +
        [p.code for p in processes]
    )

    employees = Employee.objects.filter(
        employment_status='ACTIVE'
    ).select_related('user', 'position').order_by('employee_number')

    all_comp = {
        (c.employee_id, c.master_process_id): c.level
        for c in ProcessCompetencyMatrix.objects.all()
    }

    for emp in employees:
        row = [
            emp.employee_number,
            emp.user.get_full_name(),
            emp.position_title,
            emp.user.department.name if emp.user.department else emp.department,
        ]
        for proc in processes:
            row.append(all_comp.get((emp.pk, proc.pk), 'NONE'))
        writer.writerow(row)

    return response
