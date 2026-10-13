---
name: j-devflow
description: 機能追加やバグ修正を、一行のアイデアから人間の承認ゲート手前までこのハーネスで進めるときに使う — 設計・計画・実装・承認前の終了処理にまたがる一気通貫の開発を開始する。「この機能を作って」「開発を始めて」「j-devflow で進めて」に該当する場合。
---

# j-devflow

## 概要

superpowers の背骨と Joifup のアダプタの上に乗る**薄いシーケンサ**。やるのは統括であり、ラップではない — 下位のスキルに指示を注入することも、その出力を作り変えることも絶対にしない。決めるのは**順序・セッション境界・引き渡し成果物・ゲート**だけである。計算（superpowers）と永続化（Joifup）は分離したままにする。

この流れは**3 つのフェーズ**からなり、ファイルの引き渡しで繋がる（永続化された `notes/plan/` のエントリが契約である）:

- **Phase A — Plan**（対話）: アイデア → 設計 → 計画。Joifup に永続化する。
- **Phase B — Implement**: 永続化された計画を読み、実装してレビューする。
- **Phase C — Approve**（人間）: 承認ゲート。マージが行われるのはここだけである。

**既定では同一セッション。** A → B → C を 1 つのセッションで回す。SDD は各タスクに fresh subagent（隔離されたコンテキスト）を与えるので、実装の隔離にセッション境界は**不要**である。Phase A の対話が長引いたとき、またはコンテキストが厳しいときに**限って Phase B を新しいセッションで開く** — 新規セッションの Phase B には、計画が self-contained であることを強制でき、計画時の対話を orchestrator のコンテキストの外に保てるという利点も加わるが、そのコスト（引き渡しをコピーし、`/clear` し、貼り付ける）は単独作業では通常見合わない。

## 使う場面

- 背骨を丸ごと通すべき、軽微でない機能追加・バグ修正。
- 1 ファイルで済む素早い修正には使わない（そのまま直す）。マージにも使わない（それは人間が持つ Phase C の役割）。

## モード — 独立した二軸

j-devflow には、異なる 2 つのリスク軸を制御する独立したモードフラグが 2 つある。自由に組み合わせられる: `/j-devflow <id>`、`-auto`、`-full`、`-full -auto`。

- **`-auto`** は **GATE 1（設計承認）** を制御する — attended（既定） vs 自動承認。
- **`-full`** は **Phase B のタスク毎レビューの範囲** を制御する — 既定（セキュリティ該当のタスクにだけタスク毎レビュー） vs 全タスクにタスク毎レビュー。**SDD の「タスク毎に fresh subagent」隔離と、ブランチ全体の最終レビューはどちらでも維持される**。

2 つは別のリスクを対象としており、必ずしも併用する必要はない。`-auto`・`-full` 以外のフラグ（廃止したフラグを含む）を付けて起動されたら、推測で読み替えず、停止して dispatcher に問う。

### GATE 1: attended（既定） vs `-auto`

起動は `/j-devflow <id>`（attended）または `/j-devflow <id> -auto`（autonomous）。このフラグが変えるのは**HUMAN GATE 1（設計承認）だけ**である — GATE 2（マージ）は絶対に変えない。GATE 2 はどちらのモードでも人間が行う。

- **attended（既定）:** brainstorming が推奨アプローチを提示する。GATE 1 で承認するのは**人間**である。
- **`-auto`:** brainstorming を丸ごと実行し（コードベース探索・代替案・設計ドキュメント）、セッションが GATE 1 で**自身の推奨アプローチを自動承認**して先に進む — 人間の待ちはない。タスク本文は出発点のアイデアにすぎず（j-task の設計上、概要レベル）、設計の権威では**ない**。設計は brainstorming から出る。

**`-auto` が安全である理由:** 設計は変わらず `notes/document/` に永続化され PR に現れるし、**GATE 2（マージ）は常に人間である**。したがって GATE 1 の自動承認が招くリスクは*手戻り*（PR レビューで設計が却下される）だけであり、安全でないマージは絶対に招かない。

