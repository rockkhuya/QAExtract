#coding: utf8

# ↓↓↓　　自作のライブラリ　　↓↓↓
from judgment import qajudgment
from htmldiff import diff

judgment = qajudgment.Judgment()


class DiffTextContent():
    """　質問の間のテキストをまとめて、保持するクラス """
    def __init__(self):
        self.text = []
        self.soup = []

    def add(self, newSoup):
        """ 新たなノードを追加するメソッド """
        #　新たノードがテキストを含まないと無視する
        if (not hasattr(newSoup, 'text')) or len(newSoup.text) < 2:
            return

        # テキストに変換して、できるだけ大きなノードのみ保持する
        newText = unicode(newSoup)
        flag = True
        for t in self.text:
            if t.find(newText) != -1:
                flag = False
                break
        if flag:
            for t in self.text:
                if newText.find(t) != -1:
                    del t
            # 新たなノードだけど、保持しているノードの兄弟ではないとダメ
            if len(self.soup) > 0:
                if newSoup not in self.soup[0].next_siblings:
                    return
            # ノードのjavascriptを削除する
            javascript = newSoup.findAll(lambda pos: (pos.name == 'a') and ('href' in pos.attrs) and (pos.attrs['href'].startswith('javascript')))
            [j.extract() for j in javascript]

            self.text.append(newText)
            self.soup.append(newSoup)

    def getAll(self):
        return "\n".join(self.text)


class multiPageExtract():
    """ マルチのページに対し、QAを抽出するクラス
        シングルのページと違い、マルチのページの場合、urlを１個ずつ処理する。
        シングルの場合、クラスタずつ処理する。

    """
    def __init__(self):
        return

    def question_extract(self, page):
        """ ページの中に質問文を抽出するメソッド　
        """
        def tagsPath(node):
            # ノードのXPATHを返すメソッド
            if node.__class__.__name__ != 'NavigableString':
                return
            result = ''
            node = node.parent
            while node != None and node.name != 'html':
                result += node.name + '|'
                node = node.parent
            return result
        # 質問文を探す
        questionArray = page.findAll(text=lambda (pos): judgment.is_question_soup(pos))
        tags_of_question = dict()
        # 質問のXPATHを考察する。
        # 一番よく出現するXPATHを取る。
        for question in questionArray:
            t = tagsPath(question)
            tags_of_question[t] = tags_of_question.get(t, 0) + 1
        path = ""
        if len(tags_of_question) == 1:
            path = tags_of_question.keys()[0]
        elif len(tags_of_question) > 1:
            dummyArray = tags_of_question.values()
            dummyArray.sort()
            if (dummyArray[0] == dummyArray[1]):
                return []
            path = [p for p in tags_of_question.keys() if tags_of_question[p] == dummyArray[0]][0]
        # このXPATHのすべてのノードを出す
        questionArray = page.findAll(text=lambda pos: tagsPath(pos) == path)
        return questionArray

    def _extract(self, page):
        # 質問を探す
        questionArray = self.question_extract(page)
        # なければ
        if len(questionArray) < 1:
            return [], []
        #　初期化
        answerArray = []
        tempQuestion = []
        min_next_step = 1000
        step_number = 0
        # 質問の間のテキストを抽出する
        for index in range(len(questionArray) - 1):
            dummyArray = DiffTextContent()
            postion = questionArray[index]
            step_number = 0
            # できるだけ大きなノードを取りたい
            while True:
                step_number += 1
                postion = postion.next
                if unicode(postion).find(unicode(questionArray[index + 1])) != -1:
                    break
                if hasattr(postion, 'text'):
                    dummyArray.add(postion)
            # 解答を保持する
            tempQuestion.append(questionArray[index])
            answerArray.append(dummyArray.getAll())
            min_next_step = min(min_next_step, step_number)

        # 最後の質問を処理する
        dummyArray = DiffTextContent()
        postion = questionArray[-1]
        for i in range(min_next_step):
            if hasattr(postion, 'next'):
                postion = postion.next
                dummyArray.add(postion)
            else:
                break
        tempQuestion.append(questionArray[-1])
        answerArray.append(dummyArray.getAll())

        return tempQuestion, answerArray

    def diffAnswer(self, answerArray):
        """ 解答の間に比較して、同じ部分を削除する"""
        # 回答文の各ペアを差分する
        dummy = diff.HTMLDiff(answerArray)

        result = []
        for i in range(len(answerArray)):
            # 差分部分を取る
            temp = [k[1] for k in dummy.diff_html(i - 1, i) if k[0] == 1]
            # 差分をまとめる
            result.append('\n<br/>\n'.join(temp))
        return result

    def multiExtract(self, html):
        """ ページの中にQAを抽出するpublicメソッド　"""
        temp_question, temp_answer = self._extract(html)
        res = self.diffAnswer(temp_answer)

        results = []
        for index in range(len(temp_question)):
            results.append([unicode(temp_question[index]), res[index]])

        return results
