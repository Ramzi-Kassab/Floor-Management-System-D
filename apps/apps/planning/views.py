"""
ARDT FMS - Planning Views
Version: 5.4
"""

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from .forms import (
    PlanningBoardForm,
    PlanningColumnForm,
    PlanningItemForm,
    PlanningItemQuickCreateForm,
    PlanningLabelForm,
    SprintForm,
    WikiPageForm,
    WikiSpaceForm,
)
from .models import (
    PlanningBoard,
    PlanningColumn,
    PlanningItem,
    PlanningLabel,
    Sprint,
    WikiPage,
    WikiPageVersion,
    WikiSpace,
)

User = get_user_model()


# =============================================================================
# Sprint Views
# =============================================================================


class SprintListView(LoginRequiredMixin, ListView):
    """List all sprints."""

    model = Sprint
    template_name = "planning/sprint_list.html"
    context_object_name = "sprints"

    def get_queryset(self):
        qs = Sprint.objects.select_related("owner", "created_by").annotate(item_count=Count("items"))

        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Sprints"
        context["status_choices"] = Sprint.Status.choices
        context["current_status"] = self.request.GET.get("status", "")
        context["today"] = timezone.now().date()
        return context


class SprintDetailView(LoginRequiredMixin, DetailView):
    """Sprint detail view with items."""

    model = Sprint
    template_name = "planning/sprint_detail.html"
    context_object_name = "sprint"

    def get_queryset(self):
        return Sprint.objects.select_related("owner", "created_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.object.code
        context["items"] = self.object.items.select_related("assignee", "column").order_by("-priority", "title")
        context["boards"] = self.object.boards.all()
        return context


class SprintCreateView(LoginRequiredMixin, CreateView):
    """Create a new sprint."""

    model = Sprint
    form_class = SprintForm
    template_name = "planning/sprint_form.html"
    success_url = reverse_lazy("planning:sprint_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Sprint"
        context["form_title"] = "Create Sprint"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Sprint created successfully.")
        return super().form_valid(form)


class SprintUpdateView(LoginRequiredMixin, UpdateView):
    """Update a sprint."""

    model = Sprint
    form_class = SprintForm
    template_name = "planning/sprint_form.html"

    def get_success_url(self):
        return reverse_lazy("planning:sprint_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.code}"
        context["form_title"] = f"Edit Sprint - {self.object.code}"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Sprint updated successfully.")
        return super().form_valid(form)


# =============================================================================
# Board Views
# =============================================================================


class BoardListView(LoginRequiredMixin, ListView):
    """List all planning boards."""

    model = PlanningBoard
    template_name = "planning/board_list.html"
    context_object_name = "boards"

    def get_queryset(self):
        return (
            PlanningBoard.objects.filter(is_active=True)
            .select_related("sprint", "owner")
            .annotate(item_count=Count("items"))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Planning Boards"
        return context


class BoardDetailView(LoginRequiredMixin, DetailView):
    """Kanban board view."""

    model = PlanningBoard
    template_name = "planning/board_detail.html"
    context_object_name = "board"

    def get_queryset(self):
        return PlanningBoard.objects.select_related("sprint", "owner")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.object.name
        context["columns"] = self.object.columns.prefetch_related(
            "items__assignee", "items__labels"
        ).order_by("sequence")
        context["labels"] = PlanningLabel.objects.all()
        context["quick_form"] = PlanningItemQuickCreateForm()
        return context


class BoardCreateView(LoginRequiredMixin, CreateView):
    """Create a new board."""

    model = PlanningBoard
    form_class = PlanningBoardForm
    template_name = "planning/board_form.html"
    success_url = reverse_lazy("planning:board_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Board"
        context["form_title"] = "Create Planning Board"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Board created successfully.")
        return super().form_valid(form)


class BoardUpdateView(LoginRequiredMixin, UpdateView):
    """Update a board."""

    model = PlanningBoard
    form_class = PlanningBoardForm
    template_name = "planning/board_form.html"

    def get_success_url(self):
        return reverse_lazy("planning:board_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.name}"
        context["form_title"] = f"Edit Board - {self.object.name}"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Board updated successfully.")
        return super().form_valid(form)


# =============================================================================
# Column Views
# =============================================================================


class ColumnCreateView(LoginRequiredMixin, CreateView):
    """Create a new column for a board."""

    model = PlanningColumn
    form_class = PlanningColumnForm
    template_name = "planning/column_form.html"

    def get_initial(self):
        initial = super().get_initial()
        board_pk = self.request.GET.get("board")
        if board_pk:
            initial["board"] = board_pk
        return initial

    def get_success_url(self):
        return reverse_lazy("planning:board_detail", kwargs={"pk": self.object.board.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Column"
        context["form_title"] = "Create Column"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Column created successfully.")
        return super().form_valid(form)


class ColumnUpdateView(LoginRequiredMixin, UpdateView):
    """Update a column."""

    model = PlanningColumn
    form_class = PlanningColumnForm
    template_name = "planning/column_form.html"

    def get_success_url(self):
        return reverse_lazy("planning:board_detail", kwargs={"pk": self.object.board.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.name}"
        context["form_title"] = f"Edit Column - {self.object.name}"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Column updated successfully.")
        return super().form_valid(form)


# =============================================================================
# Planning Item Views
# =============================================================================


class ItemListView(LoginRequiredMixin, ListView):
    """List planning items (backlog view)."""

    model = PlanningItem
    template_name = "planning/item_list.html"
    context_object_name = "items"
    paginate_by = 50

    def get_queryset(self):
        qs = PlanningItem.objects.select_related("board", "column", "sprint", "assignee").prefetch_related("labels")

        # Search
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(code__icontains=q) | Q(title__icontains=q))

        # Filter by type
        item_type = self.request.GET.get("type")
        if item_type:
            qs = qs.filter(item_type=item_type)

        # Filter by status (column done)
        status = self.request.GET.get("status")
        if status == "done":
            qs = qs.filter(column__is_done_column=True)
        elif status == "active":
            qs = qs.filter(column__is_done_column=False, column__is_backlog_column=False)
        elif status == "backlog":
            qs = qs.filter(column__is_backlog_column=True)

        # Filter by assignee
        assignee = self.request.GET.get("assignee")
        if assignee:
            qs = qs.filter(assignee_id=assignee)

        return qs.order_by("-priority", "-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Planning Items"
        context["search_query"] = self.request.GET.get("q", "")
        context["type_choices"] = PlanningItem.ItemType.choices
        context["current_type"] = self.request.GET.get("type", "")
        context["users"] = User.objects.filter(is_active=True).order_by("username")
        return context


class ItemDetailView(LoginRequiredMixin, DetailView):
    """Planning item detail."""

    model = PlanningItem
    template_name = "planning/item_detail.html"
    context_object_name = "item"

    def get_queryset(self):
        return PlanningItem.objects.select_related(
            "board", "column", "sprint", "assignee", "reporter", "parent", "created_by"
        ).prefetch_related("labels", "children")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.object.code
        context["children"] = self.object.children.select_related("assignee", "column")
        return context


class ItemCreateView(LoginRequiredMixin, CreateView):
    """Create a new planning item."""

    model = PlanningItem
    form_class = PlanningItemForm
    template_name = "planning/item_form.html"
    success_url = reverse_lazy("planning:item_list")

    def get_initial(self):
        initial = super().get_initial()
        board_pk = self.request.GET.get("board")
        if board_pk:
            initial["board"] = board_pk
        column_pk = self.request.GET.get("column")
        if column_pk:
            initial["column"] = column_pk
        sprint_pk = self.request.GET.get("sprint")
        if sprint_pk:
            initial["sprint"] = sprint_pk
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Item"
        context["form_title"] = "Create Planning Item"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.reporter = self.request.user

        # Generate code if not provided
        if not form.instance.code:
            last = PlanningItem.objects.order_by("-id").first()
            next_num = (last.id + 1) if last else 1
            form.instance.code = f"ARDT-{next_num:04d}"

        messages.success(self.request, "Item created successfully.")
        return super().form_valid(form)


class ItemUpdateView(LoginRequiredMixin, UpdateView):
    """Update a planning item."""

    model = PlanningItem
    form_class = PlanningItemForm
    template_name = "planning/item_form.html"

    def get_success_url(self):
        return reverse_lazy("planning:item_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.code}"
        context["form_title"] = f"Edit Item - {self.object.code}"
        return context

    def form_valid(self, form):
        # Track completion
        if form.instance.column and form.instance.column.is_done_column:
            if not form.instance.completed_date:
                form.instance.completed_date = timezone.now().date()
        else:
            form.instance.completed_date = None

        messages.success(self.request, "Item updated successfully.")
        return super().form_valid(form)


# =============================================================================
# Label Views
# =============================================================================


class LabelListView(LoginRequiredMixin, ListView):
    """List all labels."""

    model = PlanningLabel
    template_name = "planning/label_list.html"
    context_object_name = "labels"

    def get_queryset(self):
        return PlanningLabel.objects.annotate(item_count=Count("items"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Labels"
        return context


class LabelCreateView(LoginRequiredMixin, CreateView):
    """Create a new label."""

    model = PlanningLabel
    form_class = PlanningLabelForm
    template_name = "planning/label_form.html"
    success_url = reverse_lazy("planning:label_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Label"
        context["form_title"] = "Create Label"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Label created successfully.")
        return super().form_valid(form)


class LabelUpdateView(LoginRequiredMixin, UpdateView):
    """Update a label."""

    model = PlanningLabel
    form_class = PlanningLabelForm
    template_name = "planning/label_form.html"
    success_url = reverse_lazy("planning:label_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.name}"
        context["form_title"] = f"Edit Label - {self.object.name}"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Label updated successfully.")
        return super().form_valid(form)


# =============================================================================
# Wiki Views
# =============================================================================


class WikiSpaceListView(LoginRequiredMixin, ListView):
    """List wiki spaces."""

    model = WikiSpace
    template_name = "planning/wiki_space_list.html"
    context_object_name = "spaces"

    def get_queryset(self):
        return WikiSpace.objects.select_related("owner").annotate(page_count=Count("pages"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Wiki"
        return context


class WikiSpaceDetailView(LoginRequiredMixin, DetailView):
    """Wiki space with pages tree."""

    model = WikiSpace
    template_name = "planning/wiki_space_detail.html"
    context_object_name = "space"

    def get_queryset(self):
        return WikiSpace.objects.select_related("owner")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.object.name
        context["root_pages"] = self.object.pages.filter(parent__isnull=True).order_by("sequence", "title")
        return context


class WikiSpaceCreateView(LoginRequiredMixin, CreateView):
    """Create wiki space."""

    model = WikiSpace
    form_class = WikiSpaceForm
    template_name = "planning/wiki_space_form.html"
    success_url = reverse_lazy("planning:wiki_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Wiki Space"
        context["form_title"] = "Create Wiki Space"
        return context

    def form_valid(self, form):
        if not form.instance.owner:
            form.instance.owner = self.request.user
        messages.success(self.request, "Wiki space created successfully.")
        return super().form_valid(form)


class WikiSpaceUpdateView(LoginRequiredMixin, UpdateView):
    """Update wiki space."""

    model = WikiSpace
    form_class = WikiSpaceForm
    template_name = "planning/wiki_space_form.html"

    def get_success_url(self):
        return reverse_lazy("planning:wiki_space_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.name}"
        context["form_title"] = f"Edit Wiki Space - {self.object.name}"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Wiki space updated successfully.")
        return super().form_valid(form)


class WikiPageDetailView(LoginRequiredMixin, DetailView):
    """Wiki page view."""

    model = WikiPage
    template_name = "planning/wiki_page_detail.html"
    context_object_name = "wiki_page"

    def get_queryset(self):
        return WikiPage.objects.select_related("space", "parent", "created_by", "last_edited_by")

    def get_object(self):
        obj = super().get_object()
        # Increment view count
        WikiPage.objects.filter(pk=obj.pk).update(view_count=obj.view_count + 1)
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.object.title
        context["children"] = self.object.children.order_by("sequence", "title")
        context["siblings"] = (
            WikiPage.objects.filter(space=self.object.space, parent=self.object.parent)
            .exclude(pk=self.object.pk)
            .order_by("sequence", "title")
        )
        return context


class WikiPageCreateView(LoginRequiredMixin, CreateView):
    """Create wiki page."""

    model = WikiPage
    form_class = WikiPageForm
    template_name = "planning/wiki_page_form.html"

    def get_initial(self):
        initial = super().get_initial()
        space_pk = self.request.GET.get("space")
        if space_pk:
            initial["space"] = space_pk
        parent_pk = self.request.GET.get("parent")
        if parent_pk:
            initial["parent"] = parent_pk
        return initial

    def get_success_url(self):
        return reverse_lazy("planning:wiki_page_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Wiki Page"
        context["form_title"] = "Create Wiki Page"
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.last_edited_by = self.request.user
        messages.success(self.request, "Wiki page created successfully.")
        return super().form_valid(form)


class WikiPageUpdateView(LoginRequiredMixin, UpdateView):
    """Update wiki page."""

    model = WikiPage
    form_class = WikiPageForm
    template_name = "planning/wiki_page_form.html"

    def get_success_url(self):
        return reverse_lazy("planning:wiki_page_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Edit {self.object.title}"
        context["form_title"] = f"Edit - {self.object.title}"
        return context

    def form_valid(self, form):
        # Create version before saving
        WikiPageVersion.objects.create(
            page=self.object,
            version_number=self.object.versions.count() + 1,
            title=self.object.title,
            content=self.object.content,
            change_summary=f"Edited by {self.request.user.username}",
            changed_by=self.request.user,
        )

        form.instance.last_edited_by = self.request.user
        messages.success(self.request, "Wiki page updated successfully.")
        return super().form_valid(form)


# =============================================================================
# Delete Views
# =============================================================================


class SprintDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a sprint."""

    model = Sprint
    template_name = "planning/confirm_delete.html"
    success_url = reverse_lazy("planning:sprint_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete {self.object.code}"
        context["object_type"] = "Sprint"
        context["object_name"] = self.object.code
        context["cancel_url"] = reverse_lazy("planning:sprint_detail", kwargs={"pk": self.object.pk})
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Sprint {self.object.code} deleted successfully.")
        return super().form_valid(form)


class BoardDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a board."""

    model = PlanningBoard
    template_name = "planning/confirm_delete.html"
    success_url = reverse_lazy("planning:board_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete {self.object.name}"
        context["object_type"] = "Board"
        context["object_name"] = self.object.name
        context["cancel_url"] = reverse_lazy("planning:board_detail", kwargs={"pk": self.object.pk})
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Board {self.object.name} deleted successfully.")
        return super().form_valid(form)


class ColumnDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a column."""

    model = PlanningColumn
    template_name = "planning/confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("planning:board_detail", kwargs={"pk": self.object.board.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete {self.object.name}"
        context["object_type"] = "Column"
        context["object_name"] = self.object.name
        context["cancel_url"] = reverse_lazy("planning:board_detail", kwargs={"pk": self.object.board.pk})
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Column {self.object.name} deleted successfully.")
        return super().form_valid(form)


class ItemDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a planning item."""

    model = PlanningItem
    template_name = "planning/confirm_delete.html"
    success_url = reverse_lazy("planning:item_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete {self.object.code}"
        context["object_type"] = "Item"
        context["object_name"] = f"{self.object.code} - {self.object.title}"
        context["cancel_url"] = reverse_lazy("planning:item_detail", kwargs={"pk": self.object.pk})
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Item {self.object.code} deleted successfully.")
        return super().form_valid(form)


class LabelDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a label."""

    model = PlanningLabel
    template_name = "planning/confirm_delete.html"
    success_url = reverse_lazy("planning:label_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete {self.object.name}"
        context["object_type"] = "Label"
        context["object_name"] = self.object.name
        context["cancel_url"] = reverse_lazy("planning:label_list")
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Label {self.object.name} deleted successfully.")
        return super().form_valid(form)


class WikiSpaceDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a wiki space."""

    model = WikiSpace
    template_name = "planning/confirm_delete.html"
    success_url = reverse_lazy("planning:wiki_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete {self.object.name}"
        context["object_type"] = "Wiki Space"
        context["object_name"] = self.object.name
        context["cancel_url"] = reverse_lazy("planning:wiki_space_detail", kwargs={"pk": self.object.pk})
        context["warning"] = "This will also delete all pages in this wiki space!"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Wiki space {self.object.name} deleted successfully.")
        return super().form_valid(form)


class WikiPageDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a wiki page."""

    model = WikiPage
    template_name = "planning/confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("planning:wiki_space_detail", kwargs={"pk": self.object.space.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = f"Delete {self.object.title}"
        context["object_type"] = "Wiki Page"
        context["object_name"] = self.object.title
        context["cancel_url"] = reverse_lazy("planning:wiki_page_detail", kwargs={"pk": self.object.pk})
        if self.object.children.exists():
            context["warning"] = "This page has child pages that will also be affected!"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Wiki page '{self.object.title}' deleted successfully.")
        return super().form_valid(form)
