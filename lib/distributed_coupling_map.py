from qiskit.transpiler import CouplingMap
from qiskit_ibm_runtime.fake_provider import FakeLondonV2

"""
From documentation: https://docs.quantum.ibm.com/api/qiskit/qiskit.transpiler.CouplingMap
"""

# coupling list ring: Return a coupling map of n qubits connected to each of their neighbors in a ring.
def build_coupling_list_ring(num_qubits: int, num_group: int):
    coupling_list = []
    for i in range(num_group):
        cm = CouplingMap.from_ring(num_qubits, bidirectional=True)
        edges = [
            (i * num_qubits + node1, i * num_qubits + node2)
            for node1, node2 in cm.get_edges()
        ]
        coupling_list.extend(edges)

    for i in range(1, num_group):
        coupling_list.append((i * num_qubits, i * num_qubits - 1))
        coupling_list.append((i * num_qubits - 1, i * num_qubits))
    return coupling_list

# coupling list full: Return a fully connected coupling map on n qubits.
def build_coupling_list_full(num_qubits: int, num_group: int):
    coupling_list = []
    for i in range(num_group):
        cm = CouplingMap.from_full(num_qubits, bidirectional=True)
        edges = [
            (i * num_qubits + node1, i * num_qubits + node2)
            for node1, node2 in cm.get_edges()
        ]
        coupling_list.extend(edges)

    for i in range(1, num_group):
        coupling_list.append((i * num_qubits, i * num_qubits - 1))
        coupling_list.append((i * num_qubits - 1, i * num_qubits))
    return coupling_list

# coupling list line: Return a coupling map of n qubits connected in a line.
def build_coupling_list_line(num_qubits: int, num_group: int):
    cm = CouplingMap.from_line(num_qubits=num_qubits * num_group, bidirectional=True)
    return cm.get_edges()

# coupling list grid: Return a coupling map of qubits connected on a grid of num_rows x num_columns.
def build_coupling_list_grid(num_rows: int, num_columns: int, num_group: int):
    coupling_list = []
    multiplier = num_rows * num_columns
    for i in range(num_group):
        cm = CouplingMap.from_grid(num_rows, num_columns, bidirectional=True)
        edges = [
            (i * multiplier + node1, i * multiplier + node2)
            for node1, node2 in cm.get_edges()
        ]
        coupling_list.extend(edges)

    for i in range(1, num_group):
        coupling_list.append((i * multiplier, i * multiplier - 1))
        coupling_list.append((i * multiplier - 1, i * multiplier))
    return coupling_list

# coupling list t_horizontal: Return a coupling map of 5 T-shaped qubits connected on longer end.
def build_coupling_list_t_horizontal(
    num_group: int,
):  # num qubits = 5, horizontal connect with 4
    coupling_list = []
    fake_london = FakeLondonV2()
    cm = fake_london.coupling_map
    num_qubits = fake_london.num_qubits
    for i in range(num_group):
        edges = [
            (i * num_qubits + node1, i * num_qubits + node2)
            for node1, node2 in cm.get_edges()
        ]
        coupling_list.extend(edges)

    for i in range(1, num_group):
        coupling_list.append((i * num_qubits, i * num_qubits - 1))
        coupling_list.append((i * num_qubits - 1, i * num_qubits))
    return coupling_list

# coupling list t_vertical: Return a coupling map of 5 T-shaped qubits connected on shorter end.
def build_coupling_list_t_vertical(num_group: int):
    coupling_list = []
    fake_london = FakeLondonV2()
    cm = fake_london.coupling_map
    num_qubits = fake_london.num_qubits
    for i in range(num_group):
        edges = [
            (i * num_qubits + node1, i * num_qubits + node2)
            for node1, node2 in cm.get_edges()
        ]
        coupling_list.extend(edges)

    for i in range(1, num_group):
        coupling_list.append((i * num_qubits, i * num_qubits - 3))
        coupling_list.append((i * num_qubits - 3, i * num_qubits))
    return coupling_list