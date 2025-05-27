# 📚 IMPORTER LES BIBLIOTHÈQUES
import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import io

# 📄 CONFIGURATION DE LA PAGE
st.set_page_config(
    page_title="ANALYSE DES DONNÉES DE PERFORMANCES AER",
    layout="wide",
    page_icon="📊"
)

# 🖥️ TITRE ET DESCRIPTION
st.title("📊 ANALYSE DES DONNÉES DE PERFORMANCES AER")
st.markdown("""
Cette application interactive vous permet d'explorer les données de performances des centrales solaires rétro-cédées à l'AER.
""")

# === Initialisation session_state pour validation formulaire ===
if "infos_valides" not in st.session_state:
    st.session_state.infos_valides = False

# 📝 FORMULAIRE D’INFOS SITE & AGENT
st.markdown("### 🏗️ Informations sur la centrale et l'opérateur")
with st.form("infos_site"):
    col1, col2 = st.columns(2)
    with col1:
        nom_site = st.text_input("🏭 Nom du site", placeholder="Ex : Centrale PV de Ndiob")
        capacite_site = st.text_input("🔋 Capacité installée (kWc)", placeholder="Ex : 33")
        date_analyse = st.date_input("📅 Date de l’analyse")
    with col2:
        nom_agent = st.text_input("👤 Nom de l’agent", placeholder="Ex : Aissatou Diop")
        fonction_agent = st.text_input("🏢 Structure / Fonction", placeholder="Ex : AER - Superviseur technique")

    submit_infos = st.form_submit_button("✅ Enregistrer les informations")

    if submit_infos:
        # Vérifier que tous les champs sont remplis
        if not all([nom_site.strip(), capacite_site.strip(), nom_agent.strip(), fonction_agent.strip()]):
            st.error("⚠️ Merci de remplir **tous** les champs avant de continuer.")
            st.session_state.infos_valides = False
        else:
            st.success("✅ Informations enregistrées avec succès.")
            st.session_state.infos_valides = True
            st.info(f"""
            **📌 Fiche de site :**
            - Nom du site : `{nom_site}`
            - Capacité : `{capacite_site} kWc`
            - Date d’analyse : `{date_analyse.strftime('%d/%m/%Y')}`

            **👤 Opérateur :**
            - Nom : `{nom_agent}`
            - Structure / Fonction : `{fonction_agent}`
            """)

# === BLOQUER LA SUITE SI FORMULAIRE NON VALIDÉ ===
if not st.session_state.infos_valides:
    st.warning("⚠️ Merci de remplir et valider les informations du site et de l’agent avant de charger un fichier CSV.")
    st.stop()

# 📥 Upload CSV
st.sidebar.header("📤 Charger un fichier CSV")
uploaded_file = st.sidebar.file_uploader("Sélectionnez un fichier de données", type=["csv"])

