import os
import sys

import yaml


def _check_params_in_config(params, base_config):
    """
    Checks the presence and validity of required parameters in a given configuration, and
    populates a new configuration dictionary based on the default values and mandatory
    status of the parameters.

    This function ensures that all necessary parameters are present in the provided
    base configuration. If a mandatory parameter is missing, it terminates the program.

    :param params: A list of tuples containing parameter information. Each tuple should
        include the parameter name (str), a boolean indicating if the parameter is
        mandatory, and a default value for optional parameters.
    :param base_config: A dictionary representing the base configuration where parameter
        values will be fetched if they exist.

    :return: A dictionary containing the keys and values of the updated configuration.
    """
    config = {}
    for param in params:
        # Parameter exists in config
        if param[0] in base_config:
            config[param[0]] = base_config[param[0]]
        # Parameter doesn't exist but is mandatory
        elif param[1]:
            print('Error: Config file "config.yaml" doesn\'t contain the mandatory parameter "' + param[0] + '".')
            sys.exit(-1)
        # Parameter doesn't exist and is not mandatory and a default value exists
        elif len(param) > 2:
            config[param[0]] = param[2]

    return config


def _replace_param_by_env_var(base_config: dict[str, any], env_vars: dict):
    """
    Replace placeholders in the base configuration dictionary with corresponding environment
    variables from the provided dictionary. The placeholders in the base configuration must
    follow the format `${ENV_VAR_NAME}`. If an environment variable referenced in the base
    configuration is not found in the `env_vars` dictionary, the program will print an
    error message and terminate.

    :param base_config: A dictionary representing the base configuration, with values
        containing placeholders for environment variables in the format `${ENV_VAR_NAME}`.
    :type base_config: dict[str, any]
    :param env_vars: A dictionary containing the mappings of environment variable names
        (keys) to their respective values (strings).
    :type env_vars: dict

    :return: A dictionary where placeholders in the base configuration keys are replaced
        with actual values from the environment variables dictionary.
    :rtype: dict
    """
    config = {}
    for key in base_config:
        if isinstance(base_config[key], str) and '$' in base_config[key]:
            env_var = base_config[key].split('{')[1].split('}')[0]
            if env_var in env_vars:
                config[key] = base_config[key].replace('${' + env_var + '}', env_vars[env_var])
            else:
                print('Error: Environment variable "' + env_var + '" is not defined.')
                sys.exit(-1)
        else:
            config[key] = base_config[key]
    return config


_USE_TEMPLATE_MARKER = 'use_template'
_GIT_REPOSITORY_MARKER = 'git_repository'


