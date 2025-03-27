#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# ========== CONFIGURATION ==========
# Base directories
BASE_DIR="/home/robaina/Documents/NewAtlantis/cgem-forge"
DATA_DIR="${BASE_DIR}/data"
TESTS_DATA_DIR="${BASE_DIR}/tests/data"

# Output directories
RECONSTRUCTION_OUTPUT="${BASE_DIR}/tests/test_reconstruction/gems"
ANALYSIS_OUTPUT="${BASE_DIR}/tests/test_analysis"
VISUALIZATION_OUTPUT="${BASE_DIR}/tests/test_visualization"

# Input files
GENOME_TABLE="${TESTS_DATA_DIR}/genome_table.tsv"
MEDIA_DB="${DATA_DIR}/media/media_db.tsv"
ABUNDANCES="${TESTS_DATA_DIR}/abundances.tsv"

# Parameters
THREADS_CARVEME=8
THREADS_MICOM=12
THREADS_EXCHANGES=10
SAMPLE_ID="TARA_ARC_108"
MEDIUM_ID="MARINE"
COMPARTMENT="m"
MAX_UPTAKE=10.0
ABUNDANCE_CUTOFF=0.01
GROWTH_TRADEOFF=0.5
SOLVER="hybrid"
cGEM_EXCHANGE_STRATEGY="pFBA"
ABS_TOL=1e-6
REL_TOL=1e-6
SANKEY_FLUX_CUTOFF=0.1

# Docker images
RECONSTRUCTION_IMAGE="ghcr.io/new-atlantis-labs/cgem-forge-reconstruction:latest"
ANALYSIS_IMAGE="ghcr.io/new-atlantis-labs/cgem-forge-analysis:latest"
VISUALIZATION_IMAGE="ghcr.io/new-atlantis-labs/cgem-forge-visualization:latest"

# ========== HELPER FUNCTIONS ==========
function log_step() {
    echo "====================================="
    echo "STEP: $1"
    echo "====================================="
}

function ensure_directory() {
    if [ ! -d "$1" ]; then
        mkdir -p "$1"
        echo "Created directory: $1"
    fi
}

# ========== ENSURE DIRECTORIES EXIST ==========
log_step "Creating output directories"
ensure_directory "$RECONSTRUCTION_OUTPUT"
ensure_directory "$ANALYSIS_OUTPUT"
ensure_directory "$VISUALIZATION_OUTPUT"

# ========== WORKFLOW STEPS ==========
log_step "1. Generating genome-scale metabolic models"
docker run --rm \
    -v "${BASE_DIR}:/app/cgem-forge" \
    -v "${GENOME_TABLE}:/app/input.tsv" \
    -v "${RECONSTRUCTION_OUTPUT}:/app/output" \
    ${RECONSTRUCTION_IMAGE} \
    /app/input.tsv \
    -o /app/output \
    -p "${THREADS_CARVEME}" \
    --tsv

log_step "2. Getting medium from media database"
docker run --rm \
    -v "${DATA_DIR}:/app/data" \
    -v "${ANALYSIS_OUTPUT}:/app/results" \
    ${ANALYSIS_IMAGE} \
    get_medium_from_media_db \
    --media-db /app/data/media/media_db.tsv \
    --medium-id "${MEDIUM_ID}" \
    --compartment "${COMPARTMENT}" \
    --max-uptake "${MAX_UPTAKE}" \
    --outfile /app/results/marine_media.tsv

log_step "3. Building taxa table"
docker run --rm \
    -v "${TESTS_DATA_DIR}:/app/data" \
    -v "${RECONSTRUCTION_OUTPUT}:/app/gems_scip" \
    -v "${ANALYSIS_OUTPUT}:/app/results" \
    ${ANALYSIS_IMAGE} \
    build_taxa_table \
    --sample_id "${SAMPLE_ID}" \
    --abundances /app/data/abundances.tsv \
    --gems_dir /app/gems_scip \
    --out_taxatable /app/results/micom_database.tsv

log_step "4. Building community genome-scale metabolic model (cGEM)"
docker run --rm \
    -v "${ANALYSIS_OUTPUT}:/app/data" \
    -v "${ANALYSIS_OUTPUT}:/app/results" \
    -v "${RECONSTRUCTION_OUTPUT}:/app/gems_scip" \
    ${ANALYSIS_IMAGE} \
    build_cgem \
    --taxa_table /app/data/micom_database.tsv \
    --outdir /app/results \
    --abundance_cutoff "${ABUNDANCE_CUTOFF}" \
    --gems_dir /app/gems_scip \
    --threads "${THREADS_EXCHANGES}" \
    --solver ${SOLVER}

log_step "5. Calculating exchange fluxes"
docker run --rm \
    -v "${ANALYSIS_OUTPUT}:/app/results" \
    "${ANALYSIS_IMAGE}" \
    get_exchanges \
    --manifest /app/results/manifest.csv \
    --outdir /app/results \
    --media_file /app/results/marine_media.tsv \
    --growth_tradeoff "${GROWTH_TRADEOFF}" \
    --threads "${THREADS_MICOM}" \
    --out_exchanges /app/results/exchanges.tsv \
    --strategy "${cGEM_EXCHANGE_STRATEGY}" \
    --presolve \
    --rtol "${REL_TOL}" \
    --atol "${ABS_TOL}" \

log_step "6. Generating network visualization"
docker run --rm \
    -v "${ANALYSIS_OUTPUT}:/data" \
    -v "${VISUALIZATION_OUTPUT}:/app/results" \
    ${VISUALIZATION_IMAGE} \
    --exchanges-file /data/exchanges.tsv \
    --flux-cutoff "top10" \
    --visualization-type network

log_step "7. Generating heatmap visualization"
docker run --rm \
    -v "${ANALYSIS_OUTPUT}:/data" \
    -v "${VISUALIZATION_OUTPUT}:/app/results" \
    ${VISUALIZATION_IMAGE} \
    --exchanges-file /data/exchanges.tsv \
    --visualization-type heatmap \
    --output-dir /app/results \
    --normalize-heatmap \
    --cluster-heatmap

log_step "8. Generating Sankey diagram visualization"
docker run --rm \
    -v "${ANALYSIS_OUTPUT}:/data" \
    -v "${VISUALIZATION_OUTPUT}:/app/results" \
    ${VISUALIZATION_IMAGE} \
    --exchanges-file /data/exchanges.tsv \
    --visualization-type sankey \
    --output-dir /app/results \
    --sankey-flux-cutoff ${SANKEY_FLUX_CUTOFF}

echo "====================================="
echo "Workflow completed successfully!"
echo "====================================="