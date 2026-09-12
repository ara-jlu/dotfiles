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

j-devflow には、異なる 2 つのリスク軸を制御する独立したモードフラグが 2 つある。自由に組み合わせられる: `/j-devflow <id>`、`-auto`、`-light`、`-light -auto`。

- **`-auto`** は **GATE 1（設計承認）** を制御する — attended（既定） vs 自動承認。
- **`-light`** は **Phase B のレビュー深度** を制御する — full（タスク毎の subagent ＋ **タスク毎レビュー** ＋ 最終レビュー） vs light（タスク毎の subagent、**タスク毎レビューなし**、最終レビューのみ）。**SDD の「タスク毎に fresh subagent」隔離はどちらのモードでも維持される**。`-light` が落とすのはタスク毎レビューの層だけである（008 followup は、この層が効いていないことを示した。効いているのは SDD の隔離である）。

2 つは別のリスクを対象としており、必ずしも併用する必要はない。ただし実際には**`-light` を単体で使う場面はほとんどない**: 動機となったケース（追随タスクの連鎖がプロセスのオーバーヘッドにトークンを食う）が報われるのは GATE 1 も無人のときだけなので、想定される組み合わせは `-light -auto` である。

### GATE 1: attended（既定） vs `-auto`

起動は `/j-devflow <id>`（attended）または `/j-devflow <id> -auto`（autonomous）。このフラグが変えるのは**HUMAN GATE 1（設計承認）だけ**である — GATE 2（マージ）は絶対に変えない。GATE 2 はどちらのモードでも人間が行う。

- **attended（既定）:** brainstorming が推奨アプローチを提示する。GATE 1 で承認するのは**人間**である。
- **`-auto`:** brainstorming を丸ごと実行し（コードベース探索・代替案・設計ドキュメント）、セッションが GATE 1 で**自身の推奨アプローチを自動承認**して先に進む — 人間の待ちはない。タスク本文は出発点のアイデアにすぎず（j-task の設計上、概要レベル）、設計の権威では**ない**。設計は brainstorming から出る。

**`-auto` が安全である理由:** 設計は変わらず `notes/document/` に永続化され PR に現れるし、**GATE 2（マージ）は常に人間である**。したがって GATE 1 の自動承認が招くリスクは*手戻り*（PR レビューで設計が却下される）だけであり、安全でないマージは絶対に招かない。

**`-auto` のエスカレーション条件 — 停止して dispatcher に問う（絶対に自動承認しない）:**
- スキーマ変更 / データ移行 / 削除 / セキュリティ・認証ポリシー / 公開 API 契約の変更 — 不可逆で影響範囲が大きい（GATE 2 では遅すぎる）。
- brainstorming が、その作業は単一の spec に収まらない / 分解が必要と判断した — これは設計ではなくスコープの判断である。
- 推奨アプローチが本当に紙一重であるか、実質的なトレードオフを抱えている（例: データ整合性 vs 速度） — 人間が下すべき判断である。
- fix ループが Critical/Important をすべて解消できない。

それ以外（推奨が明確に優位で、低リスク）なら自動承認して続行する。エスカレーションは**dispatcher への停止と問い合わせ**（起動した PM / セッション）であり、hard fail ではない: 停止し、問いを提示し、回答を得て再開する。したがって dispatcher は、完成した PR だけでなく、問いで停止しているセッションにも注意を払わなければならない。

### Phase B: full（既定） vs `-light`

どちらのモードも `subagent-driven-development` で実装する（タスク毎に fresh subagent — SDD のタスク毎の**隔離**はどちらでも維持される）。違いは**レビューの層**だけである:

- **full（既定）:** タスク毎に SDD の fresh subagent、**タスク毎**に `task-reviewer`、そのあとブランチ全体の最終レビュー。手順書の手順 7-8 を参照。
- **`-light`:** タスク毎に SDD の fresh subagent（**full と同じ**）、**タスク毎の `task-reviewer` はなし**、続けて**ブランチ全体の最終レビューを 1 回だけ**行う。手順書の手順 7-8 を参照。

