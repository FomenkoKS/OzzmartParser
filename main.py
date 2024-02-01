from typing import Union
from playwright.sync_api import sync_playwright
from fastapi import FastAPI
import json
import re
import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
}

def get_domain(url):
    pattern = "(\w+)(\.\w+)\/"
    match = re.findall(pattern, url)
    if match:
        return match[0][0]
    return None


def get_platform(url):
    k = requests.get(url, headers=headers).text
    soup = BeautifulSoup(k, "html.parser")
    scripts = soup.findAll("script", {"src": True})

    platforms = ["woocommerce", "shopify"]

    for script in scripts:
        print(script["src"])
        for platform in platforms:
            if platform in script["src"]:
                return platform
    return None


f = open('locators.json')
locators_mapping = json.load(f)

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.post("/whois")
def whois(url: str):
    markets = ["amazon", "alibaba"]
    domain = get_domain(url)

    if domain in markets:
        platform = domain
    else:
        platform = get_platform(url)

    return {"domain": domain, "platform": platform}


@app.get("/parse/{marketplace}/")
def parse_marketplace(
    marketplace: str,
    me: Union[str, None] = None,
    marketplaceID: Union[str, None] = None,
):
    if marketplace in locators_mapping:
        market_locators = locators_mapping[marketplace]

        with sync_playwright() as playwright:
            chromium = playwright.chromium
            browser = chromium.launch()
            page = browser.new_page()
            merchant_url = market_locators["url"].format(
                me=me, marketplaceID=marketplaceID
            )
            page.goto(merchant_url)
            next_button_disabled = False
            data = []

            while next_button_disabled == False:
                page.wait_for_selector(market_locators["pagination-container"])
                next_button = page.locator(
                    "%s %s"
                    % (
                        market_locators["pagination-container"],
                        market_locators["pagination-next"],
                    )
                )
                data = parse_product_page(page, data, market_locators)
                print("Collect %s products" % len(data))
                next_button_disabled = (market_locators["pagination-disabled"]) in str(
                    next_button.get_attribute("class")
                )

                if (
                    next_button.element_handles()[0]
                    .get_property("disabled")
                    .json_value()
                    == True
                ):
                    next_button_disabled = True

                if next_button_disabled == False:
                    next_button.click()

            browser.close()
            return data
    else:
        return {"error": "not found marketplace"}


def parse_product_page(page, data, market_locators):
    products = page.locator(market_locators["product-card"]).element_handles()
    print("Find %s products" % len(products))

    for product in products:
        title = product.query_selector(market_locators["title"]).inner_text()
        price_handle = product.query_selector(market_locators["price"])
        img_handle = product.query_selector(market_locators["img_url"])
        
        if price_handle is not None:
            price = price_handle.inner_text()
        else:
            price = "none"
        
        if img_handle is not None:
            img_url = img_handle.get_property("src").json_value()
        else:
            img_url = "none"

        link = (
            product.query_selector(market_locators["link"])
            .get_property("href")
            .json_value()
        )
        data.append({"title": title, "price": price, "img_url": img_url, "link": link})
    return data


@app.post("/parse")
def parse_by_url(url: str):
    platform = whois(url)['platform']
    
    if platform in locators_mapping:
        market_locators = locators_mapping[platform]
        with sync_playwright() as playwright:
            chromium = playwright.chromium
            browser = chromium.launch()
            page = browser.new_page()
            page.goto(url)
            next_button_disabled = False
            data = []

            while next_button_disabled == False:
                page.wait_for_selector(market_locators["product-card"])
                next_button = page.locator(market_locators["pagination-next"])
                data = parse_product_page(page, data, market_locators)
                print("Collect %s products" % len(data))
                
                if len(next_button.element_handles()) == 0:
                    next_button_disabled = True
                else:
                    if "pagination-disabled" in market_locators:
                        next_button_disabled = (market_locators["pagination-disabled"]) in str(
                            next_button.get_attribute("class")
                        )

                    if (
                        next_button.element_handles()[0]
                        .get_property("disabled")
                        .json_value()
                        == True
                    ):
                        next_button_disabled = True

                if next_button_disabled == False:
                    next_button.click()

            browser.close()
            return data
    else:
        return {"error": "not found marketplace"}
