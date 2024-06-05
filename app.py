import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st

# Load datasets
ratings = pd.read_csv('ratings.csv')
movies = pd.read_csv('moviesV2.csv')

# Merge ratings and movies datasets
data = pd.merge(ratings, movies, on='movieId')

# Create a pivot table for user-item matrix
user_item_matrix = data.pivot_table(index='userId', columns='title', values='rating')


# Replace NaNs with 0s for similarity calculation
user_item_matrix_filled = user_item_matrix.fillna(0)

# Compute item-item similarity matrix using cosine similarity
item_similarity_matrix = cosine_similarity(user_item_matrix_filled.T)
item_similarity_df = pd.DataFrame(item_similarity_matrix, index=user_item_matrix.columns, columns=user_item_matrix.columns)

# Create a genre matrix
genres = movies['genres'].str.get_dummies(sep='|')
movies_with_genres = pd.concat([movies, genres], axis=1)

# Define functions to get similar items and recommend movies
def get_similar_items(movie_title, n=5):
    similar_scores = item_similarity_df[movie_title]
    similar_movies = similar_scores.sort_values(ascending=False).index[1:n+1]
    return similar_movies

def recommend_movies(user_id, n=5):
    # Get user's rated movies
    user_ratings = user_item_matrix.loc[user_id].dropna()

    # Initialize an empty recommendation score dictionary
    recommendation_scores = {}

    # Loop through user's rated movies
    for movie, rating in user_ratings.items():
        similar_movies = get_similar_items(movie, n)
        for similar_movie in similar_movies:
            if similar_movie not in user_ratings.index:
                if similar_movie not in recommendation_scores:
                    recommendation_scores[similar_movie] = 0
                recommendation_scores[similar_movie] += rating * item_similarity_df[movie][similar_movie]

    # Sort the recommendations by score
    sorted_recommendations = sorted(recommendation_scores.items(), key=lambda x: x[1], reverse=True)
    return [movie for movie, score in sorted_recommendations[:n]]

def recommend_movies_by_genres(selected_genres, n=5):
    # Filter movies that contain at least one of the selected genres
    genre_filter = movies_with_genres[selected_genres].sum(axis=1) > 0
    filtered_movies = movies_with_genres.loc[genre_filter].copy()

    # Sort movies by the number of matching genres
    filtered_movies['genre_match_count'] = filtered_movies[selected_genres].sum(axis=1)
    recommended_movies = filtered_movies.sort_values(by='genre_match_count', ascending=False).head(n)

    return recommended_movies[['movieId', 'title', 'genres']]

def recommend_movies_by_release_year(year, n=5):
    # Filter movies released in the specified year
    filtered_movies = movies[movies['release_year'] == year]

    # Sort movies by popularity (e.g., average rating)
    sorted_movies = filtered_movies.sort_values(by='average_rating', ascending=False).head(n)

    return sorted_movies[['movieId', 'title', 'genres']]

# Function to recommend movies by release decade
def recommend_movies_by_release_decade(decade, n=5):
    # Extract start and end years of the decade
    start_year = decade
    end_year = decade + 9

    # Filter movies released in the specified decade
    filtered_movies = movies[(movies['release_year'] >= start_year) & (movies['release_year'] <= end_year)]

    # Sort movies by popularity (e.g., average rating)
    sorted_movies = filtered_movies.sort_values(by='average_rating', ascending=False).head(n)

    return sorted_movies[['movieId', 'title', 'genres']]

# Streamlit app
st.title("Movie Recommendation System")

# Sidebar for navigation
page = st.sidebar.selectbox("Choose a page", ["Collaborative Filtering", "Genre-Based Recommendation", "By Release Year"])

if page == "Collaborative Filtering":
    st.header("Collaborative Filtering")

    # User input
    user_id = st.number_input("Enter User ID", min_value=1, max_value=len(user_item_matrix.index), value=1)
    num_recommendations = st.slider("Number of Recommendations", min_value=1, max_value=20, value=5)

    # Recommend movies
    recommendations = recommend_movies(user_id, num_recommendations)
    st.write(f"Top {num_recommendations} recommendations for user {user_id}:")
    for i, movie in enumerate(recommendations):
        st.write(f"{i + 1}. {movie}")

elif page == "Genre-Based Recommendation":
    st.header("Genre-Based Recommendation")

    # User input for genre selection
    available_genres = list(genres.columns)
    selected_genres = st.multiselect("Select Genres", available_genres)
    num_recommendations = st.slider("Number of Recommendations", min_value=1, max_value=20, value=5)

    # Recommend movies based on genres
    if st.button("Recommend"):
        recommendations = recommend_movies_by_genres(selected_genres, num_recommendations)
        st.write(f"Top {num_recommendations} recommendations for genres {selected_genres}:")
        for i, row in recommendations.iterrows():
            st.write(f"{i + 1}. {row['title']} ({row['genres']})")
            

elif page == "By Release Year":
    st.header("Recommendation by Release Year")

    # User input for release year or decade
    release_year = st.number_input("Enter Release Year", min_value=1900, max_value=2024, value=2020)
    num_recommendations = st.slider("Number of Recommendations", min_value=1, max_value=20, value=5)

    # Check if recommendation button is clicked
    recommend_by_year = st.button("Recommend by Year")
    if recommend_by_year:
        # Extract release year from movie titles
        movies['release_year'] = movies['title'].str.extract(r'\((\d{4})\)$')
        
        # Filter movies by release year
        filtered_movies = movies[movies['release_year'] == str(release_year)]
        
        # Check if any movies are found for the given year
        if not filtered_movies.empty:
            recommendations_year = filtered_movies.head(num_recommendations)
            st.write(f"Top {num_recommendations} recommendations for {release_year}:")
            for i, row in recommendations_year.iterrows():
                st.write(f"{i + 1}. {row['title']} ({row['genres']})")
        else:
            st.write(f"No movies found for the year {release_year}. Please try another year.")
