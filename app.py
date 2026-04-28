import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# --- LOGIK-FUNKTIONEN ---

def berechne_einkommensteuer(zu_versteuerndes_einkommen):
    """
    Berechnung der deutschen Einkommensteuer (Tarif 2024) gemäß § 32a EStG.
    """
    X = zu_versteuerndes_einkommen
    if X <= 11604:
        return 0
    elif X <= 17009:
        y = (X - 11604) / 10000
        return (117.74 * y + 1500) * y
    elif X <= 66760:
        y = (X - 17009) / 10000
        return (192.59 * y + 2397) * y + 969.12
    elif X <= 277825:
        return 0.42 * X - 10602.13
    else:
        return 0.45 * X - 18713.84

def berechne_progressionsvorbehalt(zu_versteuerndes_einkommen, steuerfreier_betrag):
    fiktives_gesamteinkommen = zu_versteuerndes_einkommen + steuerfreier_betrag
    fiktive_steuer = berechne_einkommensteuer(fiktives_gesamteinkommen)
    if fiktives_gesamteinkommen > 0:
        effektiver_steuersatz = fiktive_steuer / fiktives_gesamteinkommen
    else:
        effektiver_steuersatz = 0
    return effektiver_steuersatz * zu_versteuerndes_einkommen

def berechne_rentensteuer_anteil(rentenbeginn_jahr):
    basis_jahr = 2022
    basis_anteil = 82.0
    if rentenbeginn_jahr <= basis_jahr:
        return min(100.0, basis_anteil + (rentenbeginn_jahr - 2000))
    else:
        jahre_nach_2022 = rentenbeginn_jahr - 2022
        return min(100.0, basis_anteil + jahre_nach_2022 * 0.5)

# --- SESSION STATE ---
if "einnahmen" not in st.session_state:
    st.session_state.einnahmen = [
        {"name": "Gesetzliche Rente", "betrag": 2200.0, "typ": "Gesetzlich", "start": 2031, "ende": 2065},
        {"name": "Betriebsrente", "betrag": 600.0, "typ": "bAV", "start": 2031, "ende": 2065},
    ]

# --- UI STRUKTUR ---
st.set_page_config(page_title="Ruhestands-Cockpit PRO", layout="wide")
st.title("🛡️ Ruhestands-Cockpit: Präzisions-Planer")

with st.sidebar:
    st.header("Zentrale Parameter")
    geburtsjahr = st.number_input("Geburtsjahr", value=1965)
    aktuelles_jahr = 2026
    
    st.divider()
    st.subheader("Zeitstrahl-Simulation")
    betrachtungsjahr = st.slider("Betrachtungsjahr", aktuelles_jahr, geburtsjahr + 100, aktuelles_jahr)
    alter = betrachtungsjahr - geburtsjahr
    st.info(f"Alter im Jahr {betrachtungsjahr}: **{alter} Jahre**")

    st.divider()
    st.subheader("Meilensteine")
    rentenbeginn = st.number_input("Rentenbeginn (Jahr)", value=2031)
    atz_simulieren = st.checkbox("ATZ einplanen", value=False)
    if atz_simulieren:
        atz_start = st.number_input("ATZ Beginn (Jahr)", value=rentenbeginn - 6)
        atz_dauer = st.slider("ATZ Dauer (Jahre)", 1, 10, 6)
        atz_ende = atz_start + atz_dauer
    else:
        atz_start, atz_ende = 9999, 9999

    if betrachtungsjahr < atz_start and betrachtungsjahr < rentenbeginn:
        phase = "Aktiv"
    elif atz_simulieren and atz_start <= betrachtungsjahr < rentenbeginn:
        phase = "ATZ"
    else:
        phase = "Rente"
    st.success(f"Aktuelle Phase: **{phase}**")
    
    st.divider()
    st.subheader("Einnahmequellen")
    with st.expander("➕ Neue Quelle hinzufügen"):
        n_name = st.text_input("Name", value="Private Rente")
        n_typ = st.selectbox("Typ", ["Gesetzlich", "bAV", "Privat", "Kapital", "Sonstiges"])
        n_betrag = st.number_input("Monatsbetrag (€)", value=500.0)
        n_start = st.number_input("Start (Jahr)", value=rentenbeginn)
        n_ende = st.number_input("Ende (Jahr)", value=2065)
        if st.button("Hinzufügen"):
            st.session_state.einnahmen.append({"name": n_name, "betrag": n_betrag, "typ": n_typ, "start": n_start, "ende": n_ende})
            st.rerun()

    to_delete = []
    for i, e in enumerate(st.session_state.einnahmen):
        col_e1, col_e2 = st.columns([0.8, 0.2])
        col_e1.write(f"**{e['name']}** ({e['betrag']}€)")
        if col_e2.button("🗑️", key=f"del_{i}"): to_delete.append(i)
    if to_delete:
        for idx in sorted(to_delete, reverse=True): st.session_state.einnahmen.pop(idx)
        st.rerun()

    st.divider()
    st.subheader("Finanzen Aktuell")
    aktuelles_brutto = st.number_input("Aktuelles Brutto-Gehalt (Monat)", value=6000.0)
    atz_aufstockung_pct = st.slider("ATZ-Aufstockung AG (%)", 20, 50, 20)
    aktuelles_netto = st.number_input("Aktuelles Netto-Einkommen (Monat)", value=4500.0)
    show_values = st.checkbox("Werte in Diagrammen anzeigen", value=True)

    st.divider()
    st.subheader("Haushaltsbuch")
    ausgaben_kategorien = {"Wohnen": 1200, "Mobilität": 250, "Lebensmittel": 400, "Versicherungen": 150, "Gesundheit": 100, "Freizeit": 300, "Sonstiges": 200}
    ausgaben_input, anpassungsfaktor_input = {}, {}
    for kat, d_wert in ausgaben_kategorien.items():
        c1, c2 = st.columns([0.6, 0.4])
        ausgaben_input[kat] = c1.number_input(f"{kat}", value=float(d_wert), key=f"c_{kat}")
        anpassungsfaktor_input[kat] = c2.slider(f"RV%", 0, 200, 100, key=f"a_{kat}")

