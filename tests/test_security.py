# pyright: reportAny=false, reportExplicitAny=false
from unittest.mock import MagicMock, patch

from libs import constants
from libs.stages import execute_stages


@patch("libs.stages.subprocess.run")
@patch("libs.stages.os.chdir")
def test_shell_false_usage(mock_chdir: MagicMock, mock_run: MagicMock) -> None:
    _ = mock_chdir
    # This test verifies that shell=False is used and command is tokenized
    stages = [{constants.NAME: "SecurityTest", constants.COMMAND: ['echo "Hello; ls"']}]
    mock_run.return_value.returncode = 0  # type: ignore

    _ = execute_stages(
        stages,
        artifacts_enabled=None,
        continue_if_fail=False,
        logger=MagicMock(),
        disp_output=False,
    )

    # Verify that it is now using shell=False
    args, kwargs = mock_run.call_args  # type: ignore
    assert kwargs.get("shell") is False  # type: ignore
    assert args[0] == ["echo", "Hello; ls"]
