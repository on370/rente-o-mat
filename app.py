# Rente-O-Mat PRO
import streamlit as st
import warnings
# Unterdrücke alle Kaleido-bezogenen DeprecationWarnings
warnings.filterwarnings("ignore", message=".*Kaleido versions less than 1.0.0.*")
from ui.sidebar import render_sidebar
from ui.charts import create_sankey, create_trend_chart, create_wealth_chart, create_break_even_chart
from logic.engine import calculate_financials_for_year, generate_trend_data, calculate_break_even_data
from config import FULL_VERSION, DATENSCHUTZ_INFO

st.set_page_config(page_title="Rente-O-Mat PRO", layout="wide")

# --- WELCOME DIALOG & DISCLAIMER ---
if "disclaimer_accepted" not in st.session_state:
    st.session_state.disclaimer_accepted = False

if not st.session_state.disclaimer_accepted:
    st.title("🛡️ Willkommen beim Rente-O-Mat")
    st.subheader(f"Version {FULL_VERSION}")
    st.warning("""
    **DISCLAIMER:** Achtung, der Renten-Planer ist noch in der Entwicklung und kann fehlerhaft oder unvollständig sein. 
    Alle Angaben müssen durch den/die Nutzer:in überprüft werden. Benutzung auf eigenes Risiko.
    """)
    st.info(DATENSCHUTZ_INFO)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("✅ Einverstanden", width='stretch'):
            st.session_state.disclaimer_accepted = True
            st.rerun()
    st.stop()

st.title("🛡️ Rente-O-Mat: Der Lebens-Finanz-Planer")
st.caption(FULL_VERSION)

# --- SIDEBAR & PARAMETER ---
p = render_sidebar()

# --- DATEN-GENERIERUNG (Zentral für alle Tabs) ---
jahre_liste = list(range(p['aktuelles_jahr'], p['geburtsjahr'] + 96))
df_timeline = generate_trend_data(jahre_liste, p)

def get_current_meilensteine(p):
    """Berechnet die Liste der Meilensteine basierend auf den aktuellen Parametern."""
    meilensteine = [{"jahr": p['aktuelles_jahr'], "label": "Start", "color": "#7F8C8D"}]
    if p.get('atz_simulieren'):
        meilensteine.append({"jahr": p['atz_start'], "label": "ATZ-A", "color": "#2E86C1"})
        atz_mitte = p['atz_start'] + (p['atz_dauer'] / 2)
        meilensteine.append({"jahr": atz_mitte, "label": "ATZ-P", "color": "#F1C40F"})
    meilensteine.append({"jahr": p['rentenbeginn'], "label": "Rente", "color": "#28B463"})
    return meilensteine

def st_display_table(df, filename, money_cols=None, pct_cols=None):
    """Hilfsfunktion zum Anzeigen einer formatierten Tabelle mit CSV-Download."""
    if money_cols is None: money_cols = []
    if pct_cols is None: pct_cols = []
    
    # UI Formatting
    format_dict = {}
    for col in df.columns:
        if col in money_cols:
            format_dict[col] = lambda x: f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "")
        elif col in pct_cols:
            format_dict[col] = lambda x: f"{x:,.1f} %".replace(".", ",")
        elif col == "Jahr" or col == "Alter":
            format_dict[col] = lambda x: f"{int(x)}"
            
    st.dataframe(df.style.format(format_dict), width='stretch')
    
    # CSV Export (ohne Euro-Zeichen, mit Semikolon und Dezimalkomma)
    csv = df.to_csv(index=False, sep=';', decimal=',')
    st.download_button(
        label=f"📥 {filename} als CSV speichern",
        data=csv,
        file_name=f"{filename}.csv",
        mime='text/csv',
    )

