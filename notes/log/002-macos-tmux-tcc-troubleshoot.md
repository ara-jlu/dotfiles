---
ID: NOTE-41
Project: devops
created_at: '2026-07-12'
tag:
- log
title: macOS tmux "Operation not permitted"(TCC)トラブルシュート 作業ログ [2026-07-12]
updated_at: '2026-07-12'
---

# macOS tmux "Operation not permitted"(TCC)トラブルシュート 作業ログ [2026-07-12]

## 概要

別作業(joifup 開発)の最中、tmux 内で動かしている Claude Code が突然
`~/Documents` 配下へ **`Operation not permitted` (EPERM)** を返し始めた。
「tmux 内で Claude を動かしていると時々起きる」という既知の体感事象。

調査の結果、**macOS TCC(Transparency, Consent, and Control)が保護フォルダ(`~/Documents`)への
アクセスを "responsible process" 単位で制御しており、daemon 化した tmux サーバがその責任プロセスに
なるため、tmux バイナリに Full Disk Access が無いと tmux 内全プロセスが拒否される**ことを特定。
tmux バイナリへ FDA を付与して解消(**kill-server 不要で即反映**)。dotfiles にトラブルシュート
ドキュメント(`notes/document/002-macos-tmux-tcc-operation-not-permitted.md`)を作成した。

環境: macOS 15.7.3 (Sequoia, 24G419) / tmux 3.6a / Homebrew(`/opt/homebrew`)。

---

### 1. 発症

- ある `python3 <skill>/scripts/md2joifup.py …` 実行が突然:
  ```
  can't open file '/Users/ara/.claude/skills/md2joifup/scripts/md2joifup.py': [Errno 1] Operation not permitted
  ```
- 続けて repo 内ファイルの `head` / `ls <dir>` / エディタ Read も一律 EPERM。
- 特徴的だったのが **`ls -l <file>`(stat)は成功するのに `open`/`readdir` だけ失敗**する点。
  これは権限(mode)の問題ではなく、上位のアクセス制御(TCC/サンドボックス)が
  open 系 syscall を弾いている兆候。
- 直前に別プロセス(subagent)の作業や `dangerouslyDisableSandbox` を挟んでいたため、
  最初は「Claude のサンドボックスが締まったか?」を疑ったが、sandbox 無効化でも回復せず → OS 側を疑う方針に切替。

### 2. 切り分け(アクセス probe)

保護フォルダ内外で挙動が割れるかを確認:

```sh
for p in "$HOME/.zshrc" "/tmp" "$HOME/.claude/settings.json" "$HOME/Documents"; do
  if ls "$p" >/dev/null 2>&1; then echo "OK   $p"; else echo "DENY $p"; fi
done
```

結果:

| パス | 結果 |
|---|---|
| `~/.zshrc` | OK |
| `/tmp` | OK |
| `~/.claude/settings.json` | OK |
| `~/Documents` | **DENY** |

→ **`~/Documents`(TCC 保護フォルダ)だけが拒否**。権限一般の問題ではなく TCC の保護フォルダ問題だと確定。

- `~/.claude/skills` も拒否されていた理由:
  ```sh
  ls -ld ~/.claude/skills
  # lrwxr-xr-x … ~/.claude/skills -> /Users/ara/Documents/workspace/dotfiles/.claude/skills
  ```
  **`~/.claude/skills` は `~/Documents` 配下(dotfiles)への symlink** なので巻き添えで拒否。
  → skill スクリプト(md2joifup 等)が全滅していたのはこれが原因。

### 3. tmux プロセス構造の確認

```sh
echo "$TMUX"          # /private/tmp/tmux-501/default,3716,0  → server PID = 3716
ps -o pid,ppid,comm -p 3716
#   3716     1 tmux      → 親は launchd(PID 1)
lsof -p 3716 | awk '$4=="txt"{print $NF}'
#   /opt/homebrew/Cellar/tmux/3.6a/bin/tmux
```

> 注意: `pgrep -x tmux` は `attach-session` クライアント(別 PID)を拾う。
> **本物のサーバ PID は `$TMUX` の socket 文字列(カンマ区切り2番目)**にある。

- **tmux サーバは daemon 化して launchd に再ペアレントされている**。これが核心。

### 4. root cause 確定

macOS TCC は保護フォルダ(`~/Documents` `~/Desktop` `~/Downloads` 等)へのアクセスを
**"responsible process"(責任プロセス)単位**で許可する。

