import scrapy


class GenericSpider(scrapy.Spider):
    name = "generic"
    custom_settings = {
        "DOWNLOAD_DELAY": 0.2,
        "ROBOTSTXT_OBEY": False,
        "DEPTH_LIMIT": 2,
    }

    def __init__(self, start_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if start_url is None:
            raise ValueError("Provide start_url")
        self.start_urls = [start_url]

    def parse(self, response):
        content_type = response.headers.get("Content-Type", b"").decode().lower()

        if "text" in content_type or "html" in content_type:
            yield {"url": response.url, "html": response.text}
        else:
            self.logger.debug(
                f"Skipping non-text content at {response.url} ({content_type})"
            )
            return  # stop processing binary files

        # Follow valid links
        for href in response.css("a::attr(href)").getall():
            if href and href.startswith(("http", "/")):
                yield response.follow(href, self.parse)
