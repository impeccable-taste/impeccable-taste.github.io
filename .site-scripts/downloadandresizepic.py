import os
import sys
import requests
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

def downloadandresizefile(image_save_location, review_filename):
    url_input = input("Enter the image URL: ").strip()
    image_url = url_input if url_input else None
    if image_url is not None:
        num_input = int(input("Gimme a number: ").strip())
        movie_filename = f"{review_filename}-{num_input:02d}"
        download_and_resize_image(image_url, image_save_location, movie_filename)
    else:
        print("\tERROR: no link provided")

def get_save_location():
    review_publish_date = datetime.now().strftime("%Y-%m-%d")
    image_save_location = IMAGE_LOCATION + "/" + review_publish_date
    image_save_location = os.path.abspath(image_save_location)
    if not os.path.exists(image_save_location):
        print(f"\tERROR: directory [{image_save_location}] doesn't exist.")
        return None
    return image_save_location

def getalldata():
    review_name_input = input("Enter the name: ").strip()
    review_filename = create_review_filename(review_name_input)
    image_save_location = get_save_location()
    if (image_save_location == None):
        tryAgain = input("Try again? (no or empty to quit) ").strip()
        if ((tryAgain != None) and (tryAgain == "y")):
            getalldata()
    else:
        downloadandresizefile(image_save_location, review_filename)

if __name__ == "__main__":
    getalldata()
