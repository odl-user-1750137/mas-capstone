#!/bin/bash
set -e

github_username="${GITHUB_USERNAME}"
github_pat="${GITHUB_PAT}"
github_repo_url="${GITHUB_REPO_URL}"
github_user_email="${GITHUB_USER_EMAIL}"

remote_url="https://${github_username}:${github_pat}@${github_repo_url#https://}"

mkdir -p temp_git_repo
cp index.html temp_git_repo/
cd temp_git_repo
git init
git config user.name "$github_username"
git config user.email "$github_user_email"
git add index.html
git commit -m "Auto-push from multi-agent system"
git branch -M main
git remote add origin "$remote_url"
git push -u origin main
