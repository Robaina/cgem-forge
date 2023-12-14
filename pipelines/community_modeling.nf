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
params.solver = "gurobi"
params.exchanges = true
params.elasticities = false

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
    path "${params.out_taxatable}"

    script:
    """
    python src/build_taxa_table.py \
        "${params.sample_id}" \
        ${abundances} \
        ${gems} \
        --output ${params.out_taxatable}
    """
}

process BuildCommunityGEM {
    publishDir params.outdir, mode: "copy"

    input:
    path taxaTable from BuildTaxaTable.out

    output:
    path "manifest.csv"
    path "*.pickle"

    script:
    """
    python src/build_gems.py \
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
    path manifest from BuildGems.out.collect()
    path marine_media

    output:
    path "${params.out_exchanges}"

    script:
    """
    python src/get_exchanges.py \
        ${manifest} \
        . \
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
    path "${params.out_elasticities}"

    script:
    """
    python src/get_elasticities.py \
        ${cgem_pickle} \
        --fraction ${params.growth_tradeoff} \
        --output ${params.out_elasticities}
    """
}

// Workflow
workflow {
    BuildTaxaTable(abundances_ch, gems_ch)
    BuildCommunityGEM(BuildTaxaTable.out)
    if (params.exchanges) {
        GetExchanges(BuildCommunityGEM.out.collect(), marine_media_ch)

    }
    if (params.elasticities) {
        GetElasticities(BuildCommunityGEM.out.collect { it.name.endsWith('.pickle') })
    }
}
