"""
Tests for Planning app models.
"""
import pytest
from datetime import date, timedelta
from django.contrib.auth import get_user_model

from apps.planning.models import (
    Sprint, PlanningBoard, PlanningColumn, PlanningLabel,
    PlanningItem, PlanningItemLabel, PlanningItemWatcher,
    WikiSpace, WikiPage, WikiPageVersion
)

User = get_user_model()


class TestSprintModel:
    """Tests for Sprint model."""

    def test_create_sprint(self, db, test_user):
        """Test creating a sprint."""
        sprint = Sprint.objects.create(
            name='Test Sprint',
            code='SPRINT-TEST',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=14),
            status=Sprint.Status.PLANNING,
            created_by=test_user
        )
        assert sprint.pk is not None
        assert sprint.code == 'SPRINT-TEST'

    def test_sprint_str(self, sprint):
        """Test sprint string representation."""
        assert 'SPRINT-01' in str(sprint)
        assert 'Sprint 1' in str(sprint)

    def test_sprint_progress_percent(self, sprint):
        """Test sprint progress calculation."""
        # 10 completed out of 40 = 25%
        assert sprint.progress_percent == 25

    def test_sprint_progress_zero_capacity(self, db, test_user):
        """Test sprint progress with zero capacity."""
        sprint = Sprint.objects.create(
            name='Empty Sprint',
            code='SPRINT-EMPTY',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            capacity_points=0,
            completed_points=0,
            created_by=test_user
        )
        assert sprint.progress_percent == 0

    def test_sprint_status_choices(self, db, test_user):
        """Test sprint status choices."""
        for status, _ in Sprint.Status.choices:
            sprint = Sprint.objects.create(
                name=f'Sprint {status}',
                code=f'SPRINT-{status}',
                start_date=date.today(),
                end_date=date.today() + timedelta(days=14),
                status=status,
                created_by=test_user
            )
            assert sprint.status == status


class TestPlanningBoardModel:
    """Tests for PlanningBoard model."""

    def test_create_board(self, db, test_user):
        """Test creating a planning board."""
        board = PlanningBoard.objects.create(
            name='Test Board',
            code='TEST-BOARD',
            owner=test_user
        )
        assert board.pk is not None
        assert board.name == 'Test Board'
        assert board.is_active is True

    def test_board_str(self, planning_board):
        """Test board string representation."""
        assert str(planning_board) == 'Development Board'

    def test_board_with_sprint(self, planning_board, sprint):
        """Test board linked to sprint."""
        assert planning_board.sprint == sprint
        assert planning_board in sprint.boards.all()


class TestPlanningColumnModel:
    """Tests for PlanningColumn model."""

    def test_create_column(self, db, planning_board):
        """Test creating a planning column."""
        column = PlanningColumn.objects.create(
            board=planning_board,
            name='In Progress',
            code='IN_PROGRESS',
            sequence=1
        )
        assert column.pk is not None
        assert column.board == planning_board

    def test_column_str(self, planning_column):
        """Test column string representation."""
        assert 'Development Board' in str(planning_column)
        assert 'To Do' in str(planning_column)

    def test_column_done_flag(self, done_column):
        """Test done column flag."""
        assert done_column.is_done_column is True
        assert done_column.is_backlog_column is False

    def test_column_unique_together(self, db, planning_board, planning_column):
        """Test unique constraint on board+code."""
        with pytest.raises(Exception):
            PlanningColumn.objects.create(
                board=planning_board,
                name='Duplicate',
                code='TODO',  # Same code as existing column
                sequence=99
            )


class TestPlanningLabelModel:
    """Tests for PlanningLabel model."""

    def test_create_label(self, db):
        """Test creating a planning label."""
        label = PlanningLabel.objects.create(
            name='Bug',
            color='#dc2626',
            description='Bug fix items'
        )
        assert label.pk is not None
        assert label.name == 'Bug'

    def test_label_str(self, planning_label):
        """Test label string representation."""
        assert str(planning_label) == 'High Priority'

    def test_label_default_color(self, db):
        """Test label default color."""
        label = PlanningLabel.objects.create(name='Test Label')
        assert label.color == '#6b7280'


class TestPlanningItemModel:
    """Tests for PlanningItem model."""

    def test_create_item(self, db, test_user, planning_board, planning_column):
        """Test creating a planning item."""
        item = PlanningItem.objects.create(
            code='ARDT-TEST',
            title='Test Task',
            item_type=PlanningItem.ItemType.TASK,
            board=planning_board,
            column=planning_column,
            created_by=test_user
        )
        assert item.pk is not None
        assert item.code == 'ARDT-TEST'

    def test_item_str(self, planning_item):
        """Test item string representation."""
        assert 'ARDT-001' in str(planning_item)
        assert 'user authentication' in str(planning_item)

    def test_item_type_choices(self, db, test_user):
        """Test item type choices."""
        for item_type, _ in PlanningItem.ItemType.choices:
            item = PlanningItem.objects.create(
                code=f'ARDT-{item_type}',
                title=f'Test {item_type}',
                item_type=item_type,
                created_by=test_user
            )
            assert item.item_type == item_type

    def test_item_priority_choices(self, db, test_user):
        """Test item priority choices."""
        for i, (priority, _) in enumerate(PlanningItem.Priority.choices):
            item = PlanningItem.objects.create(
                code=f'ARDT-P{i}',
                title=f'Test {priority}',
                priority=priority,
                created_by=test_user
            )
            assert item.priority == priority

    def test_item_parent_child_relationship(self, db, test_user, planning_item):
        """Test item hierarchy."""
        subtask = PlanningItem.objects.create(
            code='ARDT-002',
            title='Subtask',
            item_type=PlanningItem.ItemType.SUBTASK,
            parent=planning_item,
            created_by=test_user
        )
        assert subtask.parent == planning_item
        assert subtask in planning_item.children.all()


