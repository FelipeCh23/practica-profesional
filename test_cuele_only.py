# test_cuele_only.py
import matplotlib.pyplot as plt
from blast_cuts import (
    cuele_sarrios, cuele_sueco, cuele_coromant,
    cuele_cuna, cuele_abanico, cuele_bethune
)

def plot_cuele(holes, ax, title):
    ax.set_aspect('equal'); ax.grid(True); ax.set_title(title)
    xs = [h["x"] for h in holes]; ys = [h["y"] for h in holes]
    colors = ["C2" if h["delay"]==0 else ("C1" if h["delay"]==1 else ("C3" if h["delay"]==2 else "k")) for h in holes]
    ax.scatter(xs, ys, c=colors, s=60)
    for h in holes:
        ax.text(h["x"], h["y"], str(h["delay"]), fontsize=8, ha='center', va='bottom')

fig, axs = plt.subplots(2,3, figsize=(10,7))
plot_cuele(cuele_sarrios(d_core=0.15), axs[0,0], "Sarrios")
plot_cuele(cuele_sueco(d_core=0.15, roca_dura=False), axs[0,1], "Sueco (medio)")
plot_cuele(cuele_coromant(d_core=0.18), axs[0,2], "Coromant")
plot_cuele(cuele_cuna(d_core=0.20, n_pairs=3, ang_deg=70), axs[1,0], "Cuña")
plot_cuele(cuele_abanico(radio=0.5, n=10), axs[1,1], "Abanico")
plot_cuele(cuele_bethune(d_core=0.20), axs[1,2], "Bethune")
plt.tight_layout(); plt.show()
