#!/bin/bash

{
    github_username="${GITHUB_USERNAME}"
    github_pat="${GITHUB_PAT}"
    github_repo_url="${GITHUB_REPO_URL}"
    github_user_email="${GITHUB_USER_EMAIL}"

    # Correct assignment (no space around =)
    repo_url="https://${github_username}:${github_pat}@${github_repo_url}"

    echo "Using repo URL: $repo_url"

    # Optional: Configure Git identity if needed
    git config user.name "$github_username"
    git config user.email "$github_user_email"

    git add index.html
    git commit -m "Auto commit - Added or updated index.html" || echo "Nothing to commit."
    git push -u "$repo_url" HEAD:main

    echo "Push Successful"
    read -p "Press any key to close..."
} > script_output.log 2>&1