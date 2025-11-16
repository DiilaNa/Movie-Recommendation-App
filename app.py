import streamlit as st
import pickle
import pandas as pd
import requests
import os
import gdown  # for large Google Drive files

# ------------------- Load environment variables -------------------
API_KEY = st.secrets["API_KEY"]
FILE_ID = st.secrets["FILE_ID"]  # Google Drive file ID for similarity.pkl

if not API_KEY:
    raise ValueError("API_KEY not found. Please check your .env file or Streamlit secrets.")
if not FILE_ID:
    raise ValueError("FILE_ID not found. Please check your .env file or Streamlit secrets.")

# ------------------- Function to load Google Drive pickle -------------------
def load_pkl_from_gdrive(file_id, output_name="similarity.pkl"):
    url = f"https://drive.google.com/uc?id={file_id}"
    if not os.path.exists(output_name):
        st.info("Downloading similarity file from Google Drive...")
        gdown.download(url, output_name, quiet=False)
    with open(output_name, "rb") as f:
        data = pickle.load(f)
    return data

# ------------------- Load Data -------------------
# Movies dictionary from local file
movies_dict = pickle.load(open(os.path.join("Assets", "movies.pkl"), "rb"))
movies = pd.DataFrame(movies_dict)

# Similarity matrix from Google Drive
similarity = load_pkl_from_gdrive(FILE_ID)

# ------------------- Helper Functions -------------------
def fetch_poster(movie_id):
    response = requests.get(
        f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US'
    )
    data = response.json()
    return "https://image.tmdb.org/t/p/w500" + data['poster_path']

def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies = []
    recommended_movies_posters = []
    for i in movies_list:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movies.append(movies.iloc[i[0]].title)
        recommended_movies_posters.append(fetch_poster(movie_id))
    return recommended_movies, recommended_movies_posters

# ------------------- Streamlit App -------------------
st.title('🎬 Movie Recommender System')

selected_movie_name = st.selectbox(
    "Select a movie:",
    movies['title'].values
)

if st.button("Recommend", type="primary"):
    names, posters = recommend(selected_movie_name)
    col1, col2, col3, col4, col5 = st.columns(5)
    for idx, col in enumerate([col1, col2, col3, col4, col5]):
        with col:
            st.text(names[idx])
            st.image(posters[idx])
