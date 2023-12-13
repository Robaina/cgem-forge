#!/usr/bin/env nextflow
nextflow.enable.dsl=2

params.genomes_dir = './input_mags'
params.media_file = './marine_media/media_db.tsv'
params.outdir = './results'

// mags = Channel.fromPath("${params.genomes_dir}/*.fasta")
gems = Channel.fromPath("${params.gems_dir}/*.xml")


process prepare_taxa_table {
    
}


process merge_community {
    publishDir "${params.outdir}/merged_community", mode: 'copy'

    input:
    path xml_files from gems_ch

    output:
    path "merged.xml"

    script:
    """
    carve --solver gurobi \\
     --init M9[marine] \\
     --gapfill M9[marine] \\
     --mediadb ${params.media_file} \\
     --output merged.xml \\
     --fbc2 \\
     $xml_files
    """
}

workflow {
    mags.view().set { mags_ch }
    carveme( mags_ch ).view().set { gems_ch }
    merge_community( gems_ch )
    memote( gems_ch )
}
