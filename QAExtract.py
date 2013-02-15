#coding: utf8
# ↓↓↓　　pythonのライブラリ　　↓↓↓
import codecs
import urllib2
from time import clock, time
import re
import htmlentitydefs
#　↓↓↓　　第三者の公開ライブラリ　　↓↓↓
#　HTMLパーザするためのライブラリ
from bs4 import BeautifulSoup, Comment
#　↓↓↓　　自作　　↓↓↓
from crawler import spider
from htmldiff import diff
from judgment import qajudgment
import multiExtract as ME


class QAExtract():
    """
    QAExtractクラスはサイトのQAを抽出するクラス
    QAExtractの処理は：
        定義:    extractor = QAExtract(time_limit)
                    time_limitは制限時間
        クローラ：   extractor.crawl(site, depth)
                    siteはトップページのurl
                    depthは深さ
        結果:    result = extractor.extractQA()
                    resultは辞書で、キーが質問文、値は解答文
    """
    def __init__(self, time_limit):
        # 初期化
        self.data = []
        self.single_data = []
        self.multi_data = []
        self.extract_time = 0
        self.crawling_time = 0
        self.deadline = time() + time_limit
        self.multiExtract = ME.multiPageExtract()
        self.judgment = qajudgment.Judgment()

    def crawl(self, site, depth):
        """ siteをクローラする
            結果はリンクのurlとして、self.qa_contentに保持する。
        """
        # FAQを探す
        faq_finder = spider.FAQ_finder(self.deadline)
        faq = faq_finder.find(site)
        # QAページを探す
        qa_finder = spider.QA_finder(self.deadline)
        self.qa_content = qa_finder.find([k[0] for k in faq], depth=depth, domain=site)
        self.site = site

    def _singleExtract_main_(self):
        """ QAを1個しか含まないサイトを処理する
            private関数
            入力はself.dataから読み込んで、含まれたQAを渡す
        """
        # 差分クラスを定義して、self.dataから読み込む
        # diffライブラリを参照する
        template = diff.HTMLDiff(self.data)
        #　クラスタリングを行なって、クラスタを渡す
        template.cluster(len(self.data) / 2)
        groups = template.get_groups()
        # print groups

        questionArray = set()
        results = []
        # クラスタを1つグループずつ処理する
        for group in groups:
            # print "Group", group
            for index in range(len(group)):
                # 二つのページを比較する
                diffs = template.diff_html(group[index], group[index - 1])
                # 一方のページの差分だけ処理する
                dummy = [d for d in diffs if d[0] == -1]
                # 差分の中に質問文と回答文を探す
                result = self.judgment.has_question_and_answer([d[1] for d in dummy])
                # 重複の質問を抜ける
                for r in result:
                    if dummy[r[0]] not in questionArray:
                        results.append([dummy[r[0]], dummy[r[1]]])
                        questionArray.add(dummy[r[0]])

        print "The number of QA is", len(questionArray)
        return results

    def _multiExtract_main_(self):
        """ 複数のQAを含むサイトを処理する
            private関数
            入力はself.dataから読み込んで、含まれたQAを渡す
        """
        results = []
        # ページを１個ずつ処理する
        # multiExtractライブラリを参照する
        for d in self.multi_data:
            results += self.multiExtract.multiExtract(d)
        print "Extracted ", len(results), " QAs."
        return results

    def _single_multi_QASite(self):
        """ データの中に、シングルのページとマルチのページを数え、シングルのデータとマルチのデータを分ける
            入力：self.dataから
            出力:self.single_dataとself.multi_dataに分ける
        """
        # シングルのデータ。シングルのページを保持する
        self.single_data = []
        # マルチのデータ。
        self.multi_data = []

        number_of_multi_pages = 0
        number_of_single_pages = 0

        for page in self.data:
            # ページの中に質問文を数える
            questionArray = list(set(page.findAll(text=lambda (pos): self.judgment.is_question_soup(pos))))
            # 質問文は２個以上であったら、マルチのページと判断する
            if len(questionArray) >= 2:
                self.multi_data.append(page)
                number_of_multi_pages += 1
            #　質問文は１個しかないの場合
            #　質問文はなければ無視する
            elif len(questionArray) == 1:
                self.single_data.append(page)
                number_of_single_pages += 1

        print "Number of multi pages: ", number_of_multi_pages
        print "Number of single pages:", number_of_single_pages

    def _extractFromURL(self, urlSet, domain):
        """　urlのリストからページのコンテンツをダウンロードして、QAを抽出する。
            入力はurlのリストで、
            出力はQAのリストです。
        """
        allowed_domain = re.compile('(' + ').*('.join(domain.split('.'))[1:] + ')')
        start = clock()
        self.data = []

        # リンクを１つずつ
        for i in range(len(urlSet)):
            if time() > self.deadline:
                break
            # not from allowed domain
            if allowed_domain.search(urlSet[i]) == None:
                continue
            #　リンクを開く。例外に開けない場合、無視する。
            try:
                text = urllib2.urlopen(urlSet[i]).read()
            except:
                text = None
                print "Error!", urlSet[i]
            # urlが開ける場合
            if text != None and len(text) > 0:
                # HTMLをパーザしてみる。できない場合無視する
                try:
                    soup = BeautifulSoup(text)
                except:
                    continue
                # コメントを削除する
                comments = soup.findAll(text=lambda text: isinstance(text, Comment))
                [comment.extract() for comment in comments]
                # Javascriptを削除する
                scripts = soup.findAll("script")
                [script.extract() for script in scripts]
                # self.dataに保持する
                self.data.append(soup)
            else:
                print "Cant not download ", urlSet[i]

        self.crawling_time += clock() - start
        start = clock()
        # シングルのページとマルチのページを判別する
        print "======================================"
        print "======================================"
        self._single_multi_QASite()
        # マルチのページのモジュールを実行する
        print "****  Multi pages  ****"
        if len(self.multi_data) > len(self.single_data) / 2:
            results = self._multiExtract_main_()
        # シングルのページは５つ以上であったら、シングルのページのモジュールを実行する
        if len(self.single_data) > len(self.multi_data) / 2:
            print "****  Single pages  ****"
            results += self._singleExtract_main_()
        # 結果を整理する
        dummy = {}
        for result in results:
            if len(result[1]) > 2 and (result[0] not in dummy):
                dummy[result[0]] = result[1]
        # 抽出の時間を計算する
        self.extract_time += clock() - start

        return dummy

    def _unescape(self, text):
        """ &nbsp; &gt;　などのHTMLエンティティを処理する
            入力：テキスト
            出力：修正したテキスト
        """
        def fixup(m):
            text = m.group(0)
            if text[:2] == "&#":
                # character reference
                try:
                    if text[:3] == "&#x":
                        return unichr(int(text[3:-1], 16))
                    else:
                        return unichr(int(text[2:-1]))
                except ValueError:
                    pass
            else:
                # named entity
                try:
                    text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
                except KeyError:
                    pass
            return text
        return re.sub("&#?\w+;", fixup, text)

    def extractQA(self):
        """ 得られたクローラの結果から１００個のurlずつQAを抽出する。
            public関数
            入力：クローラの結果(self.crawl()関数を先に呼ばなければならい)
            出力：dict型のQAを返す。
                キーは質問文、値は回答文
        """
        results = {}
        # urlを１００個ずつ処理する
        for i in range(len(self.qa_content)):
            if (i + 1) % 100 == 0:
                results.update(self._extractFromURL([q[0] for q in self.qa_content[i - 99:i + 1]], self.site))
        # 残っているurl
        if (len(self.qa_content)) % 100 != 0:
            results.update(self._extractFromURL([q[0] for q in self.qa_content[i - (i % 100): i + 1]], self.site))
        #　重複と短い質問を削除する
        removed_question = [r for r in results if len(r.strip()) < 5]
        [results.pop(r, 0) for r in removed_question]
        # HTMLエンティティを修正する
        for r in results:
            results[r] = self._unescape(results[r])
        return results

    def get_number_of_downloaded_files(self):
        return len(self.qa_content)

    def get_crawling_time(self):
        return self.crawling_time

    def get_extract_time(self):
        return self.extract_time

