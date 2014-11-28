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
    return calendar

def get_html(url): # получает html страницы
    link = u'http://ria.ru/' + url
    try:
        response = urllib2.urlopen(link, timeout = 20)        
        html = response.read()
        html = html.decode(u'utf-8')
        html = html.replace(u'\n', u'').replace(u'\r', u'')
        response.close()
        return html
    except (IOError, httplib.HTTPException):
        return u''

def get_links(date, old_links):
    # создает список ссылок на статьи и запускает модуль
    # get_article (циклом по ссылкам за сутки)        
    links = []
    archive = u'archive/' + date # часть ссылки на страницу со статьями
    # за сутки
    links_before = re.findall(u'<a href="/(\\w+?/\\d+?/\\d+?\\.html)',
                              get_html(archive)) # массив ссылок за сутки
    for link in links_before:
        if date in link:
            if link not in old_links and link not in links:
                links.append(link)
    return links

def get_article(html, link, date, old_paragraphs): # вырезает статью и
    # метаданные из html.
    #Сохраняет статью в файл. Метаданные добавляет
    # в строку снаружи. Добавляет количество слов во внешнюю переменную
    def meta(text, filename, words_article, section, date_meta,
             link_meta):
        h = HTMLParser.HTMLParser()
        meta = h.unescape(text.group(1))
        meta = re.search(u'(?:([— А-ЯЁа-яё.()-]+)(?:,\\s*))?(\\d\\d?\\s[а-я]{2,5})?'+\
                         u'(?:[-\\s—]+)?([^,.]+)(?:,\\s*([^.,]+))?',
                         meta, flags = re.U) # ищет локацию, дату, сми, автора
        if meta != None:
            #пишет: Имя файла;Объем;Раздел;Регион;Дата + год;СМИ;Автор;Заголовок
            meta_data = filename + u'.xml' + u';' + unicode(len(words_article)) + u';' +\
                        section.group(1).replace(u';', u'') + u';' +\
                        unicode(meta.group(1)).replace(u';', u'') + u';' +\
                        date_meta.replace(u';', u'') + u';' +\
                        unicode(meta.group(3)).replace(u';', u'') + u';' +\
                        unicode(meta.group(4)).replace(u';', u'') + u';' +\
                        header.replace(u';', u'') +\
                        u';' + link_meta + u'\r\n'
        else:
            meta_data = filename + u'.xml' + u';' + unicode(len(words_article)) +\
                        u';' + section.group(1).replace(u';', u'') + u';' +\
                        u'none' + u';' + date_meta.replace(u';', u'') + u';' + u'none' +\
                        u';' + u'none' + u';' + header.replace(u';', u'') +\
                        u';' + link_meta.replace(u';', u'') + u'\r\n'
        return meta_data
    filename = re.sub(u'\\D', u'', link) # имя будущего файла
    #(завершающие цифры в ссылке)
    section = re.search(u'(\\w+?)/.+', link, flags = re.U)
    #вырезает из ссылки "раздел"
    date_meta = date[0:4] + u'.' + date[4:6] + u'.' + date[6:8]
    link_meta = u'http://ria.ru/' + link
    header = re.search(u'<meta property="og:title" content=(.+?)?>', html)
    # получение заголовка                   
    if header != None:
        header = header.group(1)
    else:
        header = u'none'
    text = re.search(u'id="article_full_text".+?<p><strong>([^<>/]+?)' +\
                     u'</strong>(.+?)<div class="clear">',
                     html, flags = re.U)
    if text != None:
        article = text.group(2)
        h = HTMLParser.HTMLParser()
        article = h.unescape(article)
        article = re.sub(u'^\\s+([\\w"\'])', u'<p>\\1', article, flags = re.U)
        ## меняет начальный пробел текста на тег <p>
        article = re.sub(u'(</p>)(<[^p])', u'\\1<p>\\2', article, flags = re.U)
        ## добавляет отсутствующие теги <p>
        article = re.sub(u'</?strong>', u'', article, flags = re.U)
        article = re.sub(u'<([^pha][^ ]*) ?[^>]*>.+?</\\1>', u'',
                         article, flags = re.U | re.DOTALL)
        ## удаляет теги и содержимое, кроме <p>, <h[1-9]>, <a href...>
        article = re.sub(u'([.!?] )<[as][^<]+>+</a>', u'\\1',
                         article, flags = re.U)
        ## удаляет ссылки, состоящие из целого предложения
        ##article = re.sub(u'<a[^<]+>>></a>', u'', article, flags = re.U)
        article = re.sub(u'</?a.*?>', u'', article, flags = re.U)
        article = re.sub(u'</?[^ph/].*?>', u'', article, flags = re.U | re.DOTALL)
        ## заголовки        
        subheaders = re.findall(u'<h[1-6].*?>(.*?)</h[1-6].*?>',
                                article, flags = re.U | re.DOTALL)
        article = re.sub(u'<h[1-6].*?>.*?</h[1-6].*?>', u'',
                         article, flags = re.U)
        article = re.sub(u'<p[^>]*></p>', u'', article, flags = re.U)
        ## иногда появляются пустые теги абзацев
        words_article = rxWords.findall(article)
        if len(words_article) >= 290:
            paragraphs = re.findall(u'<p[^>]*>([^<]+)</p>',
                                    article, flags = re.U)
            ## сохраняет абзацы для провеки на повторение в других статьях
            new_paragraphs = paragraphs
            for par in paragraphs:
                if par in old_paragraphs:
                    new_paragraphs.remove(par)
            if len(paragraphs) != len(new_paragraphs):
                return 0, new_paragraphs, u''
            ## article = re.sub(u'(</p>)(<p>)', u'\\1\\r\\n\\r\\n\\2',
            # article, flags = re.U)
            article = re.sub(u'</(?:[Pp]|[Hh][1-9])>', u'[[/p]]', article, flags=re.U)
            article = re.sub(u'<(?:[Pp]|[Hh][1-9])(?:>| [^>]*>)', u'[[p]]', article, flags = re.U)
            ## это и предыдущее проставляют пробел в начале предложения
            article = re.sub(u' >+', u'.', article, flags = re.U)
            article = re.sub(u'<[^>]*>', u'', article, flags = re.U)
            article = re.sub(u'\\s{2,}', u' ', article, flags = re.U)
            article = article.replace(u'&', u'&amp;').replace(u"'", u'&apos;')\
                      .replace(u'<', u'&lt;').replace(u'>', u'&gt;')
            header = header.replace(u'&', u'&amp;').replace(u"'", u'&apos;')\
                      .replace(u'<', u'&lt;').replace(u'>', u'&gt;')
            article = article.replace(u'[[/p]]', u'</p>\r\n')
            article = article.replace(u'[[p]]', u'<p>')
            if re.search(u'^[ \r\n]*<p>', article, flags=re.DOTALL) is None:
                article = u'<p>' + article
            if re.search(u'</p>[ \r\n]*$', article, flags=re.DOTALL) is None:
                article += u'</p>'
            article = re.sub(u'(?:<p>[ \r\n]*){2,}', u'', article, flags=re.U)
            words_article = article.split()
            folders(date)
            meta_data = meta(text, filename, words_article, section,
                             date_meta, link_meta)
            print u'статья загружена'
            xml(text, filename, link_meta, date_meta, header,
                unicode(len(words_article)), article)
            return len(words_article), paragraphs, meta_data, 1 
    return 0, [], u'', 0            

