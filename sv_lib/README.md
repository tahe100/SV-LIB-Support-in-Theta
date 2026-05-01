<!--
This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
https://gitlab.com/sosy-lab/benchmarking/sv-lib

SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers

SPDX-License-Identifier: Apache-2.0
-->

# SV-LIB: A Standard Exchange Format for Software-Verification Tasks

## Contents

This repository contains multiple useful information and tools related to
[SV-LIB](https://gitlab.com/sosy-lab/benchmarking/sv-lib), a standard exchange format for
software-verification tasks. SV-LIB is designed to facilitate the sharing and comparison of
software verification tools and benchmarks.

Currently, we provide:

* [PySvLib](./pysvlib/README.md): A Python library for working with SV-LIB files.
* [Examples](./examples/): A collection of example SV-LIB files.
* [An ANTLR4 grammar](./grammar/README.md) for parsing SV-LIB files.
* [Images and Diagrams](./assets), including the SV-LIB logo, for use in distribution
  media like papers and presentations.

## Tutorials and Documentation

There exist a few good sources of documentation and tutorials for SV-LIB, including:

* The [SV-LIB 1.0 technical report](https://doi.org/10.48550/arXiv.2511.21509).
* A [short tutorial on SV-LIB](https://gitlab.com/sosy-lab/research/data/sv-lib-demo) showing the motivation of SV-LIB
  and how to use it.

## Further Tools supporting SV-LIB

Several tools already support SV-LIB as input format, including:

* [CPAchecker](https://cpachecker.sosy-lab.org/)
* [SvLibChecker](https://gitlab.com/sosy-lab/software/svlibchecker)

If your tool also supports SV-LIB, and is not in the list above, please
[open an issue](https://gitlab.com/sosy-lab/benchmarking/sv-lib/-/issues)
to let us know or create a MR!

## Archiving

We use [Zenodo](https://zenodo.org/) to archive releases of this repository
and some tools related to SV-LIB.
You can find everything which has been archived in the
[SV-LIB Software community on Zenodo](https://zenodo.org/communities/sv-lib-software).

## References

- [SV-LIB 1.0: A Standard Exchange Format for Software-Verification Tasks](https://doi.org/10.48550/arXiv.2511.21509),
  by Dirk Beyer, Gidon Ernst, Martin Jonáš, Marian Lingsch-Rosenfeld.
  Technical Report, arXiv (2025).
