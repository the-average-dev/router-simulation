"""
routing/routing_table.py
========================
Per-router next-hop lookup table.

Data model
----------
    routing_table[dst_router_id] = (next_hop_router_id, link_id)

Where:
    dst_router_id      : any hashable — the destination router
    next_hop_router_id : the *immediate* neighbour to forward to
    link_id            : identifier of the outgoing link (used by router.py
                         to find the SimPy link resource)

The table is populated by a routing algorithm (Dijkstra, Bellman-Ford …)
and read by router.py during packet forwarding.

No SimPy. No core/ imports. Pure data structure.
"""

from __future__ import annotations

from typing import Any, Dict, Hashable, Iterator, Optional, Tuple

RouterId = Hashable
LinkId   = Hashable

# Each entry: (next_hop_router_id, link_id)
NextHopEntry = Tuple[RouterId, LinkId]


class RoutingTable:
    """
    Next-hop routing table for one router.

    Parameters
    ----------
    owner_id : Hashable
        The router this table belongs to (used in __repr__ and error messages).

    Examples
    --------
    >>> rt = RoutingTable(owner_id="R1")
    >>> rt.add_entry(dst="R3", next_hop="R2", link_id="L12")
    >>> rt.lookup("R3")
    ('R2', 'L12')
    >>> rt.lookup("R99")   # unknown destination
    None
    """

    def __init__(self, owner_id: RouterId) -> None:
        self.owner_id: RouterId = owner_id
        self._table: Dict[RouterId, NextHopEntry] = {}

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add_entry(
        self,
        dst: RouterId,
        next_hop: RouterId,
        link_id: LinkId,
    ) -> None:
        """
        Insert or overwrite a routing entry.

        Parameters
        ----------
        dst     : destination router id
        next_hop: immediate neighbour to forward packets to
        link_id : outgoing link to use
        """
        self._table[dst] = (next_hop, link_id)

    def remove_entry(self, dst: RouterId) -> bool:
        """
        Delete the entry for *dst*.

        Returns True if it existed, False if it was already absent.
        """
        if dst in self._table:
            del self._table[dst]
            return True
        return False

    def update_from_dict(self, entries: Dict[RouterId, NextHopEntry]) -> None:
        """
        Bulk-load entries from a dict  {dst: (next_hop, link_id)}.
        Existing entries for the same dst are overwritten.
        """
        self._table.update(entries)

    def clear(self) -> None:
        """Remove all entries (e.g. before a full re-computation)."""
        self._table.clear()

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def lookup(self, dst: RouterId) -> Optional[NextHopEntry]:
        """
        Return (next_hop, link_id) for *dst*, or None if unreachable.

        router.py should drop the packet (or send an ICMP-like signal)
        when this returns None.
        """
        return self._table.get(dst)

    def next_hop(self, dst: RouterId) -> Optional[RouterId]:
        """Convenience: return only the next-hop router id."""
        entry = self._table.get(dst)
        return entry[0] if entry else None

    def link_for(self, dst: RouterId) -> Optional[LinkId]:
        """Convenience: return only the outgoing link id."""
        entry = self._table.get(dst)
        return entry[1] if entry else None

    def is_reachable(self, dst: RouterId) -> bool:
        return dst in self._table

    # ------------------------------------------------------------------
    # Iteration / inspection
    # ------------------------------------------------------------------

    def __contains__(self, dst: RouterId) -> bool:
        return dst in self._table

    def __len__(self) -> int:
        return len(self._table)

    def __iter__(self) -> Iterator[RouterId]:
        """Iterate over destination router ids."""
        return iter(self._table)

    def items(self):
        """Yield (dst, (next_hop, link_id)) pairs."""
        return self._table.items()

    def destinations(self):
        return self._table.keys()

    def to_dict(self) -> Dict[RouterId, NextHopEntry]:
        """Return a shallow copy of the internal dict."""
        return dict(self._table)

    # ------------------------------------------------------------------
    # Pretty print
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"RoutingTable(owner={self.owner_id!r}, entries={len(self._table)})"

    def pretty_print(self) -> str:
        """
        Return a human-readable table string, e.g. for logging:

            RoutingTable for R1
            -------------------
            Dst     Next-hop   Link
            R2      R2         L12
            R3      R2         L12
            R4      R4         L14
        """
        lines = [f"RoutingTable for {self.owner_id}", "-" * 34,
                 f"{'Dst':<10} {'Next-hop':<12} {'Link'}"]
        for dst, (nh, lnk) in sorted(self._table.items(), key=lambda x: str(x[0])):
            lines.append(f"{str(dst):<10} {str(nh):<12} {lnk}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Factory helper — build a full {router_id: RoutingTable} mapping
# ---------------------------------------------------------------------------

def build_routing_tables(
    raw: Dict[RouterId, Dict[RouterId, NextHopEntry]]
) -> Dict[RouterId, "RoutingTable"]:
    """
    Convenience factory used by Dijkstra / Bellman-Ford output.

    Parameters
    ----------
    raw : {owner_id: {dst: (next_hop, link_id), ...}, ...}

    Returns
    -------
    dict[RouterId, RoutingTable]
    """
    tables: Dict[RouterId, RoutingTable] = {}
    for owner, entries in raw.items():
        rt = RoutingTable(owner_id=owner)
        rt.update_from_dict(entries)
        tables[owner] = rt
    return tables
