; This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
; https://gitlab.com/sosy-lab/benchmarking/sv-lib
;
; SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
;
; SPDX-License-Identifier: Apache-2.0

; --- 1 Parameter, 0 Return Value ---
define void @one_param_no_ret(i32 %a) {
entry:
  %res = add nsw i32 %a, 10
  ret void
}

; --- 0 Parameter, 1 Return Value ---
define i32 @no_param_one_ret() {
entry:
  ret i32 42
}

; --- 1 Parameter, 1 Return Value ---
define i32 @one_param_one_ret(i32 %b) {
entry:
  %res = mul nsw i32 %b, 2
  ret i32 %res
}

; --- 2 Parameters, 1 Return Value ---
define i32 @two_param_one_ret(i32 %c, i32 %d) {
entry:
  %res = add nsw i32 %c, %d
  ret i32 %res
}

define i32 @main() {
entry:
  %val2 = call i32 @no_param_one_ret()
  call void @one_param_no_ret(i32 5)
  %val3 = call i32 @one_param_one_ret(i32 %val2)
  %val4 = call i32 @two_param_one_ret(i32 %val2, i32 %val3)

  ret i32 %val4
}