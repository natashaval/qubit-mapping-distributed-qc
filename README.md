# qubit-mapping-distributed-qc
# Qubit Mapping for Simulated Distributed Quantum Computers

Required package: 
1. `pip install ipykernel qiskit pillow pylatexenc matplotlib qiskit[visualization] qiskit-ibm-runtime`
2. Benchmarking: `pip install mqt.bench openpyxl` for 5_benchmarking.ipynb and 6_table_plot.ipynb

## 0_generic_backend
Build coupling graph map with available layout are: full, line, ring, grid, t_horizontal, t_vertical

## 1_interaction_mapping
Apply InteractionLayout mapping to quantum circuit  
- Convert quantum circuit to Direct Acyclic Graph (DAG)
- Apply `InteractionLayout` mapping of the DAG to coupling map
- Rank all maps with Qubit Neighbourhood Value (QBN)
- Print best logical-to-physical with highest QBN value

## 2_interaction_layout
- Convert quantum circuit to DAG
- Apply `InteractionLayout` mapping
- Display mapped quantum circuit and logical to physical coupling map

## 3_lookahead_routing
- Convert quantum circuit to DAG
- Apply interaction layout mapping and retrieve the best layout
- Apply the mapping and fill out any empty ancilla
- Use dynamic `LookaheadSwap` routing
- Show added SWAP gates and the decomposed quantum circuit (a swap gate consists of 3 CX gates)
- Compare between BasicSwap, SabreSwap, and LookaheadSwap and the total number of added swap gates

## 4_validation_job_counts
- Transpile quantum circuit using SabreSwap and LookaheadSwap
- Run both jobs on simulated backend, get the probability counts
- Compare the result of the highest occurence between SabreSwap and LookaheadSwap
- If 70% of the highest occurences are similar, it can be concluded that the results from LookeaheadSwap are correct

