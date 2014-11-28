# -*- coding: utf-8 -*-

__author__ = "evgeny_mozhaev"
## программа получает массив дат с помощью calendar(), по дате попадает
## на страницу архива и собирает ссылки на статьи (get_links()),
## для каждой запускается модуль get_article(), он вырезает статью и метаданные.
## Статья сохраняется в модуле xml(). Запускается программа вызовом
## модуля starter()

import urllib2, codecs, re, HTMLParser, httplib, os
thisPath = os.path.abspath(u'.')
rxWords = re.compile(u'\\w+', flags=re.U)

def calendar():
    calendar = []
    def days(days):
        for i in reversed(range(days)):              
            calendar.append(str(year) + '%02d' % (month) + '%02d' % (i + 1))
    for year in reversed(range(2004, 2015)):
        for month in reversed(range(1, 13)):
            if month in [1, 3, 5, 7, 8, 10, 12]:
                days(31)
            elif month in [4, 6, 9, 11]:
                days(30)           
            elif month == 2:
                if year in [2000, 2004, 2008, 2012]:
                    days(29)
                else:
                    days(28)
    #print calendar
    return calendar

def get_html(url): # получает html страницы
    link = u'http://rbcdaily.ru/' + url
    try:
        response = urllib2.urlopen(link, timeout = 20)        
        html = response.read()
        html = html.decode(u'utf-8')
        html = html.replace(u'\n', u'').replace(u'\r', u'')
        response.close()
        return html
    except (IOError, httplib.HTTPException):
        return u''

def get_links(date, old_links): # создает список ссылок на статьи и запускает
##    модуль get_article (циклом по ссылкам за сутки)        
    print date
    links = []
    string = u''
    html = get_html(date)
    archive = re.findall(u'(<!-- Блок.+?в архиве -->.+?)(?=<!--)', html)
    # для поиска только среди
    # ссылок за эту дату, архивных (т.к. на странице есть еще ссылки
##    на современные статьи)
    for i in archive:
        string += i
    links_prelim = re.findall(u'href="/(\\w+?/[0-9]+?)"', string)
    # массив ссылок за сутки
    for link in links_prelim:
        if link not in old_links and link not in links:
            links.append(link)
    return links

def get_article(html, link, date): # вырезает статью и
    # метаданные из html.
    #Сохраняет статью в файл. Метаданные добавляет
    # в строку снаружи. Добавляет количество слов во внешнюю переменную
    filename = re.sub(u'\\D', u'', link) # имя будущего файла
    #(завершающие цифры в ссылке)
    section = re.search(u'(\\w+?)/.+', link, flags = re.U)
    section = section.group(1)
    #вырезает из ссылки "раздел"    
    link_meta = u'http://rbcdaily.ru/' + link
    author = re.search(u'class="author-name">([^<]+)</a>',
                       html, flags = re.U)
    if author != None:
        author = unicode(author.group(1))
    else:
        author = u'None'
    header = re.search(u'class=[\"\']js-title[\"\'].+?>([^<]+)</div>',
                       html, flags = re.U)
    if header != None:
        header = unicode(header.group(1))
    else:
        header = u'None'
    text = re.search(u'<div class="b-article-item-body.+?<[Pp]>(.+?)' +\
                     u'(?:</[Pp]>[^<]*|[.!?][^.!?<]*)</div>', html, flags = re.U)
    if text != None:
        h = HTMLParser.HTMLParser()
        article = h.unescape(text.group(1))
        article = re.sub(u'\\t', u'', article, flags = re.U)
        article = re.sub(u'<p>[^/]+?(?:strong|STRONG)>(—[^<]+)' +\
                         u'</(?:strong|STRONG)>', u'\\1',
                         article, flags = re.U)
        article = re.sub(u'<([^Pp][^ ]*) ?[^>]*>.*?</\\1>', u'',
                         article, flags = re.U)
        article = re.sub(u'<(?:TABLE|table).+?</(?:TABLE|table)>', u'',
                         article, flags = re.U)
        article = re.sub(u'</(?:[Pp]|[Hh][1-9])>', u'[[/p]]', article, flags=re.U)
        article = re.sub(u'<(?:[Pp]|[Hh][1-9])(?:>| [^>]*>)', u'[[p]]', article, flags = re.U)
        article = re.sub(u'<[^>]+>', u'', article)
        article = re.sub(u'\\s{2,}', u' ', article, flags = re.U)
        article = article.replace(u'&', u'&amp;').replace(u"'", u'&apos;')\
                  .replace(u'<', u'&lt;').replace(u'>', u'&gt;')
        header = header.replace(u'&', u'&amp;').replace(u"'", u'&apos;')\
                  .replace(u'<', u'&lt;').replace(u'>', u'&gt;')
        author = author.replace(u'&', u'&amp;').replace(u"'", u'&apos;')\
                  .replace(u'<', u'&lt;').replace(u'>', u'&gt;')
        section = section.replace(u'&', u'&amp;').replace(u"'", u'&apos;')\
                  .replace(u'<', u'&lt;').replace(u'>', u'&gt;')
        article = article.replace(u'[[/p]]', u'</p>\r\n')
        article = article.replace(u'[[p]]', u'<p>')
        article = re.sub(u'<p>[ \r\n]*</p>(?:\r\n)?', u'',
                         article, flags=re.U|re.DOTALL)
        if re.search(u'^[ \r\n]*<p>', article, flags=re.DOTALL) is None:
            article = u'<p>' + article
        if re.search(u'</p>[ \r\n]*$', article, flags=re.DOTALL) is None:
            article += u'</p>'
        article = re.sub(u'(?:<p>[ \r\n]*){2,}', u'', article, flags=re.U)
        words_article = rxWords.findall(article)
        if len(words_article) >= 290:
            folders(date) # создает папку
            meta_data = filename + u';' + unicode(len(words_article)) + u';' +\
                        section.replace(u';', u'') + u';' +\
                        date.replace(u';', u'') + u';' +\
                        author.replace(u';', u'') + u';' +\
                        header.replace(u';', u'') + u';' +\
                        link_meta.replace(u';', u'') + u'\r\n'
            print u'статья загружена'
            xml(filename, link_meta, date, author, header,
                unicode(len(words_article)), article)
            return len(words_article), meta_data, 1

    return 0, u'', 0

