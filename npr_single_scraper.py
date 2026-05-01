from acronyms import acronyms
from bs4 import BeautifulSoup
import datetime as dt
import json
import os
from pathlib import Path
import requests
import re
from typing import Optional

# Current timestamp format
t = dt.datetime.now(dt.timezone.utc).astimezone()
CURRENT_TIMESTAMP = t.isoformat()


def main():
    try:

        """Main scraping routine."""
        print("\n=============================================================")
        print("                 NPR Web Scraper Utility                     ")
        print("=============================================================")

        url = input("Enter the URL of the article you would like to scrape: ")

        print(f"Processing article {url}")

        # Scrape the content of the single article using the current page's HTML structure
        article_content = scrape_article_content(url)

        if article_content:
            if save_markdown_file(url, article_content, current_content):
                print("\n===========================================================")
                print(f"✅ Scraping finished! Successfully saved.")
                print("===========================================================")
        else:
            print(f"ERROR: No valid content.")
    except KeyboardInterrupt:
        print("\n***Process terminated by user keyboard input***")
        pass


def fetch_content(url: str) -> Optional[str]:
    """Fetches the HTML content directly from the specified URL."""
    print(f"--> Fetching content from: {url}")
    try:
        # Standard headers to mimic a real browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
        global current_content
        current_content = response.text
        return current_content
    except requests.exceptions.RequestException as e:
        print(f"❌ FATAL ERROR: Could not fetch URL {url}. Reason: {e}")
        return


