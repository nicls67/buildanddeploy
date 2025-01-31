# BuildAndDeploy

### A Python tool to build and deploy your projects

## Overview

**BuildAndDeploy** is a lightweight Python tool designed to streamline the process of building and deploying your
software projects. It provides an easy-to-use interface and a set of features that simplify the build and deployment
pipeline, making it suitable for both small and large-scale projects.

## Build

To build your project, simply call `build.py` and provide your working directory.

````bash
python build.py <working directory>
````

## Configuration

Working directory must contain a ``config.yaml`` file with build configuration.

The following parameters shall be provided inside the configuration :

* ``git_repository`` (string): the url the git repository you want to build
* ``display_pipeline_output`` (boolean, optional): Shows all pipeline output
* ``stages``: A list of build stages to execute, each stage containing the following parameters :
    * ``name`` (string): name of the stage
    * ``command`` (string): command to execute to build the stage

### Use of configuration templates

If the ``use_template`` tag is found in the configuration, the given template will be used. All configuration items in
the file will be ignored, except the ``git_repository`` item which remains mandatory.

Templates can also be added in a stage configuration, in this case the given template shall contain a stage
configuration only.

The following example will use the ``rust`` configuration on the given Git repository

````yaml
git_repository: http://server.com/rust-project.git
use_template: rust
````

The ``rust`` template looks like this :

````yaml
# Global configuration
display_pipeline_output: false

# Build stages
stages:
  - use_template: rust_build
  - use_template: rust_test
````

Here the stages are defined with stage templates, the ``rust_build`` template looks like this :

````yaml
name: build
command: cargo build
````


