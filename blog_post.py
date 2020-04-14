import os
import sys
import random
import requests
from base64 import b64encode
from datetime import datetime
from hashlib import sha1
from pathlib import Path
from chardet.universaldetector import UniversalDetector
import re
from time import sleep
import shutil
import glob
import json
from enum import Enum

# WSSEヘッダを作成する 
# 詳しい仕様: http://developer.hatena.ne.jp/ja/documents/auth/apis/wsse
def create_wsse_header(username, api_key):
    created = datetime.now().isoformat() + "Z"
    b_nonce = sha1(str(random.random()).encode()).digest()
    b_digest = sha1(b_nonce + created.encode() + api_key.encode()).digest()
    c = 'UsernameToken Username="{0}", PasswordDigest="{1}", Nonce="{2}", Created="{3}"'
    return c.format(username, b64encode(b_digest).decode(), b64encode(b_nonce).decode(), created)

# http://developer.hatena.ne.jp/ja/documents/blog/apis/atom に従ってxmlの形式にする
def translate_hatena_md_to_xml(title, category, body, username, draft):
    template = """\
<?xml version="1.0" encoding="utf-8"?>
<entry xmlns="http://www.w3.org/2005/Atom" xmlns:app="http://www.w3.org/2007/app">
    <title>{0}</title>
    <author><name>{1}</name></author> 
    <content type="text/x-markdown">
{2}
    </content>
    <updated>{3}</updated>
    <category term="{4}" />
    <app:control>
    <app:draft>{5}</app:draft>
    </app:control>
</entry>
    """
    now = datetime.now()
    dtime = str(now.year)+"""-"""+str(now.month)+"""-"""+str(now.day)+"""T"""+str(now.hour)+""":"""+str(now.minute)+""":"""+str(now.second)
    data = template.format(title, username, body, dtime, category, draft).encode()
    return data

# http://developer.hatena.ne.jp/ja/documents/blog/apis/atom にしたがってPOSTする
def post_hatena(data, headers, blogname, username):
    url = 'http://blog.hatena.ne.jp/{0}/{1}/atom/entry'.format(username, blogname)
    r = requests.post(url, data=data, headers=headers)

    try:
        r.raise_for_status()
    except:
        sys.stderr.write(f'Error!\nstatus_code: {r.status_code}\nmessage: {r.text}')

    start = r.text.find('<link rel="alternate" type="text/html" href="')
    end = r.text.find('"/>', start)
    length = len('<link rel="alternate" type="text/html" href="')
    return r.text[start+length:end]

# hatena photo lifeの仕様 http://developer.hatena.ne.jp/ja/documents/fotolife/apis/atom 
# PostURIの仕様に沿って画像からxmlを作成
def translate_photo_to_xml(filename):
    # filenameの内容をバイナリオブジェクトで返す
    files = Path(filename).read_bytes()
    # 拡張子extを取得
    root,ext = os.path.splitext(filename)
    ext = ext[1:]

    upload_data = b64encode(files)

    # {0} title {1} 画像の拡張子 {2} 画像をbase64エンコードしたもの
    template="""\
<entry xmlns="https://purl.org/atom/ns#">
  <title>{0}</title>
  <content mode="base64" type="image/{1}">{2}</content>
  <dc:subject>Hatena Blog</dc:subject>
</entry>"""

    # 画像のタイトルにパスを使うのこわすぎるのでタイトルはとりあえず適当につける
    return template.format('img_file', ext, upload_data.decode())

# 作成したWSSEヘッダとxmlを使って画像を投稿する
def post_photo(data, headers):
    url = 'https://f.hatena.ne.jp/atom/post/'
    r = requests.post(url, data=data, headers=headers)
 
    try:
        r.raise_for_status()
    except:
        sys.stderr.write(f'Error!\nstatus_code: {r.status_code}\nmessage: {r.text}')

    html_tag_len = len('<hatena:syntax>')
    img_tag_len = 37
    idx = r.text.find('<hatena:syntax>')
    return r.text[idx+html_tag_len:idx+html_tag_len+img_tag_len]

class status(Enum):
    main_body = 0
    inline_math = 1
    block_math = 2
    image_alt = 3
    image_path = 4

