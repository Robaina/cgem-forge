#!/usr/bin/env nextflow
nextflow.enable.dsl = 2

params.genomes_dir = params.genomes_dir ?: error("No genomes directory provided")
params.media_file = params.media_file ?: error("No media file provided")
params.medium_id = params.medium_id ?: error("No medium ID provided")
params.universe = params.universe ?: error("No universe file provided")
params.outdir = "./results"

genomes = Channel.fromPath("${params.genomes_dir}/*.fasta")

process ReconstructGEM {
    publishDir "${params.outdir}/gems", mode: 'copy'

    input:
    path fasta 

    output:
    path("${fasta.baseName}.xml")

    script:
    """
    carve --solver gurobi \\
     -o ${fasta.baseName}.xml \\
     --universe-file ${params.universe} \\
     --init ${params.medium_id} \\
     --gapfill ${params.medium_id} \\
     --mediadb ${params.media_file} \\
     ${fasta}
    """
}

workflow {
    genomes.view().set { genomes_ch }
    ReconstructGEM(genomes_ch)
}
