import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuration page (DOIT être la première commande Streamlit)
st.set_page_config(
    page_title="Bitcoin Dashboard",
    page_icon="₿",
    layout="wide"
)

# Fonction pour charger données
@st.cache_data(ttl=3600)  # Cache 1 heure
def load_bitcoin_data():
    """Charge données Bitcoin depuis CSV"""
    try:
        df = pd.read_csv('data/bitcoin_price.csv', index_col='date', parse_dates=True)
        return df
    except FileNotFoundError:
        st.error("❌ Fichier data/bitcoin_price.csv introuvable. Lance test_basics.py d'abord.")
        return None
    except Exception as e:
        st.error(f"❌ Erreur lecture données : {e}")
        return None

# --- MAIN DASHBOARD ---
st.title("₿ Bitcoin Price Dashboard")
st.markdown("---")

# Charge données
with st.spinner("Chargement des données..."):
    df = load_bitcoin_data()

# Affiche dashboard seulement si données existent
if df is not None and not df.empty:
    
    # === SECTION 1 : Métriques Clés ===
    st.header("📊 Métriques Clés")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculs
    current_price = df['price'].iloc[-1]
    avg_price = df['price'].mean()
    variation = ((current_price - avg_price) / avg_price) * 100
    min_price = df['price'].min()
    max_price = df['price'].max()
    
    # Affichage métriques
    with col1:
        st.metric(
            label="Prix Actuel",
            value=f"${current_price:,.2f}",
            delta=f"{variation:+.2f}% vs moyenne"
        )
    
    with col2:
        st.metric(
            label="Prix Moyen (30j)",
            value=f"${avg_price:,.2f}"
        )
    
    with col3:
        st.metric(
            label="Plus Bas (30j)",
            value=f"${min_price:,.2f}"
        )
    
    with col4:
        st.metric(
            label="Plus Haut (30j)",
            value=f"${max_price:,.2f}"
        )
    
    st.markdown("---")
    
    # === SECTION 2 : Graphique Prix ===
    st.header("📈 Évolution du Prix")
    
    # Créer graphique Plotly
    fig = px.line(
        df.reset_index(),
        x='date',
        y='price',
        title='Bitcoin Price (30 derniers jours)',
        labels={'date': 'Date', 'price': 'Prix (USD)'}
    )
    
    # Customisation graphique
    fig.update_layout(
        hovermode='x unified',
        xaxis_title="Date",
        yaxis_title="Prix (USD)",
        height=500
    )
    
    # Affiche graphique
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # === SECTION 3 : Données Brutes ===
    st.header("📋 Données Brutes")
    
    # Toggle pour afficher/cacher
    if st.checkbox("Afficher données complètes"):
        st.dataframe(df.sort_index(ascending=False), use_container_width=True)
    
    # Statistiques
    st.subheader("Statistiques")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Période**")
        st.write(f"- Début : {df.index[0].strftime('%Y-%m-%d')}")
        st.write(f"- Fin : {df.index[-1].strftime('%Y-%m-%d')}")
        st.write(f"- Nombre de jours : {len(df)}")
    
    with col2:
        st.write("**Prix**")
        st.write(f"- Écart-type : ${df['price'].std():,.2f}")
        st.write(f"- Médiane : ${df['price'].median():,.2f}")
        st.write(f"- Volatilité : {(df['price'].std() / df['price'].mean() * 100):.2f}%")

else:
    # Message si pas de données
    st.warning("⚠️ Aucune donnée disponible. Exécute `python test_basics.py` pour télécharger les données.")
    
    with st.expander("📖 Instructions"):
        st.code("""
# 1. Télécharge les données Bitcoin
python test_basics.py

# 2. Lance le dashboard
streamlit run dashboard/app.py
        """, language="bash")

# Footer
st.markdown("---")
st.caption(f"Dernière mise à jour : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")