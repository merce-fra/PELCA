import pytest

from app.main_window import MainWindow


@pytest.fixture
def app(qtbot):
    main_window = MainWindow()
    qtbot.addWidget(main_window)
    return main_window


def test_main_window_initialization(app):
    assert app.windowTitle() == "PELCA"
    assert app.geometry().width() == 600
    assert app.geometry().height() == 800
    assert app.file_path_edit is None
    assert app.console_text is None
    assert app.is_running is False


def test_main_window_ui_setup(app):
    assert app.centralWidget() is not None
    assert app.header is not None
    assert app.script_widget is not None
