## 概要
markdownを用いてはてなブログへ投稿する  
```$ python3 blog_post.py entry.md```

## 主な機能
* CUIのコマンド一つで投稿できます
* 数式を通常のmarkdownのように書くことができます
  * ```$$a^2$$``` を ```[tex: \displaystyle a\^2]``` と変換します
* markdown中の画像をはてなフォトライフに投稿し、対応するidを本文中に挿入します 

## 使い方
### 初期設定
1. 適当なフォルダにclone
2. `sample_api_key.json` を `api_key.json` に改名し、api_keyなどに実際のものを書き込む

### 投稿の方法
1. markdownの形式で記事を書く
* 1行目はタイトル (例) ```# title```  
* 2行目はタグ (例) ```tag:tag_name```  
* 3行目は空行  
* 4行目以降は記事本文  
  * 見出し、数式、箇条書きなどは普段通りに書ける
  * 画像を挿入したい箇所には ```\img{image_path}``` と書く  
  通常のmarkdownと同様の記法で画像を書けるように今後修正したい
2. スクリプトを実行し投稿  
```$ python3 blog_post.py entry.md```  
デフォルトでは下書きへ記事が追加される設定です  
```--nodraft``` を ```entry.md``` のあとに追加することで実際に投稿されるようになります
