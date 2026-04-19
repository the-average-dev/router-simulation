from __future__ import annotations
import math
import sys
import os
import pytest
import networkx as nx


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from queueing.base import QueueDiscipline, EnqueueResult, StatsTrackingMixin
from queueing.fifo import FifoQueue
from queueing.priority_queue import PriorityQueue
from queueing.wfq import WFQQueue
from queueing.red import REDQueue
from routing.routing_table import RoutingTable, build_routing_tables
from routing.dijkstra import dijkstra_single_source, compute_all_routing_tables as dijkstra_all
from routing.bellman_ford import (
    bellman_ford_single_source,
    compute_all_routing_tables as bf_all,
    BellmanFordRouter,
)


class MockPacket:
    id_cnt = 0

    def __init__(self, priority: int = 0, size: int = 100, birth_time: float = 0.0):
        MockPacket.id_cnt += 1
        self.id         = MockPacket.id_cnt
        self.priority   = priority
        self.size       = size
        self.birth_time = birth_time

    def __repr__(self):
        return f"Pkt(id={self.id}, pri={self.priority}, sz={self.size})"


def make_pkts(n: int, priority: int = 0, size: int = 100) -> list[MockPacket]:
    return [MockPacket(priority=priority, size=size) for _ in range(n)]




class TestFifoQueue:

    def test_enqueue_dequeue_order(self):
        q = FifoQueue(capacity=5)
        pckt = make_pkts(4)
        for p in pckt:
            assert q.enqueue(p) is True
        for p in pckt:
            assert q.dequeue() is p

    def tail_drop_if_full(self):
        q = FifoQueue(capacity=3)
        pckt = make_pkts(5)
        res = [q.enqueue(p) for p in pckt]
        assert res == [True, True, True, False, False]
        assert len(q) == 3

    def tets_dequeue_empty(self):
        q = FifoQueue(capacity=4)
        assert q.dequeue() is None

    def test_full_empty(self):
        q = FifoQueue(capacity=2)
        assert q.is_empty()
        assert not q.is_full()
        q.enqueue(MockPacket())
        assert not q.is_empty()
        assert not q.is_full()
        q.enqueue(MockPacket())
        assert q.is_full()

    def test_peek_not_remove(self):
        q = FifoQueue(capacity=4)
        p = MockPacket()
        q.enqueue(p)
        assert q.peek() is p
        assert len(q) == 1

    def test_flush_drains_queue(self):
        q = FifoQueue(capacity=4)
        pckt = make_pkts(3)
        for p in pckt:
            q.enqueue(p)
        drained = q.flush()
        assert drained == pckt
        assert q.is_empty()

    def test_stats_tracking(self):
        q = FifoQueue(capacity=3)
        for _ in range(5):
            q.enqueue(MockPacket())
        assert q.stats["enqueued"] == 3
        assert q.stats["dropped"] == 2
        assert math.isclose(q.stats["drop_rate"], 2 / 5)

    def test_capacity_zero_raises(self):
        with pytest.raises(ValueError):
            FifoQueue(capacity=0)






class TestPriorityQueue:

    def test_higher_priority_served_first(self):
        q = PriorityQueue(capacity=10)
        bulk  = MockPacket(priority=2)
        voip  = MockPacket(priority=0)
        best  = MockPacket(priority=1)
        q.enqueue(bulk)
        q.enqueue(voip)
        q.enqueue(best)
        assert q.dequeue() is voip   
        assert q.dequeue() is best   
        assert q.dequeue() is bulk   

    def test_fifo_within_same_priority(self):
        q = PriorityQueue(capacity=10)
        p1, p2, p3 = [MockPacket(priority=1) for _ in range(3)]
        for p in (p1, p2, p3):
            q.enqueue(p)
        assert q.dequeue() is p1
        assert q.dequeue() is p2
        assert q.dequeue() is p3

    def test_tail_drop_on_full(self):
        q = PriorityQueue(capacity=2)
        pckt = [MockPacket(priority=i) for i in range(4)]
        res = [q.enqueue(p) for p in pckt]
        assert res[:2] == [True, True]
        assert res[2:] == [False, False]

    def test_empty_dequeue_returns_none(self):
        q = PriorityQueue(capacity=5)
        assert q.dequeue() is None

    def test_flush_returns_priority_order(self):
        q = PriorityQueue(capacity=10)
        priorities = [2, 0, 1, 0, 2]
        pckt = [MockPacket(priority=p) for p in priorities]
        for p in pckt:
            q.enqueue(p)
        drained = q.flush()
        served_priorities = [p.priority for p in drained]
        assert served_priorities == sorted(priorities)

    def test_stats_tracking(self):
        q = PriorityQueue(capacity=3)
        for _ in range(5):
            q.enqueue(MockPacket(priority=0))
        assert q.stats["dropped"] == 2
        assert q.stats["enqueued"] == 3


