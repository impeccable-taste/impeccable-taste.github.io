import os
import requests
from PIL import Image
from imdb import IMDb
import webbrowser  # Import the webbrowser module

IMAGE_LOCATION = "../assets/img/posts/"

def download_and_resize_poster(movie_name, day, release_year=None):
    # Initialize IMDb
    ia = IMDb()

    try:
        # Search for the movie
        results = ia.search_movie(movie_name)

        if not results:
            raise ValueError(f"Movie '{movie_name}' not found on IMDb.")

        # Filter by release year if provided
        if release_year:
            movie = next((m for m in results if 'year' in m and m['year'] == release_year), None)
            if not movie:
                raise ValueError(f"Movie '{movie_name}' ({release_year}) not found on IMDb.")
        else:
            # Ask the user to choose if multiple results are found
            print(f"Multiple results found for '{movie_name}':")
            for idx, result in enumerate(results[:10], start=1):
                title = result.get('title', 'Unknown Title')
                year = result.get('year', 'Unknown Year')
                print(f"{idx}. {title} ({year})")

            choice = int(input("Enter the number of the movie you want: ").strip())
            if choice < 1 or choice > len(results[:10]):
                raise ValueError("Invalid choice.")

            movie = results[choice - 1]

        if not movie:
            raise ValueError(f"Movie '{movie_name}' ({release_year}) not found on IMDb.")

        # Get movie details (including poster)
        ia.update(movie)
        poster_url = movie.get('full-size cover url')
        movie_url = f"https://www.imdb.com/title/tt{movie.movieID}/"  # Construct IMDb URL

        if not poster_url:
            raise ValueError(f"Poster not found for movie '{movie_name}' ({release_year}).")

        # Download the poster
        response = requests.get(poster_url, stream=True)
        if response.status_code != 200:
            raise ValueError(f"Failed to download poster for movie '{movie_name}' ({release_year}).")

        # Save the poster locally
        save_location = os.path.abspath(IMAGE_LOCATION)
        date = "/2024-10-" + day + "/";
        save_location = save_location + date
        save_location = os.path.abspath(save_location)
        poster_filename = os.path.join(save_location, f"{movie_name}-cover.png".replace(" ", "-"))

        askquestion = input("is this correct? ["+ poster_filename +"]").strip()
        if askquestion == "n":
            raise ValueError(f"oops")

        with open(poster_filename, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)

        # Resize the poster
        with Image.open(poster_filename) as img:
            aspect_ratio = img.width / img.height
            new_height = 500
            new_width = int(new_height * aspect_ratio)
            img_resized = img.resize((new_width, new_height))
            img_resized.save(poster_filename)

        print(f"Poster for '{movie_name}' ({release_year}) saved as '{poster_filename}' and resized to height 500 pixels.")
        
        print(f"IMDb URL for the movie: {movie_url}")
        webbrowser.open(movie_url)  # Open the link in the default browser

    except Exception as e:
        print(f"Error: {e}")

# Example usage
if __name__ == "__main__":
    movie_name = input("Enter the movie name: ").strip()
    release_year_input = input("Enter the release year (optional): ").strip()
    release_year = int(release_year_input) if release_year_input else None
    date = input("Enter the date: ").strip()
    download_and_resize_poster(movie_name, date, release_year)
