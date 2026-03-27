from git import Repo

from libs import constants


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
    """
    return Repo.clone_from(config[constants.GIT_REPOSITORY], constants.GIT)


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
