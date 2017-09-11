A workflow definition residues in a directory of a git repository (usually the top level of the repo).

There are two required files: `metadata.yml` and `workflow.py`

## `workflow.py`

This is a python file that defines the workflow. Here's what you'll find in a typical workflow definition:

##### 1. Create the workflow object
```python
import molflow.definitions as mf
workflow = mf.WorkflowDefinition('name_of_workflow')
__workflow__ = workflow

```
Note that you should assign your workflow to the variable `__workflow__` so that molflow can find it. Also, please note that `name_of_workflow` should match the name in `metadata.yml`.

##### 2. Define the transformations

Workflows are comprised of a series of Functions, each of which runs in a specific docker container. In this section, you simply need to tell the workflow what functions it will be using.

To define a function offered by a python library, pass the module, function
name, and docker image to run it in:

```python
my_function = workflow.Function(module_name='moldesign.tools',
                                function_name='add_hydrogen',
                                docker_image='docker.io/autodesk/moldesign:moldesign_complete-0.7.4')
```

However, it's often easier and more efficient to define short collections of functions in the same directory as your workflow. For instance, to use a function defined in the file 'functions.py` in the same directory as `workflow.py`:

```python
my_function = workflow.Function(sourcefile='./functions.py',
                                function_name='workflow_function',
                                docker_image='docker.io/autodesk/moldesign:moldesign_complete-0.7.4')
```
Note that the `docker_image` argument is optional if the `sourcefile` argument is provided. If so, the docker image can also be defined by including a line of the form

```python
__DOCKER_IMAGE__ = 'docker.io/mwr/workflow:0.3.2'
```

in the sourcefile. This is useful if you wish to define many functions that all run in the same docker image.


You can also use another workflow as a function. You can either use an official, published workflow:

```python
converter = mf.get_workflow('convert', version='0.4.3')
```

or refer to a local directory:

```python
converter = mf.load_local_workflow('~/my_workflows/my_converter/workflow.py')
```


##### 3. Define the inputs
Here, we tell the workflow what pieces of data to expect.

```python
molfile = workflow.add_input('ligand', 'Ligand file')
ligand_code = workflow.add_input('ligand_code',
                                 '3-letter ligand code',
                                 default='UNL')
forcefield = workflow.add_input('forcefield',
                               'Forcefield type',
                               default='gaff2')
partial_charges = workflow.add_input('partial_charges',
                                     'Partial charge calculation method',
                                     default='am1-bcc')
```

Note that the order you define these in is significant; it defines the call singature for this workflow, both at the command line and when being called by other workflows.

##### 4. Define the workflow
Next, list the series of functions that transform the data from input to output.

```python
mol = convert(molfile, to_fmt='mdt-0.8')
ligands = get_ligands(mol)
validate(mol, ligands)
ligand_parameters = molflow.map(prep_ligand, ligands)
mol_with_ff = prep_forcefield(mol, ligand_parameters)
```

Some caveats and gotchas for this section:
 * This section does NOT execute anything - it merely defines the set of transformations.
 * All functions called here should be instances of `molflow.definitions.Function`.
 * Control statements should be avoided (`if`, `for,`, `while`, etc.).
 * However, some functional programming constructs are available (currently `mf.map` only)


##### 5. Define the outputs

Finally, identify the pieces of data that will be this workflow's outputs.

Note:
 * Data will be saved to disk with the following precedence:
   1. As a plain file (if the data is file-like)
   2. JSON (if the data is list-like or dict-like and doesn't throw an error when using JSON.dumps)
   3. CSV (for pandas dataframes)
   4. As a text file (if the data is a string, integer, or float)
   5. As a python Pickle file (only if none of the above are applicable)











## `metadata.yml`

This file lists descriptive data about the workflow. This file is only required for PUBLISHING your workflow, not running it. It does not influence the computation in any way, but is extremely important for workflow management.

UTF-8 encoding is assumed unless explicitly specified in the "encoding" field. 

Example:

```yaml
name: name_of_workflow
workflow_authors:
 - Jane M. Coder: Autodesk Research
method_authors:
 - Xiao Scientist: Scripps Research Institute
owners:
 - "@avirshup"
description: Automatically parameterize a small molecule.
methods: |
  This workflow creates amber-style parameters for a small molecule. By default, GAFF2 atom types
  are assigned with am1-bcc partial charges, but the workflow can be configured with other input
  options.
citations:
  - A URL citation: "http://ambermd.org/#AmberTools"
  - A DOI citation: "doi:10.1021/jacs.6b11039"
  - A BibTex Citation: |
    @article{fenner2012a,
             title = {One-click science marketing},
             volume = {11},
             url = {http://dx.doi.org/10.1038/nmat3283},
             doi = {10.1038/nmat3283},
             number = {4},
             journal = {Nature Materials},
             publisher = {Nature Publishing Group},
             author = {Fenner, Martin},
             year = {2012},
             month = {mar},
             pages = {261-263}}
keywords:
  - forcefield
  - small-molecule
  - parameterization
encoding: utf-8
```

Description of each field:
##### Required
 - `name`: Name of workflow, 100 characters max. All characters in this string must match `[a-zA-Z0-9./-_]`.
 - `workflow_authors`: The authors of the SOURCE CODE for the workflow. List of single-item key-value-pairs. Each pair should be of the form `[First [middle optionally] Last]: [Institution]`. [See also the optional `method_authors` field, below]
 - `methods`: Text methods section (max 5000 characters).
 - `owners`: List of github usernames CURRENTLY responsible for maintaining this workflow.
 - `citations`: List of works to credit for this workflow, as a list of key-value pairs. Each key-value pair takes the form of `[description]: [citation, permanent link, or DOI]`. [BibTeX citations](http://web.mit.edu/rsi/www/pdfs/bibtex-format.pdf) are encouraged but not required. 
 - `keywords`: list of keywords for this workflow (up to 10). All characters in a keyword must match `[a-zA-Z0-9./-_]`, and each keyword should be 30 characters or less. Keywords are case-insensitive. To aid users in finding your workflow, you should try to use terms from the list of existing keywords (Run `molflow keywords`).

##### Optional
 - `primary_citation`: Literature citation for this work. Users will be reminded to cite this work if they publish results based on this workflow.
 - `method_authors`: List of originators of this methodology (in the same form as `workflow_authors`). Only include this section if the authors listed in `workflow_authors` did no original research when writing the workflow. Otherwise, cite prior work in the "citations" section instead.
 - `encoding`: text string encoding for this file (default utf-8)

