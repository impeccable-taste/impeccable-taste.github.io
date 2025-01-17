import os
import sys
import argparse
from datetime import datetime
import pytz
from pathlib import Path

DEFAULT_TEMPLATE = "../_drafts/film-review-template.md"
DEFAULT_LOCATION = "../_posts/"
IMAGE_LOCATION = "../assets/img/posts/"

def title_case(title):
    # List of words that should not be capitalized in the middle of a title
    small_words = {"a", "an", "and", "but", "for", "if", "in", "nor", "of", "on", "or", "so", "the", "to", "up"}

    # Replace hyphens with spaces
    title = title.replace("-", " ")

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

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Create a markdown file with a template.")
    parser.add_argument("reviewTitle", help="The title for the markdown file.")
    parser.add_argument("-l", "--location", default=DEFAULT_LOCATION, help="Directory to save the markdown file.")
    parser.add_argument("-t", "--template", default=DEFAULT_TEMPLATE, help="Template file to use.")
    args = parser.parse_args()

    # Ensure the template exists
    template_path = os.path.abspath(args.template)
    if not os.path.isfile(template_path):
        print(f"Error: Template file '{template_path}' not found.")
        sys.exit(1)

    save_location = os.path.abspath(args.location)
    if not os.path.exists(save_location):
        print(f"Error: Save location '{save_location}' not found.")
        sys.exit(1)

    title = args.reviewTitle
    date = datetime.now().strftime("%Y-%m-%d")
    full_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_date = full_date + " +0100"

    # create destination directory
    save_location = save_location + "/" + date
    save_location = os.path.abspath(save_location)
    if not os.path.exists(save_location):
        os.makedirs(save_location)

    image_save_location = IMAGE_LOCATION + "/" + date
    image_save_location = os.path.abspath(image_save_location)
    if not os.path.exists(image_save_location):
        os.makedirs(image_save_location)

    # Read the template file
    with open(template_path, "r") as template_file:
        template_content = template_file.read()

    output_content = template_content.replace("{{TITLE_CAPS}}", title_case(title))
    output_content = output_content.replace("{{TITLE}}", title)
    output_content = output_content.replace("{{DATE}}", date)
    output_content = output_content.replace("1969-06-20", full_date)
    output_content = output_content.replace("draft: true", "")

    directory = Path(save_location)
    file_count = len([f for f in directory.iterdir() if f.is_file()])
    filename = f"{date}-{file_count:02d}-{title}.md"
    file_path = os.path.join(save_location, filename)

    # Write the content to the new file
    with open(file_path, "w") as output_file:
        output_file.write(output_content)

    print(f"File created: {file_path}")

if __name__ == "__main__":
    main()