class TestPlanningItemLabelModel:
    """Tests for PlanningItemLabel model."""

    def test_create_item_label(self, db, planning_item, planning_label):
        """Test creating an item-label relationship."""
        item_label = PlanningItemLabel.objects.create(
            item=planning_item,
            label=planning_label
        )
        assert item_label.pk is not None
        assert planning_label in planning_item.labels.all()

    def test_item_label_str(self, db, planning_item, planning_label):
        """Test item-label string representation."""
        item_label = PlanningItemLabel.objects.create(
            item=planning_item,
            label=planning_label
        )
        assert 'ARDT-001' in str(item_label)
        assert 'High Priority' in str(item_label)


class TestPlanningItemWatcherModel:
    """Tests for PlanningItemWatcher model."""

    def test_create_watcher(self, db, planning_item, another_user):
        """Test creating an item watcher."""
        watcher = PlanningItemWatcher.objects.create(
            item=planning_item,
            user=another_user
        )
        assert watcher.pk is not None
        assert another_user in [w.user for w in planning_item.watchers.all()]

    def test_watcher_str(self, db, planning_item, another_user):
        """Test watcher string representation."""
        watcher = PlanningItemWatcher.objects.create(
            item=planning_item,
            user=another_user
        )
        assert 'anotheruser' in str(watcher)
        assert 'ARDT-001' in str(watcher)


class TestWikiSpaceModel:
    """Tests for WikiSpace model."""

    def test_create_wiki_space(self, db, test_user):
        """Test creating a wiki space."""
        space = WikiSpace.objects.create(
            code='WIKI-TEST',
            name='Test Wiki',
            owner=test_user
        )
        assert space.pk is not None
        assert space.code == 'WIKI-TEST'

    def test_wiki_space_str(self, wiki_space):
        """Test wiki space string representation."""
        assert str(wiki_space) == 'Documentation'

    def test_wiki_space_public_flag(self, wiki_space):
        """Test wiki space public flag."""
        assert wiki_space.is_public is True


class TestWikiPageModel:
    """Tests for WikiPage model."""

    def test_create_wiki_page(self, db, test_user, wiki_space):
        """Test creating a wiki page."""
        page = WikiPage.objects.create(
            space=wiki_space,
            title='Test Page',
            slug='test-page',
            content='# Test Content',
            created_by=test_user
        )
        assert page.pk is not None
        assert page.title == 'Test Page'

    def test_wiki_page_str(self, wiki_page):
        """Test wiki page string representation."""
        assert 'DOCS/getting-started' in str(wiki_page)

    def test_wiki_page_hierarchy(self, db, test_user, wiki_space, wiki_page):
        """Test wiki page parent-child relationship."""
        child_page = WikiPage.objects.create(
            space=wiki_space,
            title='Child Page',
            slug='child-page',
            parent=wiki_page,
            created_by=test_user
        )
        assert child_page.parent == wiki_page
        assert child_page in wiki_page.children.all()

    def test_wiki_page_unique_together(self, db, test_user, wiki_space, wiki_page):
        """Test unique constraint on space+slug."""
        with pytest.raises(Exception):
            WikiPage.objects.create(
                space=wiki_space,
                title='Duplicate',
                slug='getting-started',  # Same slug
                created_by=test_user
            )


class TestWikiPageVersionModel:
    """Tests for WikiPageVersion model."""

    def test_create_version(self, db, test_user, wiki_page):
        """Test creating a wiki page version."""
        version = WikiPageVersion.objects.create(
            page=wiki_page,
            version_number=2,
            title='Updated Title',
            content='# Updated Content',
            change_summary='Updated title and content',
            changed_by=test_user
        )
        assert version.pk is not None
        assert version.version_number == 2

    def test_version_str(self, wiki_page_version):
        """Test version string representation."""
        assert 'v1' in str(wiki_page_version)

    def test_version_unique_together(self, db, test_user, wiki_page, wiki_page_version):
        """Test unique constraint on page+version_number."""
        with pytest.raises(Exception):
            WikiPageVersion.objects.create(
                page=wiki_page,
                version_number=1,  # Same version
                title='Duplicate',
                content='Duplicate content',
                changed_by=test_user
            )
