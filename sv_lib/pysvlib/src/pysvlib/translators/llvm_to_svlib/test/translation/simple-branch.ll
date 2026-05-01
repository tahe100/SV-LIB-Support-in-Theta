; This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
; https://gitlab.com/sosy-lab/benchmarking/sv-lib
;
; SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
;
; SPDX-License-Identifier: Apache-2.0

define i1 @branch() {
entry:
    ; set y to 0
    %y = add i1 0, 0

    ; if i1 == 1, then jump to %if
    ; if i1 == 0, then jump to %else
    br i1 %y, label %if, label %else

if:
    ; y = y + 1
    %y_inc = add i1 %y, 1

    ; Return the final value of y i.e. 0
    ret i1 %y

else:
    ; Return 40
    ret i1 0
}