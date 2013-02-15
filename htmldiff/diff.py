#coding: utf8
# ↓↓↓　pythonのライブラリ　↓↓↓
from time import clock
import re

# ↓↓↓ 第三者の公開ライブラリ ↓↓↓
# クラスタリング手法のライブラリ
from sklearn.cluster import DBSCAN
# sklearnライブラリの要求
from numpy import array, argwhere
# HTMLパーザのライブラリ
from bs4 import Comment
# 文字列の差分をするライブラリ。元々はGoogleのだが、自分が目的に応じて書き直した
from google.diff_match_patch import diff_match_patch

lineWithMultiTags = re.compile(u'>\s*<')


def cleanupHTML(soup):
    # if Soup is plain text
    if soup.__class__.__name__ == 'unicode' or soup.__class__.__name__ == 'str':
        return re.sub(lineWithMultiTags, '>\n<', unicode(soup))

    # Soup is BeautifulSoup
    # Remove comments
    comments = soup.findAll(text=lambda text: isinstance(text, Comment))
    [comment.extract() for comment in comments]

    if hasattr(soup, 'body') and soup.body != None:
        soup = soup.body
        return re.sub(lineWithMultiTags, '>\n<', unicode(soup))
    else:
        return unicode(soup.prettify())


class HTMLDiff():
    """
        HTML差分を抽出するクラス
        クラスタリング手法も提供する。
    """
    def __init__(self, htmlset):
        start = clock()
        self.DIFF_DELETE = -1
        self.DIFF_INSERT = 1
        self.DIFF_EQUAL = 0

        self.htmls = htmlset
        self.groups = []
        self.size = len(htmlset)
        self.noise = []
        self.lineArray = []
        self.zip = []
        self.dmp = diff_match_patch()
        self.lineHash = {}
        self.lineArray.append('')

        def diff_linesToCharsMunge(text):
            """ １行を１文字に変換するハッシュメソッド """
            chars = []
            # Walk the text, pulling out a substring for each line.
            # text.split('\n') would would temporarily double our memory footprint.
            # Modifying text would create many large strings to garbage collect.
            lineStart = 0
            lineEnd = -1
            while lineEnd < len(text) - 1:
                lineEnd = text.find('\n', lineStart)
                if lineEnd == -1:
                    lineEnd = len(text) - 1
                line = text[lineStart:lineEnd + 1]
                lineStart = lineEnd + 1
                if line in self.lineHash:
                    chars.append(unichr(self.lineHash[line]))
                else:
                    self.lineArray.append(line)
                    self.lineHash[line] = len(self.lineArray) - 1
                    chars.append(unichr(len(self.lineArray) - 1))
            return "".join(chars)

        # すべてのHTMLソースがハッシュ関数で文字列に変換する
        for h in self.htmls:
            self.zip.append(diff_linesToCharsMunge(cleanupHTML(h)))
        # print 'Init time : ', clock() - start

    def diff_charsToLines(self, diffs):
        """ 文字列から元の行に逆変換する """
        for x in xrange(len(diffs)):
            text = []
            for char in diffs[x][1]:
                text.append(self.lineArray[ord(char)])
            diffs[x] = (diffs[x][0], "".join(text))
        return diffs

    def _diff_str(self, A, B):
        """ 二つの文字列の差分を返す　"""
        diffs = self.dmp.diff_main(self.zip[A], self.zip[B])
        # Rediff any replacement blocks
        diffs.append((self.DIFF_EQUAL, ''))
        pointer = 0
        count_delete = 0
        count_insert = 0
        text_delete = ''
        text_insert = ''
        while pointer < len(diffs):
            if diffs[pointer][0] == self.DIFF_INSERT:
                count_insert += 1
                text_insert += diffs[pointer][1]
            elif diffs[pointer][0] == self.DIFF_DELETE:
                count_delete += 1
                text_delete += diffs[pointer][1]
            elif diffs[pointer][0] == self.DIFF_EQUAL:
                # Upon reaching an equality, check for prior redundancies.
                if count_delete >= 1 and count_insert >= 1:
                # Delete the offending records and add the merged ones.
                    a = [(self.DIFF_INSERT, text_insert), (self.DIFF_DELETE, text_delete)]
                    diffs[pointer - count_delete - count_insert:pointer] = a
                    pointer = pointer - count_delete - count_insert + len(a)
                count_insert = 0
                count_delete = 0
                text_delete = ''
                text_insert = ''
            pointer += 1

        diffs.pop()  # Remove the dummy entry at the end.
        return diffs

    def diff_score(self, A, B):
        """ 二つの文字列の差分スコアを返す　"""
        lineMode = self._diff_str(A, B)
        return len(lineMode)

    def diff_html(self, A, B):
        """ ハッシュの二つの文字列の差分を抽出して、元の行に変換して返す　"""
        lineMode = self._diff_str(A, B)
        lineMode = self.diff_charsToLines(lineMode)
        # Edit and output texts that are deleted
        diff = []
        for d in lineMode:
            temp = d[1].strip()
            if d[0] != 0 and ((d[0], temp) not in diff):
                diff.append((d[0], temp))
        return diff

    def cluster(self, Eps=10):
        """ クラスタリングのメソッド """
        weightArray = [[0 for x in range(self.size)] for y in range(self.size)]
        start = clock()
        # Weight array
        for i in range(self.size):
            for j in range(i + 1, self.size):
                weightArray[i][j] = self.diff_score(i, j)
                weightArray[j][i] = weightArray[i][j]
        print "Diff Array : ", clock() - start
        start = clock()
        # DBSCAN clustering
        numpy_type = array(weightArray)
        db = DBSCAN(eps=Eps, min_samples=2).fit(numpy_type)
        print "DBSCAN : ", clock() - start
        # return groups
        labels = db.labels_
        for k in set(labels):
            class_numbers = [index[0] for index in argwhere(labels == k)]
            if k == -1:
                self.noise = class_numbers
            else:
                self.groups.append(class_numbers)

    def get_groups(self):
        return self.groups

    def get_noise(self):
        return self.noise

    def get_zip(self):
        return self.zip

    def get_lineHash(self):
        return self.lineHash

    def get_lineArray(self):
        return self.lineArray
