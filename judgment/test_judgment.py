#coding: utf8
import qajudgment as judgment
from bs4 import BeautifulSoup, Comment

question = """
<a name="more"></a>

<!--
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns:trackback="http://madskills.com/public/xml/rss/module/trackback/"
         xmlns:dc="http://purl.org/dc/elements/1.1/">
<rdf:Description
rdf:about="http://www.hikaritv.net/support/faq/answer/?entry_id=10063"
    trackback:ping="http://www.hikaritv.net/support/faq/tb.php/10063"
    dc:title="「ひかりＴＶ」はパソコンでも視聴できますか？"
    dc:identifier="http://www.hikaritv.net/support/faq/answer/?entry_id=10063"
    dc:subject="その他"
    dc:description="「ひかりＴＶ」はチューナー機能対応PCを除いて、パソコンでのご視聴はできません。&lt;br&gt;            ひかりＴＶチューナー機能対応PCについては&lt;a href=&quot;/iptv/&quot;&gt;こちら&lt;/a&gt;（PCページ）をご覧ください。..."
    dc:creator="answer"
    dc:date="2000-12-29T13:32:28+09:00"/ >
</rdf:RDF>
-->
        </div></div>

"""

page = BeautifulSoup(question)
comments = page.findAll(text=lambda text: isinstance(text, Comment))
[comment.extract() for comment in comments]
questionArray = list(set(page.findAll(text=lambda (pos): judgment.is_question_soup(pos))))

postion = page.findAll(text=True)[0]

print len(questionArray)
print questionArray
