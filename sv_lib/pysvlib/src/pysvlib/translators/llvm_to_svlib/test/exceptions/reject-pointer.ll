; This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
; https://gitlab.com/sosy-lab/benchmarking/sv-lib
;
; SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
;
; SPDX-License-Identifier: Apache-2.0

; Function: int identity(int %val)
define i32 @identity(i32 %val) {
entry:
    ; Allocate 4 bytes (i32) on the stack.
    ; It returns a pointer (i32*).
    %ptr = alloca i32

    ; Store the input %val into the memory at %ptr.
    store i32 %val, i32* %ptr

    ; Load the value back from the memory at %ptr into a new register.
    %retrieved_val = load i32, i32* %ptr

    ; Return the value we just loaded
    ret i32 %retrieved_val
}