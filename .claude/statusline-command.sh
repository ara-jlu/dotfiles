#!/bin/sh
input=$(cat)
model=$(echo "$input" | jq -r '.model.display_name // .model.id // "Unknown"')
used=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
remaining=$(echo "$input" | jq -r '.context_window.remaining_percentage // empty')

if [ -n "$used" ] && [ -n "$remaining" ]; then
  ctx=$(printf "Context: %.0f%% used (%.0f%% remaining)" "$used" "$remaining")
else
  ctx="Context: --"
fi

five=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
week=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')
rate=""
if [ -n "$five" ] && [ -n "$week" ]; then
  rate=$(printf " | Limits: 5h=%.0f%% 7d=%.0f%%" "$five" "$week")
elif [ -n "$five" ]; then
  rate=$(printf " | Limits: 5h=%.0f%%" "$five")
elif [ -n "$week" ]; then
  rate=$(printf " | Limits: 7d=%.0f%%" "$week")
fi

printf "%s | %s%s" "$model" "$ctx" "$rate"
