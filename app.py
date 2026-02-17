import streamlit as st
import pickle
import pandas as pd
import requests
import gdown
import os
from concurrent.futures import ThreadPoolExecutor
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Movie Recommendation System",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── SPEED FIX 1: Reuse HTTP Session ──────────────────────────────────────────
@st.cache_resource
def get_session():
    session = requests.Session()
    retry = Retry(total=2, backoff_factor=0.1)
    adapter = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=20)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500&family=DM+Serif+Display:ital@0;1&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"] {
    background: #0a0a0f;
    color: #e8e4dc;
    font-family: 'DM Sans', sans-serif;
}

[data-testid="stAppViewContainer"] {
    background: radial-gradient(ellipse at 20% 0%, #1a0a2e 0%, #0a0a0f 50%),
                radial-gradient(ellipse at 80% 100%, #0d1a0a 0%, transparent 50%);
    min-height: 100vh;
}

#MainMenu, footer, header, [data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }

.block-container {
    max-width: 1400px !important;
    padding: 0 2rem 4rem !important;
}

.hero {
    text-align: center;
    padding: 4rem 0 3rem;
    position: relative;
}

.hero::before {
    content: '';
    position: absolute;
    top: 0; left: 50%;
    transform: translateX(-50%);
    width: 600px; height: 1px;
    background: linear-gradient(90deg, transparent, #c9a84c, transparent);
}

.hero-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: clamp(4rem, 10vw, 8rem);
    line-height: 0.9;
    letter-spacing: 0.02em;
    color: #f0ece4;
    margin-bottom: 0.5rem;
}

.hero-title span {
    color: #c9a84c;
    font-family: 'DM Serif Display', serif;
    font-style: italic;
}

.hero-subtitle {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.95rem;
    font-weight: 300;
    color: #8a8478;
    letter-spacing: 0.05em;
    margin-top: 1rem;
}

.search-label {
    font-size: 0.65rem;
    font-weight: 500;
    letter-spacing: 0.35em;
    color: #c9a84c;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
    display: block;
}

[data-testid="stSelectbox"] > label { display: none !important; }

[data-testid="stSelectbox"] > div > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(201,168,76,0.3) !important;
    border-radius: 3px !important;
    color: #e8e4dc !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 1rem !important;
    transition: border-color 0.3s !important;
}

[data-testid="stSelectbox"] > div > div:hover {
    border-color: rgba(201,168,76,0.7) !important;
}

[data-testid="stSelectbox"] > div > div:focus-within {
    border-color: #c9a84c !important;
    box-shadow: 0 0 0 2px rgba(201,168,76,0.1) !important;
}

[data-testid="stButton"] > button {
    width: 100% !important;
    background: linear-gradient(135deg, #c9a84c 0%, #e8c870 50%, #c9a84c 100%) !important;
    background-size: 200% auto !important;
    color: #0a0a0f !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.3em !important;
    text-transform: uppercase !important;
    border: none !important;
    border-radius: 3px !important;
    padding: 0.9rem 2rem !important;
    margin-top: 1rem !important;
    cursor: pointer !important;
    transition: all 0.4s ease !important;
}

[data-testid="stButton"] > button:hover {
    background-position: right center !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 30px rgba(201,168,76,0.3) !important;
}

.section-header {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}

.section-line {
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(201,168,76,0.5), transparent);
}

.section-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.5rem;
    letter-spacing: 0.15em;
    color: #c9a84c;
}

.section-count {
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    color: #8a8478;
    text-transform: uppercase;
}

.movie-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 4px;
    overflow: hidden;
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    position: relative;
}

.movie-card:hover {
    transform: translateY(-8px);
    border-color: rgba(201,168,76,0.4);
    box-shadow: 0 20px 60px rgba(0,0,0,0.5), 0 0 0 1px rgba(201,168,76,0.2);
}

.movie-card img {
    width: 100%;
    aspect-ratio: 2/3;
    object-fit: cover;
    display: block;
    transition: transform 0.4s ease;
}

.movie-card:hover img { transform: scale(1.03); }

.movie-card-overlay {
    position: absolute;
    bottom: 0; left: 0; right: 0;
    background: linear-gradient(transparent, rgba(0,0,0,0.95));
    padding: 2rem 0.75rem 0.75rem;
    opacity: 0;
    transition: opacity 0.3s ease;
}

.movie-card:hover .movie-card-overlay { opacity: 1; }

.movie-rank {
    position: absolute;
    top: 0.5rem; left: 0.5rem;
    background: #c9a84c;
    color: #0a0a0f;
    font-family: 'Bebas Neue', sans-serif;
    font-size: 0.9rem;
    width: 1.8rem; height: 1.8rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 2px;
    z-index: 2;
}

.movie-title-card {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.8rem;
    font-weight: 500;
    color: #f0ece4;
    line-height: 1.3;
    margin-top: 0.6rem;
    text-align: center;
    padding: 0 0.2rem;
}

[data-testid="stSpinner"] { color: #c9a84c !important; }

[data-testid="stAlert"] {
    background: rgba(201,168,76,0.1) !important;
    border: 1px solid rgba(201,168,76,0.3) !important;
    border-radius: 3px !important;
    color: #c9a84c !important;
}

.gold-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(201,168,76,0.4), transparent);
    margin: 3rem 0;
}

[data-testid="column"] { padding: 0 0.4rem !important; }

@keyframes fadeSlideUp {
    from { opacity: 0; transform: translateY(24px); }
    to   { opacity: 1; transform: translateY(0); }
}

