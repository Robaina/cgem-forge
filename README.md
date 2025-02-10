cGEM modeling pipeline

# TODO:

1. Check containers, update if necessary
2. Add container foor genomeSelector, taking inputs from Leviathan
3. Clean repositoory, add tutorial nbs and docs as needed
4. Add visualization module: e.g. interaction networks
5. Update universal model database, including newer models for photosynthetizers
6. Contact Steve to build workflow from containers
7. Find cool name for the tool!


## Workflow architecture

node_0_a -> select representative genomes (optional), inputs from Leviathan traits matrix and abundances, output set of representative genomes to build a cGEM
node_0_b -> build GEMs from representative genomes, inputs from node_0_a, plus medium file, plus universal metabolic models, output xml files, one per genome/GEM
node_1_a -> SMETANA, inputs from node_0_b, plus parameters, output SMETANA output table
node_1_b -> MICOM, build cGEMs plus analyses, inputs from node_0_b, plus parameters, output MICOM output table, MICOM cGEM file