**`-auto` のエスカレーション条件 — 停止して dispatcher に問う（絶対に自動承認しない）:**
- スキーマ変更 / データ移行 / 削除 / セキュリティ・認証ポリシー / 公開 API 契約の変更 — 不可逆で影響範囲が大きい（GATE 2 では遅すぎる）。
- brainstorming が、その作業は単一の spec に収まらない / 分解が必要と判断した — これは設計ではなくスコープの判断である。
- 推奨アプローチが本当に紙一重であるか、実質的なトレードオフを抱えている（例: データ整合性 vs 速度） — 人間が下すべき判断である。
- 設計書の fresh レビュー（手順 3）の後に、「直した」以外に振り分けた Critical/Important、再レビューを 2 回回しても解消しきれない Critical/Important、または前提の一覧で「合わない」かつ芯の前提が残っている。あるいは、指摘を直した結果として推奨アプローチが変わった（直して再レビューが clean でも止める）。「不明」かつ芯の前提はここに入らない — 止めずに手順 10 で PR 本文に運ぶ。
- fix ループが Critical/Important を解消しきれない。

それ以外（推奨が明確に優位で、低リスク）なら自動承認して続行する。エスカレーションは**dispatcher への停止と問い合わせ**（起動した PM / セッション）であり、hard fail ではない: 停止し、問いを提示し、回答を得て再開する。したがって dispatcher は、完成した PR だけでなく、問いで停止しているセッションにも注意を払わなければならない。

### Phase B: 既定 vs `-full`

どちらのモードも `subagent-driven-development` で実装する（タスク毎に fresh subagent — SDD のタスク毎の**隔離**はどちらでも維持される）。違いは**タスク毎レビューを入れる範囲**だけである:

| | 既定 | `-full` |
|---|---|---|
| タスク毎に fresh subagent（SDD の隔離） | あり | あり |
| タスク毎の `task-reviewer` | 該当タスクだけ | 全タスク |
| タスク毎の `ecc:security-reviewer` | 該当タスクだけ | 該当タスクだけ |
| ブランチ全体の最終レビュー | あり | あり |

「該当タスク」の物差し（セキュリティ該当の区分）、判定の外れの確かめ方、progress ledger の記録規則は、グローバルの `~/.claude/CLAUDE.md` の「レビュー統合」にある。ここには写さない。判定するのは手順 7 の冒頭の orchestrator であり、writing-plans には何も注入しない（計画を読む側で判定する）。

**既定でタスク毎レビューを絞る理由:** 重要な正しさの網は、SDD の「タスク毎に fresh subagent」の隔離と、ブランチ全体の最終レビューである。タスク毎レビューの層は、実測でほとんど欠陥を拾っていない。ただし実測の n は小さいので directional として扱い、全タスクに戻す `-full` を残す。根拠の数字は dotfiles の `notes/document/017-devflow-full-flag-design.md` にある。**ブランチ全体の最終レビューは絶対に弱めない**: これは常に fresh subagent であり、実装した subagent や orchestrator の会話は絶対に受け取らない（自己レビューのバイアス）。

**`-full` を付けるかを決めるのは誰か:** 起動時に dispatcher（PM セッションか人間）が決める（`-auto` の起動時の選択と同じ形）。タスク毎レビューを入れるタスクは、j-devflow の orchestrator が計画から決める。`joifup-pm/SKILL.md` を参照。

**Phase B の停止条件（両モード共通） — 停止して dispatcher に問う:**
- 設計に無かったスキーマ変更・データ移行・削除・セキュリティや認証のポリシーの変更・公開 API の契約変更が必要だと判明した — `-auto` の条件と同じ、不可逆で影響範囲が大きい区分である。

`-auto` と同じ「停止して問う」機構である: 停止し、dispatcher に問いを提示し、回答を得て再開する。

## 手順書

status・tag・フォルダ名は Joifup のスキーマ（`.joifup/databases/<id>/schema.yaml`）を読む — 絶対にハードコードしない。