def capture_charts_for_pdf(p, df_timeline):
    """Erzeugt alle Diagramme als PNG-Bytes für das PDF."""
    import io
    from ui.charts import create_sankey, create_trend_chart, create_wealth_chart
    
    charts = {}
    meilensteine = get_current_meilensteine(p)

    try:
        # 1. Sankey Aktiv (Status Quo)
        sq_labels, sq_sources, sq_targets, sq_values = [], [], [], []
        def add_sq(s, t, v):
            if v > 0.1:
                if s not in sq_labels: sq_labels.append(s)
                if t not in sq_labels: sq_labels.append(t)
                sq_sources.append(sq_labels.index(s)); sq_targets.append(sq_labels.index(t)); sq_values.append(v)
        
        a_sq_sum = sum(p['ausgaben_input'].values())
        d_sq = p['aktuelles_netto'] - a_sq_sum
        add_sq("Aktuelles Netto", "Haushalts-Budget", p['aktuelles_netto'])
        if d_sq > 0: add_sq("Haushalts-Budget", "Überschuss", d_sq)
        elif d_sq < 0: add_sq("Unterdeckung", "Haushalts-Budget", abs(d_sq))
        for k, v in p['ausgaben_input'].items(): add_sq("Haushalts-Budget", k, v)
        
        fig_sq = create_sankey(sq_labels, sq_sources, sq_targets, sq_values, "Aktueller Cashflow", True)
        charts["sankey_aktiv"] = fig_sq.to_image(format="png", width=1000, height=500)
        
        # 2. Sankey Rente (Erstes Rentenjahr)
        renten_jahre = df_timeline[df_timeline["Phase"] == "Rente"]
        if not renten_jahre.empty:
            res = renten_jahre.iloc[0].to_dict()
            l_r, s_r, t_r, v_r = [], [], [], []
            def add_r(s, t, v):
                if v > 0.1:
                    if s not in l_r: l_r.append(s)
                    if t not in l_r: l_r.append(t)
                    s_r.append(l_r.index(s)); t_r.append(l_r.index(t)); v_r.append(v)
            
            exclude = ["Jahr", "Phase", "Brutto", "EkSt", "Soli", "KiSt", "Steuern", "Steuersatz", "Sozialabgaben", "Netto-Einkommen", "Bedarf", "Überschuss/Defizit", "Rentenabschlag", "Beitragsverlust", "Steuerpflichtiger_Rentenanteil", "Netto-GRV", "Kapitalzuwachs_Sonder", "Gesetzliche Rente (Potenzial)"]
            income_sources = {k: v for k, v in res.items() if k not in exclude and not k.startswith("EXP_") and not k.startswith("ASSET_VAL_") and not k.startswith("_debug") and v > 0}
            for k, v in income_sources.items(): add_r(k, "Brutto-Einkommen", v)
            add_r("Brutto-Einkommen", "Steuern & Abgaben", res['Steuern'] + res['Sozialabgaben'])
            add_r("Brutto-Einkommen", "Netto-Verfügbar", res['Netto-Einkommen'])
            add_r("Netto-Verfügbar", "Bedarf (Lebenshaltung)", res['Bedarf'])
            ue = res['Überschuss/Defizit']
            if ue > 0: add_r("Netto-Verfügbar", "Überschuss", ue)
            elif ue < 0: add_r("Defizit", "Netto-Verfügbar", abs(ue))
            
            fig_r = create_sankey(l_r, s_r, t_r, v_r, f"Cashflow im 1. Rentenjahr ({int(res['Jahr'])})", True)
            charts["sankey_rente"] = fig_r.to_image(format="png", width=1000, height=500)
            
        # 3. Trends
        fig_wealth = create_wealth_chart(df_timeline)
        charts["trend_assets"] = fig_wealth.to_image(format="png", width=1000, height=500)
        
        fig_income = create_trend_chart(df_timeline, meilensteine)
        charts["trend_income"] = fig_income.to_image(format="png", width=1000, height=500)
        
    except Exception as e:
        st.error(f"Fehler bei der Bild-Generierung: {e}")
        
    return charts

# --- HAUPTBEREICH (TABS) ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Sankey-Analyse", "📈 Zeitliche Entwicklung", "💰 Vermögensentwicklung", "⚖️ Strategie-Check", "📑 Dein Briefing"])

