from fpdf import FPDF
import pandas as pd
import datetime

def _L1(text):
    """Konvertiert Text in latin-1 für FPDF Standard-Fonts."""
    return text.encode('latin-1', 'replace').decode('latin-1')

class BriefingPDF(FPDF):
    def __init__(self, nutzer_name=""):
        super().__init__()
        self.nutzer_name = nutzer_name

    def header(self):
        # Dokument-Überschrift (Deutlich größer)
        self.set_font('helvetica', 'B', 18)
        self.set_text_color(41, 128, 185) # Blau
        
        titel = f"Rente-O-Mat | Persönliches Briefing für {self.nutzer_name}"
        self.cell(0, 10, _L1(titel), border=False, align='L')
        self.ln(15)

    def footer(self):
        # Seitennummerierung unten
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        
        # Generierungsdatum
        date_str = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        self.cell(0, 10, _L1(f'Generiert am {date_str} | Seite {self.page_no()}/{{nb}}'), align='C')


import io

def fmt_jahr_monat_de(val_float):
    jahr = int(val_float)
    monat = int(round((val_float - jahr) * 12)) + 1
    if monat > 12:
        jahr += 1
        monat -= 12
    monate_namen = [
        "Januar", "Februar", "März", "April", "Mai", "Juni",
        "Juli", "August", "September", "Oktober", "November", "Dezember"
    ]
    return f"{monate_namen[monat - 1]} {jahr}"

