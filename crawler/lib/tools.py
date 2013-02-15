#! c:/Python27/python.exe
# -*- coding: utf-8 -*-
import MeCab
from liblinearutil import *

from . import tagFeatureExtract


tagger = MeCab.Tagger('-Ochasen')


def compare(x, y):
    # ２つのノードを完全一致で比較する関数
    if x.attrs != y.attrs:
        return False
    tx = str(x).replace(' ', '')
    tx = tx.replace('\t', '')

    ty = str(y).replace(' ', '')
    ty = ty.replace('\t', '')

    if tx != ty:
        return False

    return True


def structcompare(x, y):
    #２つのノードを構造的で比較する関数
    if x.attrs.keys() != y.attrs.keys():
        return False
    if x.name != y.name:
        return False
    if x.parent.name != y.parent.name:
        return False

    return True


def mecabParse(text):
    text = text.strip()
    node = tagger.parseToNode(text.encode('utf8'))
    dummy = []
    mecabParse = []
    node = node.next  # BOS
    while node:
        if len(node.surface) > 0:
            dummy.append(node.surface)
        node = node.next

    length = len(dummy)

    for i in range(min(3, length / 2)):
        mecabParse.append(dummy[i])

    mecabParse.append('MID')  # 真ん中に立っている

    for i in range(min(3, length / 2), 0, -1):  # EOS
        mecabParse.append(dummy[length - i])

    return mecabParse


def is_the_only_string_within_a_tag(s):
    """
        Return True if this string is the only child of
       its parent tag.
    """
    return (s == s.parent.string)


def likehood(pos):
    # Tag だけ処理する
    if str(type(pos)) != "<class 'bs4.element.Tag'>":
        return False
    #　タグ<answer>とタグ<question>を使わない
    if pos.name == 'answer' or pos.name == 'question':
        return False

    # ノードがひとつしかない子を持っている、かつは、文字列を含まない場合、そのノードを測定しない
    # 例えば、<a><b>1234</b></a>のようなノードがあったら、タグ<a>を要らなく、<b>1234</b>のみ使う
    #if pos.text != pos.string:
    #    return False

    if (len(pos.contents) == 1 and
            str(type(pos.contents[0])) == "<class 'bs4.element.Tag'>"):
        return False
    #質問の中に、コンテンツが多すぎるとあまり良くない
    #if (len(pos.contents) > 3):
    #    return False

    #深さも制限する。質問文について深さを0;1に制限する
    #if len(pos.text) > 100:
    #    return False

    #ノードの長さも制限する。n＝５にする
    if len(pos.text) < 5:
        return False

    if tagFeatureExtract.depthMeasure(pos, 3, 5):
        return False

    return True
