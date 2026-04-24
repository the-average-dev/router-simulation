# **Authors & Contributions**

**Team Name:** Three Idiots  
**Course:** CS572 – Modelling and Simulation  

| Name                  | Roll Number | Role / Main Focus Area |
| --------------------- | ----------- | ---------------------- |
| Harshal Maru          | 2303113     | Core Engine & Architecture |
| Siddharth Suryavanshi | 2303325     | Analytics & Visualization  |
| Om Joshi              | 2303311     | Queuing & Routing Logic    |

---

# **Detailed Contributions**

### Harshal Maru
**Focus:** Project Architecture, Core Simulation Engine, and Topologies.
* **`core/`**: Developed the underlying SimPy discrete-event environment, defining the Packet, Link, Router, and Network lifecycles.
* **`topology/`**: Implemented the graph building factories (Linear, Mesh, Partial Mesh, Star, Ring, Tree).
* **`traffic/`**: Built the Poisson-based traffic generator and randomized packet factories.
* **`config/` & `main.py`**: Handled JSON configuration parsing, dynamic parameter injection, and the command-line interface.
* **Project Setup**: Managed repository structure, `README.md`, `AUTHORS.md`, `requirements.txt`, and `.gitignore`.

### Om Joshi
**Focus:** Queuing Disciplines and Network Routing Algorithms.
* **`queueing/`**: Designed and implemented multiple queue management disciplines, including:
  * Baseline FIFO (First-In-First-Out)
  * Priority Queuing (PQ)
  * RED (Random Early Detection) for congestion avoidance
  * WFQ (Weighted Fair Queuing) for traffic class fairness
* **`routing/`**: Implemented pathfinding logic using NetworkX, including:
  * Static Dijkstra shortest-path computation.
  * Dynamic Bellman-Ford distance-vector routing (capable of adapting to link failures).

### Siddharth Suryavanshi
**Focus:** Data Collection, Mathematical Metrics, and Visualization.
* **`metrics/`**: Developed the passive `MetricsCollector` to securely log simulation events without bottlenecking the core engine.
  * Implemented `per_router.py` (Drop Rates, Queue Lengths, Acceptance logic).
  * Implemented `end_to_end.py` (Average Delay, Throughput, Hop Counts).
* **`viz/`**: Built the Matplotlib visualization suite.
  * `plot_metrics.py` (Queue length step-plots and Utilization/Drop rate bar charts).
  * `plot_delay_cdf.py` (Cumulative Distribution Functions for QoS traffic analysis).
  * `plot_topology.py` (Dynamic network map rendering).

### Shared Contributions
* Integration of modules and pipeline testing.
* Implementation of edge-case handling 
* Debugging, mathematical verification of simulation outputs, and final code polishing.