import ast
import numpy as np
from qiskit.transpiler import CouplingMap
from qiskit.dagcircuit import DAGCircuit


class InteractionMapping:
    def __init__(self, coupling_map: CouplingMap, dag: DAGCircuit):
        super().__init__()
        self.coupling_map = coupling_map
        self.dag = dag
        self.maps = []  # return tuple (logical qubit q_i, physical qubit Q_i)
        self.assigned_qubits = []
        self.assigned_physical_qubits = []
        self.qpi_rank = {}  # dict key = map of tuple(log, phy); value = total_qpi_value
        self.swap_add = 0  # TODO: to be removed

        # run calculation
        self.calculate_final_maps()

    def calculate_logical_priority(
        self, dag: DAGCircuit
    ):  # the total number of operation gates in logical wire
        priority_dict = {qubit: 0 for qubit in range(dag.num_qubits())}
        for node in dag.two_qubit_ops():
            for qubit in [
                qubit._index for qubit in node.qargs
            ]:  # handle two-qubit gate only
                priority_dict[qubit] += 1
        return priority_dict

    def calculate_physical_connectivity(
        self, coupling_map: CouplingMap
    ):  # the total number of edges per node in coupling map
        return {
            qubit: len(list(coupling_map.neighbors(qubit)))
            for qubit in coupling_map.physical_qubits
        }

    def calculate_physical_neighbors(self, coupling_map: CouplingMap):
        return {
            qubit: list(iter(coupling_map.neighbors(qubit)))
            for qubit in coupling_map.physical_qubits
        }

    def calculate_logical_neighbors(self, dag: DAGCircuit):
        neighbor_dict = {qubit: [] for qubit in range(dag.num_qubits())}
        for node in dag.two_qubit_ops():
            log0, log1 = node.qargs[0]._index, node.qargs[1]._index
            if log1 not in neighbor_dict[log0]:
                neighbor_dict[log0].append(log1)
            if log0 not in neighbor_dict[log1]:
                neighbor_dict[log1].append(log0)
        return neighbor_dict

    def generate_qpi(self, dag: DAGCircuit):  # Qubit Pair (QP) Interaction
        total_two_gate = len(dag.two_qubit_ops())
        weight_gate = list(range(total_two_gate, 0, -1))
        interaction = np.zeros(shape=(dag.num_qubits(), dag.num_qubits()))
        for index, node in enumerate(dag.two_qubit_ops()):
            log0, log1 = node.qargs[0]._index, node.qargs[1]._index
            interaction[log0][log1] += weight_gate[index]
            interaction[log1][log0] += weight_gate[index]
        return interaction

    def adjacent_physical_qubits(
        self, assigned_physical_qubits, physical_neighbors: dict
    ) -> dict:
        adj = {}
        for physical_qubit in assigned_physical_qubits:
            adj[physical_qubit] = [
                phy_bit
                for phy_bit in physical_neighbors[physical_qubit]
                if phy_bit not in assigned_physical_qubits
            ]

        return adj

    def has_no_neighbor(
        self, curr_qubit: int, assigned_qubits: list, logical_neighbors: dict[int, list]
    ) -> bool:
        return all(
            curr_qubit not in logical_neighbors[assigned]
            for assigned in assigned_qubits
        )

    def calculate_highest_qbn(
        self, curr_logical_qubit, neighbors_physical_qubits, qpi_matrix, maps
    ):
        qbn = {}
        for assigned, available in neighbors_physical_qubits.items():
            logical_from_assigned = next(t[0] for t in maps if t[1] == assigned)
            for candidate in available:
                qbn[candidate] = (
                    qbn.get(candidate, 0)
                    + qpi_matrix[logical_from_assigned][curr_logical_qubit]
                )
            max_qbn_value = max(qbn.values(), default=0)
            if all(qbn.values()) == 0:
            # check if all QBN value is 0, then choose the first node
                qbn = {next(iter(qbn)) : 0}
            else:
                qbn = {k: v for k, v in qbn.items() if v == max_qbn_value}
        return qbn, max_qbn_value

    def highest_index(self, dicts) -> int:
        index = max(dicts, key=dicts.get)
        return index

    def extract_tuple(self, maps):
        return [t[0] for t in maps], [t[1] for t in maps]

    def add_mapping(self, pairs, m, max_qpi_value=0):
        new_mappings = []
        for mapping in m:
            if str(mapping) in self.qpi_rank:
                last_qpi_value = self.qpi_rank.pop(str(mapping))
            else:
                last_qpi_value = 0
            for pair in pairs:
                new_mapping = mapping.copy()  # Create a new list for each mapping
                new_mapping.append(pair)  # Add the pair to the new mapping
                self.qpi_rank[str(new_mapping)] = last_qpi_value + max_qpi_value
                new_mappings.append(new_mapping)  # Append the new mapping to the result
        return new_mappings

    def calculate_final_maps(self):
        # initialize
        qpi_matrix = self.generate_qpi(self.dag)
        logical_priority = self.calculate_logical_priority(self.dag)
        physical_connectivity = self.calculate_physical_connectivity(self.coupling_map)

        # check if fully connected, return corresponding index
        if all(
            value == len(self.coupling_map.physical_qubits) - 1
            for value in physical_connectivity.values()
        ):
            self.maps = [[(idx, idx) for idx in range(self.dag.num_qubits())]]
            self.qpi_rank[str(self.maps[0])] = self.coupling_map.physical_qubits
            return self.maps

        logical_neighbors = self.calculate_logical_neighbors(self.dag)
        physical_neighbors = self.calculate_physical_neighbors(self.coupling_map)

        # Assign first priority logical qubit to highest physical connectivity qubit
        high_logical = self.highest_index(logical_priority)
        high_physical = self.highest_index(physical_connectivity)
        logical_priority.pop(high_logical)
        self.maps = [[(high_logical, high_physical)]]

        while logical_priority:
            for i in range(len(self.maps)):
                m = self.maps.pop(0)
                # get highest value from dictionary, return key
                curr_qubit = self.highest_index(
                    logical_priority
                )  # Get the logical qubit with the highest QPI (Quantum Priority Index).
                curr_neighbors = logical_neighbors[
                    curr_qubit
                ]  # Obtain the logical neighbors of the current qubit.
                self.assigned_qubits, self.assigned_physical_qubits = (
                    self.extract_tuple(m)
                )
                temp_physical_connectivity = {
                    k: v
                    for k, v in physical_connectivity.items()
                    if k not in self.assigned_physical_qubits
                }  # only take physical qubits that are not occupied
                if self.has_no_neighbor(
                    curr_qubit, self.assigned_qubits, logical_neighbors
                ):
                    best_physical_bit = self.highest_index(
                        temp_physical_connectivity
                    )  # Get the unassigned physical qubit with the highest PCS (Physical Connectivity Strength).
                    m_temp = self.add_mapping([(curr_qubit, best_physical_bit)], [m])

                else:
                    neighbors_physical_qubits = self.adjacent_physical_qubits(
                        self.assigned_physical_qubits, physical_neighbors
                    )
                    best_physical_bit, max_qpi_value = self.calculate_highest_qbn(
                        curr_qubit, neighbors_physical_qubits, qpi_matrix, m
                    )  # Choose the physical location with the highest QBN (Qubit Interaction Neighborhood).
                    m_temp = self.add_mapping(
                        [(curr_qubit, phy) for phy in best_physical_bit.keys()],
                        [m],
                        max_qpi_value,
                    )

                for temp in m_temp:
                    self.maps.append(temp)
            logical_priority.pop(curr_qubit)
        return self.maps

    def get_best_qpi_layout(self):
        best_qpi_rank = self.highest_index(self.qpi_rank)
        qpi_layout = list(ast.literal_eval(best_qpi_rank))
        return qpi_layout
