### MPAS-SOM-Codes

A collection of SOM codes for ERA5 and MPAS output data. The main program is "mpas_som.py", which can be run using the run_mpas_som.sb script (you could also run this from a jupyter notebook, but it takes a long time).

The blossom.py program formats the data, and then uses the minisom.py package to train a SOM and create composites. 
The blossom_settings.json5 file must be edited to change SOM hyperparameters. To change something, you should edit the value following the colon. For instance, if I wanted to change the iterations, I would start with:

//How many times the SOM should iterate
"num_iteration": 100000,

Maybe I want the SOM to perform 100 iterations. So I would change to:

//How many times the SOM should iterate
"num_iteration": 100,
