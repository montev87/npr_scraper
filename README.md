# 📚 NPR Scraper for Obsidian

NPR Scraper for Obsidian is a comprehensive Python utility that converts [NPR](https://www.npr.org/) articles to Markdown files optimized for compatibility with [Obsidian](https://obsidian.md/). The utility identifies each individual article indexed at the time of execution, extracts all substantive content and metadata from each, and saves them as frontmatter-rich Markdown files. 

## ✨ Key Features

*   **Bulk Scraping:** Scrape all articles and transcripts from the main NPR section page in a single run.
*   **Metadata Rich:** Each saved article includes a comprehensive YAML frontmatter block containing:
    *   Title, Author, Category, and Topics.
    *   Publication Date and Timestamp.
    *   The source URL and scraper timestamp.
    *   Support for the primary article content type (`article`) or transcript (`transcript`).
*   **Advanced Content Parsing:** The scraper intelligently handles converting various HTML elements to Markdown format, such as:
    *   **Headings:** Extracts and formats HTML header tags (`<h1>`, `<h2>`, etc.) and converts to Markdown (`#`, `##`, etc.).
    *   **Media:** Processes images (including captions and credits) and preserves embedded video/audio players.
    *   **Structural Cleanliness:** Includes logic to skip common boilerplate elements, such as `pullquotes`, `bucketblocks`, and media promotions, ensuring only core journalistic content is captured.
*   **Transcript Support:** Detects and properly handles transcripts.
*   **Robust Sanitization:** Utilizes a specialized `sanitize` function to clean titles and filenames, removing characters invalid for most operating systems and Obsidian.

## 🛠️ Setup and Prerequisites

1. [Download and install Obsidian.](https://obsidian.md/download)

2. [Download and install Python.](https://www.python.org/downloads)

3. Ensure you have the following Python libraries installed in your environment. Run **one of** the commands below:

```bash
pip install -r requirements.txt
```

```bash
pip install beautifulsoup4 requests
```

Docs:
4. [Python](https://docs.python.org/3)
5. [Beautiful Soup](https://beautiful-soup-4.readthedocs.io/en/latest)
6. [Requests](https://docs.python-requests.org/en/latest/index.html)

### 📋 Configuration Notes

The script relies on several constants located at the beginning of `npr_scraper.py`:

* `OUTPUT_DIR_PATH`: Replace `***INSERT FILEPATH HERE***`. If you do not configure this setting, the articles will be downloaded to a folder named "NPR" in the same directory as the script.
* `ARTICLE_SORT`: If set to `True`, the script will sort markdown files into folders within `OUTPUT_DIR_PATH` based on NPR-provided taxonomy. If `False` (default), all files will be saved directly to `OUTPUT_DIR_PATH`.
* `ARTICLE_SELECTORS` / `ARTICLE_EXCLUDERS`: These list regular expressions/CSS classes used by the script to determine which links on the main page are valid article links. These selectors are highly dependent on NPR's current site structure and may need periodic updates.

## 🚀 Usage Guide

1.  **Configure Path:** Update `OUTPUT_DIR_PATH` in `npr_scraper.py` to the file path of your desired save location. See Configuration Notes above.
2.  **Run the Script:**
    ```bash
    python npr_scraper.py
    ```
3.  **Monitoring:** The console output will provide real-time status updates:
    *   Which URL is being processed.
    *   Whether any critical errors were encountered.
    *   The final summary of successfully saved articles.

## 🧠 Technical Deep Dive (How It Works)

The scraper is designed with efficiency in mind. Instead of making separate requests for metadata extraction, the `fetch_content` function uses a global variable (`CURRENT_CONTENT`) to store the raw HTML body of the fetched page. This ensures that when `save_markdown_file` runs, it accesses the already downloaded content without initiating a second network request, making the bulk scraping process significantly faster.

The core logic is split into two main pipelines:
1. **`scrape_article_content`:** Focuses solely on extracting and formatting the *body text*.
2. **`save_markdown_file`:** Focuses on packaging the content with all the necessary *metadata* (frontmatter) and handling the file system save operation.

## 🪨 Obsidian Integration

1. Once the script has saved the articles in your Obsidian Vault, you can use either [Obsidian Bases](https://obsidian.md/help/bases), [Dataview](https://blacksmithgu.github.io/obsidian-dataview/), or [DataCards](https://sophokles187.github.io/data-cards/#/)
2. For Bases, use the `cover_url` property. For Dataview or DataCards, use `cover`.
3. For example, use the following query in DataCards:
	```datacards
	TABLE cover AS "", published_date AS Published, category AS Category
	FROM #NPR
	WHERE type = "article"
	SORT published_timestamp DESC
	```
