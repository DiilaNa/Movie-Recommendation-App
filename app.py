import streamlit as st
import pandas as pd
import requests
import pickle
import io
import os

# ------------------ Load Secrets ------------------
API_KEY = st.secrets["API_KEY"]
FILE_ID = st.secrets["FILE_ID"]

# ------------------ Load Google Drive .pkl ------------------
def load_pkl_from_gdrive(file_id):
    """
    Downloads a pickle file from Google Drive and returns the object.
    Handles large files with confirmation token.
    """
    session = requests.Session()
    URL = "https://docs.google.com/uc?export=download"

    # Initial request
    response = session.get(URL, params={"id": file_id}, stream=True)

    # Handle large file warning
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            response = session.get(URL, params={"id": file_id, "confirm": value}, stream=True)
            break

    content = response.content

    if content[:15].startswith(b'<html>'):
        raise ValueError("Google Drive returned HTML instead of pickle. Check FILE_ID or sharing settings.")

    return pickle.load(io.BytesIO(content))

# ------------------ Load files ------------------
# Load local small file
movies_dict = pickle.load(open(os.path.join("Assets", "movies.pkl"), "rb"))
movies = pd.DataFrame(movies_dict)

# Load large file from Google Drive
similarity = load_pkl_from_gdrive(FILE_ID)

# ------------------ Fetch movie poster from TMDB ------------------
def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
    response = requests.get(url)
    data = response.json()
    return "https://image.tmdb.org/t/p/w500" + data['poster_path']

# ------------------ Recommend movies ------------------
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

# ------------------ Streamlit App ------------------
st.title("🎬 Movie Recommender System")

selected_movie_name = st.selectbox(
    "Select a movie:",
    movies['title'].values
)

if st.button("Recommend"):
    names, posters = recommend(selected_movie_name)
    
    # Display in 5 columns
    cols = st.columns(5)
    for idx, col in enumerate(cols):
        with col:
            st.text(names[idx])
            st.image(posters[idx])
