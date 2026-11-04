"""Imagen de la ficha del estudiante para el cuestionario (HU-006, tarea 6.4).

Reproduce el contenido y los textos de la ficha de la Figura 7 (sin la sección de
seguimiento, que no se evalúa en el cuestionario), con los textos fijos de HU-006.
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

TITULO_FACTORES = "Factores que más pesan en esta estimación"
AVISO = (
    "La alerta es una estimación para apoyar la decisión y no reemplaza el criterio del tutor. "
    "Los factores muestran cuánto pesa cada variable en la estimación, no las causas del abandono."
)
COLORES_NIVEL = {  # (fondo de la etiqueta, texto)
    "alto": ("#FDE2E1", "#9B1C1C"),
    "medio": ("#FEF3C7", "#7A4B00"),
    "bajo": ("#DCFCE7", "#14532D"),
}
ROJO, AZUL = "#D64545", "#2F6FD1"
FONDO, TARJETA, BORDE, TEXTO, GRIS = "#F3F4F6", "#FFFFFF", "#E5E7EB", "#111827", "#4B5563"


@dataclass
class DatosFicha:
    codigo: str
    probabilidad: float
    nivel: str  # alto, medio, bajo
    carrera: str
    turno: str
    fecha: str  # dd/mm/aaaa
    modelo: str  # por ejemplo «modelo v1.0 (1.er semestre)»
    factores: list[tuple[str, float]]  # (texto del factor, contribución SHAP) ordenados por peso
    titulo_extra: str = ""  # por ejemplo «Caso 1»


def _tarjeta(ax, x, y, w, h):
    ax.add_patch(
        FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.012", fc=TARJETA, ec=BORDE, lw=1.2)
    )


def dibujar_ficha(datos: DatosFicha, destino: Path) -> Path:
    fig = plt.figure(figsize=(16, 9.2), dpi=110)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor(FONDO)

    # Encabezado
    ax.add_patch(FancyBboxPatch((0, 0.915), 1, 0.085, boxstyle="square,pad=0", fc=TARJETA, ec=BORDE, lw=1))
    ax.text(
        0.03,
        0.957,
        f"Ficha del estudiante {datos.codigo}",
        fontsize=20,
        weight="bold",
        color=TEXTO,
        va="center",
    )
    if datos.titulo_extra:
        ax.text(0.97, 0.957, datos.titulo_extra, fontsize=15, color=GRIS, va="center", ha="right")

    # Tarjetas superiores
    y, h, w, sep = 0.735, 0.145, 0.2225, 0.0133
    titulos = ["Probabilidad de abandono", "Nivel de urgencia", "Carrera / turno", "Cálculo"]
    for i, titulo in enumerate(titulos):
        x = 0.03 + i * (w + sep)
        _tarjeta(ax, x, y, w, h)
        ax.text(x + 0.015, y + h - 0.035, titulo, fontsize=13, color=GRIS, va="center")
    x0 = 0.03
    ax.text(
        x0 + 0.015,
        y + 0.045,
        f"{datos.probabilidad:.2f}".replace(".", ","),
        fontsize=30,
        weight="bold",
        color=TEXTO,
        va="center",
    )
    x1 = 0.03 + (w + sep)
    fondo, color = COLORES_NIVEL[datos.nivel]
    ax.text(
        x1 + 0.015,
        y + 0.05,
        datos.nivel.capitalize(),
        fontsize=22,
        weight="bold",
        color=color,
        va="center",
        bbox={"boxstyle": "round,pad=0.35,rounding_size=0.8", "fc": fondo, "ec": "none"},
    )
    x2 = 0.03 + 2 * (w + sep)
    texto_carrera = (
        datos.carrera if "nocturno" in datos.carrera.lower() else f"{datos.carrera} · {datos.turno}"
    )
    carrera = "\n".join(textwrap.wrap(texto_carrera, 26))
    ax.text(
        x2 + 0.015, y + 0.05, carrera, fontsize=15, weight="bold", color=TEXTO, va="center", linespacing=1.3
    )
    x3 = 0.03 + 3 * (w + sep)
    calculo = f"{datos.fecha}\n{datos.modelo}"
    ax.text(
        x3 + 0.015, y + 0.05, calculo, fontsize=14, weight="bold", color=TEXTO, va="center", linespacing=1.35
    )

    # Factores
    fy, fh = 0.06, 0.645
    _tarjeta(ax, 0.03, fy, 0.94, fh)
    ax.text(0.045, fy + fh - 0.045, TITULO_FACTORES, fontsize=17, weight="bold", color=TEXTO, va="center")
    maximo = max(abs(c) for _, c in datos.factores) or 1.0
    fila_h = 0.088
    inicio = fy + fh - 0.115
    for i, (texto, contribucion) in enumerate(datos.factores):
        cy = inicio - i * fila_h
        ax.text(
            0.05,
            cy,
            "\n".join(textwrap.wrap(texto, 58)),
            fontsize=14.5,
            color=TEXTO,
            va="center",
            linespacing=1.25,
        )
        largo = 0.32 * abs(contribucion) / maximo
        color = ROJO if contribucion > 0 else AZUL
        ax.add_patch(
            FancyBboxPatch(
                (0.51, cy - 0.013),
                max(largo, 0.006),
                0.026,
                boxstyle="round,pad=0,rounding_size=0.006",
                fc=color,
                ec="none",
            )
        )
        ax.text(
            0.86,
            cy,
            "Aumenta el\nriesgo" if contribucion > 0 else "Disminuye el\nriesgo",
            fontsize=13.5,
            weight="bold",
            color=color,
            va="center",
            linespacing=1.15,
        )
        if i < len(datos.factores) - 1:
            ax.plot([0.045, 0.955], [cy - fila_h / 2, cy - fila_h / 2], color=BORDE, lw=1)
    ax.text(
        0.045,
        fy + 0.045,
        "\n".join(textwrap.wrap(AVISO, 130)),
        fontsize=13,
        color=GRIS,
        va="center",
        linespacing=1.3,
    )

    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino, facecolor=FONDO)
    plt.close(fig)
    return destino
