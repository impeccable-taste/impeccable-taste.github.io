import os
import sys
import time
import webbrowser
import requests
from datetime import datetime
from pathlib import Path
from PIL import Image
from io import BytesIO

# DEFAULTS AND CONSTANTS
DEFAULT_TEMPLATE = "../_drafts/film-review-template.md"
DEFAULT_LOCATION = "../_posts/"
IMAGE_LOCATION = "../assets/img/posts/"
DEBUG_MODE = False

# TMDB API CONFIGURATION
TMDB_API_TOKEN = os.getenv(
    "TMDB_API_TOKEN",
	"eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJhZTY1ZjcwZDg0MjMxODgxNzg3ZTlhM2Q0NzI5NDMzMCIsIm5iZiI6MTc4NjQ0MjY4Mi45NTEsInN1YiI6IjZhN2FmM2JhOWU2NTZiNmQ1ZWI3MzE0ZSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.hDr-AxGfHU3-NMG1hBLKCSHLIVt2ih-qh4ylIsECjBs"
)

TMDB_API_BASE = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p"
TMDB_POSTER_SIZE = "w500"
POSTER_HEIGHT = 500

# COLORS
BLACK = '\033[30m'
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m' # orange on some systems
BLUE = '\033[34m'
MAGENTA = '\033[35m'
CYAN = '\033[36m'
LIGHT_GRAY = '\033[37m'
DARK_GRAY = '\033[90m'
BRIGHT_RED = '\033[91m'
BRIGHT_GREEN = '\033[92m'
BRIGHT_YELLOW = '\033[93m'
BRIGHT_BLUE = '\033[94m'
BRIGHT_MAGENTA = '\033[95m'
BRIGHT_CYAN = '\033[96m'
WHITE = '\033[97m'
RESET = '\033[0m' # called to return to standard terminal text color

# TMDB API HELPERS
def get_tmdb_headers():
    if (
        not TMDB_API_TOKEN
        or TMDB_API_TOKEN == "PASTE_YOUR_TMDB_READ_ACCESS_TOKEN_HERE"
    ):
        raise ValueError(
            "TMDb API token is missing. "
            "Add your Read Access Token to TMDB_API_TOKEN."
        )
    return {
        "Authorization": f"Bearer {TMDB_API_TOKEN}",
        "accept": "application/json"
    }

def tmdb_request(endpoint, params=None):
    url = f"{TMDB_API_BASE}/{endpoint.lstrip('/')}"
    response = requests.get(
        url,
        headers=get_tmdb_headers(),
        params=params,
        timeout=20
    )
    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        raise RuntimeError(
            f"TMDb API request failed ({response.status_code}): "
            f"{response.text[:500]}"
        ) from e
    return response.json()

def search_tmdb_movie(title, release_year=None):
    params = {
        "query": title,
        "language": "en-US",
        "page": 1,
        "include_adult": False
    }
    if release_year:
        params["year"] = release_year
    data = tmdb_request("search/movie", params)
    return data.get("results", [])

def get_tmdb_movie_details(movie_id):
    return tmdb_request(f"movie/{movie_id}", {"language": "en-US"})

def get_tmdb_external_ids(movie_id):
    return tmdb_request(f"movie/{movie_id}/external_ids")

# TITLE HELPERS
# this changes the input from "lOrD oF tHe riNgs" to "lord-of-the-rigns"
def create_review_filename(title):
    title = title.replace("'", "")
    title = title.replace(" ", "-")
    title = title.replace("_", "-")
    return title.lower()

# this changes the input from "lOrD oF tHe riNgs" to "Lord of the Rings"
def prettify_title(title):
    # List of words that should not be capitalized in the middle of a title
    small_words = {"a", "an", "and", "but", "for", "if", "in", "nor", "of", "on", "or", "so", "the", "to", "up"}

    # Replace hyphens with spaces
    title = title.replace("-", " ")
    title = title.replace("_", " ")

    # Split the string into words
    words = title.split()

    # Early out if nothing's found
    if not words:
        return ""

    # Capitalize the first word and any words not in the small_words set
    result = [words[0].capitalize()]  # Always capitalize the first word

    for word in words[1:]:
        # Capitalize the word if it's not a "small" word
        if word.lower() not in small_words:
            result.append(word.capitalize())
        else:
            result.append(word.lower())

    # Join the words back into a single string
    return " ".join(result)

# IMAGE DOWNLOAD HELPERS
def download_and_resize_image(image_url, save_location, file_name):
    try:
        # Fetch the image from the URL
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()  # Raise an error for HTTP issues

        # Open the image from the fetched content
        with Image.open(BytesIO(response.content)) as img:
            # Calculate new dimensions while maintaining the aspect ratio
            img = img.convert("RGB")
            width, height = img.size
            new_height = POSTER_HEIGHT
            new_width = int((new_height / height) * width)

            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            save_path = os.path.join(save_location, f"{file_name}.png")

            if not DEBUG_MODE:
                # Ensure save location exists
                os.makedirs(save_location, exist_ok=True)
                # Save the image in PNG format
                img.save(save_path, "PNG")
        print(YELLOW+"Image saved successfully at "+DARK_GRAY+save_location+"\\"+YELLOW+f"{file_name}.png"+RESET)
    except Exception as e:
        print(BRIGHT_RED+"An error occurred downloading the image: "+RESET+str(e))