class Config:
    """
    Handles the loading and validation of configuration from a YAML file.

    This class is responsible for ensuring that configuration parameters
    are correctly specified in a `config.yaml` file existing in the current
    directory. It verifies both global configuration parameters and per-stage
    configuration parameters. If any required parameter is missing or
    misconfigured, the program exits with an error. The class loads the configuration
    details into attributes for further use within the program.

    :ivar global_config (`dict`): A dictionary containing validated global configuration
              parameters loaded from the `config.yaml` file.
    :ivar stages (`list`): A list of dictionaries for each stage, with their configuration
              parameters validated against mandatory requirements.
    """
    _GLOBAL_CONFIGURATION_PARAMS = [(_GIT_REPOSITORY_MARKER, True), ('display_pipeline_output', False, False)]
    _STAGES_CONFIGURATION_PARAMS = [('name', True), ('command', True)]
    _ARTIFACTS_CONFIGURATION_PARAMS = [('name', False), ('archive', False, False), ('assemble', False, False)]

    def __init__(self):
        """
        Represents the configuration loader class which initializes and processes configuration
        from a `config.yaml` file. If templates are used for global or stage-specific configuration,
        the templates are prioritized and processed. This class ensures all necessary parameters
        are validated and detected in the configuration.

        Raises:
            SystemExit: If the `config.yaml` configuration file is missing, lacks required parameters,
            or specific templates are unavailable, the program terminates with an error.

        """
        # Check if config.yaml exists in the current directory
        self.stages = None
        if os.path.isfile("config.yaml"):
            print('Config file "config.yaml" found in the current directory.')
        else:
            print('Error: Config file "config.yaml" is missing in the current directory.')
            sys.exit(-1)

        # Load configuration from YAML file
        base_config = yaml.load(open("config.yaml"), Loader=yaml.SafeLoader)

        # Retrieve environment variables
        if 'project_vars' in base_config and base_config['project_vars']:
            print('Retrieving environment variables...')
            self.env_vars = {}
            for var in base_config['project_vars']:
                # Check only one key is defined for each environment variable
                if len(var.keys()) != 1:
                    print('Error: Each item in "project_vars" must contain exactly one key.')
                    sys.exit(-1)
                key, value = var.popitem()
                self.env_vars[key] = value
        else:
            print('No environment variables to retrieve.')

        # If a template shall be used, do not analyse remaining parameters
        # Replace local configuration with template, only git repository is added from local config
        if _USE_TEMPLATE_MARKER in base_config:
            template_file = base_config[_USE_TEMPLATE_MARKER]
            template_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'templates')
            template_full_file = os.path.join(template_dir, template_file + '.yaml')
            if os.path.isfile(template_full_file):
                print('Using template "' + template_file + '" for global configuration.')
                # Get Git repo from local config
                if _GIT_REPOSITORY_MARKER in base_config:
                    git_repo = base_config[_GIT_REPOSITORY_MARKER]
                else:
                    print(
                        'Error: Config file "config.yaml" doesn\'t contain the mandatory parameter "' + _GIT_REPOSITORY_MARKER + '".')
                    sys.exit(-1)

                # Replace local config with template
                base_config = yaml.load(open(template_full_file), Loader=yaml.SafeLoader)
                base_config[_GIT_REPOSITORY_MARKER] = git_repo

        # Analyse global configuration : check for each existing parameter if it is configured
        self.global_config = _check_params_in_config(self._GLOBAL_CONFIGURATION_PARAMS, base_config)
        # Environment variables replacement
        self.global_config = _replace_param_by_env_var(self.global_config, self.env_vars)

        # Analyse stages configuration
        if 'stages' in base_config:
            self.stages = []
            for stage in base_config['stages']:
                # If a template shall be used, do not analyse remaining parameters
                # Replace local configuration with template
                if _USE_TEMPLATE_MARKER in stage:
                    template_file = stage[_USE_TEMPLATE_MARKER]
                    template_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'templates')
                    template_full_file = os.path.join(template_dir, template_file + '.yaml')
                    if os.path.isfile(template_full_file):
                        print('Using template "' + template_file + '" for stage')

                        # Open template file and replace local configuration
                        stage = yaml.load(open(template_full_file), Loader=yaml.SafeLoader)
                    else:
                        print('Error: Template "' + template_file + '" doesn\'t exist in the templates directory.')
                        sys.exit(-1)

                # Check stage configuration
                stage_config = _check_params_in_config(self._STAGES_CONFIGURATION_PARAMS, stage)
                stage_config = _replace_param_by_env_var(stage_config, self.env_vars)
                if 'artifacts' in stage:
                    # Get artifacts configuration
                    stage_config['artifacts'] = _check_params_in_config(self._ARTIFACTS_CONFIGURATION_PARAMS,
                                                                        stage['artifacts'])
                    stage_config['artifacts'] = _replace_param_by_env_var(stage_config['artifacts'], self.env_vars)

                    # Get paths for artifacts
                    if 'paths' in stage['artifacts']:
                        stage_config['artifacts']['paths'] = []
                        for path in stage['artifacts']['paths']:
                            stage_config['artifacts']['paths'].append(path)
                    else:
                        print('Error: Artifacts configuration doesn\'t contain the mandatory parameter "paths".')
                        sys.exit(-1)

                self.stages.append(stage_config)
        else:
            print('Error: Config file "config.yaml" doesn\'t contain the mandatory parameter "stages".')
            sys.exit(-1)
