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


def _replace_param_by_env_var_in_str(base_str: str, env_vars: dict):
    """
    Replace placeholders in a string with corresponding environment variable values.

    This function checks if a given string contains placeholders for environment
    variables in the format "${VAR_NAME}". If such a placeholder is found, it replaces
    it with the value of the corresponding key from the provided dictionary of
    environment variables. If the environment variable is not found in the dictionary,
    an error is printed, and the program terminates with a non-zero exit code.

    :param base_str: Input string that may contain environment variable placeholders in the
        format "${VAR_NAME}". If no placeholder is detected, the original string is
        returned unchanged.
    :type base_str: str
    :param env_vars: Dictionary of environment variables, where the keys represent variable
        names and values represent the corresponding environment variable's value.
        Used to resolve the placeholders in the input string.
    :type env_vars: dict
    :return: The input string with placeholders replaced by their corresponding environment
        variable values if any placeholders are present; the original string otherwise.
    :rtype: str

    :raises SystemExit: If a placeholder's referenced environment variable is not found
        in the dictionary, the program terminates and prints an error message to stderr.
    """
    if '$' in base_str:
        env_var = base_str.split('{')[1].split('}')[0]
        if env_var in env_vars:
            return base_str.replace('${' + env_var + '}', env_vars[env_var])
        else:
            print('Error: Environment variable "' + env_var + '" is not defined.')
            sys.exit(-1)
    else:
        return base_str


def _replace_param_by_env_var_in_dict(base_config: dict[str, any], env_vars: dict):
    """
    Replaces parameters in a dictionary with environment variable values if applicable.

    This function iterates through a given configuration dictionary and checks if any
    string-type value can be replaced by a corresponding value from the provided
    environment variables dictionary. If the value is not a string or no replacement
    is required, it retains the original value. The resulting updated dictionary
    is returned.

    :param base_config: The base configuration dictionary whose values may need
        replacement with environment variable values.
    :type base_config: dict[str, any]
    :param env_vars: A dictionary of environment variables used for potential
        replacement of values in the base configuration.
    :type env_vars: dict
    :return: A new dictionary with updated values, where applicable, by replacing
        the relevant strings with the corresponding environment variable values.
    :rtype: dict
    """
    config = {}
    for key in base_config:
        if isinstance(base_config[key], str):
            config[key] = _replace_param_by_env_var_in_str(base_config[key], env_vars)
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
    _GLOBAL_CONFIGURATION_PARAMS = [(_GIT_REPOSITORY_MARKER, True), ('display_pipeline_output', False, False),
                                    ('generate_artifacts', False, False), ('disable_artifacts', False, False)]
    _STAGES_CONFIGURATION_PARAMS = [('name', True), ('command', True)]
    _ARTIFACTS_CONFIGURATION_PARAMS = [('name', False), ('archive', False, False), ('assemble', False, False),
                                       ('enabled', False, True)]

    def __init__(self):
        """
        Initializes the configuration for a project based on the provided YAML configuration
        file, environment variables, and optional templates. The class processes global
        parameters, stage configurations, and artifact paths, ensuring all mandatory
        fields are provided and supporting replacement of parameters using environment
        variables.

        Raises an error and exits the program if critical configurations or files are
        missing. Supports the use of pre-defined templates to replace large sections of
        the configuration.

        Raises
        ------
        SystemExit
            If the configuration file or required parameters are missing, or if templates
            or artifacts are misconfigured.
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

        # Replace local configuration with template, except for git repository and artifacts generation
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
        self.global_config = _replace_param_by_env_var_in_dict(self.global_config, self.env_vars)

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

                # Check stage configuration and environment variables replacement
                stage_config = _check_params_in_config(self._STAGES_CONFIGURATION_PARAMS, stage)
                stage_config = _replace_param_by_env_var_in_dict(stage_config, self.env_vars)

                if 'artifacts' in stage:
                    # Get artifacts configuration and environment variables replacement
                    stage_config['artifacts'] = _check_params_in_config(self._ARTIFACTS_CONFIGURATION_PARAMS,
                                                                        stage['artifacts'])
                    stage_config['artifacts'] = _replace_param_by_env_var_in_dict(stage_config['artifacts'],
                                                                                  self.env_vars)

                    # Get paths for artifacts
                    if 'paths' in stage['artifacts']:
                        stage_config['artifacts']['paths'] = []
                        for path in stage['artifacts']['paths']:
                            stage_config['artifacts']['paths'].append(
                                _replace_param_by_env_var_in_str(path, self.env_vars))
                    else:
                        print('Error: Artifacts configuration doesn\'t contain the mandatory parameter "paths".')
                        sys.exit(-1)

                self.stages.append(stage_config)
        else:
            print('Error: Config file "config.yaml" doesn\'t contain the mandatory parameter "stages".')
            sys.exit(-1)
