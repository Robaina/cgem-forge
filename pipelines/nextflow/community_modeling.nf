#!/usr/bin/env nextflow
nextflow.enable.dsl = 2

// Define parameters with default values where appropriate
params.gems_dir = params.gems_dir ?: error("No genomes directory provided")
params.abundances = params.abundances ?: error("No abundances file provided")
params.sample_id = params.sample_id ?: error("No sample ID provided")
params.media_file = params.media_file ?: error("No media file provided")
params.outdir = "./results"
params.out_taxatable = "taxa_table.tsv"
params.out_exchanges = "exchanges.tsv"
params.out_elasticities = "elasticities.tsv"
params.growth_tradeoff = 0.5
params.abundance_cutoff = 0.01
params.threads = 10
params.solver = "hybrid"
params.exchanges = true
params.elasticities = false
params.scripts_dir = "./src"

// Channels
Channel.fromPath(params.abundances).set { abundances_ch }
Channel.fromPath("${params.gems_dir}/*").set { gems_ch }
Channel.fromPath("${params.media_file}").set { marine_media_ch }

// Processes
process BuildTaxaTable {
    publishDir params.outdir, mode: "copy"

    input:
    path abundances
    path gems

    output:
    path "${params.out_taxatable}", emit: taxaTable

    script:
    """
    python ${params.scripts_dir}/build_taxa_table.py \
        "${params.sample_id}" \
        ${params.abundances} \
        ${params.gems_dir} \
        --output ${params.out_taxatable}
    """
}

process BuildCommunityGEM {
    publishDir params.outdir, mode: "copy"

    input:
    path taxaTable

    output:
    path "manifest.csv", emit: cgem_manifest
    path "*.pickle", emit: cgem_pickle

    script:
    """
    python ${params.scripts_dir}/build_cgem.py \
        ${taxaTable} \
        --out_folder . \
        --cutoff ${params.abundance_cutoff} \
        --threads ${params.threads} \
        --solver ${params.solver}
    """
}

process GetExchanges {
    publishDir params.outdir, mode: "copy"

    input:
    path manifest
    path marine_media

    output:
    path "${params.out_exchanges}", emit: exchanges

    script:
    """
    python ${params.scripts_dir}/get_exchanges.py \
        ${manifest} \
        ${params.outdir} \
        ${marine_media} \
        --tradeoff ${params.growth_tradeoff} \
        --threads ${params.threads} \
        --output ${params.out_exchanges}
    """
}

process GetElasticities {
    publishDir params.outdir, mode: "copy"

    input:
    path cgem_pickle

    output:
    path "${params.out_elasticities}", emit: elasticities

    script:
    """
    python ${params.scripts_dir}/get_elasticities.py \
        ${cgem_pickle} \
        --fraction ${params.growth_tradeoff} \
        --output ${params.out_elasticities}
    """
}

// Workflow
workflow {
    BuildTaxaTable(abundances_ch, gems_ch)
    BuildCommunityGEM(BuildTaxaTable.out.taxaTable)
    if (params.exchanges) {
        GetExchanges(BuildCommunityGEM.out.cgem_manifest, marine_media_ch)

    }
    if (params.elasticities) {
        GetElasticities(BuildCommunityGEM.out.cgem_pickle)
    }
}
