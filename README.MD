This script provides functions for retrieving domain and platform information from a given URL, and parsing product information from the provided URL through pagination.

Functions:
- get_domain(url: str) -> str: Extracts the domain from the provided URL.
- get_platform(url: str) -> Union[str, None]: Retrieves the platform information from the URL's HTML content.
- parse_product_page(page, data, market_locators) -> list: Parses product information from a web page using Playwright and returns a list of products.
- whois(url: str) -> dict: API endpoint for getting domain and platform information by URL.
- parse_by_url(url: str) -> Union[dict, list]: API endpoint for parsing products by URL through pagination.

Endpoints:
- /whois: POST request to get domain and platform information by URL.
- /parse: POST request to parse products by URL through pagination.

Dependencies:
- typing: Type annotations for function parameters and return values.
- playwright.sync_api: Synchronous version of the Playwright library for automated testing.
- fastapi: Web framework for building APIs with Python.
- json: Manipulation of JSON data.
- re: Regular expression operations.
- requests: HTTP library for sending requests.
- bs4: Beautiful Soup library for web scraping.

Note:
- This documentation only covers the main functions and API endpoints. Additional dependencies and configuration files may be required for the script to run effectively.

