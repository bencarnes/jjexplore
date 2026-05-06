from src import config


def test_window_dimensions_are_positive():
    assert config.WINDOW_WIDTH > 0
    assert config.WINDOW_HEIGHT > 0


def test_target_fps_is_positive():
    assert config.TARGET_FPS > 0


def test_window_title_is_nonempty_string():
    assert isinstance(config.WINDOW_TITLE, str)
    assert config.WINDOW_TITLE.strip() != ""


def test_project_directories_exist():
    assert config.PROJECT_ROOT.is_dir()
    assert config.ASSETS_DIR.is_dir()
    assert config.MAPS_DIR.is_dir()
