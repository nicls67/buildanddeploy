import re
from urllib.parse import urlparse

from git import Repo

from libs import constants


def is_valid_git_url(url: str) -> bool:
    """
    Validates a Git repository URL to prevent argument injection and SSRF.
    
    :param url: The Git repository URL to validate.
    :type url: str
    :return: True if the URL is valid and safe, False otherwise.
    :rtype: bool
    """
    if not isinstance(url, str):
        return False

    url = url.strip()
    if url.startswith("-"):
        return False

    if re.search(r"\s", url):
        return False

    parsed = urlparse(url)
    allowed_schemes = {"http", "https", "git", "ssh"}

    if parsed.scheme in allowed_schemes:
        return True

    # Check for SCP-like syntax (e.g. git@github.com:user/repo.git)
    # Ensure it's not a local file path or an ext:: command
    scp_pattern = re.compile(r"^([a-zA-Z0-9_.\-]+@)?[a-zA-Z0-9_.\-]+:/?.*$")

    # Explicitly block known dangerous schemes parsed as such if scp matches
    if parsed.scheme in {"file", "ext"}:
        return False

    if scp_pattern.match(url):
        return True

    return False


def clone_repo(config):
    """
    Clones a remote repository to a specified directory using the provided configuration.

    :param config: A dictionary containing configuration details, including
        the repository URL and target directory path as keys. This
        parameter is expected to include essential information required
        for cloning the repository.
    :type config: dict
    :return: The cloned repository object after a successful clone operation.
    :rtype: Repo
    :raises git.exc.GitCommandError: If cloning the repository fails.
    :raises ValueError: If the configured repository URL is invalid or unsafe.
    """
    repo_url = config[constants.GIT_REPOSITORY]
    if not is_valid_git_url(repo_url):
        raise ValueError(f"Invalid or unsafe Git repository URL: {repo_url}")

    return Repo.clone_from(repo_url, constants.GIT)


def update_repo(repo, config):
    """
    Updates a local Git repository to match the desired state specified in the
    configuration. The update can be based on a specific commit, tag, or branch,
    as detailed in the configuration parameter.

    :param repo: The local repository instance to be updated
    :type repo: Repo
    :param config: A dictionary containing configuration values that specify
        the desired state for the repository. May include:
        - constants.GIT_COMMIT: A specific commit hash to checkout.
        - constants.GIT_TAG: A specific tag to checkout.
        - constants.GIT_BRANCH: A branch to checkout. If the branch does not
          exist locally, it will be created tracking the remote branch.
    :type config: dict
    :return: None
    :raises git.exc.GitCommandError: If updating the repository fails.
    """
    repo.remotes.origin.fetch()

    # Discard all local changes
    repo.git.reset("--hard")

    # Determine which reference to update to based on configuration
    if constants.GIT_COMMIT in config and config[constants.GIT_COMMIT]:
        # If a specific commit is specified, checkout that commit
        repo.git.checkout(config[constants.GIT_COMMIT])
    elif constants.GIT_TAG in config and config[constants.GIT_TAG]:
        # If a specific tag is specified, checkout that tag
        repo.git.checkout(config[constants.GIT_TAG])
    else:
        # Otherwise, use the configured branch
        branch_name = config[constants.GIT_BRANCH]

        # Check if a local branch exists
        local_branch_exists = branch_name in (
            ref.name.split("/")[-1] for ref in repo.heads
        )

        if not local_branch_exists:
            # Create a new local branch that tracks the remote branch
            repo.git.checkout("-b", branch_name, "origin/" + branch_name)
        else:
            # Checkout the existing local branch
            repo.git.checkout(branch_name)

        # Pull the latest changes
        repo.remotes.origin.pull()