**`-light` が安全である理由（008 followup の実測）:** 重要な正しさの網は SDD の**「タスク毎に fresh subagent」隔離**であり、`-light` はこれを維持する。`-light` が落とすタスク毎の*レビュー*は、実測（008 followup、task 195、cell-C=SDD-no-review vs cell-D=inline-with-review、各 2 反復）で**効いていない**と分かった: レビューを行った側だけが唯一の critical な退行を生み、*両方*のレビュー層がそれを見逃した一方、タスク毎レビューなしの側は中核要件について正しいままだった。ただし n=2 なので directional として扱い、下記のエスカレーション条件を維持する。`-light` が絶対に弱めてはならないのは**ブランチ全体の最終レビュー**である: これは*常に* fresh subagent であり、受け取るのは diff だけで、実装した subagent や orchestrator のコンテキストは絶対に受け取らない（自己レビューのバイアス）。タスク毎の早期検出層を落とすことは `-light` で受け入れたトレードオフである。SDD の隔離（旧 inline の `-light`）やレビュアの独立性を落とすことは受け入れない — だから `-light` はもう inline の `executing-plans` を意味しない。

**どのタスクを `-light` にするかを決めるのは誰か:** 起動時に、dispatch する PM セッションが決める — j-devflow 自身はタスクの適格性を判断しない（`-auto` の起動時の選択と同じ形）。`joifup-pm/SKILL.md` を参照。

**`-light` のエスカレーション条件 — 停止して dispatcher に問い、そのタスクの残りは full の Phase B に戻す:**
- diff が 認証 / 入力 / 秘密 / API / 機微データ に触れる — full モードで既に `ecc:security-reviewer` を要求しているのと同じ区分である。ここでは最終レビュー 1 回では足りない。
- スキーマ変更・データ移行・削除・公開 API 契約の変更が必要だと判明した — `-auto` の条件と同じ、不可逆で影響範囲が大きい区分である。
- スコープが想定を超えて広がった（例: 1〜2 ファイルで済むと見ていた修正が無関係なモジュールにまで広がる） — 「light で足りる」という前提が成り立たなくなる。
- ブランチ全体の最終レビューが Critical/Important を返す — fix ループは通常どおり回すが、`-light` が早期の検出点を飛ばしていることに留意する。

`-auto` と同じ「停止して問う」機構である: 停止し、dispatcher に問いを提示し、回答を得て再開する。

## 手順書

status・tag・フォルダ名は Joifup のスキーマ（`.joifup/databases/<id>/schema.yaml`）を読む — 絶対にハードコードしない。

**Phase A — Plan（対話）**
1. `tasks/` の下に Joifup の **Task** を用意する: 新規 → `/j-task` を実行する。既存の backlog → その filename id を使う。その id を控える — すべてがこれを起点にする。
2. ブランチ: **ハイフン命名（スラッシュなし）** ＋ TASK-id の注入 — `feature-001-slug` であり、`feature/001-slug` では**ない**。ネイティブの `EnterWorktree` は worktree ディレクトリ名で `/` を `+` に置き換えるし、スラッシュ由来の worktree は SDD subagent の書き込みを主チェックアウトへ漏らした実績がある（tasks/154, 155、根本原因は 156）。隔離は `superpowers:using-git-worktrees` で行う。repo の `branch` スキルは使わない（Notion 向けである）。**隔離したら、worktree の絶対ルートを一度だけ取得し、実行全体を通じた正典とする: `WT="$(git rev-parse --show-toplevel)"`**（SDD の progress-ledger ヘッダに記録する）。すべての SDD dispatch は `<WT>` に固定する — 手順 7 と ガード → Worktree の隔離 を参照。
3. `superpowers:brainstorming` → 設計。**HUMAN GATE 1: 設計承認 — 承認されるまでコードを書かない**（attended: 人間が承認する。`-auto`: セッションが brainstorming 自身の推奨アプローチを自動承認し、**モード**の規定に従ってエスカレーションする）。subagent には絶対にしない（これは設計の対話である）。設計ドキュメントを書くときは**staging パス**（scratchpad）を指定し、`docs/superpowers/specs/` は指定し**ない**。そこに commit も**しない**。手順 4 が spec の唯一の commit である。
4. staging した spec を `md2joifup` で `notes/document/` へ（`--type document --task <id>`）。この移動 ＋ frontmatter が spec の**唯一の commit** である。（brainstorming が既に `docs/superpowers/specs/` の下に commit していた場合、md2joifup の既定の移動がそれを取り除く — その移設を commit する。）
5. `superpowers:writing-plans` → タスク分解された計画。同じ規則が適用される: **staging パス**に書き、`docs/superpowers/plans/` には書か**ない**。そこに commit も**しない**。
6. staging した計画を `md2joifup` で `notes/plan/` へ（`--type plan --task <id>`） — 計画の**唯一の commit** である。必要なら Task を In progress に移す。**これが引き渡し成果物である。Phase A はここで終わる。**

