---
description: 新規プロジェクトで必要な.claude/配下のファイルを詳細ヒアリングしながら作成
user-invocable: true
disable-model-invocation: true
---

# 動的コンテキスト

プロジェクトファイル検出:
```
!`ls package.json docker-compose.yml pnpm-workspace.yaml tsconfig.json 2>/dev/null`
```

## 概要

新規プロジェクトのセットアップを支援するスキルです。
以下の3ファイルを作成します：

- `.claude/settings.local.json` - プロジェクト固有の環境変数
- `.claude/project/local-setup.md` - ローカル環境セットアップ手順
- `.claude/project/testing-strategy.md` - テスト戦略

## 前提条件

- プロジェクトルートディレクトリで実行すること
- `.claude/` ディレクトリが存在しない場合は自動作成

## 実行フロー

### Phase 1: コードベース分析

まず以下のファイル・ディレクトリを確認し、技術スタックを自動検出します：

**検出対象:**
- `package.json` - dependencies, devDependencies, scripts
- `yarn.lock` / `pnpm-lock.yaml` / `bun.lockb` - パッケージマネージャー
- `docker-compose.yml` / `Dockerfile` - Docker使用有無
- `next.config.*` / `vite.config.*` / `tsconfig.json` - フレームワーク
- `jest.config.*` / `vitest.config.*` / `pytest.ini` - テストツール
- `playwright.config.*` / `cypress.config.*` - E2Eツール
- `supabase/` / `firebase.json` / `.env*` - 外部サービス
- ディレクトリ名（リポジトリ名として使用）

### Phase 2: 基本情報のヒアリング

1. **プロジェクト名**
   - リポジトリ名（ディレクトリ名）を取得
   - PascalCase変換版も生成（ハイフン/アンダースコア区切りを変換）
   - question: "プロジェクト名を選択してください"
   - header: "Project"
   - options (例: リポジトリ名が `my-app` の場合):
     - label: "my-app"
     - label: "MyApp"

2. **Notion連携**
   - question: "Notion連携を設定しますか？（plan2notionスキルで使用）"
   - header: "Notion"
   - options:
     - label: "はい"
       description: "プロジェクトIDを入力"
     - label: "後で設定"
       description: "settings.local.jsonを後から編集"

   「はい」の場合、続けてプロジェクトIDの入力を求める

### Phase 3: 技術スタック確認

コードベース分析結果を提示し、確認を求めます。

**検出結果の提示例:**
```
コードベースを分析しました：

- フレームワーク: Next.js 15 (App Router)
- パッケージマネージャー: npm
- Docker: docker-compose.yml あり
- 外部サービス: Supabase, Stripe
- テストツール: Jest + React Testing Library
- E2E: Playwright
```

3. **技術スタック確認**
   - question: "検出した技術スタックは正しいですか？（違う場合はOtherで指摘）"
   - header: "Tech Stack"
   - options:
     - label: "正しい"

### Phase 4: テスト戦略確認

検出されたテストツールに基づいて確認します。

4. **カバレッジ目標**
   - question: "テストカバレッジ目標を選択してください"
   - header: "Coverage"
   - options:
     - label: "80%+（推奨）"
       description: "高品質を維持"
     - label: "60%+"
       description: "基本的なカバレッジ"
     - label: "目標なし"
       description: "カバレッジは追跡しない"

5. **クリティカルパス**（E2Eツールが検出された場合のみ）
   - CLAUDE.mdや既存コードからクリティカルパスを推測して提案
   - question: "E2E必須のクリティカルパスを確認してください（違う場合はOtherで指摘）"
   - header: "Critical"
   - options:
     - label: "提案内容でOK"

## Phase 5: ファイル生成

ヒアリング結果に基づいて以下のファイルを生成します。

### 1. settings.local.json

```json
{
  "env": {
    "NOTION_PROJECT_ID": "<入力されたID or 空文字>",
    "NOTION_PROJECT_NAME": "<入力された名前 or プロジェクト名>"
  }
}
```

### 2. project/local-setup.md

フレームワークとDockerの選択に基づいてテンプレートを生成。

### 3. project/testing-strategy.md

テスト関連の選択に基づいてテンプレートを生成。

## 実行手順

1. `.claude/` ディレクトリを確認・作成
2. AskUserQuestionツールで Phase 2-4 のヒアリングを実行
3. 回答に基づいてファイル内容を生成
4. `.claude/project/` ディレクトリを作成
5. 3つのファイルを書き込み
6. 作成完了を報告

## 完了後の出力

```
✅ プロジェクトセットアップ完了

## 作成されたファイル
- .claude/settings.local.json
- .claude/project/local-setup.md
- .claude/project/testing-strategy.md

## 次のステップ
1. settings.local.json の NOTION_PROJECT_ID を確認・設定
2. local-setup.md を参考に環境をセットアップ
3. 実装開始時は /implementation スキルを使用
```

## 既存ファイルの扱い

- `.claude/settings.local.json` が既に存在する場合：上書き確認を行う
- `.claude/project/` 内のファイルが既に存在する場合：上書き確認を行う
- 上書きを拒否された場合はスキップして続行