# markdownをはてな用に色々変換
def translate_markdown_to_hatena_md(textname, headers):   
    blog_title = ''
    blog_category = ''
    blog_body = ''
    row = 0
    state = status.main_body
    with open(textname) as f:
        for s in f.read().splitlines():
            # 1行目はタイトル，2行目はカテゴリ，3行目はスルー
            if row == 0:
                blog_title = s[2:]
                row += 1
                continue
            elif row == 1:
                blog_category = s[5:]
                row += 1
                continue
            elif row == 2:
                row += 1
                continue
            
            skip = False
            alt_text = ''
            photoname = ''
            for i in range(len(s)):
                # $$の2文字目とか1文字skipしたいとき
                if skip:
                    skip = False
                    continue
                # 状態遷移
                if state == status.main_body:
                    if i+1<len(s) and s[i:i+2] == '$$':
                        blog_body += '[tex: \displaystyle'
                        state = status.block_math
                        skip = True
                    elif s[i] == '$':
                        blog_body += '[tex:'
                        state = status.inline_math
                    elif i+1<len(s) and s[i:i+2] == '![':
                        state = status.image_alt
                        skip = True
                    elif s[i]=='<':
                        blog_body += '&lt;'
                    elif s[i]=='>':
                        if i==0:
                            blog_body += '>'
                        else:
                            blog_body += '&gt;'
                    elif s[i]=='[':
                        blog_body += '['
                    elif s[i]==']':
                        blog_body += ']'
                    elif s[i]=='&':
                        blog_body += '&amp;'
                    elif s[i]=='\"':
                        blog_body += '&quot;'
                    elif s[i]=='\'':
                        blog_body += '&apos;'
                    else:
                        blog_body += s[i]
                elif state == status.inline_math:
                    if s[i] == '$':
                        blog_body += ']'
                        state = status.main_body
                    elif s[i] == '^' or s[i] == '_':
                        blog_body += '\\' + s[i]
                    elif s[i]=='<':
                        blog_body += ' \lt '
                    elif s[i]=='>':
                        blog_body += ' \gt '
                    elif s[i]=='[':
                        blog_body += ' \lbrack '
                    elif s[i]==']':
                        blog_body += ' \\rbrack ' # \rがCRと認識されないように\\r
                    elif s[i]=='&':
                        blog_body += '&amp;'
                    elif s[i]=='\"':
                        blog_body += '&quot;'
                    elif s[i]=='\'':
                        blog_body += '&apos;'
                    else:
                        blog_body += s[i]
                elif state == status.block_math:
                    if i+1<len(s) and s[i:i+2] == '$$':
                        blog_body += ']'
                        state = status.main_body
                        skip = True
                    elif s[i] == '^' or s[i] == '_':
                        blog_body += '\\' + s[i]
                    elif s[i]=='<':
                        blog_body += ' \lt '
                    elif s[i]=='>':
                        blog_body += ' \gt '
                    elif s[i]=='[':
                        blog_body += ' \lbrack '
                    elif s[i]==']':
                        blog_body += ' \\rbrack ' # \rがCRと認識されないように\\r
                    elif s[i]=='&':
                        blog_body += '&amp;'
                    elif s[i]=='\"':
                        blog_body += '&quot;'
                    elif s[i]=='\'':
                        blog_body += '&apos;'
                    else:
                        blog_body += s[i]
                elif state == status.image_alt:
                    if i+1<len(s) and s[i:i+2]=='](':
                        state = status.image_path
                        skip = True
                    elif s[i]=='<':
                        alt_text += '&lt;'
                    elif s[i]=='>':
                        alt_text += '&gt;'
                    elif s[i]=='[':
                        alt_text += '['
                    elif s[i]==']':
                        alt_text += ']'
                    elif s[i]=='&':
                        alt_text += '&amp;'
                    elif s[i]=='\"':
                        alt_text += '&quot;'
                    elif s[i]=='\'':
                        alt_text += '&apos;'
                    else:
                        alt_text += s[i] 
                elif state == status.image_path:
                    if s[i]==')':
                        state = status.main_body
                        print("""{0} の投稿を開始""".format(photoname))
                        data = translate_photo_to_xml(photoname)
                        imageid = post_photo(data, headers)
                        print("""投稿に成功\n画像のidは[{0}:alt={1}]""".format(imageid, alt_text))
                        blog_body += """[{0}:alt={1}]""".format(imageid, alt_text)
                        photoname = ''
                        alt_text = ''
                    elif s[i]=='<':
                        photoname += '&lt;'
                    elif s[i]=='>':
                        photoname += '&gt;'
                    elif s[i]=='[':
                        photoname += '['
                    elif s[i]==']':
                        photoname += ']'
                    elif s[i]=='&':
                        photoname += '&amp;'
                    elif s[i]=='\"':
                        photoname += '&quot;'
                    elif s[i]=='\'':
                        photoname += '&apos;'
                    else:
                        photoname += s[i]                

            # 行末にspace2つを追加 ただし```cppのあとに入れるとsyntax highlightが消えるのでいれない
            if s[:6] == '```cpp':
                blog_body += '\n'
            else:
                blog_body += '  \n'
    
    return blog_title, blog_category, blog_body

def main():
    # api_key などを取得
    api_key_path = os.path.join(os.path.dirname(__file__), 'api_key.json')
    config = json.load(open(api_key_path, "r"))
    api_key = config["api_key"]
    blogname = config["blogname"]
    username = config["username"]

    # コマンドライン引数から 変換するmarkdown，下書き投稿か？ を取得
    draft = 'yes'
    if len(sys.argv) >= 2:
        # コマンドライン引数の一つ目に変換するmarkdownを指定する
        textname = sys.argv[1]
        if len(sys.argv) >= 3:
            if sys.argv[2] == '--nodraft':
                draft = 'no'
            else:
                print('error: 存在しないオプションが指定されています')
    else:
        print('error: markdownファイルを指定してください')

    print('markdown から xml への変換を開始')
    headers = {'X-WSSE': create_wsse_header(username, api_key)}
    blog_title, blog_category, blog_body = translate_markdown_to_hatena_md(textname, headers)
    blog_data = translate_hatena_md_to_xml(blog_title, blog_category, blog_body, username, draft)
    print('markdown から xml への変換に成功')
    print('はてなブログへの投稿を開始')
    manage_url = 'https://blog.hatena.ne.jp/{0}/{1}/entries'.format(username, blogname)
    entry_url = post_hatena(blog_data, headers, blogname, username)
    print('はてなブログへの投稿に成功')
    print('記事url：{1}\n記事の管理url：{0}'.format(manage_url, entry_url))

if __name__ == '__main__':
    main()