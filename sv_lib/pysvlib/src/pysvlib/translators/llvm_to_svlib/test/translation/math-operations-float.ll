; This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
; https://gitlab.com/sosy-lab/benchmarking/sv-lib
;
; SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
;
; SPDX-License-Identifier: Apache-2.0

define void @math_operations_float(float %a, float %b) {
entry:
    ; addition: a + b
    %sum = fadd float %a, %b

    ; multiplication: sum * 2.0
    ; note: constants must be represented as floats (e.g., 2.0)
    %product = fmul float %sum, 2.0

    ; division: product / b
    %quotient = fdiv float %product, %b

    ; subtraction: quotient - a
    %diff = fsub float %quotient, %a

    ; mandatory ret instruction for void functions
    ret void
}