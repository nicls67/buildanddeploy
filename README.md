# BuildAndDeploy

### A Python tool to build and deploy your projects

## Overview

**BuildAndDeploy** is a lightweight Python tool designed to streamline the process of building and deploying your
software projects. It provides an easy-to-use configuration and a set of features that simplify the build and deployment
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
* ``display_pipeline_output`` (boolean, optional): Shows all pipeline output (`false` by default)
* ``generate_artifacts`` (boolean, optional): Activates artifacts generation (`true` by default). If `true`, all
  artifacts will be generated, no matter what is configured inside the states
* ``disable_artifacts`` (boolean, optional): Disables all artifacts generation (`false` by default). if `true`, no
  artifact will be generated, no matter what is configured inside the states. ``generate_artifacts`` has priority over
  this setting.
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

### Artifacts

Each stage may produce artifacts. `BuildAndDeploy` can retrieve them and archive them for you. To activate artifacts
management, add the `artifacts` parameter inside a stage configuration.
`artifacts` item shall be correctly configured :

* ``name`` (string, optional): name of the artifact file produced by `BuildAndDeploy`. If not provided, original
  artifact name will be kept
* ``paths`` (list of strings, mandatory): list of paths to artifacts to retrieve. Use `*` for wildcard in paths. Paths
  can be either a file or a directory
* ``archive`` (boolean, optional): archive the artifacts into a zip file (`false` by default)
* ``assemble`` (boolean, optional): in case multiple paths are defined, assemble the artifacts into a single archive (
  `false` by default)
* ``enabled`` (boolean, optional): enables artifact generation (`true` by default). Can be overwritten by global
  configuration.

Example for `rust build` stage :

````yaml
name: build
command: cargo build
artifacts:
  name: example
  archive: true
  assemble: true
  paths:
    - target/debug/*.exe
````

Artifacts will be available in the `artifacts` directory inside the working directory

### Use of project variables

You can use project variables in your configuration. To do so, use the `${VAR_NAME}` syntax inside the configuration.
Project variables are declared with the `project_vars` statement inside the configuration.
Only the main `config.yaml` file (not the templates) can define project variables.

Example in `config.yaml`:

````yaml
project_vars:
  - project_name: my_project_name
````

Example in a stage:

````yaml
name: build
command: cargo build
artifacts:
  name: ${project_name}
  archive: true
  assemble: true
  paths:
    - target/debug/${project_name}.exe
````
