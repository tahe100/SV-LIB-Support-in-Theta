; This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
; https://gitlab.com/sosy-lab/benchmarking/sv-lib
;
; SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
;
; SPDX-License-Identifier: Apache-2.0

define i32 @fun() {
entry:
    %sum = add i32 1, 1
    br label %other_block

other_block:
    %sum = add i32 0, 0
    br label %final_block

final_block:
    ret i32 0
}