**Phase A — Plan（対話）**
1. `tasks/` の下に Joifup の **Task** を用意する: 新規 → `/j-task` を実行する。既存の backlog → その filename id を使う。その id を控える — すべてがこれを起点にする。
2. ブランチ: **ハイフン命名（スラッシュなし）** ＋ TASK-id の注入 — `feature-001-slug` であり、`feature/001-slug` では**ない**。ネイティブの `EnterWorktree` は worktree ディレクトリ名で `/` を `+` に置き換えるし、スラッシュ由来の worktree は SDD subagent の書き込みを主チェックアウトへ漏らした事例がある（tasks/154, 155、根本原因は 156）。隔離は `superpowers:using-git-worktrees` で行う。repo の `branch` スキルは使わない（Notion 向けである）。**隔離したら、worktree の絶対ルートを一度だけ取得し、実行全体を通じた正典とする: `WT="$(git rev-parse --show-toplevel)"`**（SDD の progress-ledger ヘッダに記録する）。すべての SDD dispatch は `<WT>` に固定する — 手順 7 と ガード → Worktree の隔離 を参照。
3. `superpowers:brainstorming` → 設計。**HUMAN GATE 1: 設計承認 — 承認されるまでコードを書かない**（attended: 人間が承認する。`-auto`: セッションが brainstorming 自身の推奨アプローチを自動承認し、**モード**の規定に従ってエスカレーションする）。設計の対話そのものは subagent には絶対にしない。書いた設計書の読み取りレビューは、下のとおり fresh な subagent に出す。設計ドキュメントを書くときは**staging パス**（scratchpad）を指定し、`docs/superpowers/specs/` は指定し**ない**。そこに commit も**しない**。手順 4 が spec の唯一の commit である。
   - **設計書の fresh レビュー（GATE 1 の前）:** GATE 1 は brainstorming の checklist 8（書いた設計書を人間が読む）を指す。checklist 7（自己レビュー）の後、checklist 8 の前に、`references/spec-review-prompt.md` の文面で fresh な subagent に設計書を読ませる。渡すのはタスク本文と staging の設計書のパスだけで、会話は渡さない。dispatch は手順 7 の Worktree 固定の契約の (a)(b) に従う。入力の渡し方は手順 7 の (c) の例外に従う。指摘は 1 件ずつ「直した / 判断を仰ぐ / 採らない（理由）」に振り分ける。Critical/Important、または前提の一覧で「合わない」かつ芯の前提を直したら、前回の指摘と振り分けの表（staging と同じ scratchpad に置く）を渡して fresh に再レビューする（2 回まで。修正したセッションの自己チェックにしない）。2 回で解消しきれなければ、attended は GATE 1 で人間に出し、`-auto` はエスカレーションする。直した物が無ければ再レビューは回さない。Minor はブロックしない。attended → 振り分けの表と、前提の一覧の「合わない」「不明」を添えて GATE 1 に出す。推奨アプローチが崩れたら、人間の判断で checklist 5（節ごとの提示）に戻る。GATE 1 で人間が修正を求めたら、修正後にもう一度回す（再レビューの回数は数え直す。人間が不要と言えば省く）。`-auto` → **モード**のエスカレーション条件に従う。「不明」かつ芯の前提では止めず、設計書に「未確認の前提」の節を設けて書き残す。根拠（097 の実例、superpowers v5.0.6 が subagent の spec レビューを廃止したこととの関係）は dotfiles の `notes/document/016-devflow-spec-fresh-review-design.md` にある。
4. staging した spec を `md2joifup` で `notes/document/` へ（`--type document --task <id>`）。この移動 ＋ frontmatter が spec の**唯一の commit** である。（brainstorming が既に `docs/superpowers/specs/` の下に commit していた場合、md2joifup の既定の移動がそれを取り除く — その移設を commit する。）
5. `superpowers:writing-plans` → タスク分解された計画。同じ規則が適用される: **staging パス**に書き、`docs/superpowers/plans/` には書か**ない**。そこに commit も**しない**。
6. staging した計画を `md2joifup` で `notes/plan/` へ（`--type plan --task <id>`） — 計画の**唯一の commit** である。必要なら Task を In progress に移す。**これが引き渡し成果物である。Phase A はここで終わる。**