.card-animate { animation: fadeSlideUp 0.5s ease forwards; }
.card-animate:nth-child(1)  { animation-delay: 0.05s; }
.card-animate:nth-child(2)  { animation-delay: 0.10s; }
.card-animate:nth-child(3)  { animation-delay: 0.15s; }
.card-animate:nth-child(4)  { animation-delay: 0.20s; }
.card-animate:nth-child(5)  { animation-delay: 0.25s; }
.card-animate:nth-child(6)  { animation-delay: 0.30s; }
.card-animate:nth-child(7)  { animation-delay: 0.35s; }
.card-animate:nth-child(8)  { animation-delay: 0.40s; }
.card-animate:nth-child(9)  { animation-delay: 0.45s; }
.card-animate:nth-child(10) { animation-delay: 0.50s; }

.footer {
    text-align: center;
    padding: 2rem 0;
    font-size: 0.7rem;
    letter-spacing: 0.2em;
    color: #3a3832;
    text-transform: uppercase;
}
</style>
""", unsafe_allow_html=True)


# ─── SPEED FIX 2: Cache Data Loading ──────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_data():
    # Download similarity.pkl from Google Drive if not exists
    if not os.path.exists('similarity.pkl'):
        with st.spinner('Loading model data for first time... Please wait...'):
            gdown.download(
                'https://drive.google.com/uc?id=1ZCGeFmaxDDKj-2hvrr1P20qJc_41Ym8r',
                'similarity.pkl',
                quiet=False
            )
    movies_df = pickle.load(open("movies.pkl", "rb"))
    similarity = pickle.load(open("similarity.pkl", "rb"))
    return movies_df, similarity


# ─── SPEED FIX 3: Cache Posters for 24hrs ─────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=86400)
def fetch_poster(movie_id):
    try:
        session = get_session()
        response = session.get(
            'https://api.themoviedb.org/3/movie/{}?api_key=740af96fbec8fce4528e25a90efb30ed'.format(movie_id),
            timeout=3  # SPEED FIX 4: Reduced timeout to 3s
        )
        data = response.json()
        if "poster_path" in data and data["poster_path"]:
            return "https://image.tmdb.org/t/p/w342/" + data["poster_path"]  # SPEED FIX 5: w342 faster than w500
    except:
        pass
    return "https://via.placeholder.com/342x513/1a1a2e/c9a84c?text=No+Poster"


# ─── SPEED FIX 6: Parallel Poster Fetching ────────────────────────────────────
def recommend(movie_name, movies_df, similarity):
    movie_index = movies_df[movies_df["title"] == movie_name].index[0]
    distance = similarity[movie_index]

    movies_list = sorted(
        list(enumerate(distance)),
        reverse=True,
        key=lambda x: x[1]
    )[1:11]

    names, ids = [], []
    for i in movies_list:
        ids.append(movies_df.iloc[i[0]]['id'])
        names.append(movies_df.iloc[i[0]].title)

    # Fetch all 10 posters at the same time
    with ThreadPoolExecutor(max_workers=10) as executor:
        posters = list(executor.map(fetch_poster, ids))

    return names, posters


# ─── SPEED FIX 7: Load Data Once at Startup ───────────────────────────────────
movies_df, similarity = load_data()

# ─── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-title">MOVIE <span>Recommendation</span> SYSTEM</div>
    <div class="hero-subtitle">Discover films crafted for your taste</div>
</div>
""", unsafe_allow_html=True)

# ─── Search ────────────────────────────────────────────────────────────────────
_, center, _ = st.columns([1, 2, 1])

with center:
    st.markdown('<span class="search-label">Choose your film</span>', unsafe_allow_html=True)
    selected_movie = st.selectbox(
        label="movie",
        options=["— Select a Movie —"] + list(movies_df["title"].values),
        label_visibility="collapsed"
    )
    recommend_btn = st.button("Discover Similar Films")

# ─── Results ───────────────────────────────────────────────────────────────────
if recommend_btn:
    if selected_movie == "— Select a Movie —":
        st.warning("Please select a movie to get recommendations.")
    else:
        with st.spinner("Curating your recommendations..."):
            names, posters = recommend(selected_movie, movies_df, similarity)

        st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="section-header">
            <div class="section-line"></div>
            <div>
                <div class="section-title">Because you liked {selected_movie}</div>
                <div class="section-count">10 curated recommendations</div>
            </div>
            <div class="section-line" style="background: linear-gradient(90deg, transparent, rgba(201,168,76,0.5));"></div>
        </div>
        """, unsafe_allow_html=True)

        # ── Row 1 ──
        cols = st.columns(5)
        for idx in range(5):
            with cols[idx]:
                st.markdown(f"""
                <div class="movie-card card-animate">
                    <div class="movie-rank">{idx + 1}</div>
                    <img src="{posters[idx]}" alt="{names[idx]}" loading="lazy"/>
                    <div class="movie-card-overlay">
                        <div style="color:#c9a84c;font-size:0.6rem;letter-spacing:0.2em">▶ VIEW</div>
                    </div>
                </div>
                <div class="movie-title-card">{names[idx]}</div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Row 2 ──
        cols2 = st.columns(5)
        for idx in range(5, 10):
            with cols2[idx - 5]:
                st.markdown(f"""
                <div class="movie-card card-animate">
                    <div class="movie-rank">{idx + 1}</div>
                    <img src="{posters[idx]}" alt="{names[idx]}" loading="lazy"/>
                    <div class="movie-card-overlay">
                        <div style="color:#c9a84c;font-size:0.6rem;letter-spacing:0.2em">▶ VIEW</div>
                    </div>
                </div>
                <div class="movie-title-card">{names[idx]}</div>
                """, unsafe_allow_html=True)

        st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)

# ─── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    Movie Recommendation System — Powered by TMDB & Machine Learning
</div>
""", unsafe_allow_html=True)