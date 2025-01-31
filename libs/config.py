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
        # Parameter doesn't exist and is not mandatory
        else:
            config[param[0]] = param[2]

    return config


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
    _GLOBAL_CONFIGURATION_PARAMS = [('git_repository', True), ('display_pipeline_output', False, False)]
    _STAGES_CONFIGURATION_PARAMS = [('name', True), ('command', True)]

    def __init__(self):
        """
        Initializes and validates application configuration by loading it from a YAML file,
        ensuring that mandatory global and stage parameters are present.

        Config file requirements:
            - The `config.yaml` file must be present in the current directory. Absence of
              this file will terminate execution with an error.
            - The root of the configuration must contain mandatory global parameters and
              a `stages` key specifying stage-specific configurations. Omission of the
              `stages` parameter will result in termination with an error.

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

        # Analyse global configuration : check for each existing parameter if it is configured
        self.global_config = _check_params_in_config(self._GLOBAL_CONFIGURATION_PARAMS, base_config)

        # Analyse stages configuration
        if 'stages' in base_config:
            self.stages = []
            for stage in base_config['stages']:
                # If a template shall be used, do not analyse remaining parameters
                if 'use_template' in stage:
                    template_file = stage['use_template']
                    template_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'templates')
                    template_full_file = os.path.join(template_dir, template_file + '.yaml')
                    if os.path.isfile(template_full_file):
                        print('Using template "' + template_file + '" for stage "' + '".')

                        # Open template file
                        template_config = yaml.load(open(template_full_file), Loader=yaml.SafeLoader)
                        self.stages.append(_check_params_in_config(self._STAGES_CONFIGURATION_PARAMS, template_config))
                    else:
                        print('Error: Template "' + template_file + '" doesn\'t exist in the templates directory.')
                        sys.exit(-1)
                else:
                    self.stages.append(_check_params_in_config(self._STAGES_CONFIGURATION_PARAMS, stage))
        else:
            print('Error: Config file "config.yaml" doesn\'t contain the mandatory parameter "stages".')
            sys.exit(-1)