def scrape_article_content(url: str) -> Optional[str]:
    """
    Parses the main HTML content to extract the primary article body text.
    """
    try:
        html_content = fetch_content(url)
        soup = BeautifulSoup(html_content, "html.parser")
    except ValueError as e1:
        print(f"ERROR: Could not parse URL {url}. Reason: {e1}")
        return

    formatted_content_list = []

    # Header
    header_parts = []

    # Category
    article_category_container = soup.find("div", attrs={"class": "slug-wrap"})
    if article_category_container:
        article_category = article_category_container.find("a")
        if article_category:
            href = article_category.get("href")
            text = article_category.get_text(strip=True)
            header_parts.append(f"[{text}]({href})")

    # Title
    article_title_container = soup.find("div", class_="storytitle")
    if article_title_container:
        article_title = f"# {article_title_container.get_text(strip=True)}"
        header_parts.append(article_title)
    else:
        # Return None if article does not have title (prints error in main)
        return None

    # Date
    article_date_container = soup.find("time")
    if article_date_container:
        date = article_date_container.find("span", attrs={"class": "date"})
        if date:
            date = date.get_text(strip=True)
        time = article_date_container.find("span", attrs={"class": "time"})
        if time:
            time = time.get_text(strip=True)
        header_parts.append(f"{date} - {time}")

    # Byline
    authors = []
    author_container = soup.find("div", id="storybyline")
    if author_container:
        author_containers = author_container.find_all("a")
        if author_containers:
            for a in author_containers:
                parent = a.parent
                if "byline__photo" not in parent.get("class", []):
                    href = a.get("href")
                    text = a.get_text(strip=True)
                    authors.append(f"[{text}]({href})")
            authors = ", ".join(authors)
            header_parts.append(f"By {authors}")

    header = "\n".join(header_parts)
    formatted_content_list.append(header)

    # Main content
    global main_content_selector
    main_content_selector = "storytext"
    global main_content_area
    main_content_area = soup.find("div", id=main_content_selector)

    # Check for embedded audio player
    audio_player = soup.find("input", attrs={"class": "embed-url embed-url-no-touch"})
    if audio_player:
        header_container = soup.find("time", attrs={"class": "audio-module-duration"})
        if header_container:
            header_time = header_container.get_text(strip=True).split(":")
            header = f"## {header_time[0]}-Minute Listen"
        else:
            header = "## Listen"
        audio_player = audio_player.get("value")
        if main_content_area:
            formatted_content_list.append(f"{header}\n\n{audio_player}\n\n## Story")
        else:
            formatted_content_list.append(f"{header}\n\n{audio_player}")

    if main_content_area:
        print(f"    -> Processing main content.")
        main_header_tags = main_content_area.find_all(
            ["h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "div"]
        )

        if not main_header_tags:
            print(
                f"Warning: No <h> or <p> tags found inside the main content container. Returning None."
            )
            return None

        for tag in main_header_tags:

            # Global exclusions
            is_excluded = False

            # Exclude bucketblocks
            if has_ancestor_with_class(tag, "bucketblock"):
                is_excluded = True

            # Exclude pullquotes
            if has_ancestor_with_class(tag, "pullquote"):
                is_excluded = True

            # Exclude media promos
            if has_ancestor_with_class(tag, "mediapromo"):
                is_excluded = True

            # Skip the tag if its parent is excluded
            if is_excluded:
                continue

            # Determine tag type and format accordingly
            tag_name = tag.name

            if tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                # Convert HTML <h> tags to markdown format
                try:
                    level = int(tag_name[1])
                    markdown_header = "#" * level
                    text = tag.get_text(strip=True)
                    formatted_content_list.append(f"{markdown_header} {text}")
                except ValueError:
                    pass  # Skip if tag naming convention is broken

            elif tag_name == "div":
                # Handle images
                if tag.has_attr("class") and "image" in tag.get("class", []):
                    image_parts = []
                    image_container = tag.find("img")
                    alt = image_container.get("alt")
                    src = image_container.get("src")
                    embed = f"![{alt}]({src})"
                    image_parts.append(embed)

                    # Handle captions
                    caption_container = tag.find("div", attrs={"class": "caption-wrap"})
                    caption = caption_container.find("p")
                    if caption:
                        caption_parts = []
                        for content in caption.contents:
                            if isinstance(content, str):
                                text_node = content.strip()
                                if text_node:
                                    caption_parts.append(f"*{text_node}*")

                            if hasattr(content, "name"):
                                text_inside = content.get_text(strip=True)
                                if content.name == "em":
                                    caption_parts.append(f"*{text_inside}*")
                        caption = reconstruct(caption_parts)
                        image_parts.append(caption)

                    # Handle credit
                    credit = tag.find("span", attrs={"class": "credit"})
                    if credit:
                        text_inside = credit.get_text(strip=True)
                        if f"*{text_inside}*" not in image_parts:
                            image_parts.append(f"*{text_inside}*")

                    image = "\n".join(image_parts)
                    formatted_content_list.append(image)

                # Handle embedded videos
                if tag.has_attr("class") and "npr-video" in tag.get("class", []):
                    # Check for and handle embedded video
                    embedded_video_container = soup.find(
                        "div", attrs={"data-jwplayer": True}
                    )
                    if embedded_video_container:
                        embedded_video_json = embedded_video_container.get(
                            "data-jwplayer"
                        )
                        if embedded_video_json:
                            try:
                                data = json.loads(embedded_video_json)
                                iframe = f"<iframe id='jw_embed' width='600' height='338' src='{data.get("embedLink")}' frameborder='0' scrolling='no'></iframe>"
                                if iframe:
                                    formatted_content_list.append(iframe)
                            except json.JSONDecodeError:
                                pass

            elif tag_name == "p":
                paragraph_segments = []
                parent = tag.parent

                for content in tag.contents:

                    # Skip captions (handled with images)
                    if isinstance(content, str) and "caption" in parent.get(
                        "class", []
                    ):
                        continue

                    # Embedded video credit
                    if isinstance(content, str) and "credit" in tag.get("class", []):
                        if iframe:
                            text_node = content.strip()
                            if text_node:
                                paragraph_segments.append(f"*{text_node}*")

                    # All standard paragraphs
                    elif isinstance(content, str):
                        text_node = content.strip()
                        if text_node:
                            paragraph_segments.append(text_node)

                    # If the content is a tag
                    elif hasattr(content, "name"):
                        # Extract the text and the link from the tag
                        text_inside = content.get_text(strip=True)
                        parent_has_class = hasattr(parent, "class")
                        # Format tags
                        # Embedded video credit (skips any other credits)
                        if hasattr(tag, "class") and "credit" in tag.get("class", []):
                            if iframe:
                                paragraph_segments.append(f"*{text_inside}*")
                            else:
                                continue
                        # Skip captions
                        if parent_has_class:
                            try:
                                parent_class = parent.get("class", [])
                            except TypeError:
                                pass
                            if "caption" in parent_class:
                                continue
                        # Handle links
                        if content.name == "a" and content.has_attr("href"):
                            href = content.get("href")
                            paragraph_segments.append(f"[{text_inside}]({href})")
                        # Handle italics
                        if content.name == "em":
                            if text_inside:
                                paragraph_segments.append(f"*{text_inside}*")
                        # Handle bold
                        if content.name == "strong":
                            paragraph_segments.append(f"**{text_inside}**")
                        # Handle the inexplicable use of <br>
                        if content.name == "br":
                            paragraph_segments.append(f"\n")
                        # Handle disclaimers (no nested formatting support)
                        if "disclaimer" in tag.get("class", []):
                            paragraph_segments.append(f"*{text_inside}*")
                paragraph = reconstruct(paragraph_segments)
                if paragraph:
                    formatted_content_list.append(paragraph)

            # Get lists
            elif tag.name == "ul":
                list_parts = []
                list_items = tag.find_all("li")
                for item in list_items:
                    for content in item.contents:
                        if isinstance(content, str):
                            text = content.strip()
                            list_parts.append(f"  • {text}")
                        if hasattr(content, "name"):
                            if content.name == "a":
                                if hasattr(content, "href"):
                                    href = content.get("href")
                                    text_parts = []
                                    for c in content.contents:
                                        if isinstance(c, str):
                                            text = c.strip()
                                        elif hasattr(c, "name"):
                                            if c.name == "em":
                                                text = f"*{c.get_text(strip=True)}*"
                                        text_parts.append(text)
                                    text = reconstruct(text_parts)
                                link = f"[{text}]({href})"
                                list_parts.append(f" • {link}")
                formatted_content = "\n".join(list_parts)
                formatted_content_list.append(formatted_content)

        # Join the list of formatted blocks
        article_content = "\n\n".join(formatted_content_list)

    else:
        print(
            f"    -> Could not find main content container for {url}. Checking for transcript."
        )
        article_content = "\n\n".join(formatted_content_list)

    """Transcript Support"""
    global transcript_content_selector
    transcript_content_selector = "transcript storytext"
    global transcript_content_area
    transcript_content_area = soup.find("div", class_=transcript_content_selector)

    if not transcript_content_area:
        print(f"    -> No transcript detected.")
        return article_content
    else:
        print(f"    -> Processing transcript.")

        formatted_content_list = []
        transcript_header = f"## Transcript"
        formatted_content_list.append(transcript_header)
        transcript_paragraphs = transcript_content_area.find_all("p")

        for paragraph in transcript_paragraphs:
            for content in paragraph.contents:
                try:
                    text = content.strip()
                except TypeError:
                    continue
                # Omit disclimaer from main loop
                if text and "disclaimer" in paragraph.get("class", []):
                    continue
                elif text:
                    formatted_content_list.append(text)

        # Disclaimer loop
        disclaimer_paragraph = transcript_content_area.find(
            "p", attrs={"class": "disclaimer"}
        )
        if disclaimer_paragraph:
            disclaimer_paragraphs = transcript_content_area.find_all(
                "p", attrs={"class": "disclaimer"}
            )
        if disclaimer_paragraphs:
            for paragraph in disclaimer_paragraphs:
                disclaimer_parts = []
                for content in paragraph.contents:
                    if isinstance(content, str):
                        try:
                            text = content.strip()
                        except TypeError:
                            continue
                        if text not in disclaimer_parts:
                            disclaimer_parts.append(f"*{text}*")
                    elif hasattr(content, "name"):
                        try:
                            text = content.get_text(strip=True)
                        except TypeError:
                            continue
                        if text and content.name == "a":
                            href = content.get("href")
                            disclaimer_parts.append(f"*[{text}]({href})*")
                disclaimer = " ".join(disclaimer_parts)
                formatted_content_list.append(disclaimer)
        transcript_content = "\n\n".join(formatted_content_list)
        article_content = f"{article_content}\n\n{transcript_content}"
        return article_content


def save_markdown_file(url: str, content: str, html_content: str):
    soup = BeautifulSoup(html_content, "html.parser")

    """Save the content to a uniquely named Markdown file."""

    article_title_container = soup.find("div", class_="storytitle")
    if article_title_container:
        if main_content_area:
            article_title = f'"{article_title_container.get_text(strip=True).replace(':', ' -').replace('"', '\'')}"'
        elif transcript_content_area:
            article_title = (
                f'"{article_title_container.get_text(strip=True).replace(':', ' -').replace('"', '\'')} (Transcript)"'
            )
    else:
        return None

    # Create a filesystem-safe filename
    filename = f"{sanitize(article_title)}.md"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = Path(f"{script_dir}/NPR/{filename}")
    print(f"    -> Saving markdown file to {file_path}")

    # Make new folders, if needed.
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(
            f"FATAL ERROR: Could not create directory structure {file_path.parent}. Check permissions. Error: {e}"
        )
        return False

    try:
        # Add Markdown YAML frontmatter header for Obsidian
        article_author_container = soup.find(
            "meta", attrs={"name": "cXenseParse:author"}
        )
        if article_author_container:
            article_author = article_author_container.get("content").split("|")
        else:
            article_author = "N/A"

        # Date
        article_date_container = soup.find("meta", attrs={"name": "date"})
        if article_date_container:
            article_date = article_date_container.get("content")

        # Timestamp
        article_timestamp_container = soup.find(
            "meta", attrs={"name": "cXenseParse:publishtime"}
        )
        if article_timestamp_container:
            article_timestamp = article_timestamp_container.get("content")

        # Topic(s)
        article_topics = []
        article_topics_container = soup.find(
            "meta", attrs={"name": "cXenseParse:taxonomy"}
        )
        if article_topics_container:
            article_topics = article_topics_container.get("content").replace(":", " -").split("/")
        else:
            article_topics = ["N/A"]

        # Category
        article_category_wrapper = soup.find("div", attrs={"class": "slug-wrap"})
        if article_category_wrapper:
            article_category_container = article_category_wrapper.find("a")
            if article_category_container:
                article_category = article_category_container.get_text(strip=True).replace(":", " -")
                if article_category not in article_topics:
                    article_topics.append(article_category)
        elif len(article_topics) >= 1:
            article_category = article_topics[-1]
        else:
            article_category = "N/A"
        
        # Add NPR's tags to topics
        try:
            tag_list = soup.find("div", class_="tags")
            if tag_list:
                tags = tag_list.find_all("li")
                for tag in tags:
                    text = tag.get_text(strip=True).title().split(" ")
                    for i in range(len(text)):
                        word = text[i]
                        if word.upper() in acronyms:
                            text[i] = word.upper()
                    text = " ".join(text)
                    article_topics.insert(-1, text)
        except Exception as e:
            pass

        # Tags
        article_tags = ["NPR"]
        if "N/A" not in article_topics:
            for topic in article_topics:
                if len(topic) <= 25:
                    article_tags.append((sanitize(topic)).replace(" ", "").replace(".", ""))
        if "N/A" != article_category:
            if article_category not in article_topics:
                if len(article_category) <= 25:
                    article_tags.append((sanitize(article_category)).replace(" ", "").replace(".", ""))

        if main_content_area:
            article_type = "article"
        elif transcript_content_area:
            article_type = "transcript"

        article_cover_container = soup.find(
            "meta", attrs={"name": "cXenseParse:zbq-imageUrl"}
        )
        if article_cover_container:
            cover = f"<picture><img src='{article_cover_container.get('content')}'/></picture>"
            cover_url = article_cover_container.get("content")

        markdown_content = f"---\ntitle: {article_title}\noutlet: NPR\nsource: {url}\nauthor: {article_author}\ncategory: {article_category}\ntopics: {article_topics}\ntype: {article_type}\npublished_date: {article_date}\npublished_timestamp: {article_timestamp}\nscraped_timestamp: {CURRENT_TIMESTAMP}\ncover: {cover}\ncover_url: {cover_url}\ntags: {article_tags}\n---\n\n{content}"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        return True

    except Exception as e:
        print(f"ERROR: Could not save file {filename}: {e}")
        return False


def has_ancestor_with_class(element: str, attr: str):
    """
    Check if element (tag) has ancestor with class="attr"
    """
    current = element.parent
    while current:
        if attr in current.get("class", []):
            return True
        current = current.parent
    return False


def reconstruct(paragraph_segments: list) -> str:
    """
    Reconstruct the paragraph string with punctuation-aware spacing.
    Check if the next segment starts with punctuation that should
    be attached to the previous word.
    """
    formatted_content = ""

    # Punctuation characters that should NOT have a preceding space
    attachable_chars = ".!?,';:)]}’\""

    # Assemble parts
    for segment in paragraph_segments:
        if not formatted_content:
            if segment:
                # First segment: just start the string
                formatted_content = segment
        else:
            if segment == "\n":
                formatted_content += "\n"
            else:
                segment = segment.strip()
                # Check if the current segment starts with punctuation
                if segment and segment[0] in attachable_chars:
                    # Attach directly without adding a space
                    formatted_content += segment
                # Handle italicized punctuation by checking second char
                elif len(segment) > 1 and segment[1] in attachable_chars:
                    formatted_content += segment
                else:
                    # Otherwise, add a space before the segment
                    formatted_content += " " + segment

    # Clean and return
    if formatted_content:
        # Handle adjacent italics edge case
        cleaned_content = re.sub(r"(?<=.)\*\*(?=.)", "", formatted_content)
        return cleaned_content


def sanitize(raw_text: str) -> str:
    """
    Clean and sanitize a string (e.g., an article title) to be Obsidian and filesystem safe.
    This function removes characters invalid for Obsidian and most operating systems.
    """
    # Remove specified illegal characters: *, \, /, <, >, :, |, ?, and ".
    cleaned_text = re.sub(r"[*\\/<>:|\?\"]", "", raw_text)

    # Collapse sequences of whitespace and dashes into single spaces.
    cleaned_text = re.sub(r"[\s-]+", " ", cleaned_text).strip()

    # Ensure the resulting string isn't empty
    if not cleaned_text:
        return "Untitled"

    return cleaned_text


if __name__ == "__main__":
    main()