# --- TAB 1: SANKEY ---
with tab1:
    # 1. STATUS QUO CONTAINER
    with st.container(border=True):
        st.subheader("📊 1. Status Quo (Aktivphase Heute)")
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
        st.plotly_chart(create_sankey(sq_labels, sq_sources, sq_targets, sq_values, "Aktueller Cashflow", p['show_values']), width='stretch')
        with st.expander("Daten zum Status Quo anzeigen"):
            import pandas as pd
            df_sq_data = pd.DataFrame([
                {"Kategorie": "Einnahmen", "Posten": "Aktuelles Netto", "Betrag": p['aktuelles_netto']},
                {"Kategorie": "Bilanz", "Posten": "Überschuss/Defizit", "Betrag": d_sq}
            ] + [{"Kategorie": "Ausgaben", "Posten": k, "Betrag": v} for k, v in p['ausgaben_input'].items()])
            st_display_table(df_sq_data, "Status_Quo_Cashflow", money_cols=["Betrag"])

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. SIMULATIONS CONTAINER
    with st.container(border=True):
        st.subheader("🎯 2. Simulations-Analyse")
        
        # Zeitstrahl-Navigation direkt hier
        slider_options = df_timeline["Label"].tolist()
        if "betrachtungslabel" not in st.session_state or str(st.session_state.betrachtungslabel) not in slider_options:
            st.session_state.betrachtungslabel = slider_options[0]
        else:
            st.session_state.betrachtungslabel = str(st.session_state.betrachtungslabel)
            
        label_formatting = {}
        for idx, row in df_timeline.iterrows():
            lbl = row["Label"]
            phase = row["Phase"]
            
            # Ordne Phase das passende Symbol & Namen zu
            if phase == "Aktiv":
                emoji = "📍"
                phase_lbl = "Aktiv"
            elif phase == "ATZ(A)":
                emoji = "🔵"
                phase_lbl = "ATZ(A)"
            elif phase == "ATZ(P)":
                emoji = "🟡"
                phase_lbl = "ATZ(P)"
            elif phase == "Rente":
                emoji = "🟢"
                phase_lbl = "Rente"
            else:
                emoji = "⚪"
                phase_lbl = phase
                
            label_formatting[lbl] = f"{lbl} ({emoji} {phase_lbl})"

        # Slider für den Zeitraum (Unterstützt geteilte Übergangsjahre wie 2027 (01))
        selected_label = st.select_slider(
            "Simulation für Zeitraum:",
            options=slider_options,
            value=st.session_state.betrachtungslabel,
            format_func=lambda x: label_formatting.get(x, x),
            key="b_label_slider"
        )
        st.session_state.betrachtungslabel = selected_label
        
        # Daten für den gewählten Zeitraum holen
        res = df_timeline[df_timeline["Label"] == selected_label].iloc[0].to_dict()
        
        # Phasen-Anzeige & Meilensteine
        c1, c2 = st.columns([0.4, 0.6])
        with c1:
            phase_label = res['Phase']
            if phase_label == "Aktiv": st.info(f"Phase: **Aktivphase**")
            elif "ATZ" in phase_label: st.warning(f"Phase: **Altersteilzeit** ({phase_label})")
            else: st.success(f"Phase: **Ruhestand**")
        
        with c2:
            def fmt_j(j): return f"{j:.1f}".replace(".0", "") if j % 1 != 0 else f"{int(j)}"
            m_text = f"📍 Heute: {p['aktuelles_jahr']} | 🟢 Rente: {fmt_j(p['rentenbeginn'])}"
            if p['atz_simulieren']:
                atz_mitte = p['atz_start'] + (p['atz_dauer'] / 2)
                m_text = f"🔵 ATZ-A: {fmt_j(p['atz_start'])} | 🟡 ATZ-P: {fmt_j(atz_mitte)} | 🟢 Rente: {fmt_j(p['rentenbeginn'])}"
            st.caption(m_text)
        
        st.divider()

        # KENNZAHLEN DASHBOARD
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Brutto", f"{res['Brutto']:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
        col2.metric("Netto", f"{res['Netto-Einkommen']:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."), 
                    help="Das Netto wird auf Basis des zu versteuernden Einkommens (zvE) berechnet.")
        col3.metric("Steuerlast", f"{res['Steuersatz']:.1f} %")
        
        ueberschuss = res['Überschuss/Defizit']
        ueberschuss_color = "normal" if ueberschuss >= 0 else "inverse"
        col4.metric("Überschuss", f"{ueberschuss:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."), delta=f"{ueberschuss:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."), delta_color=ueberschuss_color)
        
        # SANKEY AUFBAU
        l_r, s_r, t_r, v_r = [], [], [], []
        def add_r(s, t, v):
            if v > 0.1:
                if s not in l_r: l_r.append(s)
                if t not in l_r: l_r.append(t)
                s_r.append(l_r.index(s))
                t_r.append(l_r.index(t))
                v_r.append(v)

        # Brutto-Aufschlüsselung & Potenzial-Logik (K4 - robust)
        pot = res.get('Gesetzliche Rente (Potenzial)', 0)
        bv = res.get('Beitragsverlust', 0)
        ra = res.get('Rentenabschlag', 0)
        
        for e in p['einnahmen']:
            jahr_float = res.get('Jahr_Float', float(res['Jahr']))
            if jahr_float >= e.get("start", 0) and jahr_float <= e.get("ende", 9999):
                val = res.get(e["name"], 0.0)
                if val > 0 and e["typ"] != "Gesetzlich":
                    add_r(e["name"], "Brutto", val)
        
        # NEU: Entnahmen aus Assets im Sankey anzeigen
        for k, v in res.items():
            if k.startswith("Entnahme: ") and v > 0:
                add_r(k, "Brutto", v)
        
        # GRV: Aggregierter Potenzial-Flow
        if pot > 0:
            jahr_float = res.get('Jahr_Float', float(res['Jahr']))
            grv_names = [e["name"] for e in p['einnahmen'] if e['typ'] == 'Gesetzlich'
                         and jahr_float >= e.get('start', 0) and jahr_float <= e.get('ende', 9999)
                         and res.get(e['name'], 0) > 0]
            label = grv_names[0] if grv_names else "Gesetzliche Rente"
            
            if bv > 0 or ra > 0:
                # Abzüge vorhanden → über Potenzial-Knoten leiten
                add_r(label, "GRV (Potenzial)", pot)
                grv_auszahlung = pot - bv - ra
                if grv_auszahlung > 0:
                    add_r("GRV (Potenzial)", "Brutto", grv_auszahlung)
                if bv > 0:
                    add_r("GRV (Potenzial)", "Beitragsverlust", bv)
                if ra > 0:
                    add_r("GRV (Potenzial)", "Rentenabschlag", ra)
            else:
                # Keine Abzüge → direkt ins Brutto
                add_r(label, "Brutto", pot)
            
        # Spezialfälle Aktiv/ATZ (direkt ins Brutto)
        if res['Phase'] == "Aktiv" and "Gehalt" in res:
             add_r("Arbeitseinkommen", "Brutto", res["Gehalt"])
        elif res['Phase'] in ["ATZ(A)", "ATZ(P)"]:
             if "Gehalt (ATZ)" in res: add_r("ATZ-Gehalt", "Brutto", res["Gehalt (ATZ)"])
             if "Aufstockung" in res: add_r("AG-Aufstockung", "Brutto", res["Aufstockung"])

        # Abzüge vom Brutto (jetzt korrekt balanciert)
        if res['EkSt'] > 0: add_r("Brutto", "Einkommensteuer", res['EkSt'])
        if res['Soli'] > 0: add_r("Brutto", "Soli", res['Soli'])
        if res['KiSt'] > 0: add_r("Brutto", "Kirchensteuer", res['KiSt'])
        if res['Sozialabgaben'] > 0: add_r("Brutto", "Sozialabgaben", res['Sozialabgaben'])
        
        add_r("Brutto", "Netto-Einkommen", res['Netto-Einkommen'])
        add_r("Netto-Einkommen", "Verfügbares Budget", res['Netto-Einkommen'])
        
        if res['Überschuss/Defizit'] > 0:
            add_r("Verfügbares Budget", "Liquiditäts-Überschuss", res['Überschuss/Defizit'])
        elif res['Überschuss/Defizit'] < 0:
            add_r("Liquiditäts-Unterdeckung", "Verfügbares Budget", abs(res['Überschuss/Defizit']))

        for k in p['ausgaben_kategorien']:
            val = res.get(f"EXP_{k}", 0.0)
            if val > 0: add_r("Verfügbares Budget", k, val)
            
        st.plotly_chart(create_sankey(l_r, s_r, t_r, v_r, f"Cashflow Simulation {selected_label}", p['show_values']), width='stretch')
        with st.expander(f"Details zum Zeitraum {selected_label} anzeigen"):
            # Relevante Zeilen aus 'res' extrahieren
            sim_data = []
            for k, v in res.items():
                if k in ["Brutto", "Netto-Einkommen", "Bedarf", "Überschuss/Defizit", "EkSt", "Soli", "KiSt", "Sozialabgaben"]:
                    sim_data.append({"Posten": k, "Wert": v})
                elif k.startswith("EXP_") or k.startswith("Entnahme: ") or k in p['ausgaben_kategorien']:
                    sim_data.append({"Posten": k.replace("EXP_", ""), "Wert": v})
            
            import pandas as pd
            df_sim_year = pd.DataFrame(sim_data)
            st_display_table(df_sim_year, f"Simulation_{selected_label.replace(' ', '_')}", money_cols=["Wert"])