def download_tmdb_poster(poster_path, save_location, file_name):
    if not poster_path:
        raise ValueError("TMDb does not have a poster for this movie.")
    
    poster_url = (f"{TMDB_IMAGE_BASE}/{TMDB_POSTER_SIZE}{poster_path}")
    
    save_location = os.path.abspath(save_location)
    poster_filename = os.path.join(save_location, f"{file_name}-cover.png")

    print(BRIGHT_BLUE+"Downloading TMDb poster: "+YELLOW+poster_url+RESET)

    if not DEBUG_MODE:
        os.makedirs(save_location, exist_ok=True)
        response = requests.get(poster_url, timeout=30)
        response.raise_for_status()
        with Image.open(BytesIO(response.content)) as img:
            img = img.convert("RGB")
            aspect_ratio = img.width / img.height
            new_height = POSTER_HEIGHT
            new_width = int(new_height * aspect_ratio)
            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            img_resized.save(poster_filename, "PNG")
    print(BRIGHT_BLUE+"Poster saved: "+YELLOW+poster_filename+RESET)
    print(BRIGHT_BLUE+"Poster resized to "+YELLOW+f"{POSTER_HEIGHT} pixels high."+RESET)


# MOVIE SEARCH AND SELECTION
def choose_tmdb_movie(results, movie_title):
    if not results:
        raise ValueError(f"Movie '{movie_title}' was not found on TMDb.")
    
    displayed_results = results[:10]
    num_results = len(displayed_results)
    
    print(YELLOW+f"{len(results)}"+DARK_GRAY+" results found for "+BLUE + movie_title+DARK_GRAY+":"+RESET)
    for idx, movie in enumerate(displayed_results, start=1):
        year = movie.get("release_date", "")[:4]
        if not year:
            year = "Unknown"
        print(
            DARK_GRAY+f"\t{idx}. "+YELLOW+movie.get("title", "Unknown title")+
            " "+BRIGHT_BLUE+f"({year})"+RESET
        )

    while True:
        choice_text = input(BRIGHT_BLUE+"Enter the number of the movie you want: "+RESET).strip()
        if not choice_text:
            choice = 1
        else:
            try:
                choice = int(choice_text)
            except ValueError:
                print(BRIGHT_RED+"Please enter a valid number."+RESET)
                continue

        if 1 <= choice <= num_results:
            return displayed_results[choice - 1]
        print(BRIGHT_RED+f"Please choose a number between 1 and {num_results}."+RESET)

# MAIN MOVIE LOOKUP
def download_and_resize_poster(movie_filename, movie_pretty_title, image_save_location, release_year=None):
    try:
        # SEARCH TMDB
        print(BRIGHT_CYAN+"\nSearching TMDb..." + RESET)
        results = search_tmdb_movie(movie_pretty_title, release_year)
        chosen_movie = choose_tmdb_movie(results,movie_pretty_title)
        movie_id = chosen_movie["id"]

        # GET MOVIE DETAILS
        print(BRIGHT_CYAN + "\nRetrieving movie details..." + RESET)
        movie = get_tmdb_movie_details(movie_id)
        poster_path = movie.get("poster_path")

        # GET IMDB ID
        external_ids = get_tmdb_external_ids(movie_id)
        imdb_id = external_ids.get("imdb_id")

        # CONSTRUCT URLS
        tmdb_url = (f"https://www.themoviedb.org/movie/{movie_id}")

        if imdb_id:
            imdb_url = (f"https://www.imdb.com/title/{imdb_id}/")
            imdb_images_url = (f"https://www.imdb.com/title/{imdb_id}/mediaindex/")

        else:
            imdb_url = None
            imdb_images_url = None

        # DOWNLOAD TMDB POSTER
        print(BRIGHT_BLUE + "\nMovie found: " + YELLOW + movie.get("title", movie_pretty_title) + RESET)
        download_tmdb_poster(poster_path, image_save_location, movie_filename)

        # OPEN BROWSER PAGES
        if imdb_url:
            print(BRIGHT_BLUE +"\nIMDb URL for the movie: " +YELLOW + imdb_url + RESET)
            webbrowser.open(imdb_url)
            print(BRIGHT_BLUE +"IMDb URL for the movie gallery: " +YELLOW + imdb_images_url + RESET)
            webbrowser.open(imdb_images_url)
        else:
            print(
                BRIGHT_YELLOW +"\nNo IMDb ID was found for this TMDb entry. "
                "IMDb pages will not be opened." +RESET
            )

        print(BRIGHT_BLUE + "TMDb URL for the movie: " + YELLOW + tmdb_url + RESET)
        webbrowser.open(tmdb_url)

        # OPTIONAL CUSTOM IMAGE
        url_input = input(BRIGHT_BLUE + "\nEnter the image URL (optional): " + RESET).strip()

        if url_input:
            download_and_resize_image(url_input,image_save_location,movie_filename)

    except Exception as e:
        print(BRIGHT_RED +"\nAn error occurred: " +RESET + str(e))

