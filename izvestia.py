__author__ = "ira_pavlova"

import urllib2, re, codecs, os, HTMLParser
h = HTMLParser.HTMLParser()
arr = 0

k = codecs.open('izvestiya.csv', 'w', 'utf-8-sig')
k.write(u'Имя файла;Заголовок;Подзаголовок;' +
        u'Авторы;Дата;Рубрика;Количество словоформ\r\n')


def get_text(page):
    m = re.search('<div class="text_block" itemprop="articleBody" ' +
                       u'style="position: relative">(.*?)' +
                       u'<div class="get_html_block tooltip_block">',
                       page, flags = re.U|re.DOTALL)
    text = m.group(1)
    text = re.sub('<div class="img_block ">(.*?)</p></div>', u'', text, flags=re.DOTALL)
    text = re.sub(u'</(?:[Pp]|[Hh][1-9])>', u'[[/p]]', text, flags=re.U)
    text = re.sub(u'<(?:[Pp]|[Hh][1-9])(?:>| [^>]*>)', u'[[p]]', text, flags = re.U)
    text = re.sub('<.*?>', u'', text)
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
    return text

def get_headline(page):
    m = re.search('<title>(.*?)</title>',
                       page, flags = re.U|re.DOTALL)
    headline = m.group(1)
    headline = re.sub('<.*?>', u'', headline)
    headline = h.unescape(headline)
    headline = re.sub(u' - Известия', u'', headline)
    return headline

def get_subtitle(page):
    m = re.search('<h2 class="subtitle">(.*?)</h2>',
                       page, flags = re.U|re.DOTALL)
    subtitle = m.group(1)
    subtitle = h.unescape(subtitle)
    return subtitle

def get_author(page):
    m = re.search('itemprop="author">(.*?)' +
                  '</a>', page,
                  flags = re.U|re.DOTALL)
    if m:
        author = m.group(1)
        author = h.unescape(author)
    else:
        author = ""
    return author


def get_day(page):
    m = re.search(u'datetime="[0-9]*-[0-9]*-(.*?)T', page, flags = re.U|re.DOTALL)
    day = m.group(1)
    return day

def get_month(page):
    m = re.search(u'datetime="[0-9]*-(.*?)-', page, flags = re.U|re.DOTALL)
    month = m.group(1)
    return month

def get_year(page):
    m = re.search(u'datetime="(.*?)-',
                  page, flags = re.U|re.DOTALL)
    year = m.group(1)
    return year

def get_rubric(page):
    m = re.search(u'<a href="/rubric/[0-9]*" >(.*?)</a>',
                  page, flags = re.U|re.DOTALL)
    rubric = m.group(1)
    return rubric

def write_article(fname, href, date, author, header, words, article):
    header = header.replace(u'&', u'&amp;').replace(u"'", u'&apos;')\
             .replace(u'<', u'&lt;').replace(u'>', u'&gt;')
    content = u'<?xml version="1.0" encoding="utf-8"?>\r\n' +\
          u'<DOCUMENT>\r\n\t<METATEXT>\r\n\t\t<URL>' + href + u'</URL>\r\n' +\
          u'\t\t<SOURCE>Известия</SOURCE>\r\n' +\
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

for n in range (472425, 575169):
#for n in range (572425, 572495):
    try:
        f = 'http://izvestia.ru/news/' + str(n)
        page = urllib2.urlopen(f).read()
        page = page.decode(u'utf-8')
        text = get_text(page)
        words = text.strip().split()
        if len(words) < 250:
            continue
        count = len(words)
        arr += count
        author = get_author(page)
        subtitle = get_subtitle(page)
        day = get_day(page)
        month = get_month(page)
        year = get_year(page)
        rubric = get_rubric(page)
        if year not in d1:
            d1[year] = count
    
        if d1[year] < 2700000:
            d1[year] += count
            headline = get_headline(page)
            date = year + u'.' + month + u'.' + day
            print headline
            print author
            print subtitle
            print count
            print date
            fname = year + u'/' + month + u'/' + str(n) + u'.txt'
            href = u'http://izvestia.ru/news/' + str(n)
            k.write(year + u'/' + month + u'/' + str(n) + u';' +
                    headline.replace(u';', u',') + ';' +
                    subtitle.replace(u';', u',') + ';' +
                    author.replace(u';', u',') + ';' +
                    date + ';' + rubric + ';' + str(count) + '\r\n')
            if not os.path.exists(year + u'/' + month):
                os.makedirs(year + u'/' + month)
            write_article(fname, href, date, author, headline, count, text)

    except:
        print u'Could not open ' + f            


print arr

k.close()        




       
