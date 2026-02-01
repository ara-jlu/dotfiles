# PATH
export PATH="$HOME/.local/bin:$PATH"

# Completion
autoload -Uz compinit && compinit
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Z}'  # 小文字で大文字もマッチ
zstyle ':completion:*' menu select                     # 矢印キーで候補を選択
zstyle ':completion:*' list-colors ${(s.:.)LS_COLORS}  # 候補に色付け
setopt AUTO_CD            # ディレクトリ名だけでcd
setopt CORRECT            # コマンドのtypo修正を提案
setopt COMPLETE_IN_WORD   # 単語の途中でも補完

# Git Alias
alias g='git'
# Claude Alias
alias cc='claude'
alias ccyolo='claude --dangerously-skip-permissions'

# Ensure UTF-8 tty mode (fixes Japanese in iOS NeoServer + tmux)
if [[ -t 0 ]]; then
  stty iutf8 2>/dev/null
fi
