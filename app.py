import streamlit as st
from logic.engine import calculate_financials_for_year, generate_trend_data, get_phase
from ui.sidebar import render_sidebar
from ui.charts import create_sankey, create_trend_chart

# --- INITIALISIERUNG ---
if "einnahmen" not in st.session_state:
    st.session_state.einnahmen = [
        {"name": "Gesetzliche Rente", "betrag": 2200.0, "typ": "Gesetzlich", "start": 2031, "ende": 2065},
        {"name": "Betriebsrente", "betrag": 600.0, "typ": "bAV", "start": 2031, "ende": 2065},
    ]

st.set_page_config(page_title="Rente-O-Mat PRO", layout="wide")
st.title("🛡️ Rente-O-Mat: Präzisions-Planer")

# --- SIDEBAR & PARAMETER ---
p = render_sidebar()

# --- HAUPTBEREICH (TABS) ---
tab1, tab2 = st.tabs(["📊 Sankey-Analyse", "📈 Zeitliche Entwicklung"])

with tab1:
# ... (keine Änderungen im tab1) ...
    # 1. Status Quo Analyse
    st.subheader("1. Status Quo (Aktivphase)")
    sq_labels, sq_sources, sq_targets, sq_values = [], [], [], []
    
    def add_sq(s, t, v):
        if v > 0.1:
            if s not in sq_labels: sq_labels.append(s)
            if t not in sq_labels: sq_labels.append(t)
            sq_sources.append(sq_labels.index(s))
            sq_targets.append(sq_labels.index(t))
            sq_values.append(v)
    
    a_sq_sum = sum(p['ausgaben_input'].values())
    d_sq = p['aktuelles_netto'] - a_sq_sum
    add_sq("Aktuelles Netto", "Haushalts-Budget", p['aktuelles_netto'])
    if d_sq > 0: add_sq("Haushalts-Budget", "Liquiditäts-Überschuss", d_sq)
    elif d_sq < 0: add_sq("Liquiditäts-Unterdeckung", "Haushalts-Budget", abs(d_sq))
    for k, v in p['ausgaben_input'].items(): add_sq("Haushalts-Budget", k, v)
    st.plotly_chart(create_sankey(sq_labels, sq_sources, sq_targets, sq_values, "Aktueller Cashflow", p['show_values']), use_container_width=True)

    # 2. Simulations-Analyse
    res = calculate_financials_for_year(p['betrachtungsjahr'], p)
    st.divider()
    st.subheader(f"2. Simulation: {res['Phase']} ({p['betrachtungsjahr']})")
    
    l_r, s_r, t_r, v_r = [], [], [], []
    def add_r(s, t, v):
        if v > 0.1:
            if s not in l_r: l_r.append(s)
            if t not in l_r: l_r.append(t)
            s_r.append(l_r.index(s))
            t_r.append(l_r.index(t))
            v_r.append(v)

    # Brutto-Aufschlüsselung im Sankey
    if res['Phase'] == "Aktiv":
        add_r("Arbeitseinkommen", "Brutto", p['aktuelles_brutto'])
    elif res['Phase'] in ["ATZ(A)", "ATZ(P)"]:
        h_br = p['aktuelles_brutto'] / 2
        auf = h_br * (p['atz_aufstockung_pct'] / 100)
        add_r("ATZ-Gehalt", "Brutto", h_br)
        add_r("AG-Aufstockung", "Brutto", auf)
    else: # Rente
        for e in p['einnahmen']:
            if p['betrachtungsjahr'] >= e["start"] and p['betrachtungsjahr'] <= e["ende"]:
                add_r(e["name"], "Brutto", e["betrag"])

    add_r("Brutto", "Steuern", res['Steuern'])
    add_r("Brutto", "Sozialabgaben", res['Sozialabgaben'])
    add_r("Brutto", "Verfügbares Budget", res['Netto-Einkommen'])

    if res['Überschuss/Defizit'] > 0:
        add_r("Verfügbares Budget", "Liquiditäts-Überschuss", res['Überschuss/Defizit'])
    elif res['Überschuss/Defizit'] < 0:
        add_r("Liquiditäts-Unterdeckung", "Verfügbares Budget", abs(res['Überschuss/Defizit']))

    for k in p['ausgaben_kategorien']:
        val = p['ausgaben_input'][k] * (p['anpassungsfaktor_input'][k]/100 if res['Phase']=="Rente" else 1.0)
        add_r("Verfügbares Budget", k, val)
        
    st.plotly_chart(create_sankey(l_r, s_r, t_r, v_r, f"Cashflow Simulation {p['betrachtungsjahr']}", p['show_values']), use_container_width=True)

with tab2:
    st.subheader("Finanzielle Entwicklung bis Alter 95")
    show_tax_rate = st.checkbox("Effektiven Steuersatz anzeigen (%)", value=False)
    
    jahre = list(range(p['aktuelles_jahr'], p['geburtsjahr'] + 96))
    df_trend = generate_trend_data(jahre, p)
    
    # Meilensteine vorbereiten (ATZ-A/P Split)
    meilensteine = []
    if p['atz_simulieren']:
        atz_mitte = p['atz_start'] + (p['atz_ende'] - p['atz_start']) / 2
        meilensteine.append({"jahr": p['atz_start'], "label": "ATZ(A)", "color": "#F39C12"})
        meilensteine.append({"jahr": atz_mitte, "label": "ATZ(P)", "color": "#F1C40F"})
    
    meilensteine.append({"jahr": p['rentenbeginn'], "label": "Rentenbeginn", "color": "#28B463"})
    for e in p['einnahmen']:
        if e["start"] > p['aktuelles_jahr'] and e["start"] != p['rentenbeginn']:
            meilensteine.append({"jahr": e["start"], "label": f"Start: {e['name']}", "color": "#8E44AD"})

    st.plotly_chart(create_trend_chart(df_trend, meilensteine, show_tax_rate=show_tax_rate), use_container_width=True)
    
    with st.expander("Datentabelle anzeigen"):
        st.dataframe(df_trend.style.format("{:.2f}€", subset=["Brutto", "Steuern", "Sozialabgaben", "Netto-Einkommen", "Bedarf", "Überschuss/Defizit"]).format("{:.1f}%", subset=["Steuersatz"]), use_container_width=True)
