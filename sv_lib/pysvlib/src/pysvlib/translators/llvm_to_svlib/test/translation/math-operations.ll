; This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
; https://gitlab.com/sosy-lab/benchmarking/sv-lib
;
; SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
;
; SPDX-License-Identifier: Apache-2.0

define void @math_operations(i32 %a, i32 %b) {
entry:
    ; addition: a + b
    %sum = add i32 %a, %b

    ; multiplication: sum * 2
    %product = mul i32 %sum, 2

    ; signed division: product / b
    ; note: 'sdiv' is used for signed integers
    %quotient = sdiv i32 %product, %b

    ; subtraction: quotient - a
    %diff = sub i32 %quotient, %a

    ; mandatory ret instruction for void functions
    ret void
}