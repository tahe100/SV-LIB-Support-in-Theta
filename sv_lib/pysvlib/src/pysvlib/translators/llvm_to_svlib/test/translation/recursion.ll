; This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
; https://gitlab.com/sosy-lab/benchmarking/sv-lib
;
; SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
;
; SPDX-License-Identifier: Apache-2.0

define void @indirect_recursion_pairB(i32 %x, float %y) {
entry:
  call void @indirect_recursion_triangle3(i32 %x)
  %cond = fcmp olt float %y, 345.0
  br i1 %cond, label %if.then, label %if.end

if.then:
  %y_new = fadd float %y, 1.0
  call void @indirect_recursion_pairA(i32 %x, float %y_new)
  br label %if.end

if.end:
  ret void
}

; --- Main ---
define i32 @main() {
entry:
  ; direct_recursion(1);
  call void @direct_recursion(i32 1)

  ; indirect_recursion_pairA(2, 2.0);
  call void @indirect_recursion_pairA(i32 2, float 2.0)

  ; indirect_recursion_triangle1(3);
  call void @indirect_recursion_triangle1(i32 3)

  ; no_recursion(4);
  call void @no_recursion()

  ret i32 0
}

define void @indirect_recursion_triangle2(i32 %z) {
entry:
  %z_new = sub nsw i32 %z, 21
  call void @indirect_recursion_triangle3(i32 %z_new)
  ret void
}

; --- Direct Recursion ---
define void @direct_recursion(i32 %a) {
entry:
  %a_new = add nsw i32 %a, 3
  %cond = icmp slt i32 %a_new, 100
  br i1 %cond, label %if.then, label %if.end

if.then:
  call void @direct_recursion(i32 %a_new)
  br label %if.end

if.end:
  ret void
}

; --- Indirect Recursion Pair ---
define void @indirect_recursion_pairA(i32 %x, float %y) {
entry:
  %cond = icmp slt i32 %x, 177
  br i1 %cond, label %if.then, label %if.end

if.then:
  %x_add = add nsw i32 %x, 2
  call void @indirect_recursion_pairB(i32 %x_add, float %y)
  br label %if.end

if.end:
  ret void
}

; --- Indirect Recursion Triangle ---
define void @indirect_recursion_triangle1(i32 %z) {
entry:
  %z_new = sub nsw i32 %z, 42
  call void @indirect_recursion_triangle2(i32 %z_new)
  ret void
}

; --- No Recursion ---
define void @no_recursion() {
entry:
  ret void
}

define void @indirect_recursion_triangle3(i32 %z) {
entry:
  %z_modulo = srem i32 %z, 2
  %cond = icmp eq i32 %z_modulo, 0
  br i1 %cond, label %if.even, label %if.odd

if.even:
  call void @indirect_recursion_triangle2(i32 %z)
  br label %if.end

if.odd:
  call void @indirect_recursion_triangle1(i32 %z)
  br label %if.end

if.end:
  ret void
}