import re
import requests
from bs4 import BeautifulSoup as BS
import numpy as np
import pandas as pd
import json
import re

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:65.0) Gecko/20100101 Firefox/65.0"

def handle_query_result(result,key_words):
    links = []
    titles = []
    result_array = []

    for founded in result.find_all('div', class_='yuRUbf'):
        anchors = founded.find_all('a')
        if anchors:
            link = anchors[0]['href']
            title = founded.find('h3').text

            for key_word in key_words:
                if link.find(key_word) != -1:
                    links.append(link)
                    titles.append(title)

    result_array.append(links)
    result_array.append(titles)

    result_array_np = np.array(result_array)
    result_array_pd = pd.DataFrame(result_array_np.transpose(1, 0), columns=['link', 'title'])

    return result_array_pd

def handle_gotten_links(links,titles):
    tags = ['p','font']
    tags_article_text = {'itemprop':'articleBody',
                         'class':
                                ['l-island-a',
                                                           'article-container',
                                                           'article-formatted-body',
                                                           'pw-post-body-paragraph',
                                                           'article','post-body',
                                                           'post_content',
                                                           'article-body',
                                                           'textBlock',
                                                           'uni-blog-article-container',
                                                            'stack center-images stack--block type']}
    ex_headers = ['References',
                  'СПИСОК ЦИТИРУЕМОЙ ЛИТЕРАТУРЫ',
                  'Список литературы / References',
                  'СПИСОК ЛИТЕРАТУРЫ',
                  'ЛИТЕРАТУРА',
                  'Библиографический список',
                  'Список используемой литературы:']

    data = {}
    data['elements'] = []

    for link in links:
        URL = link
        headers = {"user-agent": USER_AGENT}
        try:
            resp = requests.get(URL, headers=headers)
            if resp.status_code == 200:
                soup = BS(resp.content, "html.parser")

                article_text = ""
                for tag_article_text_key in tags_article_text:
                    if isinstance(tags_article_text[tag_article_text_key],list):
                        for el in tags_article_text[tag_article_text_key]:
                            article_text = soup.find_all('div',el)
                            if len(article_text) != 0:
                                break
                    else:
                        article_text = soup.find_all('div',
                                                     {tag_article_text_key: tags_article_text[tag_article_text_key]})
                        if len(article_text) != 0:
                            break

                    if len(article_text) == 0:
                         continue

                article_text_for_add = ''
                json_el = {"from": link}
                for text in article_text:
                    article_text_for_add += re.sub("\s+|\n|\s+$",' ',text.text) + '\n'

                    for ex_header in ex_headers:
                        references_el = text.find_all_next(text = ex_header)

                        ref_a = []
                        for tag in tags:
                            if len(references_el) == 0:
                                continue

                            references_list = references_el[0].find_all_next(tag)

                            if len(references_list) == 0:
                                continue

                            for ref in references_list:
                                ref_a.append(ref.text)

                            json_el['ref'] = ref_a
                            article_text_for_add_splited = article_text_for_add.split(ex_header)
                            if len(article_text_for_add_splited) != 0:
                                article_text_for_add = article_text_for_add_splited[0]

                json_el['text'] = article_text_for_add
                data['elements'].append(json_el)

        except Exception as e:
            print(e)

    with open('data.json', 'w',encoding="utf-8") as outfile:
        json.dump(data, outfile,ensure_ascii=False,indent=4)


def query(query,key_words):
    query = query
    query = query.replace(' ', '+')
    url = f'https://google.com/search?q={query}'
    headers = {"user-agent": USER_AGENT}
    resp = requests.get(url, headers=headers)

    if resp.status_code == 200:
        soup = BS(resp.content,'html.parser')
        links_df = handle_query_result(soup,key_words)
        handle_gotten_links(links_df['link'], links_df['title'])

if __name__ == '__main__':
    v_query = input()
    print("Ключевые слова записываются через #")
    v_key_words = input()
    v_key_words_array = v_key_words.split('#')

    query(v_query, v_key_words_array)
