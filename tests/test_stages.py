import subprocess
from unittest.mock import patch, MagicMock
from libs.stages import execute_stages
from libs import constants


@patch("libs.stages.subprocess.run")
@patch("libs.stages.os.chdir")
def test_execute_stages_success(mock_chdir, mock_run):
    stages = [{constants.NAME: "Build", constants.COMMAND: ['echo "Building"']}]
    mock_run.return_value.returncode = 0

    result = execute_stages(
        stages,
        artifacts_enabled=None,
        continue_if_fail=False,
        logger=MagicMock(),
        disp_output=False,
    )

    assert result is True
    mock_chdir.assert_called_once_with(constants.GIT)
    mock_run.assert_called_once_with(
        ["echo", "Building"],
        shell=False,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


@patch("libs.stages.subprocess.run")
@patch("libs.stages.os.chdir")
def test_execute_stages_fail_continue(mock_chdir, mock_run):
    stages = [{constants.NAME: "Build", constants.COMMAND: ['echo "Building"']}]
    mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="Error msg")

    result = execute_stages(
        stages,
        artifacts_enabled=None,
        continue_if_fail=True,
        logger=MagicMock(),
        disp_output=False,
    )

    assert result is True
    mock_chdir.assert_called_once_with(constants.GIT)
    mock_run.assert_called_once_with(
        'echo "Building"',
        shell=True,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


@patch("libs.stages.subprocess.run")
@patch("libs.stages.os.chdir")
def test_execute_stages_fail_abort(mock_chdir, mock_run):
    stages = [{constants.NAME: "Build", constants.COMMAND: ['echo "Building"']}]
    mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="Error msg")

    result = execute_stages(
        stages,
        artifacts_enabled=None,
        continue_if_fail=False,
        logger=MagicMock(),
        disp_output=False,
    )

    assert result is False
    mock_chdir.assert_called_once_with(constants.GIT)


def test_execute_stages_empty():
    result = execute_stages(
        [],
        artifacts_enabled=None,
        continue_if_fail=False,
        logger=MagicMock(),
        disp_output=False,
    )
    assert result is True
