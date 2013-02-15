#coding: utf8
# ↓↓↓　　Pythonのライブラリ　　↓↓↓
# 正規表現のライブラリ
import re
# ↓↓↓　　第三者の公開ライブラリ　　↓↓↓
# 形態素解析のライブラリ
import MeCab


class Judgment():
    """ QAを判別するクラス
        また、QAの関係も測定する
    """
    def __init__(self):
        # 初期化する
        self.htmltag = re.compile(r'<.*?>')
        self.anketto = re.compile(u'(情報|解答|問題)?.*(役に|参考|解決)', re.UNICODE)
        self.tagger = MeCab.Tagger('-Ochasen')
        self.keywords = [u'ですか', u'？', u'ますか', u'たいのですが', u'教えてください', u'でしょうか']

    def mecabParse(self, text):
        """ mecabを使って、形態素解析する
            名詞と動詞のみ使う。他に無視する
        """
        text = text.strip()
        node = self.tagger.parseToNode(text.encode('utf8'))
        dummy = []
        node = node.next  # BOS
        while node:
            if node.feature.startswith(('名詞', '動詞')):
                dummy.append(node.surface)
            node = node.next
        return dummy

    def has_html_tag(self, text):
        # 正規表現を使って、HTMLタグがあるかないか確認する関数
        if self.htmltag.search(text):
            return True

    def has_question_keyword(self, text):
        # 質問キーワードを含むかどうか
        for keyword in self.keywords:
            if text.find(keyword) != -1:
                return True
        return False

    def is_question(self, text):
        """ ある文書が質問か否か判別する関数
            入力：普通のテキスト
            出力：True or False
        """
        # begin = text.find('>')
        # end = text.rfind('<')
        # if begin + 1 < end:
        #     text = text[begin: end]
        # タイトルには'|'文字がよく出現する。タイトルは質問とまちがいやすいですので、'|'文字を含んだら、無視する
        if text.find(u'|') > -1 or text.find(u'｜') > -1:
            return False
        # 質問文は、HTMLタグがなく、質問キーワードを含む
        if (not self.has_html_tag(text)) and self.has_question_keyword(text):
            return True
        else:
            return False

    def is_question_soup(self, soup):
        """ 質問か否か判別する関数
            入力：BeautifulSoupのNavigableString（パーザで得られた結果）
            出力：True or False
        """
        # 普通のテキストに変換する
        text = unicode(soup)
        # テキストのタグを取る
        parent = soup.parent
        # テキストは質問か
        if not self.is_question(text):
            return False
        # タグは<a>の場合、属性hrefがリンクであったら、質問ではない
        if parent.name == 'a' and ('href' in parent.attrs):
            if parent.attrs['href'] != None:
                if not parent.attrs['href'].startswith('javascript'):
                    return False
        # タグは<li>であったら、質問ではない
        if parent.name == 'li':
            return False
        # アンケートのしつもんか否か。アンケートであったら、無視する
        if self.anketto.search(text):
            return False
        # すべての条件を満たしたら、質問だと判別する
        return True

    # def relationScore(self, text1, text2):
    #     if self.has_question_keyword(text2):
    #         return 0.0
    #     q_mono = self.mecabParse(text1)
    #     a_mono = self.mecabParse(text2)
    #     count = 0
    #     for word in q_mono:
    #         count += a_mono.count(word)
    #     return count * 1.0 / min(len(q_mono), len(a_mono))

    def is_answer(self, question, answer):
        """　解答か否か判別する関数
            入力:BeautifulSoup
        """
        # 解答は、質問キーワードを含まない
        if self.has_question_keyword(answer):
            return False
        # 質問文と回答文を形態素解析する
        q_mono = self.mecabParse(question)
        a_mono = self.mecabParse(answer)
        count = 0
        # 共通の単語を数える
        for word in q_mono:
            count += a_mono.count(word)
        # 解答はドット（。）を含まなければならない
        dot_numbers = answer.count(u'。')
        # 共通単語が２個い所、ドットが１個以上あったら。
        return count >= 2 and dot_numbers >= 1

    def has_question_and_answer(self, texts):
        """ 得られた差分の結果の中に、質問文と回答文を探す関数
            QAを見つけたら、QAの番号を返す。
            入力：差分のリスト
            QAを１個だけ抽出する。
        """
        result = []
        for i in range(len(texts)):
            # 質問文を探す
            if self.is_question(texts[i]):
                for j in range(i + 1, len(texts)):
                    # 解答文を探す
                    if self.is_answer(texts[i], texts[j]):
                        return [(i, j)]
                        # result.append((i, j))

        return result
