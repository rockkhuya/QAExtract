#coding: utf8
""" FOR QUESTION
    Node's tag-features extraction.
    Return children-tags features and parent-tags features.
    method : tagFeatures(sub, depth) with:
        sub : parse tree
        depth: depth of childrens

    タグの属性も利用する。
    タグのclass, alt, id, nameのみ使う

"""
attrSet = [u'質問', u'件名', u'問い', u'誰何', u'問いかけ', u'問い合わせ',
           u'照会', u'聞く', u'自問', u'質疑', u'下問', u'尋ねる',
           u'q', u'Q', u'que', u'Que', u'QUE',
           u'question', u'Question', u'QUESTION',
           u'title', u'tit', u'Title']

attrName = ['class', 'alt', 'id', 'name']


def depthMeasure(sub, depth, limit):
    #ノードの深さを測定する関数
    #深さがdepthより大きい場合Trueを返す
    if limit == 0:
        return True
    if (depth == 0):
        return True
    if sub.text == sub.string:
        return False
    for ct in sub.contents:
        if str(type(ct)) == "<class 'bs4.element.Tag'>":
            if depthMeasure(ct, depth - 1, limit - 1):
                return True

    return False


def tagFeaturesTiny(sub, depth):
    #タグ素性を取る関数
    def regex(node):
        if node == None:
            return ''
        ans = '<' + node.name
        for attr in node.attrs:
            ans += ' ' + attr
        ans += '>'
        return ans

    def childrenTags(sub, depth):
        # sub tags
        # recursive method
        if sub == None:
            return

        if (depth <= 0):
            return

        if sub.text == sub.string:
            return
        for ct in sub.contents:
            # only tags.
            if str(type(ct)) == "<class 'bs4.element.Tag'>":
                PATH.append(regex(ct))
                # print out PATH
                dummy = ''
                for i in range(len(PATH)):
                    dummy += PATH[i]
                tagsSet.append('c-' + dummy)
                childrenTags(ct, depth - 1)
                del PATH[len(PATH) - 1]

    def parentTags(node):
        # parent tags
        if node == None:
            return

        dummy = ''
        loop = 2
        while node != None and node.name != 'html':
            dummy = regex(node) + dummy
            tagsSet.append('p-' + dummy)
            node = node.parent
            #new
            loop -= 1
            if loop == 0:
                break

    def attrFeatures(node, pos):
        if node == None:
            return

        flag = False
        for attr in attrName:
            if attr in node.attrs:
                for val in attrSet:
                    for x in node.attrs[attr]:
                        if x.find(val) > -1:
                            #tagの属性の中に質問の関係の単語がある
                            tagsSet.append('%s-<%s %s=1>' % (pos, node.name, attr))
                            return
                        flag = True

        if flag:
            tagsSet.append('%s-<%s %s=0>' % (pos, node.name, attr))

    tagsSet = []
    PATH = []
    #new
    depth = 1

    childrenTags(sub, depth)
    parentTags(sub)

    # p - parent
    # m - myself
    # c - child
    attrFeatures(sub.parent, 'p')
    attrFeatures(sub, 'm')
    for ch in sub.contents:
        if str(type(ch)) == "<class 'bs4.element.Tag'>":
            attrFeatures(ch, 'c')

    return tagsSet
