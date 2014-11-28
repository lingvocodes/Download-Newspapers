__author__ = "ira_pavlova"

import urllib2, re, codecs, os, HTMLParser
h = HTMLParser.HTMLParser()

k = codecs.open('sovsport.csv', 'w', 'utf-8-sig')
k.write(u'Имя файла;Заголовок;Авторы;Дата;Рубрика;Количество словоформ\r\n')

def get_text(page):
##    m = re.search('</div>\n<div xmlns:str="http://exslt.org/strings" class="news-page">' +
##                    '(.*?)</p><hr />',
##                       page, flags = re.U|re.DOTALL)
    m = re.search(u'<div class="material-text">(.*?)</div>', page, flags=re.U|re.DOTALL)
    text = m.group(1)
    text = re.sub('<p align="center"><i>(.*?)</i><br /></p>', u'', text, flags=re.U|re.DOTALL)
    text = re.sub(u'</(?:[Pp]|[Hh][1-9])>', u'[[/p]]', text, flags=re.U)
    text = re.sub(u'<(?:[Pp]|[Hh][1-9])(?:>| [^>]*>)', u'[[p]]', text, flags = re.U)
    text = re.sub('<.*?>', u' ', text)
    text = h.unescape(text)
    text = re.sub('[\r\n]', u' ', text, flags=re.DOTALL)
    text = re.sub(u'\\s{2,}', u' ', text, flags = re.U)
    text = text.replace(u'&', u'&amp;').replace(u"'", u'&apos;')\
              .replace(u'<', u'&lt;').replace(u'>', u'&gt;')
    text = text.replace(u'[[/p]]', u'</p>\r\n')
    text = text.replace(u'[[p]]', u'<p>')
    if re.search(u'^[ \r\n]*<p>', text, flags=re.DOTALL) is None:
        text = u'<p>' + text
    if re.search(u'</p>[ \r\n]*$', text, flags=re.DOTALL) is None:
        text += u'</p>'
    text = re.sub(u'<p> *@[^<>]{,200}</p>', u'', text, flags=re.U)
    #print text
    return text

def get_headline(page):
    m = re.search('<title>(.*?)</title>',
                       page, flags = re.U|re.DOTALL)
    headline = m.group(1)
    headline = re.sub('<.*?>', u'', headline)
    headline = h.unescape(headline)
    headline = re.sub(u'\\[Народная газета\\] - Новости - Советский [Сс]порт',
                      u'', headline)
    headline = re.sub(u'- Новости - Советский [Сс]порт',
                      u'', headline)
    return headline.strip()


def get_author(page):
    m = re.search('<a[^<>]*href="/author-item/[0-9]*">(.*?)' +
                  '</a>', page,
                  flags = re.U|re.DOTALL)
    author = m.group(1)
    author = h.unescape(author)
    return author

def get_day(page):
    m = re.search('(?:<div class="date-news"[^<>]*>|<time>)([0-9]+)',
                  page, flags = re.U|re.DOTALL)
    day = m.group(1)
    return day
    
def get_month(page):
    m = re.search(u'(?:<div class="date-news"[^<>]*>|<time>)[^\r\n]*[0-9 \\r\\n\\t]+([а-яё]+)',
                  page, flags = re.U|re.DOTALL)
    month = m.group(1)
    #print month
    return month

def get_year(page):
    m = re.search(u'(20[0-9]{2}), *[0-9]{2}:', page, flags = re.U|re.DOTALL)
    year = m.group(1)
    return year

def get_rubric(page):
    m = re.search(u'class="vid">(.*?)</a> </h1>', page,
                  flags = re.U|re.DOTALL)
    if m is None:
        return u''
    rubric = m.group(1)
    return rubric

def write_article(fname, href, date, author, header, words, article):
    header = header.replace(u'&', u'&amp;').replace(u"'", u'&apos;')\
             .replace(u'<', u'&lt;').replace(u'>', u'&gt;')
    content = u'<?xml version="1.0" encoding="utf-8"?>\r\n' +\
          u'<DOCUMENT>\r\n\t<METATEXT>\r\n\t\t<URL>' + href + u'</URL>\r\n' +\
          u'\t\t<SOURCE>Советский спорт</SOURCE>\r\n' +\
          u'\t\t<DATE>' + date + u'</DATE>\r\n' +\
          u'\t\t<AUTHOR>' + author + u'</AUTHOR>\r\n' +\
          u'\t\t<TITLE>' + header + u'</TITLE>\r\n' +\
          u'\t\t<WORDCOUNT>' + str(words) + u'</WORDCOUNT>\r\n' +\
          u'\t</METATEXT>\r\n\t<TEXT>\r\n\t\t' + article + u'\r\n' +\
          u'\t</TEXT>\r\n' + u'</DOCUMENT>'
    l = codecs.open(fname, 'w', 'utf-8')
    l.write(content)
    l.close()


d1 = {} 
d2 = {u'января':'01', u'февраля':'02', u'марта':'03', u'апреля':'04',
      u'мая':'05', u'июня':'06', u'июля':'07', u'августа':'08',
      u'сентября':'09', u'октября':'10', u'ноября':'11', u'декабря':'12'}

    
for n in range (700045,700100):
##    try:
        f = 'http://www.sovsport.ru/news/text-item/' + str(n)
        print n
        page = urllib2.urlopen(f).read()
        page = page.decode(u'utf-8')
        text = get_text(page)
        words = text.strip().split()
        if len(words) < 250:
            continue
        count = len(words)
        headline = get_headline(page)
        author = get_author(page)
        day = get_day(page)
        month = d2[get_month(page)]
        year = get_year(page)
        rubric = get_rubric(page)
        date = year + u'.' + month + u'.' + day
        if year not in d1:
            d1[year] = count
        else:
            d1[year] += count

        if d1[year] < 2700000:
##            print text 
##            print headline
##            print author
##            print day
##            print rubric
            fname = year + u'/' + month + u'/' + str(n) + u'.txt'
            href = u'http://www.sovsport.ru/news/text-item/' + str(n)
            k.write(year + u'/' + month + u'/' + str(n) + u';' +
                    headline.replace(u';', u',') + ';' +
                    author.replace(u';', u',') + ';' +
                    date + ';' + rubric + ';' + str(count) + '\r\n')
            if not os.path.exists(year + u'/' + month):
                os.makedirs(year + u'/' + month)
            write_article(fname, href, date, author, headline, count, text)
##    except:
##        print u'Could not open ' + f
k.close()




