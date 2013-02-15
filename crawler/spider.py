#coding: utf8
from bs4 import BeautifulSoup
import urllib2
from urlparse import urljoin
import re
import time

start_urls = ["http://www.t-card.co.jp/"]


def decode_(text):
    codes = ['shift_jis', 'utf-8', 'euc_jp', 'cp932',
              'euc_jis_2004', 'euc_jisx0213', 'iso2022_jp',
              'iso2022_jp_1', 'iso2022_jp_2', 'iso2022_jp_2004',
              'iso2022_jp_3', 'iso2022_jp_ext', 'shift_jis_2004',
              'shift_jisx0213', 'utf_16', 'utf_16_be',
              'utf_16_le', 'utf_7', 'utf_8_sig', 'mbcs']

    for code in codes:
        try:
            return text.decode(code).encode('utf8')
        except:
            continue
    print 'can not decode utf8'
    return None


class Links():
    """Cac thao tac ve Link nhu tinh diem, kiem tra la cau hoi ...
    """
    def __init__(self):
        self.link_pattern_1_0 = re.compile('faq' + '|FAQ' + '|\W[qQ][aA]\W' +
                                            '|ques.?tion' + '|shitsumon' +
                                            '|\Wq\W?and\W?a\W' + '|\W[qQ][-_]*\d*' +
                                            '|[iI]nquiry'
                                           )
        self.link_pattern_0_5 = re.compile('support|sup')
        #
        #

        self.text_pattern_1_0 = re.compile(unicode('よくある質問' +
                                            '|よくあるご質問' + '|faq' + '|FAQ' +
                                            '|Q&A' + '|q&a',
                                            'utf8')
                                           )
        self.text_pattern_0_5 = re.compile(unicode('問い合わせ' + '|サポート' +
                                            '|support', 'utf8')
                                           )

        self.links = set()
        self.contents = dict()

        return

    def allowed_domains(self, domain):
        # part = domain.split('.')
        pass

    def score(self, link, text):
        if self.link_pattern_1_0.search(link) != None:
            return 1
        if self.text_pattern_1_0.search(text) != None:
            return 1
        if self.link_pattern_0_5.search(link) != None:
            return 0.5
        if self.text_pattern_0_5.search(text) != None:
            return 0.5
        return 0

    def isQuestion(self, link, text):
        # re compile
        self.question_pattern = re.compile(unicode('ですか' +
                                              '|？' +
                                              '|ますか' +
                                              # '|か。' +
                                              # '|い。' +
                                              # '|どこ' +
                                              '',
                                      'utf8'))

        self.question_likehood = re.compile(unicode('について', 'utf8'))

        if self.question_pattern.search(text) != None:
            return 1

        if self.question_likehood.search(text) != None:
            return 0.5

        if (self.link_pattern_0_5.search(link) != None
            or self.link_pattern_1_0.search(link) != None):
            return 0.5

        return 0

    def isChecked(self, new_link):
        return new_link in self.links

    def isDownloaded(self, new_link):
        return self.contents.has_key(new_link.split('#')[0])

    def add_link_and_content(self, new_link, new_content):
        self.links.add(new_link)
        self.contents[new_link.split('#')[0]] = new_content

    def add_link(self, new_link):
        self.links.add(new_link)

    def get_link_content(self, required_link):
        if self.isDownloaded(required_link):
            return self.contents[required_link.split('#')[0]]
        else:
            return None


links_controler = Links()


class FAQ_finder():
    def __init__(self, deadline):
        self.deadline = deadline
        self.result = []
        return

    def find(self, page):
        self.allowed_domains = re.compile('(' + ').*('.join(page.split('.'))[1:] + ')')
        pages = [page]

        while True:

            newpages = set()
            for page in pages:
                if time.time() > self.deadline:
                    break
                if self.allowed_domains.search(page) == None:
                    continue
                if not links_controler.isChecked(page):
                    if links_controler.isDownloaded(page):
                        links_controler.add_link(page)
                        c = links_controler.get_link_content(page)
                    else:
                        try:
                            c = urllib2.urlopen(page)
                        except:
                            print "Could not open %s" % str(page)
                            continue

                        links_controler.add_link_and_content(page, c)
                else:
                    continue
                soup = BeautifulSoup(decode_(c.read()))
                children_links = soup('a')

                for chil in children_links:
                    if ('href' in dict(chil.attrs)):
                        url = urljoin(page, chil['href'])
                        # if url.find("'") != -1:
                        #     continue

                        url = url.split('#')[0]

                        score_ = links_controler.score(url, chil.text)

                        if (url[0:4] == 'http' and (not links_controler.isChecked(url))
                                and (score_ > 0)):
                            # them cach link co cung vi tri vao
                            newpages.add(url)

                            #index[url] = link.text
                            if score_ == 1:
                                self.result.append((url, chil.text))

                        links_controler.add_link(url)

            if len(newpages) == 0 or len(self.result) > 0:
                return self.result
            else:
                print len(newpages)

            print len(newpages)
            pages = newpages


class QA_finder():
    def __init__(self, deadline):
        self.deadline = deadline
        self.links = set()
        self.result = []
        self.LIMIT_NUMBER_PAGES = 2000
        self.allowed_domains = []
        pass

    def find(self, pages, depth, domain):
        self.allowed_domains = re.compile('(' + ').*('.join(domain.split('.'))[1:] + ')')
        score_links = Links()
        # self.result = [(k, 'aaaaaa', 0.5) for k in pages]

        for i in range(depth):
            newpages = set()
            for page in pages:
                if time.time() > self.deadline:
                    break
                if self.allowed_domains.search(page) == None:
                    continue
                if links_controler.isDownloaded(page):
                    c = links_controler.get_link_content(page)
                else:
                    try:
                        c = urllib2.urlopen(page)
                    except:
                        print "Could not open %s" % page
                        continue

                links_controler.add_link_and_content(page, c)
                html = decode_(c.read())
                soup = BeautifulSoup(html)
                links_content = soup('a')

                for link in links_content:
                    if ('href' in dict(link.attrs)):
                        url = urljoin(page, link['href'])
                        if url.find("'") != -1:
                            continue

                        # url = url.split('#')[0]
                        score_ = score_links.isQuestion(url, link.text)

                        if ((self.allowed_domains.search(page) != None) and (url not in self.links)
                                and (score_ > 0)):
                            if len(newpages) < self.LIMIT_NUMBER_PAGES:
                                newpages.add(url)
                            if len(self.result) < self.LIMIT_NUMBER_PAGES:
                                self.result.append([url, link.text, score_, soup])

                        self.links.add(url)

            if len(newpages) == 0:
                return self.result
            else:
                pass
            pages = newpages
            print "pages =", len(pages), ",results =", len(self.result)

        return self.result


if __name__ == '__main__':

    faq_finder = FAQ_finder()
    faq = faq_finder.find(start_urls)
    print [k[0] for k in faq]
    qa_finder = QA_finder()
    print qa_finder.find([k[0] for k in faq])

    # links = Links()
    # print links.score('http://www.superhotel.co.jp/faq.html', '')