# テスト
if __name__ == '__main__':
    fi = open('urls.txt', 'r')
    # toppages = ["http://www.cocacola.co.jp/"]
    toppages = [line.strip() for line in fi]
    result_log = open('results.csv', 'w')
    result_log.writelines('Name,URL,Time of crawling,Time of extracting,Number of results,Number of downloaded\n')
    result_log.close()
    extracter = QAExtract(600)
    all_crawling_time = 0
    all_extract_time = 0

    for site in toppages:
        result_log = open('results.csv', 'a')
        print ("*" * 20 + "\n") * 2
        print site
        print ("*" * 20 + "\n") * 2

        start = clock()
        extracter.crawl(site, depth=3)
        results = extracter.extractQA()
        postion = 0
        for i in range(3):
            postion = site.find('/', postion + 1)
        site = site[7:postion]
        fo = codecs.open('./results/' + site + '.htm', 'w', 'utf8')

        downloaded_files = extracter.get_number_of_downloaded_files()
        crawling_time = extracter.get_crawling_time()
        extract_time = extracter.get_extract_time()

        print site
        print 'Number of downloaded files: ', downloaded_files
        print 'Crawling time: ', crawling_time
        print 'Extract time : ', extract_time
        print 'QA results   : ', len(results)

        fo.writelines(site + '\n')
        fo.writelines('Number of downloaded files: ' + str(downloaded_files) + '\n')
        fo.writelines('Crawling time: ' + str(crawling_time) + '\n')
        fo.writelines('Extract time : ' + str(extract_time) + '\n')
        fo.writelines('QA results   : ' + str(len(results)) + '\n')

        for r in results:
            fo.writelines('Question : ' + r.strip() + '\n')
            fo.writelines('Answer   : ' + results[r] + '\n\n\n')

        result_log.writelines(' , %s,%s, %s, %s, %s\n' % (site,
                                                         str(crawling_time),
                                                         str(extract_time),
                                                         str(len(results)),
                                                         str(downloaded_files)))

        result_log.close()

        all_crawling_time += crawling_time
        all_extract_time += extract_time
        crawling_time = 0
        extract_time = 0