- 通常、端末アプリ(iTerm2/Terminal 等)が子プロセスの責任プロセスになり、端末に付けた FDA を継承する。
- **しかし tmux サーバは daemon 化して launchd の子になる**ため、tmux 内の全プロセス
  (シェル・Claude・`ls`)の責任プロセスは **tmux バイナリ自身**になり、端末アプリの FDA を継承しない。
- その tmux バイナリに Documents/FDA が無いので、tmux 内からの `~/Documents` は一律 EPERM。

→ **「端末アプリに FDA を付けても tmux 内では直らない」**のはこのため。

### 5. 「時々」の正体

FDA の許可は**バイナリの実体パス**に紐づく。`/opt/homebrew/bin/tmux` は
`…/Cellar/tmux/<version>/bin/tmux` という**バージョン入り実体パス**に解決される。
`brew upgrade tmux` でバージョンが上がると実体パスが変わり、**以前付与した FDA が旧パスに
取り残されて無効化**される → 再発する。
加えて tmux サーバが「いつ・どの文脈で起動したか」でも responsible process の解決が変わるため、
再現性が「時々」になる。

### 6. web リサーチ(裏取り)

- manaflow-ai/cmux #2866 — macOS で多重化(tmux 系)配下の保護ディレクトリが Operation not permitted。
  原因は TCC だが**確定 fix は未記載**、回避策は「保護フォルダの外へ移動」のみ。
  <https://github.com/manaflow-ai/cmux/issues/2866>
- Lapcat Software / Michael Tsai — FDA の継承と responsible process の解説。
  <https://lapcatsoftware.com/articles/FullDiskAccess.html> / <https://mjtsai.com/blog/2022/09/22/terminal-and-full-disk-access/>
- OS X Daily — 端末/シェルへの FDA 付与手順。
  <https://osxdaily.com/2018/10/09/fix-operation-not-permitted-terminal-error-macos/>
- 諸説を統合し「**端末でなく tmux バイナリ自身へ FDA**」が正解と結論。

### 7. 解消(実測)

1. System Settings → Privacy & Security → **Full Disk Access** → `+` → **⌘⇧G** で実体パス入力:
   ```
   /opt/homebrew/Cellar/tmux/3.6a/bin/tmux
   ```
   追加して **ON**。
2. **kill-server せずに** `ls ~/Documents` を試したところ **即座に回復**:
   ```
   ls ~/Documents                 -> exit 0
   worktree tasks/ readdir        -> exit 0
   head <repo file>               -> OK
   ~/.claude/skills/... (symlink) -> exit 0
   ```

> 実測(macOS 15.7.3 + tmux 3.6a): tmux バイナリへの FDA 付与のみで、**既存セッションを保ったまま**
> TCC が次回アクセスで再評価して回復した。反映されない環境では `tmux kill-server` で新サーバを立て直す
> (ただしその場合 tmux 内の全セッション=このセッションも落ちる)。

### 8. 恒久対策(ドキュメントに記載)

- **A. `brew upgrade tmux` の度に FDA を付け直す**(バージョン入りパスが変わるため)。手軽だが手動。
- **B. 作業ツリーを `~/Documents` の外へ**(例 `~/workspace`)。TCC 対象外になり本事象が原理的に起きない。
  cmux #2866 も推奨。ただし daemon の workspace_root / symlink 張り替えが伴う。
- **C. 端末アプリ FDA 運用は daemon 化により不安定** → A/B 推奨。

### 9. ドキュメント化

- `md2joifup --type document --project devops` で
  **`dotfiles/notes/document/002-macos-tmux-tcc-operation-not-permitted.md`** を作成。

---

## 学び / ブログ化メモ

- **見抜き方**: 「`ls -l <file>` は通るのに `open`/`readdir` が EPERM」+「保護フォルダだけ落ちる」+「tmux 内」= TCC×tmux をまず疑う。
- **勘所**: TCC は responsible process 単位。tmux サーバは daemon 化して launchd 子 → 責任プロセスが tmux 自身になる。**端末への FDA では効かない、tmux バイナリへ FDA**。
- **"時々"の謎解き**: `brew upgrade tmux` → Cellar のバージョン入り実体パスが変わり FDA 付与が無効化して再発。
- **落とし穴**: `~/.claude/skills` のような **Documents への symlink** は巻き添えで拒否され、原因を見えにくくする。
- 記事タイトル案: 「tmux 内で macOS が Operation not permitted を出す本当の理由 — TCC の responsible process と brew upgrade の罠」
