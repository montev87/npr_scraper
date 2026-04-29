# 📚 NPR Scraper for Obsidian

NPR Scraper for Obsidian is a comprehensive Python utility that identifies all articles and transcripts indexed by [NPR.org](https://www.npr.org/), extracts the substantive content and metadata from each, and saves them as frontmatter-rich Markdown files optimized for compatibility with [Obsidian](https://obsidian.md/).

## ✨ Key Features

*   **Bulk Scraping:** Scrape all articles and transcripts indexed by [NPR.org](https://www.npr.org/) in a single run.
*   **Metadata Rich:** Each file includes a comprehensive YAML frontmatter block, including the following:

	| Property              | Notes                  |
	| --------------------- | ---------------------- |
	| `title`               | Source title (sanitized to be Obsidian/file system safe |
	| `outlet`              | For organizational purposes - always `NPR` |
    | `source`              | Source URL |
    | `author`              | List of source authors |
    | `category`            | Source category (uses last item in NPR-provided taxonomy) |
	| `topics`              | List of source topics (combines NPR-provided taxonomy and tags) |
	| `type`                | `article` or `transcript` |
	| `published_date`      | Source published date |
	| `published_timestamp` | Source published timestamp |
	| `scraped_timestamp`   | Scraped timestamp |
	| `cover`				| Cover image embedded HTML for use with Obsidian Dataview/DataCards plugins |
	| `cover_url`           | Cover image URL for use with Obsidian Bases plugin |
	| `tags`                | List containing only `NPR` |
	
*   **Advanced Content Parsing:** The scraper intelligently handles converting various HTML elements to Markdown format, such as:
    *   **Headings:** Extracts and formats HTML header tags (`<h1>`, `<h2>`, etc.) and converts to Markdown (`#`, `##`, etc.).
    *   **Media:** Processes images (including captions and credits) and preserves embedded video/audio players (as HTML).
    *   **Structural Cleanliness:** Includes logic to skip common boilerplate elements, such as `pullquotes`, `bucketblocks`, and media promotions, ensuring only core journalistic content is captured.

## 🛠️ Setup and Prerequisites

1. If you do not already have Obsidian installed, [download and install Obsidian.](https://obsidian.md/download)

2. If you do not already have Python installed, [download and install Python.](https://www.python.org/downloads)
   
3. [Download NPR Scraper for Obsidian](https://github.com/montev87/npr_scraper/archive/refs/heads/main.zip) and unzip it.
   
4. Open `npr_scraper.py` with the text/code editor of your choice and update the `OUTPUT_DIR_PATH` variable.
    * Find the following code block:
    ```
    OUTPUT_DIR_PATH = Path(
    "***INSERT FILEPATH HERE***"
    )
    ```
    * Replace `***INSERT FILEPATH HERE***` with the path to your desired save location within your Obsidian Vault (**this will not create a subfolder within your specified path**).
    * If you do not configure this setting, the files will be saved to a folder named "NPR" in the same directory as the utility.

5. Ensure that you have the installed the required Python libraries ([Beautiful Soup](https://beautiful-soup-4.readthedocs.io/en/latest) and [Requests](https://docs.python-requests.org/en/latest/index.html)) in your Python environment by running **one of** the commands below:

	```bash
	pip install -r requirements.txt
	```
	
	```bash
	pip install beautifulsoup4 requests
	```

## 🚀 Usage Guide

1.  **Run the utility:**
    ```bash
    python npr_scraper.py
    ```
    *Also supports single-article scraping without configuration (saves the article to a folder named "NPR" in the same directory as the utility) by running the following command:*
    ```bash
    python npr_single_scraper.py
    ```
2.  **Monitor:**
    The console output will provide real-time status updates, including:
    *   Which URL is being processed.
    *   Whether any critical errors were encountered.
    *   The final summary of successfully saved articles.

### 📋 Configuration Notes

The utility relies on several other constants located at the beginning of `npr_scraper.py`:

* `ARTICLE_SORT`: Defaults to `False`. If set to `True`, the utility will sort the files into subfolders within `OUTPUT_DIR_PATH` based on the NPR-provided taxonomy. If `False`, all files will be saved directly to `OUTPUT_DIR_PATH`.
* `ARTICLE_SELECTORS` / `ARTICLE_EXCLUDERS`: These list regular expressions/CSS classes used by the utility to determine which links on the main page are valid article links. **These selectors are highly dependent on NPR's current site structure and may need periodic updates.**

## 🪨 Obsidian Integration

1. Once the utility has saved the articles in your Obsidian Vault, you can use either [Obsidian Bases](https://obsidian.md/help/bases), [Dataview](https://blacksmithgu.github.io/obsidian-dataview/), or [DataCards](https://sophokles187.github.io/data-cards/#/)
2. For Bases, use the `cover_url` property. For Dataview or DataCards, use `cover`.
3. For example, use the following query for DataCards (for Dataview, just change `datacards` to `dataview`:
	````
	```datacards
	TABLE cover AS "", published_date AS Published, category AS Category
	FROM #NPR
	WHERE type = "article"
	SORT published_timestamp DESC
 	```
	````
