import os
import sys
from logging import Logger

import yaml

import libs.constants as constants


class Config:
    """
    Handles configuration management for the application.

    This class is responsible for loading, validating, and managing the application's
    configuration from a YAML file and environment variables. It includes mechanisms
    to check the presence of required configuration parameters, retrieve defaults where
    missing, and process environment variables specified in the configuration. The
    class ensures that the configuration adheres to a predefined template and terminates
    the program in case of invalid configurations or missing mandatory parameters.

    :ivar _logger: Logger instance used for logging informational, warning, and error
                   messages during the configuration management process.
    :type _logger: Logger
    :ivar env_vars: Dictionary containing environment variables retrieved from the
                    configuration file, mapped with their corresponding values.
    :type env_vars: dict
    :ivar config: Processed and validated configuration dictionary loaded from the
                  YAML file and enhanced with defaults or updates from templates
                  as needed.
    :type config: dict
    """

    def __init__(self, logger: Logger):
        """
        Initializes the configuration and environment variables necessary for the application.

        This class constructor validates the presence of a YAML configuration file in the
        current directory, loads the configuration, retrieves environment variables, and
        ensures the overall integrity of the resulting configuration.

        :param logger: Logger instance used to log informational and error messages during
                       the initialization process.
        :type logger: Logger

        :raises SystemExit: If the configuration file is not found or if there is an issue
                            with the configuration structure such as missing keys or invalid
                            environment variable definitions.

        :attributes:
            - env_vars (dict): A dictionary containing the retrieved environment variables
                               with their respective values.
            - config (dict): The processed configuration data after validation and checks.

        """
        self._logger = logger

        # Check if config.yaml exists in the current directory
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
        """
        Validates and processes the configuration dictionary based on the provided configuration template.
        This function ensures that all parameters in the configuration are valid, retrieves default values
        for missing parameters where applicable, and extracts corresponding parameter values from the
        template. If strict validation fails, the program will terminate with an error message.

        :param config_template: The configuration template dict containing details about valid parameters,
                                their default values, mandatory status, and any specific rules required
                                for processing.
        :param config: The input configuration dict that needs to be validated and possibly enhanced
                       with template defaults or additional processing.
        :return: A dictionary representing the processed and validated configuration derived from the
                 template and input configuration.
        """
        # Check all parameters in config exist in the template
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
                    if 'vectored' in config_template[param] and config_template[param]['vectored']:
                        new_config[param] = [self._extract_param_from_config(config_template, config[param], param)]
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
        """
        Extracts a parameter value from a configuration template based on the specified parameter name.

        The function operates by checking if the given parameter name exists in the provided
        template and whether it contains sub-parameters. If sub-parameters are present, a specific
        configuration check method is called. Otherwise, the data is returned as-is.

        :param template: The configuration template in dictionary format that contains the
            parameter definition.
        :type template: dict
        :param data: The data object or value associated with the parameter to be processed.
            The precise nature of the data depends on the expected structure of the template.
        :param param_name: The name of the parameter to extract from the configuration template.
        :type param_name: str
        :return: Either the processed result of performing a configuration check on sub-parameters
            or the provided data itself if no sub-parameter check is necessary.
        """
        if 'sub_params' in template[param_name]:
            return self._configuration_check(template[param_name]['sub_params'], data)
        else:
            new_data = self._replace_param_by_env_var_in_str(data)
            return new_data

    def _add_params_from_template(self, config):
        """
        Adds parameters from a specified template file to the configuration if the template is
        enabled in the given configuration dictionary.

        This function checks if a configuration template is specified in the provided configuration
        dictionary. If a valid template file is found, it merges the template configurations with the
        existing configurations while giving precedence to the keys in the user-provided configuration.
        If the specified template file does not exist, the function logs an error and exits the program.

        :param config: Configuration dictionary for the current process. The dictionary may optionally include
            a key indicating the use of a configuration template.
        :type config: dict
        :return: Updated configuration dictionary with parameters from the specified template (if applicable).
        :rtype: dict
        """
        if constants.USE_TEMPLATE in config:
            template_file = config[constants.USE_TEMPLATE]
            template_full_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..',
                                              constants.TEMPLATES_DIR, template_file + '.yaml')
            if os.path.isfile(template_full_file):
                self._logger.info('Using template "' + template_file + '" for configuration.')

                # Get template configuration
                with open(template_full_file, 'r') as file:
                    template_config = yaml.load(file, Loader=yaml.SafeLoader)

                # Add keys from project config into the template
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
        Replaces placeholders for environment variables in the input string with their
        corresponding values from the `self.env_vars` dictionary. Placeholders are
        defined in the format `${VAR_NAME}`. If the referenced variable is not defined
        in the environment variables dictionary, it logs an error and terminates the
        program.

        :param base_str: Input string that may contain placeholders in the format
            `${VAR_NAME}` for substitution with environment variable values.
        :type base_str: str
        :return: String with environment variable placeholders replaced by their
            corresponding values, or the original string if there are no placeholders.
        :rtype: str
        """
        if isinstance(base_str, str) and '$' in base_str:
            env_var = base_str.split('{')[1].split('}')[0]
            if env_var in self.env_vars:
                return base_str.replace('${' + env_var + '}', self.env_vars[env_var])
            else:
                self._logger.error(
                    'Error: Environment variable "' + env_var + '" is not defined.')
                sys.exit(-1)
        else:
            return base_str
