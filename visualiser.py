from __future__ import annotations


def render(fa, title: str = "Finite Automaton", filename: str = "fa_graph") -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")          # non-interactive backend – no display needed
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        import networkx as nx
    except ImportError as e:
        print(f"[Visualiser] Missing library: {e}")
        print("  Run: pip install matplotlib networkx")
        return

    G = nx.MultiDiGraph()
    G.add_nodes_from(sorted(fa.states))

    # Collect edge labels: (src, dst) -> [symbols]
    edge_labels: dict[tuple, list] = {}
    for (state, sym), nexts in fa.transitions.items():
        for nxt in nexts:
            edge_labels.setdefault((state, nxt), []).append(sym)

    for (src, dst), syms in edge_labels.items():
        G.add_edge(src, dst, label=", ".join(sorted(syms)))

    # Use shell layout so states are spread in a circle
    pos = nx.shell_layout(G)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
    ax.axis("off")

    normal_states = [s for s in fa.states if s not in fa.final_states]
    final_states  = list(fa.final_states)

    node_size = 1800

    # Regular states – single circle
    nx.draw_networkx_nodes(G, pos, nodelist=normal_states,
                           node_color="#AED6F1", node_size=node_size,
                           ax=ax)
    # Final states – drawn twice (inner + outer ring) to mimic double circle
    nx.draw_networkx_nodes(G, pos, nodelist=final_states,
                           node_color="#A9DFBF", node_size=node_size,
                           ax=ax)
    nx.draw_networkx_nodes(G, pos, nodelist=final_states,
                           node_color="none", node_size=node_size * 1.35,
                           linewidths=2, ax=ax)

    nx.draw_networkx_labels(G, pos, font_size=11, font_weight="bold", ax=ax)

    # Edges – use curved arrows so self-loops and parallel edges are visible
    nx.draw_networkx_edges(
        G, pos,
        connectionstyle="arc3,rad=0.2",
        arrowsize=20,
        arrowstyle="-|>",
        edge_color="#555555",
        width=1.5,
        ax=ax,
    )

    for (src, dst), syms_list in edge_labels.items():
        label_text = ", ".join(sorted(syms_list))
        x0, y0 = pos[src]
        x1, y1 = pos[dst]
        if src == dst:          # self-loop: push label outward
            mx, my = x0 + 0.18, y0 + 0.18
        else:
            mx = (x0 + x1) / 2 + 0.06   # slight offset so it clears the arrow
            my = (y0 + y1) / 2 + 0.06
        ax.text(mx, my, label_text, fontsize=9, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))

    # Start arrow: draw a short annotation arrow pointing at the start state
    sx, sy = pos[fa.start]
    ax.annotate("", xy=(sx, sy),
                xytext=(sx - 0.28, sy),
                arrowprops=dict(arrowstyle="-|>", color="black", lw=1.5))

    # Legend
    legend_handles = [
        mpatches.Patch(color="#AED6F1", label="State"),
        mpatches.Patch(color="#A9DFBF", label="Final state"),
    ]
    ax.legend(handles=legend_handles, loc="lower right", fontsize=9)

    out = f"{filename}.png"
    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[Visualiser] Diagram saved to '{out}'")