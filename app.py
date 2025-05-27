# 📚 IMPORTER LES BIBLIOTHÈQUES
import streamlit as st
import pandas as pd
import plotly.express as px

# 📄 CONFIGURATION DE LA PAGE
st.set_page_config(
    page_title="ANALYSE DES DONNÉES DE PERFORMANCES AER",
    layout="wide",
    page_icon="📊"
)

st.title("📊 ANALYSE DES DONNÉES DE PERFORMANCES AER")
st.markdown("""
Cette application interactive vous permet d'explorer les données de performances des centrales solaires rétro-cédées à l'AER.
""")

# 🔄 FONCTION DE CHARGEMENT DES DONNÉES AVEC CACHE
@st.cache_data
def load_data():
    df = pd.read_csv("perfmg_day.csv")
    df.columns = df.columns.str.strip().str.replace(' ', '_')
    df.columns = df.columns.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
    return df

try:
    df = load_data()

    # ✅ Vérification des colonnes obligatoires
    colonnes_attendues = {"Heure_de_debut_stats", "Donnees_performance", "Valeur"}
    colonnes_manquantes = colonnes_attendues - set(df.columns)
    if colonnes_manquantes:
        st.error(f"❌ Les colonnes suivantes sont manquantes : {', '.join(colonnes_manquantes)}")
        st.stop()

    # 🕒 Conversion de la colonne date
    df["Heure_de_debut_stats"] = pd.to_datetime(df["Heure_de_debut_stats"], errors="coerce")
    df.dropna(subset=["Heure_de_debut_stats"], inplace=True)

    # 🔢 Nettoyage des valeurs numériques
    df["Valeur"] = pd.to_numeric(df["Valeur"].astype(str).str.strip(), errors="coerce")

    # 🗃️ Aperçu des données
    st.markdown("### 🗃️ Aperçu des données complètes")
    st.dataframe(df.head(), use_container_width=True)

    # 🎛️ SIDEBAR : FILTRES
    st.sidebar.header("🎛️ Paramètres de filtrage")
    valeurs_uniques = df["Donnees_performance"].dropna().unique()
    selected_type = st.sidebar.selectbox("📌 Sélectionnez un type de performance :", options=valeurs_uniques)
    filtered_df = df[df["Donnees_performance"] == selected_type]

    # 📅 Gestion de la plage de dates
    st.sidebar.header("📅 Plage de dates")
    min_date = filtered_df["Heure_de_debut_stats"].min().date()
    max_date = filtered_df["Heure_de_debut_stats"].max().date()

    if min_date == max_date:
        st.sidebar.info(f"📅 Une seule date disponible dans les données : {min_date}")
        start_date = end_date = min_date
    else:
        date_range = st.sidebar.slider(
            "📅 Sélectionnez la plage de dates :",
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date)
        )
        start_date, end_date = date_range

    # 🎨 Thème du graphique
    theme = st.sidebar.radio("🎨 Thème du graphique", ["Blanc", "Sombre"])
    plotly_template = "plotly_white" if theme == "Blanc" else "plotly_dark"

    # 🧹 Filtrage selon la date
    mask = (filtered_df["Heure_de_debut_stats"].dt.date >= start_date) & \
           (filtered_df["Heure_de_debut_stats"].dt.date <= end_date)
    filtered_df = filtered_df[mask]

    # 📤 Export CSV des données filtrées
    st.sidebar.header("💾 Exporter les données")
    csv_data = filtered_df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="📥 Télécharger les données filtrées en CSV",
        data=csv_data,
        file_name=f"donnees_{selected_type}.csv",
        mime="text/csv"
    )

    # 📅 Affichage de la date
    filtered_df["Date_affichee"] = filtered_df["Heure_de_debut_stats"].dt.strftime("%d/%m/%Y %H:%M")
    st.markdown(f"### 📂 Données filtrées : {selected_type}")
    st.dataframe(filtered_df[["Date_affichee", "Valeur"]], use_container_width=True)

    # 📊 Statistiques
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

        # Export des stats
        csv_stats = stats_df.to_csv().encode('utf-8')
        st.sidebar.download_button(
            label="📥 Télécharger les statistiques",
            data=csv_stats,
            file_name=f"stats_{selected_type}.csv",
            mime="text/csv"
        )

        # 🧠 Résumé automatique
        st.markdown("### 🧠 Résumé automatique")
        st.info(f"""
        - Nombre de points : {len(filtered_df)}
        - Moyenne : {stats['Moyenne']:.2f}
        - Max : {stats['Valeur maximale']:.2f}
        - Min : {stats['Valeur minimale']:.2f}
        - Somme totale : {stats['Total']:.2f}
        """)

        # 📈 Graphique Plotly
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
    else:
        st.warning("⚠️ Les données de 'Valeur' sont manquantes ou invalides.")
except FileNotFoundError:
    st.error("❌ Fichier CSV 'perfmg_day.csv' introuvable. Veuillez vérifier le chemin.")
except Exception as e:
    st.error(f"❌ Une erreur est survenue : {e}")
