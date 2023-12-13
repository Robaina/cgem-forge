#!/usr/bin/env nextflow
nextflow.enable.dsl = 2

params.gems_dir = ""
params.abundances = ""
params.sample_id = ""
params.media_file = ""
params.outdir = "./results"
params.out_taxatable = ""
params.growth_tradeoff = 0.5
params.cutoff = 0.01
params.threads = 10
params.solver = "gurobi"

Channel
    .fromPath(params.abundances)
    .set { abundances_ch }

Channel
    .fromPath("${params.gems_dir}/*")
    .set { gems_ch }

Channel
    .fromPath('tests/results/marine_media.tsv')
    .set { marine_media_ch }


process BuildTaxaTable {
    publishDir params.outdir, mode: 'copy'

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
    publishDir params.outdir, mode: 'copy'

    input:
    path taxaTable from BuildTaxaTable.out

    output:
    path "${params.outdir}/manifest.csv"
    path "${params.outdir}/*.pickle"

    script:
    """
    python src/build_gems.py \
        ${taxaTable} \
        --out_folder ${params.outdir} \
        --cutoff ${params.cutoff} \
        --threads ${params.threads} \
        --solver ${params.solver}
    """
}

process GetExchanges {
    publishDir params.outdir, mode: 'copy'

    input:
    path manifest from BuildGems.out.collect()
    path marine_media

    output:
    path "tests/results/exchanges.tsv"

    script:
    """
    python src/get_exchanges.py \
        ${manifest} \
        tests/results \
        ${marine_media} \
        --tradeoff ${params.growth_tradeoff} \
        --threads ${params.threads} \
        --output tests/results/exchanges.tsv
    """
}

process GetElasticities {
    publishDir params.outdir, mode: 'copy'

    input:
    path cgem_pickle

    output:
    path "tests/results/elasticities.tsv"

    script:
    """
    python src/get_elasticities.py \
        ${cgem_pickle} \
        --fraction ${params.growth_tradeoff} \
        --output tests/results/elasticities.tsv
    """
}

workflow {
    BuildTaxaTable(abundances_ch, gems_ch)
    BuildCommunityGEM(BuildTaxaTable.out)
    GetExchanges(BuildCommunityGEM.out.collect(), marine_media_ch)
    GetElasticities(BuildCommunityGEM.out.collect { it.name.endsWith('.pickle') })
}
