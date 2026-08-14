---
ID: NOTE-40
Project: devops
created_at: '2026-07-12'
tag:
- document
title: 'macOS: tmux 内で "Operation not permitted"(~/Documents アクセス拒否)'
updated_at: '2026-07-12'
---

# macOS: tmux 内で "Operation not permitted"(~/Documents アクセス拒否)

tmux 内で Claude Code / シェルを動かすと、`~/Documents` 配下(このリポジトリや dotfiles)への
アクセスが **`Operation not permitted` (EPERM)** で拒否される事象と、その原因・恒久対処。

## 症状

- tmux 内で `ls ~/Documents` / ファイル読み書きが `Operation not permitted` になる。
- `~/.zshrc`・`/tmp`・`~/.claude/settings.json` など **保護フォルダ外は正常**。
- `~/.claude/skills`(→ `~/Documents/workspace/dotfiles/.claude/skills` への symlink)も巻き添えで拒否され、
  そこに置いた skill スクリプト(例 `md2joifup.py`)が全滅する。
- `ls -l <file>`(stat)は通るのに `open` / `readdir` だけ落ちる、という TCC 特有の挙動。
- **tmux の外(素の端末)では再現しない。tmux 内でだけ・かつ「時々」起きる。**

## 原因(root cause)

macOS の **TCC (Transparency, Consent, and Control)** が `~/Documents` `~/Desktop` `~/Downloads` 等の
保護フォルダへのアクセスを **「責任プロセス (responsible process)」単位**で許可制御している。

- tmux の**サーバは daemon 化して launchd (PID 1) に再ペアレント**される。
  検証時: tmux server PID 3716 の親 = launchd。
- そのため tmux 内の全プロセス(シェル・Claude・`ls` 等)の TCC 責任プロセスは、
  起動元の端末アプリ(iTerm2 / Terminal 等)ではなく **tmux サーバのバイナリ自身**になる。
- tmux バイナリに Documents / Full Disk Access が無ければ、tmux 内からの `~/Documents` は全て EPERM。
- → **端末アプリに FDA を付けても、daemon 化した tmux サーバ配下には効かない**のが要点。

環境(検証時):
- macOS 15.7.3 (Sequoia) / tmux 3.6a
- tmux 実体: `/opt/homebrew/bin/tmux` → `/opt/homebrew/Cellar/tmux/3.6a/bin/tmux`

### なぜ「時々」なのか

FDA の許可は**バイナリの実体パス**に紐づく。`/opt/homebrew/bin/tmux` は
`…/Cellar/tmux/<version>/bin/tmux` という**バージョン入り実体パス**へ解決される。
`brew upgrade tmux` でバージョンが上がると実体パスが変わり、**以前付与した FDA が旧パスに
取り残されて無効化**→ 再発する。加えて、tmux サーバが「いつ・どの文脈で起動したか」
(権限付与の前/後、ログインシェル経由か launchd 経由か)でも責任プロセスの解決が変わり、
再現性が「時々」になる。

## 対処

### A. すぐ直す(このマシンの tmux に FDA を付与)

1. System Settings → Privacy & Security → **Full Disk Access**。
2. `+` を押し、ファイル選択ダイアログで **⌘⇧G**(パス直接入力)→ 実体パスを入力:
   `/opt/homebrew/Cellar/tmux/3.6a/bin/tmux`
   (`/opt/homebrew/bin/tmux` を選んでも macOS が実体=Cellar パスに解決して登録する。
    確実性のため実体パスを直接指定するのが吉)
3. 追加した tmux をトグル **ON**。
4. **tmux サーバを入れ替える**(既存サーバは旧 TCC 文脈のまま):
   ```sh
   tmux kill-server      # 注意: tmux 内の全セッション(この Claude セッション含む)が落ちる
   ```
   端末から tmux を起動し直すと、新サーバが FDA 付きで立ち上がる。
5. 検証: tmux 内で `ls ~/Documents` が EPERM を出さなければ解消。

> 補足(実測 / macOS 15.7.3 + tmux 3.6a): tmux バイナリへの FDA 付与のみで **kill-server 不要・
> 既存セッションを保ったまま即座に反映**された(TCC が次回アクセスで再評価)。効かない場合のみ
> 手順 4 の kill-server で新サーバを立て直す。

### B. 恒久的に安定させる(いずれか)

- **B1. `brew upgrade tmux` の度に A を再実行**(バージョン入りパスが変わるため)。最も手軽だが手動。
- **B2. 作業ツリーを保護フォルダの外へ**:`~/Documents/workspace/…` → `~/workspace/…` 等へ移動。
  `~/Documents` 外は TCC 対象外なので **本事象が原理的に起きない**(cmux #2866 でも推奨の回避策)。
  Joifup の場合は daemon の workspace_root と各 symlink の張り替えが伴う。
- **B3. 端末アプリに FDA + tmux を端末の子として使う運用**は、daemon 化により責任プロセスが
  tmux に落ちるため**単独では不安定**。B1/B2 を推奨。

## この事象を早く見抜くチェックリスト

```sh
# 1) tmux 内か
echo "$TMUX"                                   # 値があれば tmux 内
# 2) 保護フォルダだけ落ちるか
ls ~/Documents >/dev/null 2>&1; echo "Documents exit=$?"   # 1 なら拒否
ls ~/.zshrc     >/dev/null 2>&1; echo "zshrc exit=$?"       # 0 なら保護外は正常
# 3) tmux サーバの実体パスと親
S=$(echo "$TMUX" | cut -d, -f2); ps -o pid,ppid,comm -p "$S"   # 親が launchd(1)
lsof -p "$S" | awk '$4=="txt"{print $NF; exit}'                # FDA 付与すべき実体パス
```

## 参考

- manaflow-ai/cmux #2866 — macOS で多重化(tmux 系)配下の保護ディレクトリが Operation not permitted:
  https://github.com/manaflow-ai/cmux/issues/2866
- Lapcat Software — Terminal と Full Disk Access(FDA の継承と責任プロセス):
  https://lapcatsoftware.com/articles/FullDiskAccess.html
- Michael Tsai — Terminal and Full Disk Access:
  https://mjtsai.com/blog/2022/09/22/terminal-and-full-disk-access/
- OS X Daily — Fix "Operation not permitted" Terminal error:
  https://osxdaily.com/2018/10/09/fix-operation-not-permitted-terminal-error-macos/
