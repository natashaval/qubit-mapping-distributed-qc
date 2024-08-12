from qiskit.transpiler import CouplingMap, AnalysisPass, Layout
from qiskit.transpiler.target import Target
from qiskit.dagcircuit import DAGCircuit
from qiskit.transpiler.exceptions import TranspilerError

class InteractionLayout(AnalysisPass):
    def __init__(self, coupling_map: CouplingMap, initial_map: list[tuple]):        
        super().__init__()
        if isinstance(coupling_map, Target):
            self.target = coupling_map
            self.coupling_map = self.target.build_coupling_map()
            self.initial_map = initial_map
        else:
            self.target = None
            self.coupling_map = coupling_map
            self.initial_map = initial_map

    def build_layout(self, map: list[tuple], dag: DAGCircuit) -> Layout:
        cannonical_register = dag.qregs['q']
        layout = Layout()
        for logical, physical in map:
            layout.add(virtual_bit=cannonical_register[logical], physical_bit=physical)
        return layout

    def run(self, dag: DAGCircuit):
        if self.target is not None:
            if dag.num_qubits() > self.target.num_qubits:
                raise TranspilerError("Number of qubits greater than device.")
        elif dag.num_qubits() > self.coupling_map.size():
            raise TranspilerError("Number of qubits greater than device.")

        layout = self.build_layout(self.initial_map, dag)
        self.property_set["layout"] = layout
        return dag