# --- VISUALISIERUNGS-FUNKTION ---
def create_sankey(labels, sources, targets, values, title, show_vals=True):
    display_labels = []
    node_colors = []
    for i, label in enumerate(labels):
        in_s = sum([values[j] for j, t in enumerate(targets) if t == i])
        out_s = sum([values[j] for j, s in enumerate(sources) if s == i])
        v = max(in_s, out_s)
        display_labels.append(f"{label} ({v:.0f}€)" if show_vals else label)
        if "Überschuss" in label: node_colors.append("#28B463")
        elif "Unterdeckung" in label: node_colors.append("#CB4335")
        else: node_colors.append("#2E86C1")
    fig = go.Figure(data=[go.Sankey(node=dict(pad=20, thickness=25, line=dict(width=0), label=display_labels, color=node_colors),
                                 link=dict(source=sources, target=targets, value=values, color="#E5E7E9"))])
    fig.update_layout(title_text=title, font=dict(size=13, color="black", family="Arial"), template="plotly_white", height=400)
    return fig

# --- HAUPTBEREICH (TABS) ---
tab1, tab2 = st.tabs(["📊 Sankey-Analyse", "📈 Langfrist-Trend"])

with tab1:
    st.subheader("1. Status Quo (Aktivphase)")
    sq_labels, sq_sources, sq_targets, sq_values = [], [], [], []
    def add_sq(s, t, v):
        if v > 0.1:
            if s not in sq_labels: sq_labels.append(s)
            if t not in sq_labels: sq_labels.append(t)
            sq_sources.append(sq_labels.index(s)); sq_targets.append(sq_labels.index(t)); sq_values.append(v)
    
    a_sq_sum = sum(ausgaben_input.values())
    d_sq = aktuelles_netto - a_sq_sum
    add_sq("Aktuelles Netto", "Haushalts-Budget", aktuelles_netto)
    if d_sq > 0: add_sq("Haushalts-Budget", "Liquiditäts-Überschuss", d_sq)
    elif d_sq < 0: add_sq("Liquiditäts-Unterdeckung", "Haushalts-Budget", abs(d_sq))
    for k, v in ausgaben_input.items(): add_sq("Haushalts-Budget", k, v)
    st.plotly_chart(create_sankey(sq_labels, sq_sources, sq_targets, sq_values, "Aktueller Cashflow"), use_container_width=True)

    st.divider()
    st.subheader(f"2. Simulation: {phase} ({betrachtungsjahr})")
    r_ant = berechne_rentensteuer_anteil(rentenbeginn)
    l_r, s_r, t_r, v_r = [], [], [], []
    def add_r(s, t, v):
        if v > 0.1:
            if s not in l_r: l_r.append(s)
            if t not in l_r: l_r.append(t)
            s_r.append(l_r.index(s)); t_r.append(l_r.index(t)); v_r.append(v)

    if phase == "Aktiv":
        st_m = berechne_einkommensteuer(aktuelles_brutto * 12) / 12
        sv_m = aktuelles_brutto * 0.20
        net_r = aktuelles_brutto - st_m - sv_m
        add_r("Arbeitseinkommen", "Brutto", aktuelles_brutto)
        add_r("Brutto", "Steuern", st_m); add_r("Brutto", "Sozialabgaben", sv_m); add_r("Brutto", "Verfügbares Budget", net_r)
    elif phase == "ATZ":
        h_br = aktuelles_brutto / 2; auf = h_br * (atz_aufstockung_pct / 100)
        st_m = berechne_progressionsvorbehalt(h_br * 12, auf * 12) / 12
        sv_m = h_br * 0.20; net_r = (h_br + auf) - st_m - sv_m
        add_r("ATZ-Gehalt", "Brutto", h_br); add_r("AG-Aufstockung", "Brutto", auf)
        add_r("Brutto", "Steuern", st_m); add_r("Brutto", "Sozialabgaben", sv_m); add_r("Brutto", "Verfügbares Budget", net_r)
    else:
        b_g, st_b = 0, 0
        for e in st.session_state.einnahmen:
            if betrachtungsjahr >= e["start"] and betrachtungsjahr <= e["ende"]:
                add_r(e["name"], "Brutto", e["betrag"]); b_g += e["betrag"]
                if e["typ"] in ["Gesetzlich", "bAV"]: st_b += e["betrag"] * (r_ant / 100)
                elif e["typ"] == "Privat": st_b += e["betrag"] * 0.18
                else: st_b += e["betrag"]
        st_m = berechne_einkommensteuer(st_b * 12) / 12; sv_m = b_g * 0.15; net_r = b_g - st_m - sv_m
        add_r("Brutto", "Steuern", st_m); add_r("Brutto", "Sozialabgaben", sv_m); add_r("Brutto", "Verfügbares Budget", net_r)

    a_r_sum = sum([ausgaben_input[k] * (anpassungsfaktor_input[k]/100 if phase=="Rente" else 1.0) for k in ausgaben_kategorien])
    d_r = net_r - a_r_sum
    if d_r > 0: add_r("Verfügbares Budget", "Liquiditäts-Überschuss", d_r)
    elif d_r < 0: add_r("Liquiditäts-Unterdeckung", "Verfügbares Budget", abs(d_r))
    for k, v in ausgaben_input.items():
        add_r("Verfügbares Budget", k, v * (anpassungsfaktor_input[k]/100 if phase=="Rente" else 1.0))
    st.plotly_chart(create_sankey(l_r, s_r, t_r, v_r, f"Cashflow Simulation {betrachtungsjahr}"), use_container_width=True)