if uploaded_file is not None:
    @st.cache_data
    def load_data(file):
        df = pd.read_csv(file)
        df.columns = df.columns.str.strip().str.replace(' ', '_')
        df.columns = df.columns.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
        return df

    try:
        df = load_data(uploaded_file)

        # Colonnes requises
        colonnes_attendues = {"Heure_de_debut_stats", "Donnees_performance", "Valeur"}
        colonnes_manquantes = colonnes_attendues - set(df.columns)
        if colonnes_manquantes:
            st.error(f"❌ Colonnes manquantes dans le CSV : {', '.join(colonnes_manquantes)}")
            st.stop()

        # Conversion date & nettoyage
        df["Heure_de_debut_stats"] = pd.to_datetime(df["Heure_de_debut_stats"], errors="coerce")
        df.dropna(subset=["Heure_de_debut_stats"], inplace=True)
        df["Valeur"] = pd.to_numeric(df["Valeur"].astype(str).str.strip(), errors="coerce")

        # Aperçu
        st.markdown("### 🗃️ Aperçu des données complètes")
        st.dataframe(df.head(), use_container_width=True)

        # Filtrage performance
        st.sidebar.header("🎛️ Paramètres de filtrage")
        valeurs_uniques = df["Donnees_performance"].dropna().unique()
        selected_type = st.sidebar.selectbox("📌 Sélectionnez un type de performance :", options=valeurs_uniques)
        filtered_df = df[df["Donnees_performance"] == selected_type]

        # Plage de dates
        st.sidebar.header("📅 Plage de dates")
        min_date = filtered_df["Heure_de_debut_stats"].min().date()
        max_date = filtered_df["Heure_de_debut_stats"].max().date()

        if min_date == max_date:
            st.sidebar.info(f"📅 Une seule date disponible : {min_date}")
            start_date = end_date = min_date
        else:
            date_range = st.sidebar.slider(
                "📅 Sélectionnez la plage de dates :",
                min_value=min_date,
                max_value=max_date,
                value=(min_date, max_date)
            )
            start_date, end_date = date_range

        # Thème graphique
        theme = st.sidebar.radio("🎨 Thème du graphique", ["Blanc", "Sombre"])
        plotly_template = "plotly_white" if theme == "Blanc" else "plotly_dark"

        # Filtrer par date
        mask = (filtered_df["Heure_de_debut_stats"].dt.date >= start_date) & \
               (filtered_df["Heure_de_debut_stats"].dt.date <= end_date)
        filtered_df = filtered_df[mask]

        # Ajouter infos site & agent au dataframe (colonnes fixes)
        meta_data = {
            "Nom_du_site": nom_site,
            "Capacite_kWc": capacite_site,
            "Date_analyse": date_analyse.strftime("%Y-%m-%d"),
            "Nom_agent": nom_agent,
            "Fonction_agent": fonction_agent
        }
        for key, val in meta_data.items():
            filtered_df[key] = val

        # Export CSV complet (avec métadonnées)
        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.sidebar.header("💾 Exporter les données")
        st.sidebar.download_button(
            label="📥 Télécharger les données filtrées (CSV + métadonnées)",
            data=csv_data,
            file_name=f"donnees_{selected_type}.csv",
            mime="text/csv"
        )

        # Affichage des données filtrées
        filtered_df["Date_affichee"] = filtered_df["Heure_de_debut_stats"].dt.strftime("%d/%m/%Y %H:%M")
        st.markdown(f"### 📂 Données filtrées : {selected_type}")
        st.dataframe(filtered_df[["Date_affichee", "Valeur"]], use_container_width=True)

        # Statistiques
        if not filtered_df["Valeur"].isnull().all():
            st.markdown("### 📈 Statistiques de performance")
            stats = {
                "Moyenne": filtered_df["Valeur"].mean(),
                "Valeur maximale": filtered_df["Valeur"].max(),
                "Valeur minimale": filtered_df["Valeur"].min(),
                "Écart-type": filtered_df["Valeur"].std(),
                "Total": filtered_df["Valeur"].sum()
            }
            stats_df = pd.DataFrame.from_dict(stats, orient='index', columns=['Valeur'])
            stats_styled = stats_df.style.format(precision=2)
            st.table(stats_styled)

            # Export stats CSV
            csv_stats = stats_df.to_csv().encode('utf-8')
            st.sidebar.download_button(
                label="📥 Télécharger les statistiques (CSV)",
                data=csv_stats,
                file_name=f"stats_{selected_type}.csv",
                mime="text/csv"
            )

            # Résumé texte
            st.markdown("### 🧠 Résumé automatique")
            st.info(f"""
            - Nombre de points : {len(filtered_df)}
            - Moyenne : {stats['Moyenne']:.2f}
            - Max : {stats['Valeur maximale']:.2f}
            - Min : {stats['Valeur minimale']:.2f}
            - Somme totale : {stats['Total']:.2f}
            """)

            # Graphique
            fig = px.line(
                filtered_df,
                x="Heure_de_debut_stats",
                y="Valeur",
                title=f"📈 Évolution de {selected_type} dans le temps",
                labels={"Heure_de_debut_stats": "Date", "Valeur": "Valeur"},
                template=plotly_template
            )
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Valeur",
                xaxis=dict(tickformat="%d/%m/%Y")
            )
            st.plotly_chart(fig, use_container_width=True)

            # === Génération PDF résumé ===
            def generate_pdf():
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, "Rapport d'analyse des performances AER", ln=True, align='C')
                pdf.ln(10)

                pdf.set_font("Arial", '', 12)
                pdf.cell(0, 8, f"Site: {nom_site}", ln=True)
                pdf.cell(0, 8, f"Capacité installée: {capacite_site} kWc", ln=True)
                pdf.cell(0, 8, f"Date d'analyse: {date_analyse.strftime('%d/%m/%Y')}", ln=True)
                pdf.cell(0, 8, f"Agent: {nom_agent} ({fonction_agent})", ln=True)
                pdf.ln(10)

                pdf.set_font("Arial", 'B', 14)
                pdf.cell(0, 10, f"Performance: {selected_type}", ln=True)
                pdf.ln(5)

                pdf.set_font("Arial", '', 12)
                for key, val in stats.items():
                    pdf.cell(0, 8, f"{key} : {val:.2f}", ln=True)

                pdf.ln(10)
                pdf.set_font("Arial", 'I', 10)
                pdf.cell(0, 10, "Rapport généré automatiquement via l'application AER", ln=True, align='C')

                pdf_output = io.BytesIO()
                pdf.output(pdf_output)
                pdf_output.seek(0)
                return pdf_output

            st.sidebar.header("📄 Exporter le rapport")
            pdf_data = generate_pdf()
            st.sidebar.download_button(
                label="📥 Télécharger le rapport PDF",
                data=pdf_data,
                file_name=f"rapport_{selected_type}.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("⚠️ Les données de 'Valeur' sont manquantes ou invalides.")
    except Exception as e:
        st.error(f"❌ Une erreur est survenue : {e}")
else:
    st.warning("⚠️ Veuillez charger un fichier CSV pour commencer.")
