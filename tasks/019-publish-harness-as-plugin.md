---
ID: TASK-875
title: ハーネスを公開用のプラグインとして別のリポジトリに切り出す
status: Not started
Project: devops
created_at: 2026-10-16
updated_at: 2026-10-16
---

# ハーネスを公開用のプラグインとして別のリポジトリに切り出す

## 概要

dotfiles の `.claude/skills` にある j-* のスキル群（devflow・finish・task・doc・log・research など）と、その周りの CLAUDE.md・rules を、他の人が入れて使える Claude Code のプラグインとして、公開用の別リポジトリに切り出す。公開時の名前は依頼者特有の `j-` を外して汎用にし、Joifup の決まり（schema・md2joifup・tasks の番号）に頼らずに動く形にする。公開の前に、秘密が含まれていないかを専用の道具で確かめる。

## 背景

2026-10-16 に X の主軸を「Claude Code を使い込んだ実体験と、作ったもの」に変えた（root `notes/document/001-x-restart-strategy`）。速く伸びた個人の調査（root `notes/research/001-fast-growth-patterns-and-x-direction`）では、作ったものを配った人に伸び方の大きな段差があった。今の dotfiles は公開済みだが、README が nvim・tmux などの説明のままで、ハーネスが入っていることが伝わらない。

## 起票時のメモ（未検証）

- 名前の候補（依頼者の 2026-10-16 の案を Partner が具体化したもの）: プラグインのスキルは `プラグイン名:スキル名` で呼ばれるので頭の文字は要らない。j-devflow → `devflow`、j-finish → `finish`、j-task / j-doc / j-log / j-research → `task` / `doc` / `log` / `research`、md2joifup → Joifup に頼らない名前
- 危ないところ: 今の dotfiles の利用者（依頼者自身の全リポジトリ）が `j-*` と md2joifup に頼っている。切り出しで今の環境を壊さないこと
- 秘密の確認: 2026-10-16 に Partner が dotfiles の全346コミットの追加行を正規表現で確かめ、本物の秘密は見つからなかった（テスト用のおとりの値と計画書の例の値だけ）。gitleaks などの専用の道具ではないので、公開前にもう一度確かめる
- 決めることの候補: 公開する範囲（スキルだけ／rules・CLAUDE.md も／設計書の notes も）、ライセンス、superpowers・ECC への依存の書き方、dotfiles 側の README を直すか
- 出どころ: 2026-10-16 の Partner のセッション（依頼者の判断: 公開用はリポジトリを分けてよい、j- の命名は汎用にしたい）
