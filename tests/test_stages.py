import os
import subprocess
from unittest.mock import MagicMock, patch

from libs import constants
from libs.stages import execute_stages


@patch("libs.stages.subprocess.run")
@patch("libs.stages.os.chdir")
def test_execute_stages_success(mock_chdir: MagicMock, mock_run: MagicMock) -> None:
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
def test_execute_stages_fail_continue(
    mock_chdir: MagicMock, mock_run: MagicMock
) -> None:
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
        ["echo", "Building"],
        shell=False,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


@patch("libs.stages.subprocess.run")
@patch("libs.stages.os.chdir")
def test_execute_stages_fail_abort(mock_chdir: MagicMock, mock_run: MagicMock) -> None:
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
    mock_run.assert_called_once_with(
        ["echo", "Building"],
        shell=False,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_execute_stages_empty() -> None:
    result = execute_stages(
        [],
        artifacts_enabled=None,
        continue_if_fail=False,
        logger=MagicMock(),
        disp_output=False,
    )
    assert result is True


@patch("libs.stages.shutil.copy2")
@patch("libs.stages.os.path.isdir")
@patch("libs.stages.subprocess.run")
@patch("libs.stages.os.chdir")
def test_execute_stages_artifact_copy_exception(
    mock_chdir: MagicMock,
    mock_run: MagicMock,
    mock_isdir: MagicMock,
    mock_copy2: MagicMock,
) -> None:
    _ = mock_chdir
    stages = [
        {
            constants.NAME: "Build",
            constants.COMMAND: ['echo "Building"'],
            constants.ARTIFACTS: {
                constants.ENABLED: True,
                constants.PATHS: ["some_artifact.txt"],
                constants.ARCHIVE: False,
                constants.ASSEMBLE: False,
            },
        }
    ]
    mock_run.return_value.returncode = 0
    mock_isdir.return_value = False
    mock_copy2.side_effect = Exception("Copy failed")

    logger = MagicMock()
    result = execute_stages(
        stages,
        artifacts_enabled=None,
        continue_if_fail=False,
        logger=logger,
        disp_output=False,
    )

    assert result is False
    logger.error.assert_called_with(
        "   Error copying artifact some_artifact.txt to 'artifacts': Copy failed"
    )


@patch("libs.stages.subprocess.run")
@patch("libs.stages.os.chdir")
@patch("builtins.open")
def test_execute_stages_save_output(
    mock_open: MagicMock, mock_chdir: MagicMock, mock_run: MagicMock
) -> None:
    _ = mock_chdir
    stages = [{constants.NAME: "Build", constants.COMMAND: ['echo "Building"']}]
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "stdout output"
    mock_run.return_value.stderr = "stderr output"

    result = execute_stages(
        stages,
        artifacts_enabled=None,
        continue_if_fail=False,
        logger=MagicMock(),
        disp_output=False,
        save_output=True,
    )

    assert result is True
    mock_open.assert_called_with(os.path.join("..", constants.LOGS, "Build.txt"), "a")
    mock_open.return_value.__enter__.return_value.write.assert_any_call("stdout output")
    mock_open.return_value.__enter__.return_value.write.assert_any_call("stderr output")


@patch("libs.stages.subprocess.run")
@patch("libs.stages.os.chdir")
@patch("builtins.open")
def test_execute_stages_save_output_fail(
    mock_open: MagicMock, mock_chdir: MagicMock, mock_run: MagicMock
) -> None:
    _ = mock_chdir
    stages = [{constants.NAME: "Build", constants.COMMAND: ['echo "Building"']}]
    mock_run.side_effect = subprocess.CalledProcessError(
        1, "cmd", output="stdout error", stderr="stderr error"
    )

    result = execute_stages(
        stages,
        artifacts_enabled=None,
        continue_if_fail=False,
        logger=MagicMock(),
        disp_output=False,
        save_output=True,
    )

    assert result is False
    mock_open.assert_called_with(os.path.join("..", constants.LOGS, "Build.txt"), "a")
    mock_open.return_value.__enter__.return_value.write.assert_any_call("stdout error")
    mock_open.return_value.__enter__.return_value.write.assert_any_call("stderr error")
