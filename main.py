from typing import Union
from playwright.sync_api import sync_playwright
from fastapi import FastAPI
import json
import re
import requests
from bs4 import BeautifulSoup
import logging
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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
        for platform in platforms:
            if platform in script["src"]:
                return platform
    return None

def parse_product_page(page, data, market_locators):
    products = page.locator(market_locators["product-card"]).element_handles()
    logging.info("Find %s products" % len(products))

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


f = open('locators.json')
locators_mapping = json.load(f)

tags_metadata = [
    {
        "name": "whois",
        "description": "Geting domain and platform information by url",
    },
    {
        "name": "parse",
        "description": "Parse products by url through pagination",
    },
]

app = FastAPI(openapi_tags=tags_metadata)

@app.post("/whois", tags=['whois'])
def whois(url: str):
    markets = ["amazon", "alibaba"]
    domain = get_domain(url)

    if domain in markets:
        platform = domain
    else:
        platform = get_platform(url)

    return {"domain": domain, "platform": platform}

def check_health(page, url):
    amazon_link = page.get_by_role("link", name="Sorry! Something went wrong")
    print(amazon_link)
    page.screenshot(path="screenshot.png", full_page=True)
    if amazon_link != None:
        print("smthing wrong")
        page.get_by_role("link", name="Amazon.com").click()
        time.sleep(4)
        page.goto(url)
    
    page.screenshot(path="screenshot.png", full_page=True)

@app.post("/parse", tags=['parse'])
def parse_by_url(url: str):
    platform = whois(url)['platform']
    logging.info("Parse by URL: %s" % platform)
    
    if platform in locators_mapping:
        market_locators = locators_mapping[platform]
        with sync_playwright() as playwright:
            firefox = playwright.firefox
            browser = firefox.launch()
            page = browser.new_page()            
            page.goto(url)
            # check_health(page, url)         
            
            next_button_disabled = False
            data = []

            while next_button_disabled == False:
                logging.info("Wait selector %s" % market_locators["product-card"])
                page.wait_for_selector(market_locators["product-card"])
                next_button = page.locator(market_locators["pagination-next"])
                data = parse_product_page(page, data, market_locators)
                logging.info("Collect %s products" % len(data))
                
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