class TestWFQQueue:

    def test_high_weight_class_served_first(self):
        
        q = WFQQueue(capacity=20, weights={0: 10, 1: 1})
        low  = MockPacket(priority=1, size=100)
        high = MockPacket(priority=0, size=100)
        q.enqueue(low)
        q.enqueue(high)
        first = q.dequeue()
        assert first is high, "High-weight class should be served before low-weight"

    def test_all_packets_eventually_served(self):
        q = WFQQueue(capacity=20, weights={0: 5, 1: 2, 2: 1})
        pckt = [MockPacket(priority=i % 3, size=100) for i in range(9)]
        for p in pckt:
            q.enqueue(p)
        served = []
        while not q.is_empty():
            served.append(q.dequeue())
        assert len(served) == 9
        assert set(id(p) for p in served) == set(id(p) for p in pckt)

    def test_tail_drop_on_overflow(self):
        q = WFQQueue(capacity=3, weights={0: 1})
        res = [q.enqueue(MockPacket(priority=0)) for _ in range(5)]
        assert res[:3] == [True, True, True]
        assert res[3:] == [False, False]

    def test_empty_dequeue_returns_none(self):
        q = WFQQueue(capacity=5)
        assert q.dequeue() is None

    def test_virtual_clock_advances(self):
        q = WFQQueue(capacity=10, weights={0: 1})
        q.enqueue(MockPacket(priority=0, size=100))
        assert q.virtual_clock == 0.0
        q.dequeue()
        assert q.virtual_clock > 0.0

    def test_flush(self):
        q = WFQQueue(capacity=5, weights={0: 1})
        pckt = make_pkts(3, priority=0)
        for p in pckt:
            q.enqueue(p)
        drained = q.flush()
        assert len(drained) == 3
        assert q.is_empty()


class TestREDQueue:

    def test_below_min_th_no_drops(self):
        q = REDQueue(capacity=100, t_min=20, t_max=80, p_max=0.1, seed=42)
        
        for _ in range(10):
            assert q.enqueue(MockPacket()) is True

    def test_above_max_th_all_dropped(self):
        
        q = REDQueue(capacity=200, t_min=5, t_max=10, p_max=1.0, wq=0.5, seed=0)
        
        for _ in range(50):
            q.enqueue(MockPacket())
        
        assert q.avg_queue_len > q.t_max
        
        
        for _ in range(40):
            q.dequeue()
        
        for _ in range(50):
            q.enqueue(MockPacket())
        assert q.avg_queue_len > q.t_max

    def test_tail_drop_hard_capacity(self):
        q = REDQueue(capacity=5, t_min=2, t_max=4, p_max=0.1, seed=99)
        res = []
        for _ in range(10):
            res.append(q.enqueue(MockPacket()))
        
        assert sum(res) <= 5

    def test_enqueue_detailed_reasons(self):
        q = REDQueue(capacity=3, t_min=1, t_max=2, p_max=1.0, wq=0.9, seed=7)
        res = [q.enqueue_detailed(MockPacket()) for _ in range(6)]
        reasons = {r.reason for r in res}
        
        assert "admitted" in reasons

    def test_dequeue_fifo_within_red(self):
        q = REDQueue(capacity=50, t_min=40, t_max=45, p_max=0.1, seed=0)
        admitted = []
        for _ in range(10):
            p = MockPacket()
            if q.enqueue(p):
                admitted.append(p)
        for p in admitted:
            assert q.dequeue() is p

    def test_invalid_thresholds_raise(self):
        with pytest.raises(ValueError):
            REDQueue(capacity=10, t_min=50, t_max=80)   

    def test_avg_queue_len_property(self):
        q = REDQueue(capacity=100, t_min=20, t_max=80, seed=0)
        assert q.avg_queue_len == 0.0
        for _ in range(10):
            q.enqueue(MockPacket())
        assert q.avg_queue_len > 0.0