**Phase B — Implement（既定では同一セッション、コンテキストが重いときのみ新規セッション）**
7. 永続化された計画を読み、そのうえで Phase B のモードで分岐する:
   - **full（既定）:** `superpowers:subagent-driven-development` — タスク毎に fresh subagent、英語の atomic commit、タスク毎に `task-reviewer`。認証・入力・秘密・API・機微データに触れるタスクには `agentType: ecc:security-reviewer` を追加する。orchestration と fix のループは Driver が持ち続ける — subagent になるのはタスク毎の単位だけである。
   - **`-light`:** `superpowers:subagent-driven-development` — タスク毎に fresh subagent、**full と同じ**、タスク毎に英語の atomic commit — **ただしタスク毎に `task-reviewer` を dispatch してはならない。** この変更が受けるレビューはブランチ全体の最終レビュー（手順 8）だけである。下記の `-light` のエスカレーション条件に注意する。1 つでも発火したら、**そのタスクの残りはタスク毎レビューを復帰させ（full の挙動に戻し）**、dispatcher に停止して問う。
   - **Worktree 固定の契約（subagent の dispatch すべて — implementer・fix・reviewer。full も `-light` も同様）:** どちらのモードも SDD の implementer subagent と最終レビューの subagent を dispatch するので、この固定の契約は full と `-light` に**同一に**適用される。Agent の subagent は、このセッションの `EnterWorktree` の cwd を継承**しない** — fresh subagent は主チェックアウトで開始する。したがって各 dispatch は次を MUST とする: (a) `Worktree root: <WT>` を明記する（手順 2 の `$WT`）。空欄や相対的な「Work from」は絶対に書かない。(b) subagent の**最初の行動**を `cd "<WT>"` とし、続けて `test "$(git rev-parse --show-toplevel)" = "<WT>"` を assert させる — 一致しなければ**STOP して BLOCKED を報告する**。fallback ディレクトリで編集することも cargo/pnpm を実行することも絶対にしない。(c) すべてのパスを `<WT>` 相対（または `<WT>/…`）に保ち、**主チェックアウトの literal なパスを禁じる**（`.claude/worktrees/<branch>/` の部分を含まない `/Users/…/joifup/…`）。(d) build とテストを worktree の manifest に固定する — Rust では `cargo … --manifest-path "<WT>/apps/desktop/src-tauri/Cargo.toml"`。cwd を信頼する裸の `cargo` / `cargo fmt` / `pnpm` は絶対に使わない。
8. ブランチ全体のレビュー: 変更された言語に応じて `ecc:<lang>-reviewer` を入れ（diff が該当するなら `ecc:security-reviewer` も）、**diff だけ**を渡して fresh に dispatch する — 実装したセッションの会話コンテキストは絶対に渡さない。full モードでも `-light` でも同じである。Critical/Important はブロッキングであり → clean になるまで fix ループを回す。修正後の再レビューも同じ「fresh で diff のみ」の dispatch を通し、修正を行ったセッションによる自己チェックにはしない。**`-light` モードでは、この変更が受けるレビューはこれだけである** — その前にタスク毎レビューは存在しない。
9. `superpowers:verification-before-completion` ＋ テストが green。
10. **UAT 自動化 + `j-finish`**: UI 変更を含む branch は `pnpm uat --task <id>` を実行して `.uat-evidence/<id>/` に証跡を生成する（spec で確定した受け入れ基準を `apps/web/e2e/<id>.uat.spec.ts` に書いてから）。**証跡は commit しない** — `.uat-evidence/` は gitignore 済みで、画像・動画は `gh pr comment --attach` で PR に添付する（joifup tasks/295 以降）。PR 本文には pr-body recipe の `## 受け入れ基準` と `## UAT 証跡`（summary.md の PASS/FAIL 表＝テキストのみ）を載せ、画像・動画は証跡コメント側に置く。その後 `j-finish` に `--uat-evidence-dir .uat-evidence/<id>` を渡すと、push→PR→証跡コメント→Task→In review→Discord を行う。**UAT ユーザーアクション task は file しない**（旧 heavy 分岐は廃止）。UI を含まない変更では UAT を省略し `## テスト` のみで良い。**機械はここで止まる。**