def create_briefing_pdf(params, df_timeline, chart_images=None):
    """
    Erstellt ein PDF-Dokument basierend auf den Simulationsdaten.
    chart_images: Dict mit PNG-Bytes { "sankey_aktiv": bytes, "sankey_rente": bytes, "trend_assets": bytes, ... }
    """
    name = params.get('nutzer_name', 'Nutzer')
    pdf = BriefingPDF(nutzer_name=name)
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Farben & Schriften definieren
    pdf.set_draw_color(200, 200, 200)
    pdf.set_fill_color(245, 245, 245)
    
    # Disclaimer
    pdf.set_font("helvetica", "I", 7)
    pdf.set_text_color(150, 150, 150)
    disclaimer = "DISCLAIMER: Achtung, der Renten-Planer ist noch in der Entwicklung und kann fehlerhaft oder unvollständig sein. Alle Angaben müssen durch den/die Nutzer:in überprüft werden. Benutzung auf eigenes Risiko."
    pdf.multi_cell(0, 4, _L1(disclaimer))
    pdf.ln(5)

    # Relevante Daten extrahieren
    renten_jahre = df_timeline[df_timeline["Phase"] == "Rente"]
    erstes_rentenjahr = renten_jahre.iloc[0] if not renten_jahre.empty else None
    
    renten_jahr = int(params['rentenbeginn'])
    renten_alter = renten_jahr - params['geburtsjahr']
    
    letztes_jahr = df_timeline.iloc[-1]
    end_vermoegen = letztes_jahr.get("ASSET_VAL_Cash-Reserven (kum.)", 0)
    for col in df_timeline.columns:
        if col.startswith("ASSET_VAL_") and col != "ASSET_VAL_Cash-Reserven (kum.)":
            end_vermoegen += letztes_jahr.get(col, 0)
    
    # 1. Zusammenfassung
    pdf.set_font("helvetica", "B", 13)
    pdf.set_text_color(41, 128, 185)
    pdf.cell(0, 10, _L1("1. Zusammenfassung"), ln=True)
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    
    pdf.cell(0, 6, _L1(f"Gewählter Rentenbeginn: {renten_jahr} (Alter {renten_alter} Jahre)"), ln=True)
    pdf.cell(0, 6, _L1(f"Projiziertes Endvermögen (Alter 95): {end_vermoegen:,.0f} Euro").replace(",", "X").replace(".", ",").replace("X", "."), ln=True)
    
    if erstes_rentenjahr is not None:
        rentenlücke = erstes_rentenjahr["Bedarf"] - erstes_rentenjahr["Netto-Einkommen"]
        abschlag_eur = erstes_rentenjahr.get("Rentenabschlag", 0) * 12
        bedarf_summe = renten_jahre['Bedarf'].sum() * 12
        
        pdf.cell(0, 6, _L1(f"Finanzlücke 1. Rentenjahr: {rentenlücke:,.0f} Euro monatlich").replace(",", "X").replace(".", ",").replace("X", "."), ln=True)
        pdf.cell(0, 6, _L1(f"Kumulierter Gesamtbedarf (Ruhestand): {bedarf_summe:,.0f} Euro").replace(",", "X").replace(".", ",").replace("X", "."), ln=True)
        pdf.cell(0, 6, _L1(f"Rentenabschlag: ca. {abschlag_eur:,.0f} Euro / Jahr").replace(",", "X").replace(".", ",").replace("X", "."), ln=True)
    
    pdf.ln(5)
    
    # 2. Status Quo
    pdf.set_font("helvetica", "B", 13)
    pdf.set_text_color(41, 128, 185)
    pdf.cell(0, 10, _L1("2. Status Quo (Aktivphase)"), ln=True)
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    
    a_sq_sum = sum(params['ausgaben_input'].values())
    d_sq = params['aktuelles_netto'] - a_sq_sum
    
    pdf.cell(0, 6, _L1(f"Monatliches Nettoeinkommen: {params['aktuelles_netto']:,.2f} Euro").replace(",", "X").replace(".", ",").replace("X", "."), ln=True)
    pdf.cell(0, 6, _L1(f"Monatliche Ausgaben: {a_sq_sum:,.2f} Euro").replace(",", "X").replace(".", ",").replace("X", "."), ln=True)
    
    # Category breakdown for Status Quo
    pdf.ln(2)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 6, _L1("Monatliche Ausgaben nach Kategorien:"), ln=True)
    pdf.set_font("helvetica", "", 10)
    
    id_to_name = {kat["id"]: kat["name"] for kat in params.get("haushaltsbuch_kategorien", [])}
    # Group sum calculation
    group_sums = {}
    for kat in params.get("haushaltsbuch_kategorien", []):
        if not kat.get("is_group"):
            c_val = params['ausgaben_input'].get(kat["id"], 0.0)
            if c_val > 0:
                p_id = kat.get("parent_id")
                if p_id:
                    group_sums[p_id] = group_sums.get(p_id, 0.0) + c_val
                else:
                    group_sums[kat["id"]] = group_sums.get(kat["id"], 0.0) + c_val
                    
    for g_id, g_val in group_sums.items():
        g_name = id_to_name.get(g_id, g_id)
        subs = [kat for kat in params.get("haushaltsbuch_kategorien", []) if kat.get("parent_id") == g_id and params['ausgaben_input'].get(kat["id"], 0.0) > 0]
        if subs:
            pdf.cell(0, 5, _L1(f"- {g_name}: {g_val:,.2f} EUR").replace(",", "X").replace(".", ",").replace("X", "."), ln=True)
            pdf.set_font("helvetica", "I", 9)
            for s in subs:
                s_val = params['ausgaben_input'].get(s["id"], 0.0)
                pdf.cell(0, 4, _L1(f"   * {s['name']}: {s_val:,.2f} EUR").replace(",", "X").replace(".", ",").replace("X", "."), ln=True)
            pdf.set_font("helvetica", "", 10)
        else:
            pdf.cell(0, 5, _L1(f"- {g_name}: {g_val:,.2f} EUR").replace(",", "X").replace(".", ",").replace("X", "."), ln=True)

    # Sankey Aktivbild
    if chart_images and "sankey_aktiv" in chart_images:
        pdf.ln(3)
        img_data = io.BytesIO(chart_images["sankey_aktiv"])
        pdf.image(img_data, x=10, y=pdf.get_y() + 2, w=180)
        pdf.set_y(pdf.get_y() + 95) # Platz für das Bild lassen (Annahme: w=180 -> h~90)
    
    pdf.ln(10)

    # 3. Timeline
    pdf.add_page()
    pdf.set_font("helvetica", "B", 13)
    pdf.set_text_color(41, 128, 185)
    pdf.cell(0, 10, _L1("3. Chronologische Timeline (Meilensteine)"), ln=True)
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    
    timeline_items = []
    timeline_items.append((float(params['aktuelles_jahr']), f"Start der Simulation: {params['aktuelles_jahr']} (Aktivphase)"))
    
    if params.get('atz_simulieren'):
        atz_mitte = params['atz_start'] + (params['atz_dauer'] / 2)
        timeline_items.append((float(params['atz_start']), f"Beginn der Altersteilzeit (ATZ-Aktiv): {fmt_jahr_monat_de(params['atz_start'])}"))
        timeline_items.append((float(atz_mitte), f"Wechsel in die Freistellungsphase (ATZ-Passiv): {fmt_jahr_monat_de(atz_mitte)}"))
        
    timeline_items.append((float(params['rentenbeginn']), f"Renteneintritt: {fmt_jahr_monat_de(params['rentenbeginn'])}"))
    
    for e in params.get('einnahmen', []):
        if e['start'] > params['aktuelles_jahr']:
            timeline_items.append((float(e['start']), f"Start der Auszahlung von {e['name']}: {fmt_jahr_monat_de(e['start'])} ({e['betrag']:,.2f} EUR/mtl.)"))
            
    for ea in params.get('einmalige_ausgaben', []):
        t_event = float(ea['jahr']) + (int(ea.get('monat', 1)) - 1) / 12.0
        timeline_items.append((t_event, f"Einmalige Sonderausgabe '{ea['name']}': {fmt_jahr_monat_de(t_event)} ({ea['betrag']:,.2f} EUR)"))
        
    timeline_items.sort(key=lambda x: x[0])
    
    for _, item_text in timeline_items:
        pdf.cell(0, 6, _L1(f"- {item_text}").replace(",", "X").replace(".", ",").replace("X", "."), ln=True)
        
    pdf.ln(5)

    # 4. Deep Dive
    pdf.set_font("helvetica", "B", 13)
    pdf.set_text_color(41, 128, 185)
    pdf.cell(0, 10, _L1("4. Deep Dive: Erstes volles Rentenjahr"), ln=True)
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    
    if erstes_rentenjahr is not None:
        j = int(erstes_rentenjahr['Jahr'])
        b = erstes_rentenjahr['Brutto']
        sv = erstes_rentenjahr['Sozialabgaben']
        n = erstes_rentenjahr['Netto-Einkommen']
        ek = erstes_rentenjahr['EkSt']
        sol = erstes_rentenjahr['Soli']
        kis = erstes_rentenjahr['KiSt']
        zve = erstes_rentenjahr.get('_debug_zve', 0)
        st_b = erstes_rentenjahr.get('_debug_st_b', 0)
        
        pdf.cell(0, 6, _L1(f"Berechnungsjahr: {j} (Ruhestand)"), ln=True)
        pdf.cell(0, 6, _L1(f"- Summe aller Bruttoeinkünfte: {b:,.2f} EUR").replace(",", "X").replace(".", ",").replace("X", "."), ln=True)
        
        # Einnahmen auflisten
        for einnahme in params.get('einnahmen', []):
            if einnahme['start'] <= j <= einnahme.get('ende', 9999):
                v = erstes_rentenjahr.get(einnahme['name'], 0)
                if v > 0:
                    pdf.cell(0, 5, _L1(f"   * {einnahme['name']} ({einnahme['typ']}): {v:,.2f} EUR").replace(",", "X").replace(".", ",").replace("X", "."), ln=True)
                    
        pdf.cell(0, 6, _L1(f"- Abzug Sozialversicherungen (KV/PV): - {sv:,.2f} EUR").replace(",", "X").replace(".", ",").replace("X", "."), ln=True)
        pdf.cell(0, 6, _L1(f"- Projiziertes zvE (steuerliche Basis): {zve:,.2f} EUR").replace(",", "X").replace(".", ",").replace("X", "."), ln=True)
        pdf.cell(0, 6, _L1(f"- Einkommensteuer (progressive Tabelle): {ek:,.2f} EUR").replace(",", "X").replace(".", ",").replace("X", "."), ln=True)
        if sol > 0:
            pdf.cell(0, 6, _L1(f"- Solidaritätszuschlag: {sol:,.2f} EUR").replace(",", "X").replace(".", ",").replace("X", "."), ln=True)
        if kis > 0:
            pdf.cell(0, 6, _L1(f"- Kirchensteuer: {kis:,.2f} EUR").replace(",", "X").replace(".", ",").replace("X", "."), ln=True)
            
        quote = f"{((b - n) / b * 100):.1f} %".replace(".", ",") if b > 0 else "0,0 %"
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(0, 6, _L1(f"- Netto-Einkommen: {n:,.2f} EUR (Abgabenquote: {quote})").replace(",", "X").replace(".", ",").replace("X", "."), ln=True)
        pdf.set_font("helvetica", "", 10)
        
        # Sankey Rentenbild
        if chart_images and "sankey_rente" in chart_images:
            pdf.ln(3)
            img_data = io.BytesIO(chart_images["sankey_rente"])
            pdf.image(img_data, x=10, y=pdf.get_y() + 2, w=180)
            pdf.set_y(pdf.get_y() + 95)
            
    pdf.ln(5)

    # 5. Szenario-Parameter & Rechtliches
    pdf.add_page()
    pdf.set_font("helvetica", "B", 13)
    pdf.set_text_color(41, 128, 185)
    pdf.cell(0, 10, _L1("5. Szenario-Parameter & Rechtliches"), ln=True)
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    
    pdf.cell(0, 6, _L1(f"- Ausgaben-Inflation: {params['inflation_rate']} % p.a."), ln=True)
    pdf.cell(0, 6, _L1(f"- Rentenanpassung (GRV): {params['rentenanpassung_rate']} % p.a."), ln=True)
    pdf.cell(0, 6, _L1(f"- Gehaltsdynamik (reale Steigerung): {params['gehalts_dynamik']} % p.a."), ln=True)
    pdf.cell(0, 6, _L1(f"- Kirchensteuersatz: {params['kirchensteuer_satz'] * 100} %"), ln=True)
    
    pdf.ln(2)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 6, _L1("Rechtsstand & Modellierung:"), ln=True)
    pdf.set_font("helvetica", "", 9)
    rechtsstand_text = (
        "Die Steuerberechnung erfolgt iterativ pro Simulationsschritt. Es wird ein Naeherungsverfahren "
        "fuer das zu versteuernde Einkommen (zvE) angewandt, das den Abzug von Vorsorgeaufwendungen "
        "(gemaess EStG 2024) simuliert. Die Altersteilzeit beruecksichtigt die gesetzliche "
        "Mindestaufstockung in der Rentenversicherung auf 80% (Paragraph 3 AltTZG)."
    )
    pdf.multi_cell(0, 4, _L1(rechtsstand_text))
    pdf.ln(5)

    # 6. Zeitliche Entwicklung (Trends)
    if chart_images and ("trend_assets" in chart_images or "trend_income" in chart_images):
        pdf.set_font("helvetica", "B", 13)
        pdf.set_text_color(41, 128, 185)
        pdf.cell(0, 10, _L1("6. Zeitliche Entwicklung (Trends)"), ln=True)
        
        if "trend_assets" in chart_images:
            pdf.set_font("helvetica", "B", 11)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 8, _L1("Vermoegensentwicklung"), ln=True)
            img_data = io.BytesIO(chart_images["trend_assets"])
            pdf.image(img_data, x=10, y=pdf.get_y(), w=180)
            pdf.set_y(pdf.get_y() + 100)
            
        if "trend_income" in chart_images:
            pdf.ln(5)
            pdf.set_font("helvetica", "B", 11)
            pdf.cell(0, 8, _L1("Einnahmen und Ausgaben"), ln=True)
            img_data = io.BytesIO(chart_images["trend_income"])
            pdf.image(img_data, x=10, y=pdf.get_y(), w=180)
            pdf.set_y(pdf.get_y() + 100)

    # Fix: TypeError 'str' and 'int' Bug in PDF Generation
    # We do a final cleaning to make sure no invalid checks remain.
    # Exclude columns list:
    exclude = ["Jahr", "Phase", "Brutto", "EkSt", "Soli", "KiSt", "Steuern", "Steuersatz", "Sozialabgaben", "Netto-Einkommen", "Bedarf", "Überschuss/Defizit", "Rentenabschlag", "Beitragsverlust", "Steuerpflichtiger_Rentenanteil", "Netto-GRV", "Kapitalzuwachs_Sonder", "Gesetzliche Rente (Potenzial)", "Label", "Jahr_Float", "start_t", "end_t", "bar_width"]
    if erstes_rentenjahr is not None:
        res = erstes_rentenjahr.to_dict()
        income_sources = {k: v for k, v in res.items() if k not in exclude and not k.startswith("EXP_") and not k.startswith("ASSET_VAL_") and not k.startswith("_debug") and isinstance(v, (int, float)) and v > 0}

    # Output als Bytes
    return bytes(pdf.output())
