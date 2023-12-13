#!/usr/bin/env nextflow
nextflow.enable.dsl = 2

params.genomes_dir = ""
params.media_file = ""
params.outdir = "./results"
params.medium_id = ""

genomes = Channel.fromPath("${params.genomes_dir}/*")

process carveme {
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
    carveme(genomes_ch)
}