**Phase B — Implement（既定では同一セッション、コンテキストが重いときのみ新規セッション）**
7. 永続化された計画を読み、そのうえで Phase B のモードで分岐する:
   - **既定:** `superpowers:subagent-driven-development` — タスク毎に fresh subagent、英語の atomic commit。最初のタスクを dispatch する前に、計画の各タスクがセキュリティ該当の区分（グローバルの `~/.claude/CLAUDE.md` の「レビュー統合」）に当たるかを判定し、結果を progress ledger のヘッダに `<WT>` と並べて記録する。該当タスクにだけ `task-reviewer` と `agentType: ecc:security-reviewer` を入れる。該当しないタスクは、完了ごとに、グローバルの `~/.claude/CLAUDE.md` の規定どおりファイル名で判定の外れを確かめ、確かめが済んでから ledger に記録する。orchestration と fix のループは Driver が持ち続ける — subagent になるのはタスク毎の単位だけである。
   - **`-full`:** 既定と同じだが、全タスクに `task-reviewer` を入れる。`ecc:security-reviewer` は該当タスクにだけ入れ、判定の外れの確かめも既定と同じに行う（当たれば `ecc:security-reviewer` を足す）。
   - **Worktree 固定の契約（subagent の dispatch すべて — implementer・fix・reviewer。既定も `-full` も同様）:** どちらのモードも SDD の implementer subagent と最終レビューの subagent を dispatch するので、この固定の契約は既定と `-full` に**同一に**適用される。Agent の subagent は、このセッションの `EnterWorktree` の cwd を継承**しない** — fresh subagent は主チェックアウトで開始する。したがって各 dispatch は次を MUST とする: (a) `Worktree root: <WT>` を明記する（手順 2 の `$WT`）。空欄や相対的な「Work from」は絶対に書かない。(b) subagent の**最初の行動**を `cd "<WT>"` とし、続けて `test "$(git rev-parse --show-toplevel)" = "<WT>"` を assert させる — 一致しなければ**STOP して BLOCKED を報告する**。fallback ディレクトリで編集することも cargo/pnpm を実行することも絶対にしない。(c) すべてのパスを `<WT>` 相対（または `<WT>/…`）に保ち、**主チェックアウトの literal なパスを禁じる**（`.claude/worktrees/<branch>/` の部分を含まない `/Users/…/joifup/…`）。例外: 何も書き換えない設計書の fresh レビュアー（手順 3）には、staging の設計書・タスク本文・設計書が参照する `<WT>` の外のファイルを、読み取り専用の入力として絶対パスで渡してよい（(c) の目的は書き込みの漏洩を防ぐことにある）。(d) build とテストを worktree の manifest に固定する — Rust では `cargo … --manifest-path "<WT>/apps/desktop/src-tauri/Cargo.toml"`。cwd を信頼する裸の `cargo` / `cargo fmt` / `pnpm` は絶対に使わない。
8. ブランチ全体のレビュー: fresh に dispatch し、受け手ごとに渡すものを分ける — **SDD の最終 code-reviewer（spec 準拠）**には review-package と永続化された計画のパス（`[PLAN_OR_REQUIREMENTS]`）を、**`ecc:<lang>-reviewer`**（変更された言語に応じて）と、diff がセキュリティ該当の区分に触れるなら **`ecc:security-reviewer`** には review-package だけを渡す。どの受け手にも、実装した subagent と orchestrator の会話コンテキストは絶対に渡さない。既定でも `-full` でも同じである。Critical/Important はブロッキングであり → clean になるまで fix ループを回す。修正後の再レビューも同じ fresh な dispatch を通し、修正を行ったセッションによる自己チェックにはしない。**既定では、該当しないタスクの spec 準拠を見るのはこのレビューだけである。**
9. `superpowers:verification-before-completion` ＋ テストが green。
10. **UAT 自動化 + `j-finish`**: UI 変更を含む branch は `pnpm uat --task <id>` を実行して `.uat-evidence/<id>/` に証跡を生成する（spec で確定した受け入れ基準を `apps/web/e2e/<id>.uat.spec.ts` に書いてから）。**証跡は commit しない** — `.uat-evidence/` は gitignore 済みで、画像・動画は `gh pr comment --attach` で PR に添付する（joifup tasks/295 以降）。PR 本文には pr-body recipe の `## 受け入れ基準` と `## UAT 証跡`（summary.md の PASS/FAIL 表＝テキストのみ）を載せ、画像・動画は証跡コメント側に置く。その後 `j-finish` に `--uat-evidence-dir .uat-evidence/<id>` を渡すと、push→PR→証跡コメント→Task→In review→Discord を行う。**UAT ユーザーアクション task は file しない**（旧 heavy 分岐は廃止）。UI を含まない変更では UAT を省略し `## テスト` のみで良い。`-auto` で設計書に「未確認の前提」の節があれば、PR 本文の冒頭に転記する（設計書のファイルが diff に入るだけでは人間の目に届かない）。**機械はここで止まる。**

**Phase C — Approve（人間）**
11. 人間がレビューする。承認されたら: Task → Done、`chore(joifup): approve <task-id>`（英語）を commit、マージ。マージしたら、**隔離した worktree を確認なしで削除する**（`ExitWorktree` または `git worktree remove`） — マージ後の worktree は使い捨てなので、後片付けに個別の承認は要らない。尋ねない。**HUMAN GATE 2。自動でマージされるものは何もない** — 人間が持つのは承認・マージの判断だけであり、マージ後の worktree の後片付けは自動である。

