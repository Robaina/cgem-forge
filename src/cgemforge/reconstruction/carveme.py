#!/usr/bin/env python

def build_carve_command(args) -> list:
    """Build the CarveMe command with all specified arguments."""
    # Changed to use positional input argument
    cmd = ["carve", args.input, "-o", args.output]

    # Add TSV flag if provided along with processes
    if args.tsv:
        cmd.append("--tsv")
        # Only add processes argument when using TSV mode
        cmd.extend(["--processes", str(args.processes)])

    # Add solver selection
    cmd.extend(["--solver", args.solver])

    # Rest of the command building remains the same
    if args.dna:
        cmd.append("--dna")
    elif args.egg:
        cmd.append("--egg")
    elif args.diamond:
        cmd.append("--diamond")
    elif args.refseq:
        cmd.append("--refseq")

    if args.diamond_args:
        cmd.extend(["--diamond-args", args.diamond_args])

    if args.cobra:
        cmd.append("--cobra")
    elif args.fbc2:
        cmd.append("--fbc2")

    if args.ensemble:
        cmd.extend(["-n", str(args.ensemble)])

    if args.soft:
        cmd.extend(["--soft", args.soft])
    if args.hard:
        cmd.extend(["--hard", args.hard])
    if args.reference:
        cmd.extend(["--reference", args.reference])

    if args.default_score != -1.0:
        cmd.extend(["--default-score", str(args.default_score)])
    if args.uptake_score != 0.0:
        cmd.extend(["--uptake-score", str(args.uptake_score)])
    if args.soft_score != 1.0:
        cmd.extend(["--soft-score", str(args.soft_score)])
    if args.reference_score != 0.0:
        cmd.extend(["--reference-score", str(args.reference_score)])
    if args.blind_gapfill:
        cmd.append("--blind-gapfill")

    return cmd