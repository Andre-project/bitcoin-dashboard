---
trigger: manual
---

# Dash 2.18 + Dash Mantine Components 0.14 Agent Cheat Sheet

**Optimisé pour LLM (Cursor, Copilot) : Projets Fintech/Crypto Modernes.**

---

## 1. Imports minimaux
```python
import dash
import dash_mantine_components as dmc
from dash import html, dcc
from dash_iconify import DashIconify
```

---

## 2. Mantine Theme Provider
```python
app = dash.Dash(__name__)

app.layout = dmc.MantineProvider(
    theme={
      "colorScheme": "dark",
      "primaryColor": "brand-blue",
      "fontFamily": "'Inter', sans-serif",
      "colors": {  # Palette custom sur 10 niveaux
         "brand-blue": ["#E7F5FF",...,"#1864AB"]
      },
    },
    children=[...],
)
```
- Plus de `withGlobalStyles`, plus de `withNormalizeCSS` (v0.14+)
- Injecter le theme directement via le dict Python

---

## 3. Layout/Grille UI (Clean & Responsive)
```python
# Section principale
layout = dmc.Container([
    dmc.Grid([
        dmc.Col([ ... ], span=4),
        dmc.Col([ ... ], span=8)
    ], gutter="md"),
])
```
-  Grilles responsives: `dmc.Grid`, `dmc.Col`, `dmc.SimpleGrid`, `dmc.Group`, `dmc.Stack`
-  Utilisez `p="md"`,  `radius="md"`, `withBorder=True` sur `dmc.Paper`

---

## 4. Composants Clés Modernes DMC
- **Bouton**
    ```python
    dmc.Button("Action", leftSection=DashIconify(icon="tabler:plus"))
    ```
- **Input/Select :**  `leftSection` pour icône, `variant`, `radius`, `size` ultra simples
    ```python
    dmc.Select(
        data=[{"value": "btc", "label": "BTC"}],
        leftSection=DashIconify(icon="logos:bitcoin", width=18),
    )
    ```
- **Card/KPI**
    ```python
    dmc.Paper([
        dmc.Text("Solde Total"),
        dmc.Text("$3452", weight=700)
    ], radius="md", p="md", withBorder=True)
    ```
- **Notifications** (Toast)
    ```python
    dmc.Notification(
      title="Ordre exécuté !",
      message="Achat BTC à 41 241€",
      color="green",
      icon=DashIconify(icon="tabler:check")
    )
    ```

---

## 5. Icônes Pro : Dash Iconify
- `pip install dash-iconify`
- Trouver l’icône : https://icon-sets.iconify.design/
- Utiliser la clé (ex: `tabler:currency-dollar`)
    ```python
    DashIconify(icon="tabler:currency-bitcoin", width=20, color="#fcc419")
    # ou via DMC :
    dmc.Badge("BTC", leftSection=DashIconify(icon="logos:bitcoin",width=14))
    ```

---

## 6. Graphiques Plotly (avec Thème)
```python
import plotly.graph_objs as go
import plotly.io as pio

pio.templates["mon_tmpl"] = go.layout.Template(
    layout=dict(
        paper_bgcolor="#101113",
        plot_bgcolor="#1A1B1E",
        font_color="#e2e8f0",
        colorway=["#fcc419", "#339AF0", "#F03E3E"]  # extrait de ton theme
    )
)
pio.templates.default = "plotly_dark+mon_tmpl"
```

---

## 7. Astuces Production
- *Utilise toujours `dmc.Container` pour un padding global propre*
- *`leftSection` pour toutes les icônes dans cards/buttons/inputs*
- *Garde `dcc.Graph` pour les plots, tout le reste en DMC*
- *Pas de CSS custom : tout se fait par le dictionnaire `theme`*

---

## 8. Prompt Ultra-Court pour Cursor
> "Génère une page dashboard (Dash 2.18, DMC 0.14) avec `dmc.MantineProvider`. Tous les UI avec DMC (`Grid`, `Paper`, `Select`, `Button`). Pour chaque bouton/section : icône avec DashIconify (`leftSection`). Jamais de CSS custom ni Bootstrap. Utilise un thème dark dans le MantineProvider. Graphs via dcc.Graph."

---