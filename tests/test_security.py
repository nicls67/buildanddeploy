import subprocess
from unittest.mock import patch, MagicMock
from libs.stages import execute_stages
from libs import constants

@patch("libs.stages.subprocess.run")
@patch("libs.stages.os.chdir")
def test_shell_false_usage(mock_chdir, mock_run):
    # This test verifies that shell=False is used and command is tokenized
    stages = [{constants.NAME: "SecurityTest", constants.COMMAND: ['echo "Hello; ls"']}]
    mock_run.return_value.returncode = 0

    execute_stages(
        stages,
        artifacts_enabled=None,
        continue_if_fail=False,
        logger=MagicMock(),
        disp_output=False,
    )

    # Verify that it is now using shell=False
    args, kwargs = mock_run.call_args
    assert kwargs.get("shell") is False
    assert args[0] == ["echo", "Hello; ls"]