with tab2:
    st.subheader("Finanzielle Entwicklung bis Alter 95")
    jahre = list(range(aktuelles_jahr, geburtsjahr + 96))
    t_data = []
    for j in jahre:
        if j < atz_start and j < rentenbeginn: p = "Aktiv"
        elif atz_simulieren and atz_start <= j < rentenbeginn: p = "ATZ"
        else: p = "Rente"
        
        if p == "Aktiv":
            br = aktuelles_brutto; st_m = berechne_einkommensteuer(br * 12) / 12; sv_m = br * 0.20; net = br - st_m - sv_m
        elif p == "ATZ":
            h = aktuelles_brutto/2; a = h * (atz_aufstockung_pct/100)
            st_m = berechne_progressionsvorbehalt(h*12, a*12) / 12; sv_m = h*0.20; net = (h+a) - st_m - sv_m
        else:
            b, s_b = 0, 0
            for e in st.session_state.einnahmen:
                if j >= e["start"] and j <= e["ende"]:
                    b += e["betrag"]
                    if e["typ"] in ["Gesetzlich", "bAV"]: s_b += e["betrag"] * (r_ant / 100)
                    elif e["typ"] == "Privat": s_b += e["betrag"] * 0.18
                    else: s_b += e["betrag"]
            st_m = berechne_einkommensteuer(s_b * 12) / 12; sv_m = b * 0.15; net = b - st_m - sv_m
        
        ausg = sum([ausgaben_input[k] * (anpassungsfaktor_input[k]/100 if p=="Rente" else 1.0) for k in ausgaben_kategorien])
        t_data.append({"Jahr": j, "Netto-Einkommen": net, "Bedarf": ausg, "Überschuss/Defizit": net - ausg})

    df = pd.DataFrame(t_data)
    f_t = go.Figure()
    f_t.add_trace(go.Scatter(x=df["Jahr"], y=df["Netto-Einkommen"], name="Netto-Einkommen", fill='tozeroy', line=dict(color='#2E86C1')))
    f_t.add_trace(go.Scatter(x=df["Jahr"], y=df["Bedarf"], name="Bedarf", line=dict(color='#CB4335', width=3)))
    
    # Meilensteine hinzufügen
    meilensteine = []
    if atz_simulieren:
        meilensteine.append({"jahr": atz_start, "label": "Beginn ATZ", "color": "#F39C12"})
    meilensteine.append({"jahr": rentenbeginn, "label": "Rentenbeginn", "color": "#28B463"})
    
    for e in st.session_state.einnahmen:
        if e["start"] > aktuelles_jahr and e["start"] != rentenbeginn:
            meilensteine.append({"jahr": e["start"], "label": f"Start: {e['name']}", "color": "#8E44AD"})

    for m in meilensteine:
        f_t.add_vline(x=m["jahr"], line_width=2, line_dash="dash", line_color=m["color"])
        f_t.add_annotation(
            x=m["jahr"], y=1.05, yref="paper",
            text=f"{m['label']}<br>({m['jahr']})",
            showarrow=False, font=dict(color=m["color"], size=10),
            bgcolor="white", opacity=0.8
        )

    f_t.update_layout(
        template="plotly_white", 
        hovermode="x unified", 
        yaxis_title="€ / Monat",
        margin=dict(t=80)
    )
    st.plotly_chart(f_t, use_container_width=True)
    with st.expander("Tabelle anzeigen"): st.dataframe(df.style.format("{:.2f}€", subset=["Netto-Einkommen", "Bedarf", "Überschuss/Defizit"]))
