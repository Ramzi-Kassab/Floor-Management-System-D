"""
Planning App Test Fixtures
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


@pytest.fixture
def test_user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123'
    )


@pytest.fixture
def another_user(db):
    """Create another test user."""
    return User.objects.create_user(
        username='anotheruser',
        email='another@example.com',
        password='testpass123'
    )


@pytest.fixture
def sprint(db, test_user):
    """Create a test sprint."""
    return Sprint.objects.create(
        name='Sprint 1',
        code='SPRINT-01',
        goal='Complete MVP features',
        start_date=date.today(),
        end_date=date.today() + timedelta(days=14),
        status=Sprint.Status.ACTIVE,
        capacity_points=40,
        completed_points=10,
        owner=test_user,
        created_by=test_user
    )


@pytest.fixture
def planning_board(db, test_user, sprint):
    """Create a test planning board."""
    return PlanningBoard.objects.create(
        name='Development Board',
        code='DEV-BOARD',
        description='Main development board',
        sprint=sprint,
        icon='clipboard',
        color='blue',
        default_wip_limit=5,
        is_active=True,
        owner=test_user
    )


@pytest.fixture
def planning_column(db, planning_board):
    """Create a test planning column."""
    return PlanningColumn.objects.create(
        board=planning_board,
        name='To Do',
        code='TODO',
        sequence=0,
        wip_limit=10,
        color='gray',
        is_done_column=False,
        is_backlog_column=True
    )


@pytest.fixture
def done_column(db, planning_board):
    """Create a done column."""
    return PlanningColumn.objects.create(
        board=planning_board,
        name='Done',
        code='DONE',
        sequence=3,
        is_done_column=True,
        is_backlog_column=False
    )


@pytest.fixture
def planning_label(db):
    """Create a test planning label."""
    return PlanningLabel.objects.create(
        name='High Priority',
        color='#ef4444',
        description='Urgent items'
    )


@pytest.fixture
def planning_item(db, test_user, planning_board, planning_column, sprint):
    """Create a test planning item."""
    return PlanningItem.objects.create(
        code='ARDT-001',
        title='Implement user authentication',
        description='Add login/logout functionality',
        item_type=PlanningItem.ItemType.STORY,
        priority=PlanningItem.Priority.HIGH,
        board=planning_board,
        column=planning_column,
        position=0,
        sprint=sprint,
        story_points=5,
        estimated_hours=8,
        due_date=date.today() + timedelta(days=7),
        assignee=test_user,
        reporter=test_user,
        created_by=test_user
    )


@pytest.fixture
def wiki_space(db, test_user):
    """Create a test wiki space."""
    return WikiSpace.objects.create(
        code='DOCS',
        name='Documentation',
        description='Project documentation',
        icon='book',
        is_public=True,
        owner=test_user
    )


@pytest.fixture
def wiki_page(db, test_user, wiki_space):
    """Create a test wiki page."""
    return WikiPage.objects.create(
        space=wiki_space,
        title='Getting Started',
        slug='getting-started',
        icon='rocket',
        content='# Welcome\n\nThis is the getting started guide.',
        is_published=True,
        is_template=False,
        created_by=test_user
    )


@pytest.fixture
def wiki_page_version(db, test_user, wiki_page):
    """Create a test wiki page version."""
    return WikiPageVersion.objects.create(
        page=wiki_page,
        version_number=1,
        title=wiki_page.title,
        content=wiki_page.content,
        change_summary='Initial version',
        changed_by=test_user
    )


# Fixtures for base class tests
@pytest.fixture
def test_object(sprint):
    """Default test object for base class tests."""
    return sprint


@pytest.fixture
def valid_data(test_user):
    """Valid data for sprint creation."""
    return {
        'name': 'New Sprint',
        'code': 'SPRINT-NEW',
        'goal': 'Test goal',
        'start_date': date.today(),
        'end_date': date.today() + timedelta(days=14),
        'status': Sprint.Status.PLANNING,
        'capacity_points': 30,
    }
