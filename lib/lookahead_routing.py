from qiskit.transpiler import CouplingMap, TransformationPass, Layout
from qiskit.transpiler.target import Target
from qiskit.dagcircuit import DAGCircuit, DAGOpNode
from qiskit.transpiler.exceptions import TranspilerError
from qiskit.circuit.library.standard_gates import SwapGate

class DynamicLookaheadSwap(TransformationPass):
    def __init__(self, coupling_map):
        super().__init__()
        if isinstance(coupling_map, Target):
            self.target = coupling_map
            self.coupling_map = self.target.build_coupling_map()
        else:
            self.target = None
            self.coupling_map = coupling_map
        self.dlist = [] # SAVE as index, instead of DAGOpNode; only for two-qubit gates
        self.op_gates = [] # SAVE reference of gate
        self.swap_add = 0

    def list_gates(self, dag: DAGCircuit): # populate gates at current_idx because list(iter(dag.op_nodes())) shuffled bcs of greedy algorithm
        gate_list = []
        for layer in dag.layers():
            for node in layer['graph'].op_nodes():
                gate_list.append(node)
        return gate_list

    def list_gates_on_qubit_dag(self, dag: DAGCircuit): # TODO: LIST_GATE ALREADY layers(), but dependency list NOT YET
        index = 0
        dependency_list = {qubit: [] for qubit in range(dag.num_qubits())}
        for layer in dag.layers():
            for operation in layer['graph'].op_nodes():
                qubits = [qubit._index for qubit in operation.qargs]
                if len(qubits) == 2: # HANDLE ONLY TWO-QUBIT GATE IN DEPENDENCY LIST
                    for qubit in qubits: # handle single and two-qubit gate
                        dependency_list[qubit].append(index)
                index += 1
        return dependency_list
    
    def generate_possible_swaps(self, act_list: list[int], coupling_map: CouplingMap, current_layout: Layout, assigned_swap: list[tuple]):
        candi_list = []
        for act_idx in act_list:
            node = self.op_gates[act_idx]
            phy0, phy1 = current_layout.get_virtual_bits()[node.qargs[0]], current_layout.get_virtual_bits()[node.qargs[1]]
            candi_list.extend([(phy0, neighbor) for neighbor in coupling_map.neighbors(phy0) if (phy0, neighbor) not in assigned_swap + candi_list and (neighbor, phy0) not in assigned_swap + candi_list])
            candi_list.extend([(phy1, neighbor) for neighbor in coupling_map.neighbors(phy1) if (phy1, neighbor) not in assigned_swap + candi_list and (neighbor, phy1) not in assigned_swap + candi_list])
        return candi_list
    
    def calc_effect_gate(self, node: DAGOpNode, swap_nodes: tuple, coupling_map: CouplingMap, current_layout: Layout):
        idx0, idx1 = node.qargs[0]._index, node.qargs[1]._index
        phy0, phy1 = current_layout.get_virtual_bits()[node.qargs[0]], current_layout.get_virtual_bits()[node.qargs[1]]
        old_distance = self.coupling_map.distance(phy0, phy1)
        if phy0 in swap_nodes:
            phy0 = swap_nodes[1] if phy0 == swap_nodes[0] else swap_nodes[0]
        if phy1 in swap_nodes:
            phy1 = swap_nodes[1] if phy1 == swap_nodes[0] else swap_nodes[0]
            
        new_distance = coupling_map.distance(phy0, phy1)
        return old_distance - new_distance
    
    """gate_list = in logical qubit"""
    def sum_effect(self, gate_list: list[int], act_list: list[int], swap: tuple, coupling_map: CouplingMap, current_layout: Layout, str):
        is_remove = False
        total_sum = 0
        for gate_idx in gate_list:
            node = self.op_gates[gate_idx]
            if node.op.num_qubits == 2 and node.name not in ["barrier", "measure"]: # TODO: don't calculate if barrier or measure gate AND make sure that only lookahead for next wo-qubit gates ONLY
                value = self.calc_effect_gate(node=node, swap_nodes=swap, coupling_map=coupling_map, current_layout=current_layout)
                if value < 0 and gate_idx in act_list:
                    is_remove = True
                    return total_sum, is_remove
                elif value < 0:
                    break
                elif value == 0 or value == 1:
                    total_sum += value

        return total_sum, is_remove
    
    def check_gate_connectivity(self, act_list: list[int], new_dag: DAGCircuit, current_layout: Layout):
        new_act_list = []
        for act_idx in act_list:
            node = self.op_gates[act_idx]
            idx0, idx1 = node.qargs[0]._index, node.qargs[1]._index # original gate index
            phy0, phy1 = current_layout.get_virtual_bits()[node.qargs[0]], current_layout.get_virtual_bits()[node.qargs[1]]
            distance = self.coupling_map.distance(phy0, phy1)
            if  distance == 1:
                self.dlist[idx0].pop(0)
                self.dlist[idx1].pop(0)
                node.qargs = (self.cannonical_register[phy0], self.cannonical_register[phy1])
                new_dag.apply_operation_back(node.op, qargs=node.qargs) # RESOLVED ISSUE HERE, instead of sending gate memory address, send the operation; that is the reason why it yield square box during circuit.draw()
                
            else:
                new_act_list.append(act_idx)
        return new_act_list, new_dag

    def measure_node(self, node: DAGOpNode, current_layout: Layout, num_clbits) -> DAGOpNode:
        log0 = current_layout.get_physical_bits()[node.qargs[0]._index]._index
        classical0 = self.property_set['layout'].get_physical_bits()[log0]._index
        # check if only available in cargs, because not all are mapped to classical register ex: deutsch-josza mqtbench dj 10
        if classical0 < num_clbits:
            node.cargs = (self.meas_register[classical0], )
        else: # if not mapped to cargs, cast to log0 ?
            # node.cargs = (self.meas_register[log0], ) # if not mapped to cargs, change to empty
            log0 = current_layout.get_physical_bits()[classical0]._index
            classical0 = self.property_set['layout'].get_physical_bits()[log0]._index
            node.cargs = (self.meas_register[classical0], )
        return node

    def run(self, dag: DAGCircuit):

        self.dlist = self.list_gates_on_qubit_dag(dag)
        self.op_gates = self.list_gates(dag)

        # self.op_gates = list(iter(dag.op_nodes())) # ERROR because layers() is different from serial_layers() order
        new_dag = dag.copy_empty_like()

        self.cannonical_register = dag.qregs['q']
        if dag.cregs:
            self.meas_register = dag.cregs['meas'] if 'meas' in dag.cregs else dag.cregs['c']
        current_layout = Layout.generate_trivial_layout(self.cannonical_register)
        order = current_layout.reorder_bits(new_dag.qubits)
        
        # active gate list per gate, not using greedy algorithm anymore because messed up with indexing
        curr_idx = 0 # curr_idx variable to count how many operation gate in the circuit
        is_print_curr_layout = False
        for layer in dag.layers():
            self.swap_add = 0
            subdag = layer['graph']
            act_list = []
            # line 15 - 24 initialize first do while with original coupling_map
            for node in subdag.op_nodes():
                if node.op.num_qubits == 2: # only check for two-qubit gates, cannot exclude >2 gate because there is barrier
                    new_act_list, new_dag = self.check_gate_connectivity([curr_idx], new_dag, current_layout)
                    act_list = act_list + new_act_list
                else:
                    if node.name == 'measure': # TODO: handle measure node to conform with curr_layout
                        # continue
                        node = self.measure_node(node, current_layout, num_clbits=dag.num_clbits())
                        
                    # self.dlist[node.qargs[0]._index].pop(0)
                    new_dag.apply_operation_back(node.op, qargs=node.qargs, cargs=node.cargs)
                curr_idx += 1
            assigned_swap_list = [] # to avoid recursive swap
            # line 15
            while act_list: # check if act_list is not empty
                if self.swap_add > 50: # TODO: to be removed
                    raise Exception("Swap add timeout.")
                self.swap_add += 1

                act_list, new_dag = self.check_gate_connectivity(act_list, new_dag, current_layout)
                
                candi_list = self.generate_possible_swaps(act_list, self.coupling_map, current_layout, assigned_swap_list)
                # line 27 - 29
                MCPE_cost = {}
                for swap in candi_list:
                    log0, log1 = current_layout.get_physical_bits()[swap[0]]._index, current_layout.get_physical_bits()[swap[1]]._index
                    first_total_sum, is_first_remove = self.sum_effect(gate_list=self.dlist[log0], act_list=act_list, swap=swap, coupling_map=self.coupling_map, current_layout=current_layout, str='F')
                    second_total_sum, is_second_remove = self.sum_effect(self.dlist[log1], act_list, swap, self.coupling_map, current_layout, 'S')

                    if not is_first_remove and not is_second_remove:
                        MCPE_cost[swap] = first_total_sum + second_total_sum

                # check if MCPE is not empty dict
                if MCPE_cost:
                    MCPE_cost = dict(sorted(MCPE_cost.items(), key=lambda item: item[1], reverse=True))
                    # line 31 update CouplingMap with new SWAP
                    selected_swap, selected_value = next(iter(MCPE_cost.items())) # GFG take the first next key using next() and iter function is used to get the iterable conversion of dictionary items
                    if selected_value > 0: # add check only if worth it to do swap, if not will do recursive swap
                        current_layout.swap(selected_swap[0], selected_swap[1])
                        # assigned_swap_list.append(selected_swap) # TODO: IS THIS RECURSIVE?
                        
                        swap_layer = DAGCircuit()
                        swap_layer.add_qreg(self.cannonical_register)

                        swap_log0, swap_log1 = current_layout.get_physical_bits()[selected_swap[0]], current_layout.get_physical_bits()[selected_swap[1]]

                        swap_layer.apply_operation_back(SwapGate(), qargs=(swap_log0, swap_log1), cargs=())

                        order = current_layout.reorder_bits(new_dag.qubits)
                        new_dag.compose(swap_layer, qubits=order)
        return new_dag