# --- TAB 2: TREND ---
with tab2:
    st.subheader("Finanzielle Entwicklung bis Alter 95")
    show_tax_rate = st.checkbox("Effektiven Steuersatz anzeigen (%)", value=False)
    
    # Meilensteine vorbereiten
    meilensteine = []
    if p['atz_simulieren']:
        atz_mitte = p['atz_start'] + (p['atz_dauer'] / 2)
        meilensteine.append({"jahr": p['atz_start'], "label": "ATZ(A)", "color": "#F39C12"})
        meilensteine.append({"jahr": atz_mitte, "label": "ATZ(P)", "color": "#F1C40F"})
    
    meilensteine.append({"jahr": p['rentenbeginn'], "label": "Rentenbeginn", "color": "#28B463"})
    for e in p['einnahmen']:
        if e["start"] > p['aktuelles_jahr'] and e["start"] != p['rentenbeginn']:
            meilensteine.append({"jahr": e["start"], "label": f"Start: {e['name']}", "color": "#8E44AD"})

    st.plotly_chart(create_trend_chart(df_timeline, meilensteine, show_tax_rate=show_tax_rate), width='stretch')
    
    with st.expander("Datentabelle anzeigen"):
        st_display_table(df_timeline[["Jahr", "Phase", "Brutto", "Steuern", "Sozialabgaben", "Netto-Einkommen", "Bedarf", "Überschuss/Defizit", "Steuersatz"]], 
                         "Finanzielle_Entwicklung", 
                         money_cols=["Brutto", "Steuern", "Sozialabgaben", "Netto-Einkommen", "Bedarf", "Überschuss/Defizit"],
                         pct_cols=["Steuersatz"])