## ガード（全モード共通）

- **設計ゲート（手順 7 の前）:** 設計承認より前にコードを書くことは絶対にしない。attended → 人間が承認する。`-auto` → エスカレーション条件が発火し**ない限り** brainstorming 自身の推奨が自動承認され、発火したら dispatcher に停止して問う（**モード**を参照）。概要レベルのタスク本文から承認を捏造することは絶対にしない。GATE 1 の前に、設計書の fresh レビュー（手順 3）を必ず通す — 書いた本人の自己レビューだけで GATE 1 に出さない。
- **fix ループの出口（手順 10 の前）:** どのレビュアー由来であれ Critical/Important が未解決で残っていない — `-auto` も Phase B のどちらのモードもこの基準を下げてはならない。
- **手順 10 の外部アクションの前:** PR・Discord・status は外から見えて取り消しが難しい — まずテストが green でレビューが clean であることを checkpoint とする。
- **マージと Done:** 機械には構造上不可能である — どちらのモードでも Phase C（人間）に留保されている。
- **Worktree の隔離（すべての subagent。`-auto` を含む）:** subagent を主チェックアウトの外に留めているのは dispatch だけである — `EnterWorktree` が動かすのは「このセッション」だけで、その subagent は動かさない。subagent の最初の手順として `cd "<WT>"` ＋ `git rev-parse --show-toplevel` の一致 assert を持たない dispatch は絶対に出さない。`<WT>` にいると確認できない subagent は、主チェックアウトを編集するのではなく BLOCK する。安い（dispatch 開始時に一度だけ、シェルチェック 1 回）のに対し、主チェックアウトへの漏洩と復旧のコストはそれよりはるかに大きい。根本原因: tasks/156。

## よくある失敗

- 計画が、明示されていない Phase A のコンテキストに依存する — 計画は、設計の対話なしで fresh な SDD の orchestrator（あるいは将来の読者）が実行できる self-contained な契約でなければならない。（重要なのはセッション境界ではなくこちらである。SDD はいずれにせよ各タスクを隔離する。）
- 設計書を、書いた本人の自己レビューだけで GATE 1 に出す — 書いた本人は設計の対話で前提を共有しているので、前提自体の抜けが見えない（実例: fde の tasks/097 は、添付で届く入力を扱えない穴を残したまま自己レビューを通った）。手順 3 の fresh レビューを通す。
- ラップしてしまう: 順序付けに留めず、superpowers やアダプタの動作そのものを書き換える。
- Phase B（機械）からマージする、あるいは Done にする — それは人間のゲートの役割である。
- brainstorming や writing-plans に、superpowers の既定の場所（`docs/superpowers/specs|plans/`）で spec や計画を commit させる — そこは Joifup のインデックス対象（`**/notes/**` のみ）でもなく、Task にも紐づかない。commit せずに staging に置く。commit するのは `md2joifup` だけであり、行き先は `notes/document/` と `notes/plan/` である。
- ブランチ名にスラッシュを使う（`feature/154-…`）、あるいは SDD の subagent を `<WT>` に固定せず dispatch する — subagent は黙って主チェックアウトに着地し、そこで編集や `cargo fmt` を行う（観測済み: tasks 154, 155）。ブランチはハイフンで命名し、すべての dispatch に `<WT>` ＋ toplevel の assert を持たせる。
- **ブランチ全体の最終レビューに計画を要件として渡さない** — 既定では、該当しないタスクの spec 準拠を見るのは最終レビューだけである。計画のファイルが diff に入っているだけでは、照らし合わせる要件として扱われない。
- **該当の判定を writing-plans への注入で済ませる** — 計画に判定を書かせるのはラップである。判定は計画を読む側（Phase B の orchestrator）で行う。
- **ブランチ全体の最終レビューに実装のコンテキストを見せる** — 既定では、該当しないタスクにとってこれが唯一のレビューなので、常に fresh subagent が diff だけを受け取る形にしなければならず、実装した subagent や orchestrator の会話コンテキストは絶対に渡さない（その手前には、汚染された最終レビューが見逃したものを捕まえるタスク毎レビューが存在しない）。