class TestRoutingTable:

    def test_add_and_lookup(self):
        rt = RoutingTable("R1")
        rt.add_entry("R3", next_hop="R2", link_id="L12")
        assert rt.lookup("R3") == ("R2", "L12")

    def test_lookup_missing_returns_none(self):
        rt = RoutingTable("R1")
        assert rt.lookup("R99") is None

    def test_remove_entry(self):
        rt = RoutingTable("R1")
        rt.add_entry("R2", "R2", "L12")
        assert rt.remove_entry("R2") is True
        assert rt.lookup("R2") is None
        assert rt.remove_entry("R2") is False

    def test_update_from_dict(self):
        rt = RoutingTable("R1")
        rt.update_from_dict({
            "R2": ("R2", "L12"),
            "R3": ("R2", "L12"),
        })
        assert rt.lookup("R2") == ("R2", "L12")
        assert rt.lookup("R3") == ("R2", "L12")
        assert len(rt) == 2

    def test_next_hop_and_link_for_helpers(self):
        rt = RoutingTable("R1")
        rt.add_entry("R4", "R2", "L12")
        assert rt.next_hop("R4") == "R2"
        assert rt.link_for("R4") == "L12"
        assert rt.next_hop("R99") is None
        assert rt.link_for("R99") is None

    def test_is_reachable(self):
        rt = RoutingTable("R1")
        rt.add_entry("R2", "R2", "L12")
        assert rt.is_reachable("R2")
        assert not rt.is_reachable("R3")

    def test_contains_and_iter(self):
        rt = RoutingTable("R1")
        rt.add_entry("R2", "R2", "L12")
        assert "R2" in rt
        assert "R3" not in rt
        assert list(rt) == ["R2"]

    def test_clear(self):
        rt = RoutingTable("R1")
        rt.add_entry("R2", "R2", "L12")
        rt.clear()
        assert len(rt) == 0

    def test_build_routing_tables_factory(self):
        raw = {
            "R1": {"R2": ("R2", "L12"), "R3": ("R2", "L12")},
            "R2": {"R1": ("R1", "L12"), "R3": ("R3", "L23")},
        }
        tables = build_routing_tables(raw)
        assert tables["R1"].lookup("R3") == ("R2", "L12")
        assert tables["R2"].lookup("R3") == ("R3", "L23")






def _linear_graph():
    G = nx.Graph()
    G.add_edge("R1", "R2", weight=1, link_id="L12")
    G.add_edge("R2", "R3", weight=1, link_id="L23")
    G.add_edge("R3", "R4", weight=1, link_id="L34")
    return G


def _weighted_graph():
    G = nx.Graph()
    G.add_edge("R1", "R2", weight=1,  link_id="L12")
    G.add_edge("R2", "R3", weight=10, link_id="L23")
    G.add_edge("R1", "R3", weight=3,  link_id="L13")
    return G


class TestDijkstra:

    def test_single_hop(self):
        G = _linear_graph()
        rt = dijkstra_single_source(G, "R1")
        assert rt.lookup("R2") == ("R2", "L12")

    def test_multi_hop_next_hop(self):
        G = _linear_graph()
        rt = dijkstra_single_source(G, "R1")
        assert rt.next_hop("R4") == "R2"
        assert rt.link_for("R4") == "L12"

    def test_weighted_shortest_path(self):
        G = _weighted_graph()
        rt = dijkstra_single_source(G, "R1")
        assert rt.next_hop("R3") == "R3"
        assert rt.link_for("R3") == "L13"

    def test_all_tables_computed(self):
        G = _linear_graph()
        tables = dijkstra_all(G)
        assert set(tables.keys()) == {"R1", "R2", "R3", "R4"}

    def test_symmetry(self):
        G = _linear_graph()
        tables = dijkstra_all(G)
        assert tables["R1"].next_hop("R4") == "R2"
        assert tables["R4"].next_hop("R1") == "R3"

    def test_unreachable_node_has_no_entry(self):
        G = nx.Graph()
        G.add_node("R1")
        G.add_node("R2")   
        rt = dijkstra_single_source(G, "R1")
        assert rt.lookup("R2") is None

    def test_single_node_graph(self):
        G = nx.Graph()
        G.add_node("R1")
        rt = dijkstra_single_source(G, "R1")
        assert len(rt) == 0



