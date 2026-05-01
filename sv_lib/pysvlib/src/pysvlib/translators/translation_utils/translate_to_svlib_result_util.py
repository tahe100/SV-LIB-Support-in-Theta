# This file is part of SV-LIB: A Standard Exchange Format for Software-Verification Tasks
# https://gitlab.com/sosy-lab/benchmarking/sv-lib
#
# SPDX-FileCopyrightText: 2026 The SV-LIB Maintainers
#
# SPDX-License-Identifier: Apache-2.0
from typing import Any

import networkx

from pysvlib.translators.translation_utils.translate_to_svlib_result import TranslateToProcedureResult


class TranslateToSvLibResultUtil:
    @staticmethod
    def find_recursive_pools(
        translated_procedures: tuple[TranslateToProcedureResult, ...],
    ) -> tuple[tuple[TranslateToProcedureResult, ...], ...]:
        """
        Returns the pools of recursive procedures (both direct and indirect) that are found by analyzing the Strongly
        Connected Components (SCCs) of the procedure call graph.
        """
        graph = networkx.DiGraph()

        # add nodes, where each procedure represents a node
        for proc in translated_procedures:
            graph.add_node(proc.name, obj=proc)

        # add edges, where each procedure call represents an edge
        for proc in translated_procedures:
            for annotated in proc.translated_annotated:
                for statement in annotated.translated_statements:
                    if statement.called_proc_name is not None:
                        graph.add_edge(proc.name, statement.called_proc_name)

        sccs: list[list[TranslateToProcedureResult]] = []

        for scc in networkx.strongly_connected_components(graph):
            if len(scc) > 1:
                sccs.append([graph.nodes[name]["obj"] for name in scc if name in graph.nodes])
            else:
                name = next(iter(scc))
                if graph.has_edge(name, name):
                    sccs.append([graph.nodes[name]["obj"]])

        return tuple(tuple(scc) for scc in sccs)

    @staticmethod
    def sort_procedure_pools_by_dependencies(
        translated_procedures: tuple[TranslateToProcedureResult, ...],
        recursive_pools: tuple[tuple[TranslateToProcedureResult, ...], ...],
    ) -> tuple[tuple[TranslateToProcedureResult, ...], ...]:
        """
        Returns the sorted pools of procedures by creating a dependency graph where:
        - A directed dependency edge A -> B is added if any procedure in pool A calls a procedure in pool B.
        - If pool A depends on pool B (i.e., A calls B), then B appears before A.
        - Recursive procedure pools remain grouped together in the result.
        - Non-recursive procedure are treated as individual pools.

        Ensures that:
        - The inner tuples are never empty.
        - The non-recursive procedure pools always have a single element.
        """

        # map proc names to pool ids
        name_to_pool: dict[str, int] = {}
        for i, pool in enumerate(recursive_pools):
            for proc in pool:
                name_to_pool[proc.name] = i

        next_pool_id = len(recursive_pools)
        for proc in translated_procedures:
            if proc.name not in name_to_pool:
                name_to_pool[proc.name] = next_pool_id
                next_pool_id += 1

        # build reversed dependency graph
        pool_graph = networkx.DiGraph()
        for pool_id in set(name_to_pool.values()):
            pool_graph.add_node(pool_id)

        for proc in translated_procedures:
            src_pool = name_to_pool[proc.name]
            for annotated in proc.translated_annotated:
                for statement in annotated.translated_statements:
                    if statement.called_proc_name is not None and statement.called_proc_name in name_to_pool:
                        dst_pool = name_to_pool[statement.called_proc_name]
                        if src_pool != dst_pool:
                            # edge goes from called_proc_name to caller
                            # which means called_proc_name must be "visited" before caller
                            pool_graph.add_edge(dst_pool, src_pool)

        # group procedure and compute stable priorities
        pool_id_to_procedures: dict[int, list[TranslateToProcedureResult]] = {}
        for proc in translated_procedures:
            pool_id = name_to_pool[proc.name]
            pool_id_to_procedures.setdefault(pool_id, []).append(proc)

        # topological sort. because edges are called_proc_name -> caller, leaf nodes are procedures with no dependencies
        sorted_pool_ids = list(networkx.topological_sort(pool_graph))

        sorted_procedure_pools: tuple[tuple[TranslateToProcedureResult, ...], ...] = tuple(
            tuple(pool_id_to_procedures[pool_id]) for pool_id in sorted_pool_ids
        )

        # always perform sanity checks before returning
        TranslateToSvLibResultUtil.check_non_empty_inner_tuples(sorted_procedure_pools)
        TranslateToSvLibResultUtil.check_non_recursive_pools_have_single_element(
            sorted_procedure_pools, recursive_pools
        )

        return sorted_procedure_pools

    @staticmethod
    def check_non_empty_inner_tuples(tuple_with_tuples: tuple[tuple[Any, ...], ...]):
        """
        Checks if any inner tuple is empty and throws a ValueError if an empty tuple is found.
        Note that the outer tuple itself can be empty.
        """
        for inner_tuple in tuple_with_tuples:
            if len(inner_tuple) == 0:
                raise ValueError("The outer tuple contains an empty inner tuple.")

    @staticmethod
    def check_non_recursive_pools_have_single_element(
        all_procedure_pools: tuple[tuple[TranslateToProcedureResult, ...], ...],
        recursive_procedure_pools: tuple[tuple[TranslateToProcedureResult, ...], ...],
    ):
        """
        Checks if all non-recursive procedure pools (that are not in recursive_procedure_pools) have length 1 and throws
        a ValueError otherwise.
        """
        recursive_pool_names: frozenset[frozenset[str]] = TranslateToSvLibResultUtil.get_procedure_pool_names(
            recursive_procedure_pools
        )
        for proc_pool in all_procedure_pools:
            proc_pool_names: frozenset[str] = frozenset(proc.name for proc in proc_pool)
            if proc_pool_names not in recursive_pool_names and len(proc_pool) != 1:
                raise ValueError(
                    f"The following procedure pool is not recursive and has a size other than 1: {proc_pool_names}"
                )

    @staticmethod
    def get_procedure_pool_names(
        procedure_pools: tuple[tuple[TranslateToProcedureResult, ...], ...],
    ) -> frozenset[frozenset[str]]:
        """
        Converts the given procedure_pools into a set of procedure names that is useful for identifying procedure pools.
        """
        return frozenset(frozenset(proc.name for proc in proc_pool) for proc_pool in procedure_pools)
