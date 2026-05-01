; This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
; https://gitlab.com/sosy-lab/benchmarking/sv-lib
;
; SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
;
; SPDX-License-Identifier: Apache-2.0

define [2 x i32] @create_simple_array() {
entry:
    ; insert the value '1' into index 0
    %arr1 = insertvalue [2 x i32] undef, i32 1, 0

    ; insert the value '0' into index 0 and 1
    %arr2 = insertvalue [2 x i32] %arr1, i32 0, 1

    ; extract the value at index 0 (which is '0') into a virtual register
    %val0 = extractvalue [2 x i32] %arr2, 0

    ; return the completed aggregate value
    ret [2 x i32] %arr2
}