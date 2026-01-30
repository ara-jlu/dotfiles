#!/bin/bash
# Discord通知スクリプト
# 使用方法: ./discord-notify.sh "タイトル" "メッセージ" "カラー(optional)"

set -euo pipefail

TITLE="$1"
MESSAGE="$2"
COLOR="${3:-5814783}"  # デフォルト: 青色 (0x58B0FF)

# Discord Webhook URLを環境変数から取得
if [ -z "${DISCORD_WEBHOOK_URL:-}" ]; then
  echo "Error: DISCORD_WEBHOOK_URL environment variable not set" >&2
  exit 1
fi

# メンションを追加（環境変数で指定可能）
MENTION="${DISCORD_MENTION_USER:-}"
CONTENT=""
if [ -n "$MENTION" ]; then
  CONTENT="<@${MENTION}>"
fi

# 現在のブランチを取得
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

# プロジェクト名を取得
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
PROJECT_NAME=$(basename "$PROJECT_DIR")

# JSONペイロードを構築（jqで安全にエスケープ）
PAYLOAD=$(jq -n \
  --arg content "$CONTENT" \
  --arg title "$TITLE" \
  --arg message "$MESSAGE" \
  --argjson color "$COLOR" \
  --arg project "$PROJECT_NAME" \
  --arg branch "$BRANCH" \
  --arg timestamp "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
  '{
    content: $content,
    embeds: [{
      title: $title,
      description: $message,
      color: $color,
      fields: [
        {
          name: "プロジェクト",
          value: $project,
          inline: true
        },
        {
          name: "ブランチ",
          value: $branch,
          inline: true
        }
      ],
      timestamp: $timestamp
    }]
  }'
)

# Discord Webhookにポスト
curl -X POST \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" \
  "$DISCORD_WEBHOOK_URL" \
  --silent --show-error --fail

exit 0
