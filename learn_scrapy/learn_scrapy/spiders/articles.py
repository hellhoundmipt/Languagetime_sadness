# Команда для запуска scrapy crawl <spidername> -o <filename>.jl

import scrapy
import re


# Основной паук

class PdaSpider(scrapy.Spider):
    name = "pda"
    start_urls = ["http://4pda.ru"]
    allowed_domains = ["4pda.ru"]


    def parse_comments(self, response):
        users = []
        for a in response.xpath('//a[contains(@class, "nickname")]/text()'):
            yield users.append(a.extract())     #сохраняем имена юзеров, чтобы потом их удалить из комментов

        # Сохраняем статьи
        div_article = response.xpath("//div[contains(@class, 'content-box')]")
        pn = div_article[0].xpath(".//p[contains(@style, 'text-align:justify') or contains(@style, 'text-align: justify')]")
        pl = []
        for p in pn:
            pl.append(p.xpath("string()").extract_first())

        article_text = ' '.join(pl)
        yield {'article': article_text}
        
        # Сохраняем комментарии
        comment_text = ''
        pattern = re.compile('\.?\s*\r?$')
        for p in response.xpath('//p[contains(@class, "content")]/text()'):
            comment = p.extract()
            p_acceptable = True
            comment_is_full = True
            for user in users:
                if (user in comment):
                    p_acceptable = False
                    comment_is_full = False

            if ('(Комментарий удален)' in comment) or ('\r' == comment):
                p_acceptable = False
                comment_is_full = False

            if p_acceptable:
                comment_text = comment_text + comment

            if len(comment_text) > 0:
                if comment_text[-1] == '\r':
                    comment_is_full = False

            #print(p_acceptable, " ", comment_is_full)
            if p_acceptable:
                comment_text = re.sub(pattern, '. ', comment_text)

            if (comment_is_full == True) and len(comment_text) > 0:
                #делаем первую букву заглавной
                if comment_text[0].islower():
                    comment_text = comment_text.replace(comment_text[0], comment_text[0].upper(), 1)

                #вставляем пробел после последней точки
                comment_text = comment_text + ' '

                #сохраняем сами комментарии
                yield {'comment': comment_text[:-1]}
                comment_text = ''


    def parse_page(self, response):
        print("I am at page", response.url)
        table = response.xpath('//article[contains(@class, "fix-post")]')
        for articles in table.xpath('.//article[contains(@class, "post")]'):
            url_to_article = articles.xpath('.//h2[contains(@class, "list-post-title")]/a/@href').extract_first()
            if url_to_article:
                url_to_article = 'http:' + url_to_article
                yield scrapy.Request(url_to_article, callback=self.parse_comments)


    def parse(self, response):
        for page_num in range(1, 40):
            new_page = "http://4pda.ru/page/" + str(page_num)
            yield scrapy.Request(new_page, callback=self.parse_page)
