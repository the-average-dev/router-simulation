from __future__ import annotations
from typing import Any, Dict, Hashable, Iterator, Optional, Tuple

RouterId = Hashable
LinkId   = Hashable

NextHopEntry = Tuple[RouterId, LinkId]



class RoutingTable:

    def __init__(self, id: RouterId) -> None:
        self.id: RouterId = id
        self.table: Dict[RouterId, NextHopEntry] = {}


    def add_entry(
        self,
        dst: RouterId,
        next_hop: RouterId,
        link_id: LinkId,
    ) -> None:
        
        self.table[dst] = (next_hop, link_id)

    def remove_entry(self, dst: RouterId) -> bool:
        
        if dst in self.table:
            del self.table[dst]
            return True
        return False

    def update_from_dict(self, entries: Dict[RouterId, NextHopEntry]) -> None:
        
        self.table.update(entries)

    def clear(self) -> None:
        self.table.clear()


    def lookup(self, dst: RouterId) -> Optional[NextHopEntry]:
        return self.table.get(dst)

    def next_hop(self, dst: RouterId) -> Optional[RouterId]:
        entry = self.table.get(dst)
        return entry[0] if entry else None

    def link_for(self, dst: RouterId) -> Optional[LinkId]:
        entry = self.table.get(dst)
        return entry[1] if entry else None

    def is_reachable(self, dst: RouterId) -> bool:
        return dst in self.table



    def __contains__(self, dst: RouterId) -> bool:
        return dst in self.table

    def __len__(self) -> int:
        return len(self.table)

    def __iter__(self) -> Iterator[RouterId]:
        return iter(self.table)

    def items(self):
        return self.table.items()

    def destination(self):
        return self.table.keys()

    def to_dict(self) -> Dict[RouterId, NextHopEntry]:
        return dict(self.table)


    def __repr__(self) -> str:
        return f"RoutingTable(owner={self.id!r}, entries={len(self.table)})"

    def pretty_print(self) -> str:
        lines = [f"RoutingTable for {self.id}", "-" * 34,
                 f"{'Dst':<10} {'Next-hop':<12} {'Link'}"]
        for dst, (nh, lnk) in sorted(self.table.items(), key=lambda x: str(x[0])):
            lines.append(f"{str(dst):<10} {str(nh):<12} {lnk}")
        return "\n".join(lines)


def build_routing_tables(
    raw: Dict[RouterId, Dict[RouterId, NextHopEntry]]
) -> Dict[RouterId, "RoutingTable"]:
    tables: Dict[RouterId, RoutingTable] = {}
    for owner, entries in raw.items():
        rt = RoutingTable(id=owner)
        rt.update_from_dict(entries)
        tables[owner] = rt
    return tables