def xml(text, filename, link, date, header, words, article):
## создает и записывает xml
    print date
    h = HTMLParser.HTMLParser()
    meta = h.unescape(text.group(1))
    meta = re.search(u'(?:([— А-ЯЁ.-]+)(?:,\\s*))?(\\d\\d?\\s[а-я]{2,5})?' +\
                     u'(?:[-\\s—]+)?([^,.]+)(?:,\\s*([^.,]+))?',
                     meta, flags = re.U)
    content = u'<?xml version="1.0" encoding="utf-8"?>\r\n' +\
          u'<DOCUMENT>\r\n\t<METATEXT>\r\n\t\t<URL>' + link + u'</URL>\r\n' +\
          u'\t\t<SOURCE>' + unicode(meta.group(3)) + u'</SOURCE>\r\n' +\
          u'\t\t<DATE>' + date + u'</DATE>\r\n' +\
          u'\t\t<AUTHOR>' + unicode(meta.group(4)) + u'</AUTHOR>\r\n' +\
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
        os.chdir(u'РИА Новости')
    except:
        os.mkdir(u'РИА Новости')
        os.chdir(u'РИА Новости')
    year = date[0:4]
    month = date[4:6]
    day = date[6:8]
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
    while True:
        start_date = unicode(20140701)
        if start_date in calendar:
            break
        
    while True:
        num_words = unicode(20000000)
        if num_words.isnumeric() == True:
            num_words = int(num_words)
            break
    date_list = []
    for i in reversed(calendar):
        if i == start_date:
            date_list.append(i)
            break
        else:
            date_list.append(i)
    try:
        os.chdir(u'РИА Новости')
    except:
        os.mkdir(u'РИА Новости')
        os.chdir(u'РИА Новости')
    allArticles = 0
    old_links = []
    old_paragraphs = []
    # сохраняет все параграфы скачанных статей для проверки повторения
    words_total = 0
    meta_data = u'Имя файла;Объем;Раздел;Регион;Дата;СМИ;Автор;' +\
                u'Заголовок;Ссылка\r\n' #сюда сохраняются данные
    for date in reversed(date_list):
        print date
        print words_total, u'wordforms loaded'
        links = get_links(date, old_links)
        old_links.extend(links)
        for link in links:
            if words_total > num_words:
                os.chdir(thisPath)
                os.chdir(u'РИА Новости')
                f = codecs.open(u'meta.csv', u'w', u'utf-8')
                f.write(meta_data)
                f.close()
                print unicode(allArticles) + u' статей загружено'
                return
            print u'http://ria.ru/archive/' + link
            words, paragraphs, new_meta, numArticles = get_article(get_html(link),
                                                      link, date,
                                                      old_paragraphs)
            words_total += words
            old_paragraphs.extend(paragraphs)
            allArticles += numArticles
            meta_data += new_meta
    f = codecs.open(u'meta.txt', 'w', 'utf-8')
    f.write(meta_data)
    f.close()


starter(calendar())


print u'Done'
    





        


    

