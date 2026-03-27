import pytest
from unittest.mock import patch, mock_open, MagicMock
from libs.config import Config
from libs import constants


@patch("libs.config.yaml.load")
@patch("builtins.open", new_callable=mock_open)
@patch("libs.config.os.path.isfile")
def test_config_initialization(mock_isfile, mock_file, mock_yaml_load):
    mock_isfile.return_value = True

    mock_yaml_load.return_value = {
        constants.GIT_REPOSITORY: "https://github.com/test/test.git",
        constants.STAGES: [
            {constants.NAME: "Test Stage", constants.COMMAND: ['echo "Hello"']}
        ],
    }

    config = Config(MagicMock())

    assert config.config[constants.GIT_REPOSITORY] == "https://github.com/test/test.git"
    assert len(config.config[constants.STAGES]) == 1
    assert config.config[constants.STAGES][0][constants.NAME] == "Test Stage"


@patch("libs.config.os.path.isfile")
def test_config_missing_file(mock_isfile):
    mock_isfile.return_value = False
    mock_logger = MagicMock()

    with pytest.raises(SystemExit) as exc_info:
        Config(mock_logger)

    assert exc_info.value.code == 1
    mock_logger.error.assert_called_with(
        "Config file "
        + constants.CONFILE_FILE_NAME
        + " is missing in the current directory."
    )
