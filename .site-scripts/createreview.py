import os
import sys
import requests
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from PIL import Image
from imdb import IMDb
from io import BytesIO

# DEFAULTS AND CONSTANTS
DEFAULT_TEMPLATE = "../_drafts/film-review-template.md"
DEFAULT_LOCATION = "../_posts/"
IMAGE_LOCATION = "../assets/img/posts/"

# this changes the input from "lOrD oF tHe riNgs" to "lord-of-the-rigns"
def create_review_filename(title):
    title = title.replace(" ", "-")
    title = title.replace("_", "-")
    title.lower()
    return title

# this changes the input from "lOrD oF tHe riNgs" to "Lord of the Rings"
def prettify_title(title):
    # List of words that should not be capitalized in the middle of a title
    small_words = {"a", "an", "and", "but", "for", "if", "in", "nor", "of", "on", "or", "so", "the", "to", "up"}

    # Replace hyphens with spaces
    title = title.replace("-", " ")
    title = title.replace("_", " ")

    # Split the string into words
    words = title.split()

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

def download_and_resize_image(image_url, save_location, file_name):
    try:
        # Fetch the image from the URL
        response = requests.get(image_url)
        response.raise_for_status()  # Raise an error for HTTP issues

        # Open the image from the fetched content
        img = Image.open(BytesIO(response.content))

        # Calculate new dimensions while maintaining the aspect ratio
        width, height = img.size
        new_height = 500
        new_width = int((new_height / height) * width)
        img = img.resize((new_width, new_height))

        # Ensure save location exists
        os.makedirs(save_location, exist_ok=True)

        # Save the image in PNG format
        save_path = os.path.join(save_location, f"{file_name}.png")
        img.save(save_path, "PNG")

        print(f"Image saved successfully at {save_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

def download_and_resize_poster(movie_filename, movie_pretty_title, image_save_location, release_year=None):
    # Initialize IMDb
    ia = IMDb()

    try:
        # Search for the movie
        results = ia.search_movie(movie_pretty_title)

        if not results:
            raise ValueError(f"Movie '{movie_pretty_title}' not found on IMDb.")

        # Ask the user to choose if multiple results are found
        print(f"Multiple results found for '{movie_pretty_title}':")
        for idx, result in enumerate(results[:10], start=1):
            title = result.get('title', 'Unknown Title')
            print(f"{idx}. {title}")

        choice = int(input("Enter the number of the movie you want: ").strip())
        if choice < 1 or choice > len(results[:10]):
            raise ValueError("Invalid choice.")

        movie = results[choice - 1]

        if not movie:
            raise ValueError(f"Movie '{movie_pretty_title}' not found on IMDb.")

        # Get movie details (including poster)
        ia.update(movie)
        poster_url = movie.get('full-size cover url')
        movie_url = f"https://www.imdb.com/title/tt{movie.movieID}/"
        movie_images_url = f"https://www.imdb.com/title/tt{movie.movieID}/mediaindex/"

        if not poster_url:
            raise ValueError(f"Poster not found for movie '{movie_pretty_title}'.")

        # Download the poster
        response = requests.get(poster_url, stream=True)
        if response.status_code != 200:
            raise ValueError(f"Failed to download poster for movie '{movie_pretty_title}'.")

        # Save the poster locally
        save_location = os.path.abspath(image_save_location)
        poster_filename = os.path.join(save_location, f"{movie_filename}-cover.png")

        print(f"Movie found! ['{poster_filename}']")

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

        print(f"Poster for '{movie_pretty_title}' saved as '{poster_filename}' and resized to height 500 pixels.")

        print(f"IMDb URL for the movie: {movie_url}")
        webbrowser.open(movie_url)  # Open the link in the default browser
        print(f"IMDb URL for the movie pics: {movie_images_url}")
        webbrowser.open(movie_images_url)

        url_input = input("Enter the image URL (optional): ").strip()
        image_url = url_input if url_input else None
        if image_url is not None:
            download_and_resize_image(image_url, image_save_location, movie_filename)

    except Exception as e:
        print(f"Error: {e}")

def create_file_structure_and_copy_template(review_name_input, release_year):
    # Give "release year" a placeholder value if it doesn't exist
    release_year_text = "RELEASE_YEAR" if release_year is None else release_year

    # get names
    review_filename = create_review_filename(review_name_input)
    review_pretty_title = prettify_title(review_name_input)

    # Ensure the template exists
    template_path = os.path.abspath(DEFAULT_TEMPLATE)
    if not os.path.isfile(template_path):
        print(f"Error: Template file '{template_path}' not found.")
        sys.exit(1)

    save_location = os.path.abspath(DEFAULT_LOCATION)
    if not os.path.exists(save_location):
        print(f"Error: Save location '{save_location}' not found.")
        sys.exit(1)

    if not os.path.exists(os.path.abspath(IMAGE_LOCATION)):
        print(f"Error: image location was not found")
        sys.exist(1)

    # gmt offset for daylight savings
    offset_sec = time.altzone if time.daylight and time.localtime().tm_isdst else time.timezone
    offset_hours = -offset_sec // 3600
    gmt_offset = f"{offset_hours:+03d}00"

    review_publish_year = datetime.now().strftime("%Y")
    review_publish_date = datetime.now().strftime("%Y-%m-%d")
    full_review_publish_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_review_publish_date = full_review_publish_date + " " + gmt_offset

    # create destination directory for the post
    save_location = save_location + "/" + review_publish_year + "/" + review_publish_date
    save_location = os.path.abspath(save_location)
    if not os.path.exists(save_location):
        os.makedirs(save_location)

    # create destination directory for images
    image_save_location = IMAGE_LOCATION + "/" + review_publish_date
    image_save_location = os.path.abspath(image_save_location)
    if not os.path.exists(image_save_location):
        os.makedirs(image_save_location)

    # Read the template file
    with open(template_path, "r") as template_file:
        template_content = template_file.read()

    # replace placeholder content
    output_content = template_content.replace("{{TITLE_CAPS}}", review_pretty_title)
    output_content = output_content.replace("{{RELEASE_YEAR}}", release_year_text)
    output_content = output_content.replace("{{TITLE}}", review_filename)
    output_content = output_content.replace("{{DATE}}", review_publish_date)
    output_content = output_content.replace("1969-06-20", full_review_publish_date)

    # remove specific lines:
    lines = output_content.splitlines()
    filtered_lines = [line for line in lines if "draft: true" not in line]
    output_content = "\n".join(filtered_lines)  # Join the remaining lines back

    # save new review file:
    directory = Path(save_location)
    file_count = len([f for f in directory.iterdir() if f.is_file()])
    output_filename = f"{review_publish_date}-{file_count:02d}-{review_filename}.md"
    output_file_path = os.path.join(save_location, output_filename)

    # Write the content to the new file
    with open(output_file_path, "w") as output_file:
        output_file.write(output_content)

    print(f"File created: {output_file_path}")
    download_and_resize_poster(review_filename, review_pretty_title, image_save_location)

if __name__ == "__main__":
    review_name_input = input("Enter the name: ").strip().lower()
    release_year_input = input("Enter the release year (optional): ").strip()
    release_year = release_year_input if release_year_input else None

    create_file_structure_and_copy_template(review_name_input, release_year)