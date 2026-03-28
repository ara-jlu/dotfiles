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

# zsh-abbr (abbreviation expansion instead of aliases)
source /opt/homebrew/share/zsh-abbr/zsh-abbr.zsh
abbr -S -qq g=git
abbr -S -qq cl=claude
abbr -S -qq cld='claude --dangerously-skip-permissions'
abbr -S -qq cldc='claude --dangerously-skip-permissions --continue'
abbr -S -qq cla='claude --permission-mode auto'
abbr -S -qq sleepon='sudo pmset disablesleep 0'
abbr -S -qq sleepoff='sudo pmset disablesleep 1'

# Ensure UTF-8 tty mode (fixes Japanese in iOS NeoServer + tmux)
if [[ -t 0 ]]; then
  stty iutf8 2>/dev/null
fi

# bun completions
[ -s "/Users/ara/.bun/_bun" ] && source "/Users/ara/.bun/_bun"

# bun
export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"
