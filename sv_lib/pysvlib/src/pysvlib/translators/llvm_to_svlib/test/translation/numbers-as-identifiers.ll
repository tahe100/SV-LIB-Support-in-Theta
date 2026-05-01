; This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
; https://gitlab.com/sosy-lab/benchmarking/sv-lib
;
; SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
;
; SPDX-License-Identifier: Apache-2.0

define void @numbers_as_identifiers(i32 %0, i32 %1) {
2:
    %3 = add i32 %0, %1
    %4 = mul i32 %3, 2
    br label %5

5:
    %6 = sdiv i32 %4, %1
    %7 = sub i32 %6, %0
    ret void
}