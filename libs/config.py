import os
import sys
from logging import Logger

import yaml

import libs.constants as constants


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

    def __init__(self, logger: Logger):
        """
        Initializes an instance by validating and loading configuration using a YAML file. Configuration
        includes environment variables, global parameters, and stage-specific settings. Supports the ability
        to use templates for both global and stage-specific configurations. Raises errors and exits the
        application if mandatory parameters or configuration files are missing or improperly structured.

        :param logger: Logger instance used for logging diagnostic and error information.
        :type logger: Logger

        :raises SystemExit: Exits with non-zero status if critical configuration files or mandatory
                            parameters are missing. Additionally, exits if improperly structured
                            environment variables or templates are encountered.
        """
        self._logger = logger

        # Check if config.yaml exists in the current directory
        self.stages = None
        if os.path.isfile(constants.CONFILE_FILE_NAME):
            logger.info('Config file ' + constants.CONFILE_FILE_NAME + ' found in the current directory.')
        else:
            logger.error('Config file ' + constants.CONFILE_FILE_NAME + ' is missing in the current directory.')
            sys.exit(-1)

        # Load configuration from YAML file
        base_config = yaml.load(open(constants.CONFILE_FILE_NAME), Loader=yaml.SafeLoader)

        # Retrieve environment variables
        if constants.PROJECT_VARS in base_config and base_config[constants.PROJECT_VARS]:
            logger.info('Retrieving environment variables...')
            self.env_vars = {}
            for var in base_config[constants.PROJECT_VARS]:
                # Check only one key is defined for each environment variable
                if len(var.keys()) != 1:
                    logger.error('Each item in "' + constants.PROJECT_VARS + '" must contain exactly one key.')
                    sys.exit(-1)
                key, value = var.popitem()
                self.env_vars[key] = value
            del base_config[constants.PROJECT_VARS]
        else:
            logger.info('No environment variables to retrieve.')

        # Check configuration
        self.config = self._configuration_check(constants.CONFIGURATION_PARAMS, base_config)

        logger.info('')

    def _configuration_check(self, config_template: dict, config: dict) -> dict:
        # Check all parameters in config exist in template
        for param in config:
            if param not in config_template and param != constants.PROJECT_VARS and param != constants.USE_TEMPLATE:
                self._logger.error(
                    'Config file "config.yaml" contains unknown parameter "' + param + '".')
                sys.exit(-1)

        # Get template configuration if requested
        config = self._add_params_from_template(config)

        # Parse all key in template and retrieve corresponding param in config
        new_config = {}
        for param in config_template:
            if param in config:
                if isinstance(config[param], list):
                    if 'vectored' in config_template[param] and config_template[param]['vectored']:
                        param = self._add_params_from_template(param)
                        new_config[param] = [self._extract_param_from_config(config_template, element, param) for
                                             element in config[param]]
                    else:
                        self._logger.error(
                            'Parameter "' + param + '" is not a vectored parameter.')
                        sys.exit(-1)
                else:
                    new_config[param] = self._extract_param_from_config(config_template, config[param], param)

            elif config_template[param]['mandatory']:
                self._logger.error(
                    'Config file "config.yaml" doesn\'t contain the mandatory parameter "' + param + '".')
                sys.exit(-1)

            elif 'default' in config_template[param]:
                new_config[param] = config_template[param]['default']

        # Return configuration
        return new_config

    def _extract_param_from_config(self, template: dict, data, param_name: str):
        if 'sub_params' in template[param_name]:
            return self._configuration_check(template[param_name]['sub_params'], data)
        else:
            return data

    def _add_params_from_template(self, config):
        # Replace local configuration with template, except for git repository and artifacts generation
        if constants.USE_TEMPLATE in config:
            template_file = config[constants.USE_TEMPLATE]
            template_full_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..',
                                              constants.TEMPLATES_DIR, template_file + '.yaml')
            if os.path.isfile(template_full_file):
                self._logger.info('Using template "' + template_file + '" for configuration.')

                # Get template configuration
                with open(template_full_file, 'r') as file:
                    template_config = yaml.load(file, Loader=yaml.SafeLoader)

                # Add keys from project config into template
                for key in config:
                    if key not in [constants.PROJECT_VARS, constants.USE_TEMPLATE]:
                        template_config[key] = config[key]

                return template_config
            else:
                self._logger.error('Template "' + template_file + '" doesn\'t exist in the templates directory.')
                sys.exit(-1)

        else:
            return config

    def _replace_param_by_env_var_in_str(self, base_str: str):
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
            if env_var in self.env_vars:
                return base_str.replace('${' + env_var + '}', self.env_vars[env_var])
            else:
                self._logger.error(
                    'Error: Environment variable "' + env_var + '" is not defined.')
                sys.exit(-1)
        else:
            return base_str

    def _replace_param_by_env_var_in_dict(self, base_config: dict[str, any]):
        config = {}
        for key in base_config:
            if isinstance(base_config[key], str):
                config[key] = self._replace_param_by_env_var_in_str(base_config[key])
            else:
                config[key] = base_config[key]
        return config