# --- TAB 3: VERMÖGEN ---
with tab3:
    st.subheader("Detaillierte Vermögensentwicklung (Stacked Area)")
    st.caption("Die Grafik zeigt die Entwicklung einzelner Assets sowie den kumulierten Cashflow (Liquidität).")
    st.plotly_chart(create_wealth_chart(df_timeline), width='stretch')
    
    with st.expander("Vermögensdaten anzeigen"):
        # Finde alle Asset-Spalten
        asset_cols = [c for c in df_timeline.columns if c.startswith("ASSET_VAL_")]
        # Bereinige Spaltennamen für die Anzeige (Entferne Präfix)
        df_display = df_timeline[["Jahr"] + asset_cols].copy()
        df_display.columns = ["Jahr"] + [c.replace("ASSET_VAL_", "") for c in asset_cols]
        new_asset_cols = [c.replace("ASSET_VAL_", "") for c in asset_cols]
        
        st_display_table(df_display, "Vermoegensentwicklung", money_cols=new_asset_cols)

# --- TAB 4: STRATEGIE ---
with tab4:
    st.subheader("Wann lohnt sich der spätere Renteneintritt?")
    st.info("""
    Diese Analyse vergleicht deinen gewählten Rentenbeginn mit dem gesetzlichen Regelrenteneintritt. 
    Dargestellt wird die Summe der bis zum jeweiligen Alter ausgezahlten Netto-Rentenbeträge (gesetzliche Rente).
    """)
    
    
    try:
        df_be, be_jahr, be_alter = calculate_break_even_data(p)
        
        if be_jahr:
            col1, col2 = st.columns(2)
            col1.metric("Break-Even Alter", f"{be_alter} Jahre")
            col2.metric("Break-Even Jahr", f"{be_jahr}")
            
            st.success(f"Ab dem Jahr **{be_jahr}** (Alter **{be_alter}**) hast du durch die höhere monatliche Regelrente insgesamt mehr Geld erhalten als durch den früheren, aber geringeren Rentenbezug.")
        else:
            st.warning("Kein Break-Even-Punkt innerhalb der Simulation (bis Alter 100) gefunden. Ein früherer Eintritt scheint in diesem Szenario langfristig vorteilhafter oder der Unterschied ist zu gering.")

        st.plotly_chart(create_break_even_chart(df_be, be_alter), width='stretch')
        with st.expander("Break-Even Datentabelle anzeigen"):
            st_display_table(df_be, "Break_Even_Analyse", money_cols=["Netto_A", "Netto_B", "Kumuliert_A", "Kumuliert_B"])
    except Exception as e:
        st.error(f"Fehler bei der Strategie-Berechnung: {e}")
        st.info("Dies kann an fehlenden Daten in einer importierten Datei liegen. Bitte prüfe deine Eingaben in der Sidebar.")

