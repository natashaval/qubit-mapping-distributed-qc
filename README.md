# Dynamic Qubit Mapping for Simulated Distributed Quantum Computers

Required package: 
1. `pip install ipykernel qiskit pillow pylatexenc matplotlib qiskit[visualization] qiskit-ibm-runtime`
2. Benchmarking: `pip install mqt.bench openpyxl` for *5_benchmarking.ipynb* and *6_table_plot.ipynb*

## 0_generic_backend
Build coupling graph map with available layout are: full, line, ring, grid, t_horizontal, t_vertical

## 1_interaction_mapping 
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

## 5_benchmarking
- Try with several [layouts](#layouts)  
- Save in JSON tree structure: circuit_size -> algorithm_name -> size, depth, swap, interval  
use routing: BasicSwap, SabreSwap, and LookaheadSwap  
filename: `result/benchmarking_FINAL.json`  

## 6_table_plot
- parse json result in Panda DataFrame
- sorted by *benchmark* and *layout*
- print data in table format in file `.tex` in folder _latex_
- save data in `.xlsx` in folder _excel_

## Layouts
| **Layout**   | **Number of qubits** | **Number of groups** |
|--------------|----------------------|----------------------|
| Full         | 20                   | 1                    |
| Full         | 10                   | 2                    |
| Grid         | 9                    | 2                    |
| Ring         | 10                   | 2                    |
| Full         | 7                    | 3                    |
| Grid         | 8                    | 3                    |
| Ring         | 7                    | 3                    |
| Full         | 5                    | 4                    |
| Grid         | 6                    | 4                    |
| Ring         | 5                    | 4                    |
| T Horizontal | 5                    | 4                    |
| T Vertical   | 5                    | 4                    |
| Line         | 1                    | 20                   |