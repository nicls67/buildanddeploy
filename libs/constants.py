GIT = "git"
LOGS = "logs"
CONFILE_FILE_NAME = "config.yaml"
TEMPLATES_DIR = "templates"

# Constants for YAML configuration
USE_TEMPLATE = "use_template"
GIT_REPOSITORY = "git_repository"
GIT_BRANCH = "git_branch"
GIT_TAG = "git_tag"
GIT_COMMIT = "git_commit"
PROJECT_VARS = "project_vars"
ARTIFACTS = "artifacts"
GENERATE_ARTIFACTS = "generate_artifacts"
DISABLE_ARTIFACTS = "disable_artifacts"
CONTINUE_ON_FAILURE = "continue_on_failure"
DISPLAY_PIPELINE_OUTPUT = "display_pipeline_output"
SAVE_PIPELINE_OUTPUT = "save_pipeline_output"
COMMAND = "commands"
NAME = "name"
ENABLED = "enabled"
PATHS = "paths"
ARCHIVE = "archive"
ASSEMBLE = "assemble"
STAGES = "stages"

CONFIGURATION_PARAMS = {
    GIT_REPOSITORY: {
        "mandatory": True,
    },
    GIT_BRANCH: {
        "mandatory": False,
        "default": "master",
    },
    GIT_TAG: {
        "mandatory": False,
    },
    GIT_COMMIT: {
        "mandatory": False,
    },
    DISPLAY_PIPELINE_OUTPUT: {
        "mandatory": False,
        "default": False,
    },
    SAVE_PIPELINE_OUTPUT: {
        "mandatory": False,
        "default": True,
    },
    GENERATE_ARTIFACTS: {
        "mandatory": False,
        "default": False,
    },
    DISABLE_ARTIFACTS: {
        "mandatory": False,
        "default": False,
    },
    CONTINUE_ON_FAILURE: {
        "mandatory": False,
        "default": False,
    },
    STAGES: {
        "mandatory": True,
        "vectored": True,
        "sub_params": {
            NAME: {
                "mandatory": True,
            },
            COMMAND: {
                "mandatory": True,
                "vectored": True,
            },
            ARTIFACTS: {
                "mandatory": False,
                "sub_params": {
                    NAME: {
                        "mandatory": False,
                    },
                    ARCHIVE: {
                        "mandatory": False,
                        "default": False,
                    },
                    ASSEMBLE: {
                        "mandatory": False,
                        "default": False,
                    },
                    ENABLED: {
                        "mandatory": False,
                        "default": True,
                    },
                    PATHS: {
                        "mandatory": True,
                        "vectored": True,
                    },
                },
            },
        },
    },
}