# --- TAB 5: DEIN BRIEFING ---
with tab5:
    st.subheader("📑 Dein persönliches Briefing")
    st.caption("Eine umfassende Zusammenfassung deiner Finanzplanung, aller Annahmen und rechtlichen Grundlagen.")
    
    with st.expander("📊 Zusammenfassung deiner Lebens-Finanz-Planung", expanded=True):
        st.markdown("**Die wichtigsten Fakten und Projektionen aus deiner persönlichen Simulation.**")
        
        # Finde erstes Rentenjahr
        renten_jahre = df_timeline[df_timeline["Phase"] == "Rente"]
        erstes_rentenjahr = renten_jahre.iloc[0] if not renten_jahre.empty else None
        
        # Endvermögen (letztes Jahr der Simulation)
        letztes_jahr = df_timeline.iloc[-1]
        end_vermoegen = letztes_jahr.get("ASSET_VAL_Cash-Reserven (kum.)", 0)
        # Alle anderen Assets addieren
        for col in df_timeline.columns:
            if col.startswith("ASSET_VAL_") and col != "ASSET_VAL_Cash-Reserven (kum.)":
                end_vermoegen += letztes_jahr.get(col, 0)
                
        # Ø Steuersatz Rente
        avg_tax_rente = renten_jahre["Steuersatz"].mean() if not renten_jahre.empty else 0
        
        # Break Even Daten
        try:
            df_be, be_jahr, be_alter = calculate_break_even_data(p)
            be_text = f"**{be_jahr}** (Alter **{be_alter}**)" if be_jahr else "Kein Break-Even bis Alter 100"
        except:
            be_text = "Nicht verfügbar"

        if erstes_rentenjahr is not None:
            rentenluecke = erstes_rentenjahr["Bedarf"] - erstes_rentenjahr["Netto-Einkommen"]
            
            # Engine liefert Monats-Werte
            abschlag_eur_mtl = erstes_rentenjahr.get("Rentenabschlag", 0)
            abschlag_eur_jahr = abschlag_eur_mtl * 12
            
            # Beitragsverlust (Euro pro Monat) / Rentenwert = Fehlende EP gesamt
            rentenwert_dyn = erstes_rentenjahr.get("_debug_rentenwert", 39.32)
            beitragsverlust_ep = erstes_rentenjahr.get("Beitragsverlust", 0) / rentenwert_dyn if rentenwert_dyn > 0 else 0
            
            c1, c2, c3 = st.columns(3)
            c1.metric(f"Finanzlücke im 1. Rentenjahr ({int(erstes_rentenjahr['Jahr'])})", f"{rentenluecke:,.0f} € mtl.".replace(",", "X").replace(".", ",").replace("X", "."), delta="Dein Vermögen muss dies decken" if rentenluecke > 0 else "Du hast einen Überschuss", delta_color="inverse" if rentenluecke > 0 else "normal")
            c2.metric("Projiziertes Gesamtvermögen (Alter 95)", f"{end_vermoegen:,.0f} €".replace(",", "X").replace(".", ",").replace("X", "."), help="Summe aus Liquidität und allen simulierten Assets am Ende des Betrachtungszeitraums.")
            c3.metric("Ø Steuersatz im Ruhestand", f"{avg_tax_rente:.1f} %".replace(".", ","))
            
            st.divider()
            st.markdown("### Detail-Fakten")
            
            renten_jahr = int(p['rentenbeginn'])
            renten_alter = renten_jahr - p['geburtsjahr']
            jahre_im_ruhestand = 95 - renten_alter
            
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                st.markdown(f"""
                - **Gewählter Rentenbeginn:** {renten_jahr} (mit Alter {renten_alter})
                - **Break-Even (im Vergleich zur Regelrente):** {be_text}
                - **Dauer der Auszahlungsphase:** {jahre_im_ruhestand} Jahre (bis Alter 95 berechnet)
                """)
            with col_f2:
                bedarf_summe = renten_jahre['Bedarf'].sum() * 12  # Bedarf in df_timeline ist monatlich
                st.markdown(f"""
                - **Rentenabschlag (durch vorzeitigen Beginn):** {abschlag_eur_mtl:,.2f} € mtl. (ca. {abschlag_eur_jahr:,.0f} € / Jahr)
                - **Fehlende Rentenpunkte (Beitragsverlust):** ~ {beitragsverlust_ep:.2f} EP
                - **Kumulierter Gesamtbedarf im Ruhestand:** {bedarf_summe:,.0f} €
                """.replace(",", "X").replace(".", ",").replace("X", "."))
        else:
            st.info("Simulation erreicht kein Rentenjahr.")

    with st.expander("📍 Dein Status Quo (Aktivphase Heute)"):
        st.markdown(f"**Deine aktuelle Ausgangssituation im Jahr {p['aktuelles_jahr']}:**")
        a_sq_sum = sum(p['ausgaben_input'].values())
        d_sq = p['aktuelles_netto'] - a_sq_sum
        
        st.write(f"- **Monatliches Nettoeinkommen:** {p['aktuelles_netto']:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
        st.write(f"- **Monatliche Ausgaben:** {a_sq_sum:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."))
        if d_sq > 0:
            st.success(f"Du hast einen monatlichen Liquiditäts-Überschuss von **{d_sq:,.2f} €**. Dieser kann zum Vermögensaufbau genutzt werden.".replace(",", "X").replace(".", ",").replace("X", "."))
        else:
            st.warning(f"Du hast eine monatliche Unterdeckung von **{abs(d_sq):,.2f} €**. Überprüfe deine Ausgaben.".replace(",", "X").replace(".", ",").replace("X", "."))

    with st.expander("🗓️ Die Timeline (Meilensteine)"):
        st.markdown("**Chronologischer Ablauf der wichtigsten Ereignisse.**")
        
        timeline_html = "<ul>"
        timeline_html += f"<li><b>{p['aktuelles_jahr']}:</b> Start der Simulation (Aktivphase)</li>"
        
        if p['atz_simulieren']:
            atz_mitte = p['atz_start'] + (p['atz_dauer'] / 2)
            timeline_html += f"<li><b>{int(p['atz_start'])}:</b> Beginn der Altersteilzeit (Aktivphase, volles Arbeiten bei reduziertem Gehalt)</li>"
            timeline_html += f"<li><b>{int(atz_mitte)}:</b> Wechsel in die passive Altersteilzeit (Freistellung)</li>"
            
        timeline_html += f"<li><b>{int(p['rentenbeginn'])}:</b> Renteneintritt</li>"
        
        # Weitere Einkünfte
        for e in p['einnahmen']:
            if e['start'] > p['aktuelles_jahr'] and e['start'] != p['rentenbeginn']:
                timeline_html += f"<li><b>{int(e['start'])}:</b> Start der Auszahlung: {e['name']}</li>"
                
        timeline_html += "</ul>"
        st.markdown(timeline_html, unsafe_allow_html=True)

    with st.expander("⚙️ Szenario-Parameter & Rechtliches"):
        st.markdown("**Alle getroffenen Annahmen und gesetzlichen Grundlagen.**")
        st.write("Die Simulation basiert auf den folgenden dynamischen Annahmen:")
        
        params_md = f"""
        * **Ausgaben-Inflation:** {p['inflation_rate']} % p.a.
        * **Rentenanpassung (GRV):** {p['rentenanpassung_rate']} % p.a.
        * **Gehaltsdynamik:** {p['gehalts_dynamik']} % p.a. (reale Steigerung)
        * **Kirchensteuer:** {p['kirchensteuer_satz'] * 100} %
        * **Krankenversicherung:** {8.0} % (zzgl. Pflegeversicherung nach Kinderzahl)
        
        **Rechtsstand:** 
        Die Steuerberechnung erfolgt iterativ pro Jahr. Es wird ein Näherungsverfahren für das zu versteuernde Einkommen (zvE) angewandt, das den Abzug von Vorsorgeaufwendungen (gemäß EStG 2024) simuliert. Die Altersteilzeit berücksichtigt die gesetzliche Mindestaufstockung in der Rentenversicherung auf 80 % (§ 3 AltTZG).
        """
        st.markdown(params_md)

    with st.expander("🧮 Beispielrechnung (Deep Dive Erstes Rentenjahr)"):
        st.markdown("**Vollständiges mathematisches Audit-Protokoll zur Nachvollziehbarkeit.**")
        st.info("Diese Rechnung zeigt transparent, wie die Engine aus deinen Bruttoeinnahmen im ersten Rentenjahr das exakte Netto ermittelt.")
        if erstes_rentenjahr is not None:
            j = int(erstes_rentenjahr['Jahr'])
            b = erstes_rentenjahr['Brutto']
            e = erstes_rentenjahr['EkSt']
            s = erstes_rentenjahr['Soli']
            k = erstes_rentenjahr['KiSt']
            sv = erstes_rentenjahr['Sozialabgaben']
            n = erstes_rentenjahr['Netto-Einkommen']
            zve = erstes_rentenjahr.get('_debug_zve', 0)
            st_b = erstes_rentenjahr.get('_debug_st_b', 0)
            
            # Brutto aufschlüsseln
            brutto_quellen = ""
            for einnahme in p['einnahmen']:
                if einnahme['start'] <= j <= einnahme.get('ende', 9999):
                    v = erstes_rentenjahr.get(einnahme['name'], 0)
                    if v > 0:
                        v_str = f"{v:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
                        brutto_quellen += f"  - {einnahme['name']} ({einnahme['typ']}): `{v_str}`\n"
            
            # Formatierte Strings
            f_b = f"{b:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
            f_sv = f"{sv:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
            f_st_b = f"{st_b:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
            f_zve = f"{zve:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
            f_e = f"{e:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
            f_s = f"{s:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
            f_k = f"{k:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
            f_n = f"{n:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
            f_tax = f"{e+s+k:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
            quote = f"{((b - n) / b * 100):.1f} %".replace(".", ",") if b > 0 else "0,0 %"
            
            calc_md = f"""
### Jahr {j} (Erstes volles Rentenjahr)

#### 1. Einnahmen & Sozialversicherung
**Summe aller Bruttoeinkünfte:** `{f_b}`
*Zusammensetzung:*
{brutto_quellen}

**Abzug Sozialversicherung (KV/PV):** `- {f_sv}`
*(Die SV wird auf pflichtige Rentenanteile nach § 249 SGB V berechnet)*

#### 2. Steuerliche Bemessungsgrundlage
Nicht jeder Euro Rente ist steuerpflichtig. Der Besteuerungsanteil der gesetzlichen Rente richtet sich nach dem Kohortenjahr des Rentenbeginns.
* **Steuerpflichtige Basis-Einnahmen:** `{f_st_b}`
* **Abzug Vorsorgeaufwendungen (Näherung):** `- {f_sv}`
* **Zu versteuerndes Einkommen (zvE):** `{f_zve}`

#### 3. Steuerberechnung (nach Grundtabelle)
Auf das ermittelte zvE wird der progressive Steuertarif (inkl. Grundfreibetrag) angewandt.
* **Einkommensteuer:** `{f_e}`
* **Solidaritätszuschlag:** `{f_s}`
* **Kirchensteuer:** `{f_k}`

#### 4. Endergebnis
*Brutto ({f_b}) minus SV ({f_sv}) minus Steuern ({f_tax})*
* **Netto-Einkommen:** **`{f_n}`**
* **Reale Steuer- & Abgabenquote:** `{quote}`
            """
            st.markdown(calc_md)
        else:
            st.warning("Kein Rentenjahr in der Simulation erreicht.")

    with st.expander("🧑‍💻 Für Auditoren & Entwickler: Quellcode der Engine"):
        st.markdown("**100% Transparenz.** Hier findest du den originalen Python-Code, der exakt in diesem Moment in der Engine (`logic/engine.py`) läuft. Du kannst ihn in einer beliebigen Python-Umgebung kopieren und unsere Mathematik verifizieren.")
        try:
            with open("logic/engine.py", "r", encoding="utf-8") as f:
                code_content = f.read()
            st.code(code_content, language="python")
        except Exception as e:
            st.error(f"Konnte Quellcode nicht laden: {e}")

    st.divider()
    
    # PDF Export Button
    col_pdf1, col_pdf2, col_pdf3 = st.columns([1, 2, 1])
    with col_pdf2:
            with st.popover("📄 Briefing exportieren (PDF)", use_container_width=True):
                # Dateiname-Vorschlag bearbeitbar machen
                default_fn = f"RenteOMat_Briefing_{p.get('nutzer_name', 'Nutzer')}"
                fn_input = st.text_input("Dateiname (.pdf)", value=default_fn)
                
                # Bilder erfassen
                with st.spinner("Erzeuge Diagramme..."):
                    chart_imgs = capture_charts_for_pdf(p, df_timeline)
                
                from logic.pdf_export import create_briefing_pdf
                pdf_bytes = create_briefing_pdf(p, df_timeline, chart_images=chart_imgs)
                st.download_button(
                    label="Download starten",
                    data=pdf_bytes,
                    file_name=f"{fn_input}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )

# --- FOOTER & DISCLAIMER ---
st.divider()
st.caption(f"{FULL_VERSION} | **DISCLAIMER:** Achtung, der Renten-Planer ist noch in der Entwicklung und kann fehlerhaft oder unvollständig sein. Alle Angaben müssen durch den/die Nutzer:in überprüft werden. Benutzung auf eigenes Risiko.")

if st.session_state.get("global_rerun"):
    st.session_state.global_rerun = False
    st.rerun()
