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
  見出し、数式、箇条書き、画像など通常のmarkdownと同様の記法で書けるはず
2. スクリプトを実行し投稿  
```$ python3 blog_post.py entry.md```  
デフォルトでは下書きへ記事が追加される設定です  
```--nodraft``` を ```entry.md``` のあとに追加することで実際に投稿されるようになります

## 例
```
# Educational Codeforces Round 2 D. Area of Two Circles' Intersection
tag: codeforces

[問題ページ](https://codeforces.com/contest/600/problem/D)

まず2円が離れているか外接の関係にある場合、答えは0です。2円が内包か内接の関係にある場合、答えは $\pi \min(r_1, r_2)^2$ です。2円が2点で交差する場合について、2通りに場合分けを行います。

* 交点からなる線分から見て、$(x_1,y_1),(x_2,y_2)$ が反対側にある
扇形ABCから三角形ABCを引くことで、各円について斜線部の領域を求めます。
![2円の共通面積](type1-1.png)
* 交点からなる線分から見て、$(x_1,y_1),(x_2,y_2)$ が同じ側にある
半径が大きい方の円については先程と同様に、扇形から三角形を引きます。

扇形と三角形の面積を求めます。扇形については $r^2 \angle BAC / 2$、三角形については $r^2 \sin \angle BAC / 2$ で求められます。角度については内積を求める式 $\bm{a} \cdot \bm{b} = |\bm{a}||\bm{b}|\cos \angle BAC$ より $\angle BAC = \arccos (\bm{a} \cdot \bm{b}) / |\bm{a}||\bm{b}|$ と求められます。

```cpp
#include <bits/stdc++.h>
using namespace std;
using ll = long long;
using PII = pair<ll, ll>;
#define FOR(i, a, n) for (ll i = (ll)a; i < (ll)n; ++i)
#define REP(i, n) FOR(i, 0, n)
// 以下略
```  
```
