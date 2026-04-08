import os
import shutil
import sys

from git import GitCommandError, InvalidGitRepositoryError, Repo

import libs.constants as constants
from libs.config import Config
from libs.git import clone_repo, update_repo
from libs.logging import configure_logging
from libs.stages import execute_stages
from version import BUILD_AND_DEPLOY_VER


def display_help():
    """
    Displays help information for the BuildAndDeploy tool.

    This function provides functionality to output instructions on how to use
    the BuildAndDeploy tool, including its version, purpose, usage, and supported
    arguments. It is designed to assist users by providing a detailed explanation
    of the tool's utility and its required or optional arguments.

    :rtype: None
    :return: Does not return any value.
    """
    print("BuildAndDeploy version " + BUILD_AND_DEPLOY_VER + "\n")
    print("This tool builds and deploys your project\n")
    print("Usage: build.py <working_directory>\n")
    print("Arguments:")
    print(
        "  <working_directory>  Path to the directory to be used as the working directory."
    )
    print("  -h, --help           Display this help message and exit.")


######################################
## Beginning of the script build.py ##
######################################

# Check the supplied arguments
if len(sys.argv) == 2:
    if sys.argv[1] in ("-h", "--help"):
        display_help()
        sys.exit(0)
    working_dir = sys.argv[1]
    if not os.path.isdir(working_dir):
        print("Error: The given path is not a valid directory.")
        sys.exit(1)
else:
    print("Error: Bad argument supplied")
    sys.exit(1)

# Create logger
logger = configure_logging(working_dir)

logger.info("Working directory is set to: " + working_dir)
logger.info("")

# Go inside the working directory
os.chdir(working_dir)

# Get build configuration
build_config = Config(logger)

# Clone Git repository
if not os.path.isdir(constants.GIT):
    os.makedirs(constants.GIT, exist_ok=True)
    logger.info(
        "Cloning repository "
        + build_config.config[constants.GIT_REPOSITORY].split("/")[-1]
        + "..."
    )

    try:
        git_repo = clone_repo(build_config.config)
    except GitCommandError as e:
        logger.error(f"Error cloning repository: {e}")
        sys.exit(1)
else:
    logger.info("Git repository already exists. Skipping clone.")
    try:
        git_repo = Repo(constants.GIT)
    except InvalidGitRepositoryError as e:
        logger.error(f"Error opening Git repository: {e}")
        logger.info("Deleting existing Git repository and trying to clone again...")
        shutil.rmtree(constants.GIT)
        try:
            git_repo = clone_repo(build_config.config)
        except GitCommandError as e:
            logger.error(f"Error cloning repository: {e}")
            sys.exit(1)

    # Check if the existing repository matches the configured one
    if git_repo.remotes.origin.url != build_config.config[constants.GIT_REPOSITORY]:
        logger.error("Existing repository does not match the configured one.")
        sys.exit(1)

# Update Git repository
logger.info("Updating repository " + git_repo.remotes.origin.url)
update_repo(git_repo, build_config.config)

# Create artifacts directory
if os.path.isdir(constants.ARTIFACTS):
    shutil.rmtree(constants.ARTIFACTS)
os.mkdir(constants.ARTIFACTS)

# Check global artifacts activation
enable_artifacts: bool | None = None
if build_config.config[constants.GENERATE_ARTIFACTS]:
    enable_artifacts = True
elif build_config.config[constants.DISABLE_ARTIFACTS]:
    enable_artifacts = False

# Execute build stages
result = execute_stages(
    build_config.config[constants.STAGES],
    enable_artifacts,
    build_config.config[constants.CONTINUE_ON_FAILURE],
    logger,
    build_config.config[constants.DISPLAY_PIPELINE_OUTPUT],
    build_config.config[constants.SAVE_PIPELINE_OUTPUT],
)

# Logging
logger.info("")
if result:
    logger.info("Build successful")
else:
    logger.error("Build failed")

# Exit script
sys.exit(0 if result else 1)
