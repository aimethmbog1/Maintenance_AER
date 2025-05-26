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

# 🖥️ TITRE DE L'APPLICATION
st.title("📊 ANALYSE DES DONNÉES DE PERFORMANCES AER")
st.markdown("""
Cette application interactive vous permet d'explorer les données de performances des centrales solaires rétro-cédées à l'AER.
""")

# 📥 CHARGEMENT DES DONNÉES
try:
    df = pd.read_csv("perfmg_day.csv")

    # ✅ Nettoyage des noms de colonnes
    df.columns = df.columns.str.strip().str.replace(' ', '_')
    df.columns = df.columns.str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')

    if "Heure_de_debut_stats" in df.columns:
        df["Heure_de_debut_stats"] = pd.to_datetime(df["Heure_de_debut_stats"], errors="coerce")
        df.dropna(subset=["Heure_de_debut_stats"], inplace=True)
    else:
        st.error("❌ La colonne 'Heure_de_debut_stats' est introuvable dans le fichier CSV.")
        st.stop()

    # Nettoyer et convertir Valeur en numérique (supprimer espaces, convertir en float)
    if "Valeur" in df.columns:
        df["Valeur"] = df["Valeur"].astype(str).str.strip()
        df["Valeur"] = pd.to_numeric(df["Valeur"], errors='coerce')

    st.markdown("### 🗃️ Aperçu des données complètes")
    st.dataframe(df.head(), use_container_width=True)

    if "Donnees_performance" in df.columns:
        # 🧭 PARAMÈTRES DE FILTRAGE DANS LA SIDEBAR
        st.sidebar.header("🎛️ Paramètres de filtrage")

        valeurs_uniques = df["Donnees_performance"].dropna().unique()
        selected_type = st.sidebar.selectbox("📌 Sélectionnez un type de performance :", options=valeurs_uniques)

        filtered_df = df[df["Donnees_performance"] == selected_type]

        # 📅 DEUX CALENDRIERS : DATE DE DÉBUT ET DATE DE FIN
        st.sidebar.header("📅 Plage de dates")
        min_date = filtered_df["Heure_de_debut_stats"].min().date()
        max_date = filtered_df["Heure_de_debut_stats"].max().date()

        start_date = st.sidebar.date_input(
            "Date de début",
            value=min_date,
            min_value=min_date,
            max_value=max_date
        )

        end_date = st.sidebar.date_input(
            "Date de fin",
            value=max_date,
            min_value=min_date,
            max_value=max_date
        )

        if start_date > end_date:
            st.sidebar.error("❌ La date de début doit être antérieure à la date de fin.")
            st.stop()

        # 🧹 Filtrage des données selon la période
        mask = (filtered_df["Heure_de_debut_stats"].dt.date >= start_date) & \
               (filtered_df["Heure_de_debut_stats"].dt.date <= end_date)
        filtered_df = filtered_df[mask]

        # 📤 EXPORT DES DONNÉES FILTRÉES dans la sidebar
        st.sidebar.header("💾 Exporter les données")
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.sidebar.download_button(
            label="📥 Télécharger les données filtrées en CSV",
            data=csv,
            file_name=f"donnees_{selected_type}.csv",
            mime="text/csv"
        )

        # ✅ Formatage lisible des dates pour affichage
        filtered_df["Date_affichee"] = filtered_df["Heure_de_debut_stats"].dt.strftime("%d/%m/%Y %H:%M")

        st.markdown(f"### 📂 Données filtrées : {selected_type}")
        st.dataframe(filtered_df[["Date_affichee", "Valeur"]], use_container_width=True)

        # 📊 STATISTIQUES DE PERFORMANCE
        if "Valeur" in filtered_df.columns and not filtered_df["Valeur"].isnull().all():
            st.markdown("### 📈 Statistiques de performance")
            stats = {
                "Moyenne": filtered_df["Valeur"].mean(),
                "Valeur maximale": filtered_df["Valeur"].max(),
                "Valeur minimale": filtered_df["Valeur"].min(),
                "Écart-type": filtered_df["Valeur"].std(),
                "Total": filtered_df["Valeur"].sum()
            }
            stats_df = pd.DataFrame.from_dict(stats, orient='index', columns=['Valeur'])
            stats_df = stats_df.style.format(precision=2)
            st.table(stats_df)
        else:
            st.warning("⚠️ Les données de 'Valeur' sont manquantes ou invalides.")

        # 📈 VISUALISATION AVEC PLOTLY
        if "Valeur" in filtered_df.columns and not filtered_df["Valeur"].isnull().all():
            fig = px.line(
                filtered_df,
                x="Heure_de_debut_stats",
                y="Valeur",
                title=f"📈 Évolution de {selected_type} dans le temps",
                labels={"Heure_de_debut_stats": "Date", "Valeur": "Valeur"},
                template="plotly_white"
            )

            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Valeur",
                xaxis=dict(tickformat="%d/%m/%Y")
            )

            st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("❌ La colonne 'Donnees_performance' est absente du fichier CSV.")
except FileNotFoundError:
    st.error("❌ Fichier CSV 'perfmg_day.csv' introuvable. Veuillez vérifier le chemin.")
except Exception as e:
    st.error(f"❌ Une erreur est survenue : {e}")
