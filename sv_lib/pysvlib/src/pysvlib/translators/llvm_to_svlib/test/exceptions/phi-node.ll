; This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
; https://gitlab.com/sosy-lab/benchmarking/sv-lib
;
; SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
;
; SPDX-License-Identifier: Apache-2.0

; Function definition for: int add(int x0, int y0)
define i32 @add(i32 %x0, i32 %y0) {

; every LLVM function must begin with a basic block, but the name is not restricted (e.g. 'start_here:' is possible)
entry:
    ; jump directly to the loop logic.
    br label %while_cond

while_cond:
    ; PHI nodes handle variable state without pointers.
    ; If coming from 'entry', use initial arguments.
    ; If coming from 'while_body', use the updated values.
    %x_current = phi i32 [ %x0, %entry ], [ %x_inc, %while_body ]
    %y_current = phi i32 [ %y0, %entry ], [ %y_dec, %while_body ]

    ; icmp = Integer CoMParison, sgt = Signed Greater Than i.e. '>'
    ; We compare the current register value directly rather than loading from memory.
    %cmp = icmp sgt i32 %y_current, 0

    ; if i1 == 1, then jump to %while_body
    ; if i1 == 0, then jump to %while_end
    br i1 %cmp, label %while_body, label %while_end

while_body:
    ; x = x + 1
    ; %x_inc is a SSA virtual register where the result of the instruction is stored
    ; -> LLVM does not work on CPU registers + loops do not violate SSA
    %x_inc = add i32 %x_current, 1

    ; y = y - 1
    ; We perform the subtraction directly on the register value %y_current
    %y_dec = sub i32 %y_current, 1

    ; Jump back to loop condition (carrying %x_inc and %y_dec into the PHI nodes)
    br label %while_cond

while_end:
    ; Return the final value of x
    ret i32 %x_current
}