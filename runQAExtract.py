#coding: utf8
# パラメータをパーザするためPythonのライブラリ。
import getopt
import sys
import codecs
from QAExtract import QAExtract

time_limit = 600
depth = 3
site = ''
output = ''


def usage():
    print u"QAExtractの使い方："
    print u"    python runQAExtract.py -s site -t time_limit -d depth -o output"


def opt():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "s:t:d:o:")
    except getopt.GetoptError:
        # ヘルプメッセージを出力して終了
        print u"Error!"
        usage()
        sys.exit(2)

    global time_limit
    global depth
    global site
    global output

    for o, a in opts:
        if o == '-s':
            site = a
            if not (site.startswith('http://') or site.startswith('https://')):
                site = 'http://' + site
            postion = -1
            for i in range(3):
                postion = site.find('/', postion + 1)
            if site.startswith('http://'):
                output = site[7:postion] + '.htm'
            if site.startswith('https://'):
                output = site[8:postion] + '.htm'

        if o == '-t':
            time_limit = int(a)
        if o == '-d':
            depth = int(a)
        if o == '-o':
            output = a

    if site == '':
        print u'サイトを設定ください。'
        usage()
        sys.exit(2)

    if '-t' not in opts:
        print u'時間制限を設定しません。デフォルトは600秒です。'
    if '-d' not in opts:
        print u'クローラの深さを設定しません。デフォルトは3です。'
    if '-o' not in opts:
        print u'出力ファイル名を設定しません。デフォルトは%sです。' % output


def main():
    extractor = QAExtract(time_limit)
    extractor.crawl(site, depth=depth)
    results = extractor.extractQA()
    fo = codecs.open(output, 'w', 'utf8')

    downloaded_files = extractor.get_number_of_downloaded_files()
    crawling_time = extractor.get_crawling_time()
    extract_time = extractor.get_extract_time()

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


if __name__ == "__main__":
    opt()
    main()
