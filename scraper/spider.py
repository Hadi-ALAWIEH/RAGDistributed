import scrapy

class GenericSpider(scrapy.Spider):
    name = "generic"
    custom_settings = {
        "DOWNLOAD_DELAY": 0.2,
        "ROBOTSTXT_OBEY": True
    }

    def __init__(self, start_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if start_url is None:
            raise ValueError("Provide start_url")
        self.start_urls = [start_url]

    def parse(self, response):
        yield {
            "url": response.url,
            "html": response.text
        }
        # Follow a few links to show breadth (bounded)
        for href in response.css("a::attr(href)").getall()[:10]:
            yield response.follow(href, self.parse)
