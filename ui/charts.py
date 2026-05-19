import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_sankey(labels, sources, targets, values, title, show_vals=True):
    """
    Erstellt ein professionelles Sankey-Diagramm mit dynamischer Farbgebung.
    Unterstützt jetzt auch spezifische Knoten für Soli und KiSt.
    """
    display_labels = []
    node_colors = []
    
    for i, label in enumerate(labels):
        in_s = sum([values[j] for j, t in enumerate(targets) if t == i])
        out_s = sum([values[j] for j, s in enumerate(sources) if s == i])
        v = max(in_s, out_s)
        display_labels.append(f"{label} ({v:.0f}€)" if show_vals else label)
        
        low_label = label.lower()
        if "überschuss" in low_label or "ueberschuss" in low_label:
            node_colors.append("#28B463") # Grün
        elif "unterdeckung" in low_label or "abschlag" in low_label or "beitragsverlust" in low_label:
            node_colors.append("#CB4335") # Kräftiges Rot
        elif "steuer" in low_label or "soli" in low_label or "kist" in low_label or "abgaben" in low_label:
            node_colors.append("#E74C3C") # Etwas helleres Rot für Steuern/Abgaben
        else:
            node_colors.append("#2E86C1") # Standard Blau

    link_colors = []
    for t in targets:
        low_t = labels[t].lower()
        if "abschlag" in low_t or "beitragsverlust" in low_t or "abgaben" in low_t or "steuer" in low_t or "soli" in low_t:
            link_colors.append("rgba(203, 67, 53, 0.4)") # Leicht transparentes Rot
        else:
            link_colors.append("#E5E7E9")

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=20, 
            thickness=25, 
            line=dict(width=0), 
            label=display_labels, 
            color=node_colors
        ),
        link=dict(
            source=sources, 
            target=targets, 
            value=values, 
            color=link_colors
        )
    )])

    fig.update_layout(
        title_text=title, 
        font=dict(size=13, color="black", family="Arial"), 
        template="plotly_white", 
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
        separators=",."
    )
    return fig

def _get_color_by_name(name, i=0):
    """Interne Hilfsfunktion für semantische Farbgebung."""
    # Professionelle qualitative Palette (D3)
    palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]
    
    n = name.lower()
    if "gesetzlich" in n or "grv" in n or "rente" == n: return "#1f77b4" # Blau
    if "bav" in n or "betriebsrente" in n: return "#ff7f0e" # Orange
    if "gehalt" in n or "einkommen" in n: return "#17becf" # Teal
    if "aufstockung" in n: return "#e377c2" # Rosa/Magenta
    if "privat" in n: return "#2ca02c" # Grün
    if "kapital" in n or "entnahme" in n or "depot" in n or "etf" in n: return "#9467bd" # Violett
    if "cash" in n or "reserve" in n or "liquidität" in n: return "#28B463" # Kräftiges Grün
    
    return palette[i % len(palette)]

def _fmt_date(decimal_year):
    """Konvertiert Dezimaljahr (z.B. 2031.083) in lesbares Format (MM/YYYY)."""
    year = int(decimal_year)
    month = int(round((decimal_year - year) * 12)) + 1
    if month > 12: 
        month = 1
        year += 1
    return f"{month:02d}/{year}"

def get_milestone_visual_pos(df, m_jahr):
    """
    Findet die präzise X-Position eines Meilensteins auf der numerischen X-Achse.
    Fällt der Meilenstein in ein Übergangsjahr, wird er genau in die Mitte des Jahres
    (also in die Lücke zwischen den beiden geteilten Balken) auf float(Jahr) platziert.
    """
    jahr_int = int(m_jahr)
    segments = df[df["Jahr"] == jahr_int]
    if len(segments) > 1:
        return float(jahr_int)
    return m_jahr

