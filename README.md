# Router Simulation - Discrete Event Network Simulator

A highly modular, discrete-event network simulator built in Python using **SimPy** and **NetworkX**. Designed for the **CS572 – Modelling and Simulation** course at IIT, this engine accurately models packet generation, queuing theory, network routing, and link transmission physics to analyze complex network behaviors under varying loads and failure conditions.

## Key Features

* **Discrete-Event Core:** Powered by SimPy, accurately modeling real-world timing, propagation delay, and bandwidth bottlenecks down to the microsecond.
* **Dynamic Routing:** Implements both Static (**Dijkstra**) and Dynamic (**Bellman-Ford**) routing algorithms.
* **Advanced Queueing Disciplines:** Supports multiple queue scheduling algorithms:
  * `fifo`: First-In-First-Out baseline.
  * `priority`: Strict priority queueing (VoIP > Bulk > Best Effort).
  * `wfq`: Weighted Fair Queueing for proportional bandwidth sharing.
  * `red`: Random Early Detection for active queue management and congestion avoidance.
* **Custom Network Topologies:** Generate `linear`, `ring`, `star`, `mesh`, `partial_mesh`, or `tree` networks dynamically.
* **Traffic Generation:** Poisson-process based packet injection with customizable traffic classes, priority mapping, and mean packet sizes.
* **Fault Injection :** Programmable network link failures to test dynamic rerouting and network resilience mid-simulation.
* **Automated Visualization:** Generates publication-ready Matplotlib graphs for network topology, queue lengths, CDF of end-to-end delays, and router utilization/drop rates.

---

## Installation & Setup

**Prerequisites:** Python 3.1+

1. **Clone the repository:**
   ```bash
   git clone https://github.com/the-average-dev/router-simulation.git
   cd router-simulation
   ```

2. **Install the required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Required packages: `simpy`, `networkx`, `matplotlib`)*

3. **Run the simulation:**
   ```bash
   python main.py config/config.json
   ```

---

## How It Works (Simulation Pipeline)

1. **Initialization:** The simulator reads the `config.json` file, builds the requested **Topology**, and instantiates the Routers and Links.
2. **Pre-computation:** The **Routing** module calculates the optimal shortest paths across the entire graph.
3. **Traffic Generation:** The **Traffic** module continuously injects packets into random source routers based on an exponential inter-arrival distribution.
4. **Queuing & Processing:** When a packet hits a router, it is placed in the **Queue**. If the queue is full, the packet is dropped (or dropped probabilistically if using RED). The queue discipline decides the order in which packets are processed.
5. **Transmission:** The **Core** module reserves the physical link resource, calculates transmission delay, and yields the SimPy event.
6. **Data Collection:** Throughout the entire lifecycle, the **Metrics** module passively listens to events (Arrival, Enqueue, Drop, Forward, Deliver) to calculate End-to-End statistics.

---

## Project Structure

```text
router-simulation/
├── config/              # JSON configuration files for simulation parameters
├── core/                # Core SimPy logic (Simulation, Network, Router, Link, Packet)
├── metrics/             # Event collectors and statistical calculators
├── queueing/            # Queueing disciplines (FIFO, PQ, WFQ, RED)
├── routing/             # Graph traversal algorithms (Dijkstra, Bellman-Ford)
├── topology/            # Network graph generators (Mesh, Star, Tree, etc.)
├── traffic/             # Poisson-process traffic generators & Packet Factories
├── viz/                 # Matplotlib automated graphing engines
├── main.py              # CLI entry point
└── requirements.txt     # Python dependencies
```

---

## Configuration Guide (config.json)

The entire simulation is controlled via a single JSON configuration file. No code changes are necessary to test different scenarios.

```json
{
  "simulation": {
    "duration": 5000,
    "random_seed": 42
  },
  "traffic": {
    "arrival_rate": 200,             // Packets generated per second globally
    "packet_size_mean": 1024,        // Mean packet size in bytes
    "classes": ["voip", "bulk", "best_effort"],
    "class_weights": [0.2, 0.5, 0.3] // Distribution of traffic classes
  },
  "network": {
    "topology": "partial_mesh",      // linear, mesh, partial_mesh, star, ring, tree
    "num_routers": 10,
    "link_bandwidth": 2000000,       // Bits per second (bps)
    "link_delay": 0.005,             // Propagation delay in seconds
    "link_probability": 0.6          // Used for partial_mesh connectivity
  },
  "queueing": {
    "discipline": "wfq",             // fifo, priority, wfq, red
    "queue_cap": 100,                // Maximum packets a router can hold
    "wfq_weights": { "1": 5.0, "2": 2.0, "3": 1.0 },
    "red_p_max": 0.15,
    "red_wq": 0.002
  },
  "routing": {
    "algorithm": "bellman_ford"      // dijkstra, bellman_ford
  },
  "events": {
    "link_failure": {                // Chaos Monkey: Simulates mid-simulation link cuts
      "enabled": true,
      "trigger_time": 300,
      "duration": 500
    }
  }
}
```

---

## Outputs & Visualization

Upon completion, the simulator outputs a detailed text summary to the console featuring:
* **Per-Router Metrics:** Total Arrivals, Enqueues, Drops, Drop Rate %, and Queue Acceptance Rate.
* **End-to-End Metrics:** Total Delivered, Average Delay, Throughput (pkts/sec), and Average Hop Count.

Additionally, high-resolution `.png` graphs are automatically generated and saved to the `graphs/` folder:
1. `network_topology.png`: A visual node-edge map of the generated network.
2. `queue_length_over_time.png`: Step-plots showing congestion build-up and clearing for every router.
3. `acceptance_and_drop_rate.png`: A comparative bar chart identifying bottleneck routers.
4. `delay_cdf_split.png`: A Cumulative Distribution Function (CDF) graph proving Quality of Service (QoS) and traffic class prioritization.

---

## Team

**Three Idiots** — CS572 Modelling and Simulation, IIT

* **Harshal Maru**  - Core Engine, Traffic, Topology, CI/CD
* **Siddharth Suryavanshi**  - Visualization, Data Collection, Metrics Analytics
* **Om Joshi** - Queuing Disciplines, Routing Algorithms