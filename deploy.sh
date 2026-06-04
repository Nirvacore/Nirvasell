#!/usr/bin/env bash
# nirva.sell — one-command deploy helper
#
# Usage:
#   ./deploy.sh init <github-user> <repo-name>     # first-time setup
#   ./deploy.sh push "commit message"              # push updates
#   ./deploy.sh docker                              # build + run locally
#
# After `init`: open https://share.streamlit.io → New app → pick repo → add
# secret ANTHROPIC_API_KEY → done. Free hosting forever.

set -euo pipefail

cmd="${1:-help}"

case "$cmd" in
  init)
    user="${2:?Usage: ./deploy.sh init <github-user> <repo>}"
    repo="${3:?Usage: ./deploy.sh init <github-user> <repo>}"
    if [ -d .git ]; then
      echo "Already a git repo — skip init"
    else
      git init
      git branch -M main
    fi
    git add .
    git -c user.email="deploy@nirva.sell" -c user.name="nirva.sell" \
        commit -m "init nirva.sell" || echo "Nothing to commit"
    git remote add origin "git@github.com:${user}/${repo}.git" 2>/dev/null \
      || git remote set-url origin "git@github.com:${user}/${repo}.git"
    echo
    echo "Now create the repo on GitHub:"
    echo "  https://github.com/new?name=${repo}&description=nirva.sell%20AI%20Sales%20Workspace"
    echo
    echo "Then run:  git push -u origin main"
    echo
    echo "Then open: https://share.streamlit.io"
    echo "  → New app → repo=${user}/${repo} → main file=app.py"
    echo "  → Advanced settings → Secrets → paste:"
    echo "      ANTHROPIC_API_KEY = \"sk-...\""
    ;;

  push)
    msg="${2:-update}"
    git add .
    git commit -m "$msg" || echo "Nothing to commit"
    git push
    echo "Pushed. Streamlit Cloud will redeploy automatically (~1 min)."
    ;;

  docker)
    docker build -t nirva.sell . \
      && docker run --rm -p 8501:8501 \
          -e ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}" \
          -v "$(pwd)/data:/app/data" \
          nirva.sell
    ;;

  *)
    echo "nirva.sell deploy helper"
    echo
    echo "Commands:"
    echo "  init <gh-user> <repo>   Initialize git + remote, prep for push"
    echo "  push [\"message\"]       Commit + push (Streamlit Cloud auto-redeploys)"
    echo "  docker                  Build + run locally with Docker"
    echo
    echo "Streamlit Cloud (free):  https://share.streamlit.io"
    ;;
esac
