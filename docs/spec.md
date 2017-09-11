Assigning parameters to a small molecule


workflow.set_data('mol', type=MDT)

Different ways to run it:
```
1) molflow run parameterize mol=./benzene.pdb
2) molflow run parameterize c1ccccc1
3) molflow run parameterize iupac:benzene
4) molflow run parameterize mol=benzene.inchi
5) molflow run parameterize mol.pkl
6) molflow run parameterize pdb:--
7) molflow run parameterize iupac:some_file.iupac
```

Expected behaviors:
1) read the file as a PDB file
2) parse SMILES, generate reasonable 3D geometry
3) ditto
4) ditto
5) unpickle file (any recognized molecular object)
6) read PDB content from stdin
7) Read file from some_file.iupac


Molecular argument handling rules:
 0) An argument is "moelcular" if it is ANY molecular type (we can interconvert between any of these)
 1) Get data to parse:
   A. If the string is the path of a file, assume that you want the content of the file.
   B. If the argument is '--', read from stdin (reads EVERYTHING)
 2) Determine type:
   a. Explicitly set type if argument is of the form "[type]:[arg]"
   b. Otherwise, if it's a file path, use the file extension
   c. Otherwise, check if smiles, iupac, or inchi
 3) Use the correct parser to load the data
 4) Convert the data using the "convert" workflow
 

Molecular output rules:
 1) Convert output in the same way as above
 2) Write to disk
 3) Expose `molflow convert` to let users easily convert to other formats (equivalent to `molflow run convert --quiet`?)

