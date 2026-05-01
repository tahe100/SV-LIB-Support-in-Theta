; This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
; https://gitlab.com/sosy-lab/benchmarking/sv-lib
;
; SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
;
; SPDX-License-Identifier: Apache-2.0

define i32 @function_duplicate() {
entry:
    ret i32 0
}

define i32 @function_duplicate() {
entry:
    ret i32 0
}