#!/usr/bin/env python3
"""
高中有机合成路线设计程序（规则库 + 自动路径搜索）

特点：
1. 以高中常见反应为规则库（取代、消去、加成、氧化、酯化、硝化等）；
2. 输入目标产物，自动给出一条可行路线（尽量少步骤）；
3. 支持批量演示，可一键生成 100+ 个示例。
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import argparse
from typing import Dict, List, Optional, Set, Tuple

PREFIX = {
    1: "甲",
    2: "乙",
    3: "丙",
    4: "丁",
    5: "戊",
    6: "己",
    7: "庚",
    8: "辛",
    9: "壬",
    10: "癸",
}


@dataclass(frozen=True)
class Reaction:
    reactants: Tuple[str, ...]
    product: str
    condition: str
    reaction_type: str


class OrganicRouteDesigner:
    def __init__(self) -> None:
        self.name_to_id: Dict[str, str] = {}
        self.id_to_name: Dict[str, str] = {}
        self.reactions: List[Reaction] = []
        self.product_to_reactions: Dict[str, List[Reaction]] = {}

        self._build_compounds()
        self._build_reactions()

        self.starting_materials: Set[str] = {
            f"alkane:C{n}" for n in range(1, 11)
        } | {
            "alkene:C2",
            "alkene:C3",
            "alkene:C4",
            "benzene",
            "alcohol:C1",  # 工业上常见原料
            "alcohol:C2",
        }

    def _add_compound(self, cid: str, name: str) -> None:
        self.id_to_name[cid] = name
        self.name_to_id[name] = cid

    def _build_compounds(self) -> None:
        for n in range(1, 11):
            p = PREFIX[n]
            self._add_compound(f"alkane:C{n}", f"{p}烷")
            self._add_compound(f"haloalkane:C{n}", f"氯{p}烷")
            self._add_compound(f"alcohol:C{n}", f"{p}醇")
            self._add_compound(f"aldehyde:C{n}", f"{p}醛")
            self._add_compound(f"acid:C{n}", f"{p}酸")
            if n >= 2:
                self._add_compound(f"alkene:C{n}", f"{p}烯")

        for a in range(1, 11):
            for b in range(1, 11):
                cid = f"ester:C{a}:C{b}"
                name = f"{PREFIX[a]}酸{PREFIX[b]}酯"
                self._add_compound(cid, name)

        aromatic = {
            "benzene": "苯",
            "chlorobenzene": "氯苯",
            "bromobenzene": "溴苯",
            "nitrobenzene": "硝基苯",
            "aniline": "苯胺",
            "phenol": "苯酚",
        }
        for cid, name in aromatic.items():
            self._add_compound(cid, name)

    def _add_reaction(self, reactants: Tuple[str, ...], product: str, condition: str, reaction_type: str) -> None:
        rxn = Reaction(reactants=reactants, product=product, condition=condition, reaction_type=reaction_type)
        self.reactions.append(rxn)
        self.product_to_reactions.setdefault(product, []).append(rxn)

    def _build_reactions(self) -> None:
        for n in range(1, 11):
            alkane = f"alkane:C{n}"
            halo = f"haloalkane:C{n}"
            alcohol = f"alcohol:C{n}"
            aldehyde = f"aldehyde:C{n}"
            acid = f"acid:C{n}"

            self._add_reaction((alkane,), halo, "Cl₂/光照（取代）", "取代反应")
            self._add_reaction((halo,), alcohol, "NaOH(水), 加热（取代）", "取代反应")
            self._add_reaction((alcohol,), halo, "HCl/ZnCl₂ 或 SOCl₂", "取代反应")

            if n >= 2:
                alkene = f"alkene:C{n}"
                self._add_reaction((halo,), alkene, "NaOH(醇), 加热（消去）", "消去反应")
                self._add_reaction((alkene,), alcohol, "H₂O/H⁺（加成）", "加成反应")
                self._add_reaction((alcohol,), alkene, "浓H₂SO₄, 170℃（消去）", "消去反应")

            self._add_reaction((alcohol,), aldehyde, "Cu/加热 或 催化氧化", "氧化反应")
            self._add_reaction((aldehyde,), acid, "酸性KMnO₄ 或 [O]", "氧化反应")

        for a in range(1, 11):
            for b in range(1, 11):
                self._add_reaction(
                    (f"acid:C{a}", f"alcohol:C{b}"),
                    f"ester:C{a}:C{b}",
                    "浓H₂SO₄, 加热（酯化）",
                    "酯化反应",
                )

        self._add_reaction(("benzene",), "chlorobenzene", "Cl₂/FeCl₃（苯环取代）", "取代反应")
        self._add_reaction(("benzene",), "bromobenzene", "Br₂/FeBr₃（苯环取代）", "取代反应")
        self._add_reaction(("benzene",), "nitrobenzene", "浓HNO₃+浓H₂SO₄, 55℃", "硝化反应")
        self._add_reaction(("nitrobenzene",), "aniline", "Fe/HCl 还原", "还原反应")
        self._add_reaction(("chlorobenzene",), "phenol", "NaOH(高温高压), 后酸化", "水解反应")

    def compound_name(self, cid: str) -> str:
        return self.id_to_name.get(cid, cid)

    def compound_id(self, name: str) -> Optional[str]:
        return self.name_to_id.get(name)

    def all_compound_names(self) -> List[str]:
        return sorted(self.name_to_id.keys())

    @lru_cache(maxsize=None)
    def _best_cost(self, target: str, stack: Tuple[str, ...]) -> Tuple[int, Optional[Reaction]]:
        if target in self.starting_materials:
            return 0, None
        if target in stack:
            return 10**9, None

        best = (10**9, None)
        for rxn in self.product_to_reactions.get(target, []):
            total = 1
            feasible = True
            for reactant in rxn.reactants:
                c, _ = self._best_cost(reactant, stack + (target,))
                if c >= 10**9:
                    feasible = False
                    break
                total += c
            if feasible and total < best[0]:
                best = (total, rxn)
        return best

    def _collect_steps(self, target: str, seen: Set[Reaction], ordered: List[Reaction], stack: Tuple[str, ...]) -> bool:
        if target in self.starting_materials:
            return True
        _, rxn = self._best_cost(target, stack)
        if rxn is None:
            return False
        for r in rxn.reactants:
            if not self._collect_steps(r, seen, ordered, stack + (target,)):
                return False
        if rxn not in seen:
            seen.add(rxn)
            ordered.append(rxn)
        return True

    def design_route(self, target_name: str) -> Optional[List[Reaction]]:
        cid = self.compound_id(target_name)
        if cid is None:
            return None

        cost, _ = self._best_cost(cid, tuple())
        if cost >= 10**9:
            return []

        steps: List[Reaction] = []
        ok = self._collect_steps(cid, set(), steps, tuple())
        return steps if ok else []

    def route_to_text(self, target_name: str, route: Optional[List[Reaction]]) -> str:
        if route is None:
            return f"目标物“{target_name}”不在数据库中。"
        if route == []:
            return f"无法由设定起始原料合成“{target_name}”。"

        lines = [f"目标产物：{target_name}"]
        lines.append("推荐路线（按合成先后）：")
        for i, step in enumerate(route, start=1):
            reactants = " + ".join(self.compound_name(r) for r in step.reactants)
            product = self.compound_name(step.product)
            lines.append(f"{i:02d}. {reactants} → {product}    [{step.reaction_type}；条件：{step.condition}]")
        return "\n".join(lines)

    def demo_targets(self, count: int = 120) -> List[str]:
        candidates = []
        for cid, name in self.id_to_name.items():
            if cid in self.starting_materials:
                continue
            cost, _ = self._best_cost(cid, tuple())
            if cost < 10**9:
                candidates.append((cost, name))
        candidates.sort(key=lambda x: (x[0], x[1]))
        return [name for _, name in candidates[:count]]


def generate_demo_file(designer: OrganicRouteDesigner, output: str, count: int) -> None:
    targets = designer.demo_targets(count)
    lines = [
        "# 有机合成路线自动设计：示例集",
        "",
        f"共展示 {len(targets)} 个目标产物的自动规划结果。",
        "",
    ]
    for idx, target in enumerate(targets, start=1):
        route = designer.design_route(target)
        lines.append(f"## 示例 {idx}: {target}")
        lines.append("```")
        lines.append(designer.route_to_text(target, route))
        lines.append("```")
        lines.append("")

    with open(output, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description="高中有机合成路线设计程序")
    parser.add_argument("target", nargs="?", help="目标产物中文名，如：乙酸乙酯、苯胺")
    parser.add_argument("--list", action="store_true", help="列出可识别的全部化合物")
    parser.add_argument("--generate-demos", metavar="FILE", help="批量生成示例到 Markdown 文件")
    parser.add_argument("--demo-count", type=int, default=120, help="示例数量（默认120）")
    args = parser.parse_args()

    designer = OrganicRouteDesigner()

    if args.list:
        print("可识别化合物：")
        for n in designer.all_compound_names():
            print(n)
        return

    if args.generate_demos:
        generate_demo_file(designer, args.generate_demos, args.demo_count)
        print(f"已生成示例文件：{args.generate_demos}")
        return

    if not args.target:
        parser.print_help()
        print("\n示例：python3 organic_route_designer.py 乙酸乙酯")
        return

    route = designer.design_route(args.target)
    print(designer.route_to_text(args.target, route))


if __name__ == "__main__":
    main()
