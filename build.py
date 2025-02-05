import os
import sys

from git import Repo

from libs.config import Config
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
    print("BuildAndDeploy version " + BUILD_AND_DEPLOY_VER + '\n')
    print(
        "This tool builds and deploys your project\n"
    )
    print("Usage: build.py <working_directory>\n")
    print("Arguments:")
    print("  <working_directory>  Path to the directory to be used as the working directory.")
    print("  -h, --help           Display this help message and exit.")


######################################
## Beginning of the script build.py ##
######################################

print()

# Check supplied argument is a valid directory
if len(sys.argv) == 2:
    if sys.argv[1] in ("-h", "--help"):
        display_help()
        sys.exit(0)
    working_dir = sys.argv[1]
    if os.path.isdir(working_dir):
        print('Working directory is: ' + working_dir)
    else:
        print('Error: The given path is not a valid directory.')
        sys.exit(-1)
else:
    print("Error: Bad argument supplied")
    sys.exit(-1)

# Go inside working directory
os.chdir(working_dir)

# Get build configuration
build_config = Config()

# Clone Git repository
if not os.path.isdir('git'):
    os.mkdir('git')
    print('Cloning repository ' + build_config.global_config['git_repository'].split('/')[-1] + '...')
    git_repo = Repo.clone_from(build_config.global_config['git_repository'], 'git')
else:
    print('Git repository already exists. Skipping clone.')
    git_repo = Repo('git')
    # Check if existing repository matches the configured one
    if git_repo.remotes.origin.url != build_config.global_config['git_repository']:
        print('Error: Existing repository does not match the configured one.')
        sys.exit(-1)
    else:
        print('Updating repository ' + git_repo.remotes.origin.url + '...')
        git_repo.remotes.origin.fetch()
        git_repo.git.reset('--hard', 'origin/master')
        git_repo.remotes.origin.pull()

# Create artifacts directory
if os.path.isdir('artifacts'):
    for root, dirs, files in os.walk('artifacts', topdown=False):
        for file in files:
            os.remove(os.path.join(root, file))
        for directory in dirs:
            os.rmdir(os.path.join(root, directory))
    os.rmdir('artifacts')
os.mkdir('artifacts')

# Execute build stages
result = execute_stages(build_config.stages, build_config.global_config['display_pipeline_output'])
print('\n' + result[1])
