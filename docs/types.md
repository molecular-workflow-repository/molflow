This document is intended for `molflow` workflow developers, who will need to understand how to request and convert the data their workflows receive. For users, everything should "just work" - and we want to hear from you if it doesn't!

### Data types

All workflow inputs and outputs should be typed. This allows molflow to read and save data in the desired form, without requiring users to convert the data themselves.


#### Workflow input and output

`molflow` handles data at 5 key points:
 1. When a user passes in data from the command line
 2. When a user passes in data from the API
 3. When data is sent to a given task as input
 4. When data is sent FROM a given task as output
 5. When 

`molflow` supports the following datatypes:

##### Native Python Types
 - `object`:  Generic python objects.
   - CLI input: path to pickle file.
   - API input: literally anything 
   - Workflow output: A file: [outputname].pkl
 - `str`: strings.
   - CLI input: command line arguments (ascii only), or unicode can be read from a file with `contents:` type. Use `contents[utf-32]:` to specify encoding (default utf-8)
   - API input: python `str`, `bytes`, `unicode` objects
   - Workflow output:
     - If the string is shorter than 5000 characters, it is written as a field in the `results.yml` file. 
     - If the string is longer than 5000 characters, it will be written to a file named [output name].txt
 - `int`, `float`, `complex`: numbers
   - CLI input: arguments converted to using `int()` or `float()`
   - API input: arguments converted to int/float
   - Workflow output: written to the `results.yml` file 
 - `dict`, `list`, `tuple`: python compound objects
   - CLI input: JSON or YAML file only
   - API input: pass object of the appropriate type
   - Workflow output: written to the `results.yml` file 

 - `array` - TODO (numpy? pandas? csv?)

##### Files

 - `file`: For passing any file through workflows
  - CLI input: path to the file, staged to docker container and passed as a 
  - API input: TODO
  - Workflow output: Written to a file with the same name as the output field 

File/string data formats:
 - `json`: JSON data
   - CLI input: 
 - `yml`, `yaml`
 - `txt`, `text`
 - `pkl`, `p`, `pickle`

Python objects:

`MDT`, `ParmEd`, `OpenBabel`, `OpenMM`

Molecular formats:
 - `pdb`, `sdf`, `mol2`, `xyz`
 - `smiles`
 - `iupac`
 - `inchi` 


### 


### Interpreting command line arguments

When users provide workflow inputs to `molflow run` at the command line, they're ALWAYS strings. If the inputs are explicitly typed, the strings will be automatically converted to the appropriate type.


Let's start with the `multiply_it_by_two` workflow - it takes just a single input, named "number". You can pass data to it by writing the number on the command line

```bash
$ molflow run multiply_it_by_two 3 --quiet
result: 6
```

Let's create a file called "two.txt" that contains only the string "2.0". You can tell molflow to read that directly by running:

```bash
$ molflow run multiply_it_by_two contents_of:two.txt --quiet
result: 6
```


Note that you got a floating point number back, not an integer! We can explicitly make our input an integer, which (for this specific workflow), means that the output will be an integer as well:

```bash
$ molflow run multiply_it_by_two int:3 --quiet
result: 6
```


```bash
$ molflow run multiply_it_by_two number=int:readfile:two.txt --quiet
result: 6
```

### Adding types to your workflow
You can request explicit types directly to any functions you write yourself using Python 3 type annotations:




### Automatic molecular conversions
Let'



### How molflow guesses types
When explicit types AREN'T specified for a workflow's inputs and outputs, molflow will attempt to infer them. In practice, this works well for prototyping, but published workflows should generally specify types whenver possible to avoid confusion.

When you run a workflow from the CLI, without explicit types, here's how 


### Specification

#### File type

###### Case: "infile" is a workflow input explicitly typed as a file.
`run --infile=[anything]`
Sets the "infile" input to \[anything\]

`run --infile=contents:"file contents"`
Creates an anonymous file with the contents "file contents"

 
###### Case: "infile" is untyped.
There is no way to send a file object through the CLI


#### Molecular types

##### Case: "mol" is explicitly typed as an MDT molecule. 
```bash
run --mol=mol.pdb
run --mol=pdbfile:mol.pdb
run --mol=pdbfile:contents:"[pdb file contents]"
```
Molecule is automatically translated from PDB to an MDT object.

```bash
run --mol=mol.pkl
```
molflow unpickles an object from mol.pkl