def xml(filename, link, date, author, header, words, article):
## создает и записывает xml
    content = u'<?xml version="1.0" encoding="utf-8"?>\r\n' +\
          u'<DOCUMENT>\r\n\t<METATEXT>\r\n\t\t<URL>' + link + u'</URL>\r\n' +\
          u'\t\t<SOURCE>' + u'РБК Дейли' + u'</SOURCE>\r\n' +\
          u'\t\t<DATE>' + date + u'</DATE>\r\n' +\
          u'\t\t<AUTHOR>' + author + u'</AUTHOR>\r\n' +\
          u'\t\t<TITLE>' + header + u'</TITLE>\r\n' +\
          u'\t\t<WORDCOUNT>' + words + u'</WORDCOUNT>\r\n' +\
          u'\t</METATEXT>\r\n\t<TEXT>\r\n\t\t' + article + u'\r\n' +\
          u'\t</TEXT>\r\n' + u'</DOCUMENT>'
    f_article = codecs.open(filename + u'.xml', u'w', u'utf-8-sig')
    f_article.write(content)
    f_article.close()

def folders(date):
## создает папки по ходу работы прораммы    
    os.chdir(thisPath)
    try:
        os.chdir(u'RBC Daily')
    except:
        os.mkdir(u'RBC Daily')
        os.chdir(u'RBC Daily')
    year = date[0:4]
    month = date[5:7]
    day = date[8:10]
    def fold(x):
        try:
            os.chdir(x)
        except:
            os.mkdir(x)
            os.chdir(x)
    fold(year)
    fold(month)
    fold(day)

def starter(calendar):
    print 1
    while True:
        start_date = '20140701'
        print 2
        if start_date in calendar:
            break
    num_words = 20000000
    date_list = []
    for i in reversed(calendar):
        print i
        if i == start_date:
            date_list.append(i)
            break
        else:
            date_list.append(i)
    try:
        os.chdir(u'RBC Daily')
    except:
        os.mkdir(u'RBC Daily')
        os.chdir(u'RBC Daily')
    allArticles = 0
    old_links = []
    # сохраняет все параграфы скачанных статей для проверки повторения
    words_total = 0
    meta_data = u'Имя файла;Объем;Раздел;Дата;Автор;' +\
                u'Заголовок;Ссылка\r\n' #сюда сохраняются данные
    for date_cal in reversed(date_list):
        date = date_cal[0:4] + u'/' + date_cal[4:6] + u'/' + date_cal[6:8]
        print date
        print words_total, u'wordforms loaded'
        links = get_links(date, old_links)
        old_links.extend(links)
        for link in links:
            if words_total > num_words:
                os.chdir(thisPath)
                os.chdir(u'RBC Daily')
                f = codecs.open(u'meta.csv', u'w', u'utf-8')
                f.write(meta_data)
                f.close()
                print unicode(allArticles) + u' статей загружено'
                return
            print u'http://rbcdaily.ru/' + link
            words, new_meta, numArticles = get_article(get_html(link),
                                                      link, date)
            words_total += words
            allArticles += numArticles
            meta_data += new_meta
    f = codecs.open(u'meta.txt', 'w', 'utf-8')
    f.write(meta_data)
    f.close()


starter(calendar())


print u'Done'


