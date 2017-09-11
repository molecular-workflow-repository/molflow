A `molflow` workflow is a series of python functions that each run in specific docker containers. Writing a workflow is a little more work than creating a normal Python program, but the advantage is that your workflow will run ANYWHERE (that supports docker).

## Development: Your first workflow

Rather than start from scratch, let's get you started with something easy.

At the command line, run `molflow copy multiply_it_by_two --rename add_one_to_it`. This makes a copy of a simple existing workflow. In your current directory, you'll now see a folder named `add_one_to_it`:

```bash
[~]$ molflow copy multiply_it_by_two --rename add_one_to_it
[~]$ cd add_one_to_it
[add_one_to_it]$ ls
workflow.py   metadata.yml   functions.py
```

Go ahead and run this workflow, to verify that it works:
```bash
[add_one_to_it]$ molflow info ./
 {PUT METADATA DISPLAY HERE}
[add_one_to_it]$ molflow run . --number=3
 {LOGGING OUTPUT GOESHERE}
4
 ```


First, let's take a look at `functions.py`:
```python
__DOCKER_IMAGE__ = 'docker.io/python:3.6-slim'

def multiply_it_by_two(number):
    return number * 2
```

This is a completely standard python file. There's one additional piece of metadata - a variable called `__DOCKER_IMAGE__` that defines the environment where these functions will run.

Go ahead and change that 