import os
import sys

import yaml
from git import Repo

from build.stages import execute_stages
from version import BUILD_AND_DEPLOY_VER


def display_help():
    """
    Display the usage instructions for the build script.

    This function prints a help message outlining the purpose of the script,
    the expected arguments, and their descriptions. It is displayed when
    the user supplies `-h` or `--help` as an argument.
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

# Check if config.yaml exists in the current directory
if os.path.isfile("config.yaml"):
    print('Config file "config.yaml" found in the current directory.')
else:
    print('Error: Config file "config.yaml" is missing in the current directory.')
    sys.exit(-1)

# Open YAML file
build_config = yaml.load(open("config.yaml"), Loader=yaml.SafeLoader)

# Clone Git repository
if not os.path.isdir('git'):
    os.mkdir('git')
    print('Cloning repository ' + build_config['git_repository'].split('/')[-1] + '...')
    Repo.clone_from(build_config['git_repository'], 'git')
else:
    print('Repository already exists. Skipping clone.')

# Execute build stages
result = execute_stages(build_config['stages'], build_config['display_pipeline_output'])
print('\n' + result[1])