**Phase C — Approve（人間）**
11. 人間がレビューする。承認されたら: Task → Done、`chore(joifup): approve <task-id>`（英語）を commit、マージ。マージしたら、**隔離した worktree を確認なしで削除する**（`ExitWorktree` または `git worktree remove`） — マージ後の worktree は使い捨てなので、後片付けに個別の承認は要らない。尋ねない。**HUMAN GATE 2。自動でマージされるものは何もない** — 人間が持つのは承認・マージの判断だけであり、マージ後の worktree の後片付けは自動である。

## ガード（全モード共通）

- **設計ゲート（手順 7 の前）:** 設計承認より前にコードを書くことは絶対にしない。attended → 人間が承認する。`-auto` → エスカレーション条件が発火し**ない限り** brainstorming 自身の推奨が自動承認され、発火したら dispatcher に停止して問う（**モード**を参照）。概要レベルのタスク本文から承認を捏造することは絶対にしない。
- **fix ループの出口（手順 10 の前）:** どのレビュア由来であれ Critical/Important が未解決で残っていない — `-auto` も `-light` もこの基準を下げてはならない。
- **手順 10 の外部アクションの前:** PR・Discord・status は外から見えて取り消しが難しい — まずテストが green でレビューが clean であることを checkpoint とする。
- **マージと Done:** 機械には構造上不可能である — どちらのモードでも Phase C（人間）に留保されている。
- **Worktree の隔離（すべての subagent。`-auto` を含む）:** subagent を主チェックアウトの外に留めているのは dispatch だけである — `EnterWorktree` が動かすのは「このセッション」だけで、その subagent は動かさない。subagent の最初の手順として `cd "<WT>"` ＋ `git rev-parse --show-toplevel` の一致 assert を持たない dispatch は絶対に出さない。`<WT>` にいると確認できない subagent は、主チェックアウトを編集するのではなく BLOCK する。安い（dispatch 開始時に一度だけ、シェルチェック 1 回）のに対し、主チェックアウトへの漏洩と復旧のコストはそれよりはるかに大きい。根本原因: tasks/156。

## よくある失敗

- 計画が、明示されていない Phase A のコンテキストに依存する — 計画は、設計の対話なしで fresh な SDD の orchestrator（あるいは将来の読者）が実行できる self-contained な契約でなければならない。（重要なのはセッション境界ではなくこちらである。SDD はいずれにせよ各タスクを隔離する。）
- ラップしてしまう: 順序付けに留めず、superpowers やアダプタの動作そのものを書き換える。
- Phase B（機械）からマージする、あるいは Done にする — それは人間のゲートの役割である。
- brainstorming や writing-plans に、superpowers の既定の場所（`docs/superpowers/specs|plans/`）で spec や計画を commit させる — そこは Joifup のインデックス対象（`**/notes/**` のみ）でもなく、Task にも紐づかない。commit せずに staging に置く。commit するのは `md2joifup` だけであり、行き先は `notes/document/` と `notes/plan/` である。
- ブランチ名にスラッシュを使う（`feature/154-…`）、あるいは SDD の subagent を `<WT>` に固定せず dispatch する — subagent は黙って主チェックアウトに着地し、そこで編集や `cargo fmt` を行う（観測済み: tasks 154, 155）。ブランチはハイフンで命名し、すべての dispatch に `<WT>` ＋ toplevel の assert を持たせる。
- **旧 inline の `-light` を復活させる** — `-light` はもう `executing-plans` / 同一セッションの inline を意味しない。SDD（タスク毎に fresh subagent）からタスク毎レビューを引いたものである。inline の実装は正しさのばらつきを抱えていると実測（008）されたので、廃止した。
- **ブランチ全体の最終レビューに実装のコンテキストを見せる** — `-light` ではこれが唯一のレビューなので、常に fresh subagent が diff だけを受け取る形にしなければならず、実装した subagent や orchestrator の会話コンテキストは絶対に渡さない（汚染された最終レビューが見逃したものを捕まえる、その手前のタスク毎レビューは存在しない）。
