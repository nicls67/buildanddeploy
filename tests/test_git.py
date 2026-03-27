import pytest
from unittest.mock import patch, MagicMock
from libs.git import clone_repo, update_repo, is_valid_git_url
from libs import constants


def test_is_valid_git_url_valid():
    valid_urls = [
        "https://github.com/user/repo.git",
        "http://github.com/user/repo.git",
        "git://github.com/user/repo.git",
        "ssh://git@github.com/user/repo.git",
        "git@github.com:user/repo.git",
        "user@server:project.git",
        "server:project.git",
    ]
    for url in valid_urls:
        assert is_valid_git_url(url) is True


def test_is_valid_git_url_invalid():
    invalid_urls = [
        "-c core.askpass=echo",
        "--upload-pack=touch /tmp/pwned",
        "https://github.com/user/repo.git --upload-pack=pwned",
        "ssh://git@github.com/user/repo.git -o ProxyCommand='sh -c touch /tmp/pwned'",
        "file:///tmp/repo",
        "ext::sh -c 'touch /tmp/pwned'",
        "/local/path/to/repo",
        12345,
        None,
    ]
    for url in invalid_urls:
        assert is_valid_git_url(url) is False


@patch("libs.git.Repo.clone_from")
def test_clone_repo_valid_url(mock_clone_from):
    config = {constants.GIT_REPOSITORY: "https://example.com/repo.git"}
    mock_repo = MagicMock()
    mock_clone_from.return_value = mock_repo

    repo = clone_repo(config)

    mock_clone_from.assert_called_once_with(
        "https://example.com/repo.git", constants.GIT
    )
    assert repo == mock_repo


@patch("libs.git.Repo.clone_from")
def test_clone_repo_invalid_url(mock_clone_from):
    config = {constants.GIT_REPOSITORY: "--upload-pack=touch /tmp/pwned"}

    with pytest.raises(ValueError) as excinfo:
        clone_repo(config)

    assert "Invalid or unsafe Git repository URL" in str(excinfo.value)
    mock_clone_from.assert_not_called()


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
