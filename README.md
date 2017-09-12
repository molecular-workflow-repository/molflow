# Molecular Workflow Repository

- [Contents](#molecular-workflow-repository)
  * [Install](#install-cli-tool)
  * [Run it](#running-from-the-command-line)
  * [Creating your first app](#creating-your-first-app)
  * [Publishing your workflows](#publishing-your-workflows)
  * [Publishing your own apps](#publishing-your-own-apps)
  * [Workflow Advisory Board](#workflow-advisory-board)

This repository is an open, growing collection of easy-to-run molecular modeling workflows. These can be thought of as "runnable methods sections" - modular computational workflows that let scientists easily:
 1. use other published methods as components,
 2. publish their own methods, and
 3. iterate and build on other's work.


## Install CLI Tool

You can run the official workflows apps right from your browser with the [MST web application](https://molsim.bionano.autodesk.com).

If you'd like to run them from the command line, or start working on your own, you'll need to install:
 
 - [Docker](https://docs.docker.com/engine/installation/)
 - [git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
 - [Python 2.7 or 3.5+](https://www.python.org/downloads/)

After that, you can install everything else you need by running:

```bash
pip install git+https://github.com/molecular-workflow-repository/molflow.git
```


## Getting the standard and sample workflows

`molflow`'s config file, located at `~/.molflow/config`, is created the first time you run the command, and includes configuration options for where to search for local workflows. One of the standard places is in the `~/.molflow/workflows/` directory: any subdirectories under there that have the required `workflow.py` and `metadata.yml` files will appear in `molflow`'s list.

To get the set of standard and sample workflows, run the following:
```bash
mkdir -p ~/.molflow/workflows/
cd ~/.molflow/workflows/
git clone https://github.com/molecular-workflow-repository/add_two_to_it.git
git clone https://github.com/molecular-workflow-repository/convert.git
git clone https://github.com/molecular-workflow-repository/count_atoms.git
git clone https://github.com/molecular-workflow-repository/parameterize_small_molecule.git
```

Look for more at the [Molecular Workflow Repository](https://github.com/molecular-workflow-repository/)!

Future versions of `molflow` will be able to query this remote and automatically grab workflows you want to use from it.

## Running from the command line

Installing this package will put the `molflow` executable in your path.

 - To get a list of available workflows, run `molflow list`:
```
$ molflow list
Workflow location: ~/.molflow/workflows
 - add_two_to_it (v0.1.0): Add 2 to integer, float, or complex number.
 - convert (v0.1.0): Translate a molecule between a variety of file formats, chemical ids, and python objects.
 - count_atoms (v0.0.1): Returns the number of atoms in a molecule.
 - mm_minimize (v0.0.1): Minimize a biomolecule and automatically parameterize any bound small molecules.
 - parameterize_small_molecule (v0.0.1): Automatically parameterize a small molecule.
 - vertical_detachment_energy (v0.0.1): Calculate the energy necessary to photoionize a closed-shell molecule.
[...]
```
 - To get detailed information about available workflows, including versions available, run `molflow list -v`:
```
$ molflow list -v
Workflow location: ~/.molflow/workflows
 - add_two_to_it (v0.1.0): Add 2 to integer, float, or complex number.
   Versions: v0.1.0
   Branches: master

 - convert (v0.1.0): Translate a molecule between a variety of file formats, chemical ids, and python objects.
   Versions: v0.1.0
   Branches: master

 - count_atoms (v0.0.1): Returns the number of atoms in a molecule.
   Versions: v0.0.1
   Branches: master
[...]
```

 - To get more information about a workflow, run `molflow info [workflow name]`:
```yaml
$ molflow info add_two_to_it
Name: add_two_to_it
Default Version: v0.1.0
Inputs:
- number: (number) Number to add two to
Outputs:
- result: (number) Original number plus two
Description: Add 2 to integer, float, or complex number.
[...]
```

[This page](docs/workflows/metadata.md) contains a more complete description of the metadata included with each workflow.

 - To run a workflow, run `molflow run [workflow name] [input name] [input file]`, e.g.:
```yaml
$ molflow run add_two_to_it 4.0
Output directory: ~/add_two_to_it.run

Starting workflow 'add_two_to_it'
add_one.1:
  engine: 'Docker engine on host: http+docker://localunixsocket'
  image: docker.io/python:3.6-slim
  job_id: e94dfa025d722c5d0dc668ef552b5c312bc0e83a8c3da43aa2a9cefd87df7063
[...]
Finished workflow 'add_two_to_it'.

Output locations:
  result:
  - add_two_to_it.run/result.pkl
  - add_two_to_it.run/result.txt
```
NOTE: This requires that docker is running locally on your machine.

 - To run a workflow using a specific version or branch, run `molflow run -v [version or branchname] [workflow name] [input name] [input file]`.


## Creating your first app

WIP

## Publishing your workflows

WIP

 
## Publishing your own apps

WIP
 

## Workflow Advisory Board
WIP


