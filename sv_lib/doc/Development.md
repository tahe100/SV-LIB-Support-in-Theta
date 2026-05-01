<!--
This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
https://gitlab.com/sosy-lab/benchmarking/sv-lib

SPDX-FileCopyrightText: 2025 The SV-LIB Maintainers

SPDX-License-Identifier: Apache-2.0
-->

## Set Up Git Hooks

To set up Git hooks for this project, simply run these commands at project root:

```bash
git config core.hooksPath .githooks
```
This should mirror the Gitlab pipeline linting jobs, if they change the hooks and script has to be adapted accordingly