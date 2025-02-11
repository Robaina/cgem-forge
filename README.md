# cGEM-FORGE

A comprehensive framework for reconstructing and analyzing community genome-scale metabolic models (cGEMs) from metagenomic data.

## 🎯 Overview

cGEM-FORGE is a complete pipeline for building, analyzing, and visualizing community genome-scale metabolic models (cGEMs) from metagenomic data. The framework integrates several tools into a streamlined workflow for studying microbial community metabolism.

## 🔧 Features

- Automated reconstruction of individual genome-scale metabolic models (GEMs) from MAGs using CarveMe
- Community model building using MICOM
- Analysis of metabolic exchanges and trophic interactions
- Multiple visualization options for metabolic interactions
- Docker containers for easy deployment and reproducibility

## 📋 Requirements

- Docker
- Input files:
  - MAGs (Metagenome-Assembled Genomes) as protein FASTA files
  - Relative abundance data (TSV format)
  - Medium composition file (TSV format)
  - Universal model file (XML format)

## 🚀 Pipeline Steps

1. **Individual GEM Reconstruction**
   - Uses CarveMe to build metabolic models for each MAG
   - Outputs individual models in XML format

2. **Medium Preparation**
   - Generates MICOM-compatible medium files from media database
   - Configurable medium composition and uptake rates

3. **Community Model Construction**
   - Creates MICOM taxonomy table
   - Builds integrated community model
   - Outputs pickled community model

4. **Exchange Analysis**
   - Computes metabolic exchanges between community members
   - Analyzes trophic interactions
   - Configurable growth trade-offs

5. **Visualization**
   - Network diagrams of trophic interactions
   - Heatmaps of metabolic exchanges
   - Sankey diagrams of metabolic flows

## 💻 Usage

The framework consists of several Docker containers that can be run sequentially:

### 1. CarveMe Container
```bash
docker run \
  -v /path/to/microcom:/app/microcom \
  -v /path/to/config.tsv:/app/config.tsv \
  -v /path/to/results:/app/results \
  ghcr.io/new-atlantis-labs/carveme:latest \
  --config /app/config.tsv \
  --outdir /app/results \
  --processes 10
```

### 2. MICOM Container
```bash
docker run \
  -v /path/to/data:/app/data \
  -v /path/to/results:/app/results \
  ghcr.io/new-atlantis-labs/micom:latest \
  build_cgem \
  --taxa_table /app/data/micom_database.tsv \
  --outdir /app/results \
  --abundance_cutoff 0.01 \
  --threads 10 \
  --solver "hybrid"
```

### 3. Visualization Container
```bash
docker run \
  -v /path/to/data:/data \
  -v /path/to/results:/app/results \
  ghcr.io/new-atlantis-labs/cgem-viz:latest \
  --exchanges-file /data/exchanges.tsv \
  --visualization-type network
```

## 📊 Visualization Options

The framework supports three types of visualizations:

1. **Network Diagrams**
   - Shows trophic interactions between community members
   - Configurable flux cutoffs
   - Directed edges indicating metabolite exchanges

2. **Exchange Heatmaps**
   - Visualizes metabolic exchanges between species
   - Optional normalization and clustering
   - Customizable color schemes

3. **Sankey Diagrams**
   - Displays metabolic flows in the community
   - Configurable flux cutoffs
   - Interactive visualization of metabolite transfers

## 📝 Input File Formats

1. **Abundance File (TSV)**
```
id    taxonomy    abundance
MAG1  Species1    30
MAG2  Species2    40
```

2. **Medium Composition (TSV)**
```
reaction_id    max_uptake
EX_glc_e      10.0
EX_o2_e       5.0
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.