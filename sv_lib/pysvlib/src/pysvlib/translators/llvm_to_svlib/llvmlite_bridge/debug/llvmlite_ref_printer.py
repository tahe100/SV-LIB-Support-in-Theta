# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0

from llvmlite.binding import ValueRef


def debug_print_value_ref(value_ref: ValueRef):
    """
    Safely prints all available attributes of a ValueRef including operands, without triggering recursive crashes.
    Unfortunately, the debugger crashes when inspecting ValueRefs. This function should not be used in production.
    """
    if not value_ref:
        print("ValueRef: None")
        return

    # basics
    info = {
        "str": str(value_ref).strip(),
        "name": value_ref.name,
        "type": str(value_ref.type),
        "type_kind": str(value_ref.type.type_kind),
        "value_kind": str(value_ref.value_kind),
    }

    operands_preview: list[str] = []

    info["is_global"] = value_ref.is_global
    info["is_function"] = value_ref.is_function
    info["is_argument"] = value_ref.is_instruction
    info["is_instruction"] = value_ref.is_function

    # conditional Attributes (only access if the flag is True)
    if value_ref.is_instruction:
        operands_preview = [str(op).strip() for op in value_ref.operands]
        info["opcode"] = value_ref.opcode
        info["num_operands"] = len(operands_preview)

    if value_ref.is_global or value_ref.is_function:
        info["linkage"] = str(value_ref.linkage)
        info["visibility"] = str(value_ref.visibility)
        info["storage_class"] = str(value_ref.storage_class)

    if value_ref.is_function:
        info["is_declaration"] = value_ref.is_declaration

    print("--- llvmlite ValueRef ---")
    for key, value in info.items():
        print(f"{key:20}{value}")

    if operands_preview:
        print("operands")
        for i, op_str in enumerate(operands_preview):
            print(f"  [{i}] {op_str}")

    print("-------------------------")
    print("\n")