def create_trend_chart(df, meilensteine, show_tax_rate=False):
    """
    Erstellt ein gestapeltes Balkendiagramm für das Brutto-Einkommen.
    Meilensteine werden als Symbole in der Legende und gestrichelte Linien dargestellt.
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    is_categorical = "Label" in df.columns
    bar_offsets = None
    if is_categorical:
        # Berechne optimierte numerische X-Koordinaten und Breiten für die Balken
        x_coords = []
        bar_widths = []
        i = 0
        n = len(df)
        while i < n:
            row = df.iloc[i]
            jahr = row["Jahr"]
            segments = df[df["Jahr"] == jahr]
            num_segments = len(segments)
            
            if num_segments == 1:
                x_coords.append(float(jahr))
                bar_widths.append(0.7)
                i += 1
            elif num_segments == 2:
                # Erste Hälfte nach links (-0.2), zweite nach rechts (+0.2)
                # Breite jeweils 0.35, ergibt perfekten 0.05 Spalt in der Mitte
                x_coords.append(float(jahr) - 0.20)
                bar_widths.append(0.35)
                x_coords.append(float(jahr) + 0.20)
                bar_widths.append(0.35)
                i += 2
            else:
                for s_idx in range(num_segments):
                    offset = -0.2 + (s_idx / (num_segments - 1)) * 0.4 if num_segments > 1 else 0
                    x_coords.append(float(jahr) + offset)
                    bar_widths.append(0.7 / num_segments)
                i += num_segments
        
        x_vals = x_coords
    else:
        x_vals = df.get("Jahr_Float", df["Jahr"])
        bar_widths = df.get("bar_width", 0.8)
    
    # 1. Gestapelte Balken für Einkommensquellen
    exclude_cols = ["Jahr", "Jahr_Float", "bar_width", "start_t", "end_t", "Label", "Phase", "Brutto", "EkSt", "Soli", "KiSt", "Steuern", "Steuersatz", "Sozialabgaben", "Netto-Einkommen", "Bedarf", "Überschuss/Defizit", "Rentenabschlag", "Beitragsverlust", "Steuerpflichtiger_Rentenanteil", "Netto-GRV", "Kapitalzuwachs_Sonder", "Gesetzliche Rente (Potenzial)"]
    income_cols = [c for c in df.columns if c not in exclude_cols and not c.startswith("EXP_") and not c.startswith("ASSET_VAL_") and not c.startswith("_debug")]
    
    for i, col in enumerate(income_cols):
        bar_args = dict(
            x=x_vals, y=df[col], name=col,
            width=bar_widths,
            marker=dict(color=_get_color_by_name(col, i), line=dict(width=0)),
            hovertemplate="%{y:,.0f} €"
        )
        if bar_offsets is not None:
            bar_args["offset"] = bar_offsets
        fig.add_trace(
            go.Bar(**bar_args),
            secondary_y=False
        )
        
    # 2. Linie für Bedarf & Netto
    fig.add_trace(
        go.Scatter(
            x=x_vals, y=df["Bedarf"], name="Bedarf (Ausgaben)",
            line=dict(color='#CB4335', width=3),
            hovertemplate="%{y:,.0f} €"
        ),
        secondary_y=False
    )
    fig.add_trace(
        go.Scatter(
            x=x_vals, y=df["Netto-Einkommen"], name="Netto-Einkommen",
            line=dict(color='#212F3D', width=3, dash='dot'),
            hovertemplate="%{y:,.0f} €"
        ),
        secondary_y=False
    )
    
    if show_tax_rate:
        fig.add_trace(
            go.Scatter(
                x=x_vals, y=df["Steuersatz"], name="Steuersatz (%)",
                line=dict(color='#7F8C8D', width=2, dash='dot'),
                hovertemplate="%{y:.1f} %"
            ),
            secondary_y=True
        )
    
    # 3. Meilensteine als Legendeneinträge und Linien (mit Stacking-Logik)
    symbols = ["circle", "square", "diamond", "triangle-up", "star", "hexagram"]
    jahr_counts = {} # Zum Tracking von Kollisionen
    
    for i, m in enumerate(meilensteine):
        sym = symbols[i % len(symbols)]
        date_label = _fmt_date(m["jahr"])
        
        # Stacking-Offset berechnen
        jahr = round(m["jahr"], 4)
        offset_idx = jahr_counts.get(jahr, 0)
        jahr_counts[jahr] = offset_idx + 1
        
        # Y-Position leicht unter der X-Achse (gestapelt)
        y_pos = -(offset_idx * 800) # Vergrößerter Offset (800 statt 600)
        
        # Finde X-Position auf kategorialer oder numerischer Achse
        if is_categorical:
            m_pos = get_milestone_visual_pos(df, m["jahr"])
        else:
            m_pos = m["jahr"]
        
        # Punkt für Legende & Position im Chart
        fig.add_trace(
            go.Scatter(
                x=[m_pos], y=[y_pos], 
                name=f"{m['label']} ({date_label})",
                mode='markers',
                marker=dict(symbol=sym, size=12, color=m["color"], line=dict(width=1, color="white")),
                showlegend=True,
                cliponaxis=False, # Wichtig für Position außerhalb der Achse
                hoverinfo="skip"  # Nicht im vereinheitlichten Tooltip anzeigen
            ),
            secondary_y=False
        )
        
        # Die vertikale Linie
        fig.add_vline(x=m_pos, line_width=2, line_dash="dash", line_color=m["color"])

    # Layout-Optimierung
    fig.update_layout(
        template="plotly_white", 
        hovermode="x unified", 
        barmode='stack',
        bargap=0.15,
        margin=dict(t=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        separators=",.",
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="#E5E7E9",
            font_size=13,
            font_family="Arial",
            namelength=-1  # Verhindert jegliche Kürzung der Namen im Tooltip
        )
    )
    
    if is_categorical:
        fig.update_xaxes(
            type='linear',
            tickmode='array',
            tickvals=x_vals,
            ticktext=df["Label"],
            tickangle=-45
        )
    
    # Y-Achse etwas nach unten erweitern für Symbole
    y_min = -2500 if meilensteine else 0
    fig.update_yaxes(title_text="Euro pro Monat", secondary_y=False, range=[y_min, None])
    if show_tax_rate:
        fig.update_yaxes(title_text="Steuersatz (%)", secondary_y=True, range=[0, 50])
        
    return fig

def create_wealth_chart(df):
    """
    Erstellt ein Stacked Area Chart für die Vermögensentwicklung einzelner Assets.
    """
    fig = go.Figure()
    
    is_categorical = "Label" in df.columns
    if is_categorical:
        # Berechne optimierte numerische X-Koordinaten
        x_coords = []
        i = 0
        n = len(df)
        while i < n:
            row = df.iloc[i]
            jahr = row["Jahr"]
            segments = df[df["Jahr"] == jahr]
            num_segments = len(segments)
            
            if num_segments == 1:
                x_coords.append(float(jahr))
                i += 1
            elif num_segments == 2:
                x_coords.append(float(jahr) - 0.20)
                x_coords.append(float(jahr) + 0.20)
                i += 2
            else:
                for s_idx in range(num_segments):
                    offset = -0.2 + (s_idx / (num_segments - 1)) * 0.4 if num_segments > 1 else 0
                    x_coords.append(float(jahr) + offset)
                i += num_segments
        x_vals = x_coords
    else:
        x_vals = df.get("Jahr_Float", df["Jahr"])
    
    # Finde alle Asset-Spalten
    asset_cols = [c for c in df.columns if c.startswith("ASSET_VAL_")]
    
    # Sortierung: Cash-Reserven ganz oben im Stapel, damit negative Werte 
    # nicht die Basis der anderen Assets verschieben.
    if "ASSET_VAL_Cash-Reserven (kum.)" in asset_cols:
        asset_cols.remove("ASSET_VAL_Cash-Reserven (kum.)")
        asset_cols.append("ASSET_VAL_Cash-Reserven (kum.)")

    for i, col in enumerate(asset_cols):
        name = col.replace("ASSET_VAL_", "")
        color = _get_color_by_name(name, i)
        
        fig.add_trace(
            go.Scatter(
                x=x_vals, 
                y=df[col], 
                name=name,
                mode='lines',
                stackgroup='one', # Macht es zum gestapelten Flächendiagramm
                line=dict(width=0.5, color=color),
                fillcolor=color,
                hovertemplate="%{y:,.0f} €"
            )
        )
    
    # Rote Null-Linie
    fig.add_hline(y=0, line_width=2, line_color="#CB4335", line_dash="dash")
    
    fig.update_layout(
        title="Detaillierte Vermögensentwicklung nach Assets",
        template="plotly_white",
        hovermode="x unified",
        margin=dict(t=50, b=20, l=20, r=20),
        yaxis_title="Vermögen in Euro",
        xaxis_title="Jahr",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        separators=",.",
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="#E5E7E9",
            font_size=13,
            font_family="Arial",
            namelength=-1
        )
    )
    
    if is_categorical:
        fig.update_xaxes(
            type='linear',
            tickmode='array',
            tickvals=x_vals,
            ticktext=df["Label"],
            tickangle=-45
        )
    
    return fig


def create_break_even_chart(df, be_alter):
    """
    Erstellt ein Liniendiagramm zum Vergleich der kumulierten Rentenzahlungen.
    """
    fig = go.Figure()
    
    # Szenario A (Früher)
    fig.add_trace(go.Scatter(
        x=df["Alter"], y=df["Kumuliert_A"], 
        name="Wunsch-Termin (Früher)", 
        line=dict(color='#2E86C1', width=3)
    ))
    
    # Szenario B (Später)
    fig.add_trace(go.Scatter(
        x=df["Alter"], y=df["Kumuliert_B"], 
        name="Regelaltersgrenze (Später)", 
        line=dict(color='#28B463', width=3)
    ))
    
    # Break-Even Marker
    if be_alter:
        fig.add_vline(x=be_alter, line_dash="dash", line_color="red")
        fig.add_annotation(
            x=be_alter, y=df[df["Alter"] == be_alter]["Kumuliert_A"].values[0],
            text=f"Break-Even mit {be_alter} Jahren",
            showarrow=True, arrowhead=1, ax=50, ay=30,
            bgcolor="white", bordercolor="red"
        )
    
    fig.update_layout(
        title="Vergleich kumulierter Netto-Rentenbezug",
        xaxis_title="Alter",
        yaxis_title="Summe ausgezahlter Renten (€)",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        separators=",."
    )
    
    return fig