class TestBellmanFord:

    def test_single_hop(self):
        G = _linear_graph()
        rt = bellman_ford_single_source(G, "R1")
        assert rt.lookup("R2") == ("R2", "L12")

    def test_multi_hop_next_hop(self):
        G = _linear_graph()
        rt = bellman_ford_single_source(G, "R1")
        assert rt.next_hop("R4") == "R2"

    def test_weighted_path(self):
        G = _weighted_graph()
        rt = bellman_ford_single_source(G, "R1")
        assert rt.next_hop("R3") == "R3"
        assert rt.link_for("R3") == "L13"

    def test_agrees_with_dijkstra_on_linear(self):
        G = _linear_graph()
        bf_tables  = bf_all(G)
        dij_tables = dijkstra_all(G)
        for node in G.nodes:
            for dst in G.nodes:
                if dst == node:
                    continue
                assert bf_tables[node].lookup(dst) == dij_tables[node].lookup(dst), \
                    f"Mismatch at {node}→{dst}"

    def test_agrees_with_dijkstra_on_weighted(self):
        G = _weighted_graph()
        bf_tables  = bf_all(G)
        dij_tables = dijkstra_all(G)
        for node in G.nodes:
            for dst in G.nodes:
                if dst == node:
                    continue
                assert bf_tables[node].lookup(dst) == dij_tables[node].lookup(dst)

    def test_recompute_after_link_failure(self):
        
        G = nx.Graph()
        G.add_edge("R1", "R2", weight=1, link_id="L12")
        G.add_edge("R2", "R3", weight=1, link_id="L23")
        G.add_edge("R1", "R3", weight=5, link_id="L13")   

        router = BellmanFordRouter(G)
        tables = router.compute()
        assert tables["R1"].next_hop("R3") == "R2"       

        
        G.remove_edge("R1", "R2")
        tables = router.recompute()
        
        assert tables["R1"].next_hop("R3") == "R3"
        assert tables["R1"].link_for("R3") == "L13"

    def test_partitioned_graph_no_route(self):
        G = nx.Graph()
        G.add_node("R1")
        G.add_node("R2")
        rt = bellman_ford_single_source(G, "R1")
        assert rt.lookup("R2") is None

    def test_negative_cycle_raises(self):
        G = nx.DiGraph()
        G.add_edge("R1", "R2", weight=1,  link_id="L12")
        G.add_edge("R2", "R3", weight=-3, link_id="L23")
        G.add_edge("R3", "R1", weight=1,  link_id="L31")
        with pytest.raises(ValueError, match="Negative-weight cycle"):
            bellman_ford_single_source(G, "R1")



class TestCrossDiscipline:

    def test_all_disciplines_share_base_interface(self):
        disciplines = [
            FifoQueue(capacity=10),
            PriorityQueue(capacity=10),
            WFQQueue(capacity=10),
            REDQueue(capacity=100, t_min=20, t_max=80),
        ]
        for q in disciplines:
            assert isinstance(q, QueueDiscipline)
            p = MockPacket()
            q.enqueue(p)
            assert len(q) == 1
            assert not q.is_empty()
            out = q.dequeue()
            assert out is p
            assert q.is_empty()

    def test_enqueue_result_bool(self):
        r_ok   = EnqueueResult(accepted=True,  reason="admitted")
        r_drop = EnqueueResult(accepted=False, reason="tail_drop")
        assert bool(r_ok) is True
        assert bool(r_drop) is False

    def test_enqueue_result_bad_reason_raises(self):
        with pytest.raises(ValueError):
            EnqueueResult(accepted=False, reason="mystery_reason")