# MARKDOWN FILE GENERATION
def create_file_structure_and_copy_template(review_name_input,release_year):
    # PREPARE TITLES
    release_year_text = (
        "RELEASE_YEAR"
        if release_year is None
        else release_year
    )
    review_filename = create_review_filename(review_name_input)
    review_pretty_title = prettify_title(review_name_input)

    # CHECK DIRECTORIES
    template_path = os.path.abspath(DEFAULT_TEMPLATE)
    if not os.path.isfile(template_path):
        print(BRIGHT_RED + f"Error: Template file '{template_path}' not found." + RESET)
        sys.exit(1)

    base_save_location = os.path.abspath(DEFAULT_LOCATION)
    if not os.path.exists(base_save_location):
        print(BRIGHT_RED + f"Error: Save location '{base_save_location}' not found." +RESET)
        sys.exit(1)

    base_image_location = os.path.abspath(IMAGE_LOCATION)
    if not os.path.exists(base_image_location):
        print(BRIGHT_RED +f"Error: Image location '{base_image_location}' not found." +RESET)
        sys.exit(1)

    # DATE AND GMT OFFSET
    offset_sec = (
        time.altzone
        if time.daylight and time.localtime().tm_isdst
        else time.timezone
    )

    offset_hours = -offset_sec // 3600
    gmt_offset = f"{offset_hours:+03d}00"
    now = datetime.now()
    review_publish_year = now.strftime("%Y")
    review_publish_date = now.strftime("%Y-%m-%d")
    full_review_publish_date = (now.strftime("%Y-%m-%d %H:%M:%S") + " " + gmt_offset)

    # CREATE DESTINATION DIRECTORIES
    save_location = os.path.abspath(os.path.join(base_save_location, review_publish_year, review_publish_date))
    image_save_location = os.path.abspath(os.path.join( base_image_location, review_publish_date))

    if not DEBUG_MODE:
        os.makedirs(save_location, exist_ok=True)
        os.makedirs(image_save_location, exist_ok=True)

    # READ TEMPLATE
    with open(template_path, "r", encoding="utf-8") as template_file:
        template_content = template_file.read()

    # REPLACE TEMPLATE PLACEHOLDERS
    output_content = template_content.replace("{{TITLE_CAPS}}", review_pretty_title)
    output_content = output_content.replace("{{RELEASE_YEAR}}", release_year_text)
    output_content = output_content.replace("{{TITLE}}", review_filename)
    output_content = output_content.replace("{{DATE}}", review_publish_date)
    output_content = output_content.replace("1969-06-20", full_review_publish_date)

    # REMOVE DRAFT LINE
    lines = output_content.splitlines()
    filtered_lines = [
        line for line in lines
        if "draft: true" not in line
    ]
    output_content = "\n".join(filtered_lines)

    # CREATE MARKDOWN FILE
    directory = Path(save_location)
    if directory.exists():
        file_count = len([
            f for f in directory.iterdir()
            if f.is_file()
        ])
    else:
        file_count = 0

    output_filename = (
        f"{review_publish_date}-"
        f"{file_count:02d}-"
        f"{review_filename}.md"
    )

    output_file_path = os.path.join(save_location, output_filename)

    if not DEBUG_MODE:
        with open(output_file_path, "w", encoding="utf-8") as output_file:
            output_file.write(output_content)

    print(BRIGHT_BLUE + "\nMarkdown file created:" +RESET)
    print(DARK_GRAY +f"\t{save_location}\\" +YELLOW +output_filename +RESET)

    # SEARCH MOVIE AND DOWNLOAD POSTER
    download_and_resize_poster(review_filename, review_pretty_title, image_save_location, release_year)

# MAIN
if __name__ == "__main__":
    if len(sys.argv) > 1:
        DEBUG_MODE = sys.argv[1] == "-d"

    if DEBUG_MODE:
        print(BRIGHT_RED + "\nDEBUG MODE ON: no files will be created or saved\n" + RESET)

    review_name_input = input(BRIGHT_BLUE + "Enter the name: " + RESET).strip().lower()
    if not review_name_input:
        print(BRIGHT_RED + "You must enter a movie name." + RESET)
        sys.exit(1)

    release_year_input = input(BRIGHT_BLUE + "Enter the release year (optional): " +RESET).strip()
    release_year = (
        release_year_input
        if release_year_input
        else None
    )
    try:
        create_file_structure_and_copy_template(review_name_input, release_year)
    except KeyboardInterrupt:
        print(BRIGHT_YELLOW +"\nOperation cancelled." +RESET)
    except Exception as e:
        print(BRIGHT_RED + "\nFatal error: " + RESET + str(e))
        sys.exit(1)