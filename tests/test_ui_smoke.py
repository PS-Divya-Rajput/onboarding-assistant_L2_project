"""UI smoke tests using Streamlit AppTest framework.

Asserts:
- No unhandled exceptions during boot and rerun.
- Exactly 3 sample users in the persona selector.
- Exactly 3 navigation tabs present (Ask, Path, Question log).
- Navigation switching between tabs without runtime errors.
"""

from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest


def test_ui_smoke_boot_and_components():
    """Verify application boots cleanly without exceptions and exposes required selectors."""
    app_file = str(Path(__file__).resolve().parent.parent / "app.py")
    at = AppTest.from_file(app_file, default_timeout=30)
    at.run()

    # 1. Assert no runtime exceptions
    assert len(at.exception) == 0, f"AppTest threw exceptions: {at.exception}"

    # 2. Assert three users in the selector
    assert len(at.selectbox) >= 1
    user_options = at.selectbox[0].options
    assert len(user_options) == 3

    # 3. Assert four tabs present (Ask, Path, Lead oversight, Question log)
    assert len(at.radio) >= 1
    tab_options = at.radio[0].options
    assert tab_options == ["Ask", "Path", "Lead oversight", "Question log"]


def test_ui_tab_navigation():
    """Verify switching between tabs renders corresponding views without crashing."""
    app_file = str(Path(__file__).resolve().parent.parent / "app.py")
    at = AppTest.from_file(app_file, default_timeout=30)
    at.run()

    # Switch to "Path" tab
    at.radio[0].set_value("Path").run()
    assert len(at.exception) == 0

    # Switch to "Lead oversight" tab
    at.radio[0].set_value("Lead oversight").run()
    assert len(at.exception) == 0

    # Switch to "Question log" tab
    at.radio[0].set_value("Question log").run()
    assert len(at.exception) == 0

    # Switch back to "Ask" tab
    at.radio[0].set_value("Ask").run()
    assert len(at.exception) == 0

