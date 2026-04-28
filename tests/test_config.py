from unittest.mock import MagicMock, mock_open, patch

import pytest

from libs import constants
from libs.config import Config


@patch("libs.config.yaml.load")
@patch("builtins.open", new_callable=mock_open)
@patch("libs.config.os.path.isfile")
def test_config_initialization(
    mock_isfile: MagicMock, mock_file: MagicMock, mock_yaml_load: MagicMock
) -> None:
    _ = mock_file
    mock_isfile.return_value = True

    mock_yaml_load.return_value = {
        constants.GIT_REPOSITORY: "https://github.com/test/test.git",
        constants.STAGES: [
            {constants.NAME: "Test Stage", constants.COMMAND: ['echo "Hello"']}
        ],
    }

    config = Config(MagicMock())

    assert (
        str(config.config[constants.GIT_REPOSITORY])
        == "https://github.com/test/test.git"
    )
    assert len(list(config.config[constants.STAGES])) == 1
    assert str(config.config[constants.STAGES][0][constants.NAME]) == "Test Stage"


@patch("libs.config.os.path.isfile")
def test_config_missing_file(mock_isfile: MagicMock) -> None:
    mock_isfile.return_value = False
    mock_logger = MagicMock()

    with pytest.raises(SystemExit) as exc_info:
        _ = Config(mock_logger)

    assert exc_info.value.code == 1
    mock_logger.error.assert_called_with(
        "Config file "
        + constants.CONFILE_FILE_NAME
        + " is missing in the current directory."
    )


@patch("libs.config.yaml.load")
@patch("builtins.open", new_callable=mock_open)
@patch("libs.config.os.path.isfile")
def test_config_missing_mandatory_param(
    mock_isfile: MagicMock, mock_file: MagicMock, mock_yaml_load: MagicMock
) -> None:
    _ = mock_file
    mock_isfile.return_value = True

    mock_yaml_load.return_value = {
        constants.STAGES: [
            {constants.NAME: "Test Stage", constants.COMMAND: ['echo "Hello"']}
        ],
    }

    with pytest.raises(SystemExit) as exc_info:
        _ = Config(MagicMock())

    assert exc_info.value.code == 1
