"""
Tests for the Supabase integration (SupabaseManager).

These tests mock the Supabase client to verify logic without
requiring actual Supabase credentials.
"""

import pytest
from unittest.mock import patch, MagicMock


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #
@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset module-level singletons before each test."""
    import src.database.supabase_client as mod

    mod._supabase_client = None
    mod._supabase_manager = None
    yield
    mod._supabase_client = None
    mod._supabase_manager = None


@pytest.fixture
def mock_supabase():
    """Provide a mocked Supabase client that is injected into the module."""
    import src.database.supabase_client as mod

    fake_client = MagicMock()
    mod._supabase_client = fake_client
    return fake_client


@pytest.fixture
def manager(mock_supabase):
    """Build a SupabaseManager backed by the mocked Supabase client."""
    from src.database.supabase_client import SupabaseManager

    return SupabaseManager()


# ------------------------------------------------------------------ #
# Tests
# ------------------------------------------------------------------ #
class TestSupabaseManager:
    """Unit tests for SupabaseManager."""

    def test_save_lost_item_inserts_into_lost_items(self, manager, mock_supabase):
        """Saving with intention='lost' should target the lost_items table."""
        fake_response = MagicMock()
        fake_response.data = [{"id": "abc-123"}]
        mock_supabase.table.return_value.insert.return_value.execute.return_value = (
            fake_response
        )

        result = manager.save_validated_item(
            intention="lost",
            user_id="user1",
            user_email="user@example.com",
            item_data={
                "item_type": "laptop",
                "description": "Silver MacBook Pro",
                "color": "silver",
                "brand": "Apple",
                "location": "library",
                "time": "2pm",
                "confidence_score": 0.92,
                "routing": "high_quality",
                "action": "forward_to_matching",
                "validation_summary": {"overall_confidence": 0.92},
            },
        )

        mock_supabase.table.assert_called_with("lost_items")
        assert result == "abc-123"

    def test_save_found_item_inserts_into_found_items(self, manager, mock_supabase):
        """Saving with intention='found' should target the found_items table."""
        fake_response = MagicMock()
        fake_response.data = [{"id": "def-456"}]
        mock_supabase.table.return_value.insert.return_value.execute.return_value = (
            fake_response
        )

        result = manager.save_validated_item(
            intention="found",
            user_id="user2",
            user_email="finder@example.com",
            item_data={
                "item_type": "phone",
                "description": "Black iPhone 15",
                "confidence_score": 0.78,
            },
        )

        mock_supabase.table.assert_called_with("found_items")
        assert result == "def-456"

    def test_save_returns_none_on_failure(self, manager, mock_supabase):
        """When Supabase raises, save should return None (non-blocking)."""
        mock_supabase.table.return_value.insert.return_value.execute.side_effect = (
            Exception("Connection refused")
        )

        result = manager.save_validated_item(
            intention="lost",
            user_id="user1",
            user_email="u@e.com",
            item_data={"item_type": "wallet"},
        )

        assert result is None

    def test_get_lost_items(self, manager, mock_supabase):
        """get_lost_items should query lost_items table."""
        fake_response = MagicMock()
        fake_response.data = [
            {"id": "1", "item_type": "laptop"},
            {"id": "2", "item_type": "phone"},
        ]
        mock_supabase.table.return_value.select.return_value.order.return_value.limit.return_value.eq.return_value.execute.return_value = (
            fake_response
        )

        items = manager.get_lost_items(limit=10)

        mock_supabase.table.assert_called_with("lost_items")
        assert len(items) == 2

    def test_get_found_items(self, manager, mock_supabase):
        """get_found_items should query found_items table."""
        fake_response = MagicMock()
        fake_response.data = [{"id": "3", "item_type": "bag"}]
        mock_supabase.table.return_value.select.return_value.order.return_value.limit.return_value.eq.return_value.execute.return_value = (
            fake_response
        )

        items = manager.get_found_items(limit=5)

        mock_supabase.table.assert_called_with("found_items")
        assert len(items) == 1

    def test_get_item_by_id_returns_item(self, manager, mock_supabase):
        """get_item_by_id should return the matching item dict."""
        fake_response = MagicMock()
        fake_response.data = [{"id": "abc-123", "item_type": "laptop"}]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            fake_response
        )

        item = manager.get_item_by_id("abc-123", intention="lost")

        assert item is not None
        assert item["id"] == "abc-123"

    def test_get_item_by_id_returns_none_when_not_found(self, manager, mock_supabase):
        """get_item_by_id should return None for missing items."""
        fake_response = MagicMock()
        fake_response.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            fake_response
        )

        item = manager.get_item_by_id("nonexistent", intention="found")

        assert item is None


class TestGetSupabaseManager:
    """Tests for the lazy singleton getter."""

    def test_returns_none_when_no_credentials(self):
        """Without env vars, get_supabase_manager should return None."""
        from src.database.supabase_client import get_supabase_manager

        with patch.dict("os.environ", {"SUPABASE_URL": "", "SUPABASE_SERVICE_ROLE_KEY": ""}):
            mgr = get_supabase_manager()
            assert mgr is None

    def test_returns_manager_with_mock_client(self, mock_supabase):
        """With a pre-injected client, get_supabase_manager should succeed."""
        from src.database.supabase_client import get_supabase_manager

        mgr = get_supabase_manager()
        assert mgr is not None
