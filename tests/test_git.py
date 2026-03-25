from unittest.mock import patch, MagicMock
from libs.git import clone_repo, update_repo
from libs import constants


@patch("libs.git.Repo.clone_from")
def test_clone_repo(mock_clone_from):
    config = {constants.GIT_REPOSITORY: "https://example.com/repo.git"}
    mock_repo = MagicMock()
    mock_clone_from.return_value = mock_repo

    repo = clone_repo(config)

    mock_clone_from.assert_called_once_with(
        "https://example.com/repo.git", constants.GIT
    )
    assert repo == mock_repo


def test_update_repo_with_commit():
    config = {constants.GIT_COMMIT: "abcdef1234567890"}
    mock_repo = MagicMock()
    mock_repo.heads = []

    update_repo(mock_repo, config)

    mock_repo.remotes.origin.fetch.assert_called_once()
    mock_repo.git.reset.assert_called_once_with("--hard")
    mock_repo.git.checkout.assert_called_with("abcdef1234567890")


def test_update_repo_with_branch():
    config = {constants.GIT_BRANCH: "develop"}
    mock_repo = MagicMock()
    mock_ref = MagicMock()
    mock_ref.name = "origin/develop"
    mock_repo.heads = [mock_ref]

    update_repo(mock_repo, config)

    mock_repo.remotes.origin.fetch.assert_called_once()
    mock_repo.git.reset.assert_called_once_with("--hard")
    mock_repo.git.checkout.assert_any_call("develop")
    mock_repo.remotes.origin.pull.assert_called_once()
