#!/bin/bash
{
    github_username="${GITHUB_USERNAME}"
    github_pat="${GITHUB_PAT}"
    github_repo_url="${GITHUB_REPO_URL}"
    github_user_email="${GITHUB_USER_EMAIL}"
    repo_url = "https://$github_username:$github_pat@$github_repo_url"
    echo "$repo_url"
    git add index.html
    git commit -m "Auto commit - Added or updated index.html"
    git push -u "$repo_url" HEAD:main
    echo "Push Successfull"
    read -p "Press any key to close..."
} > script_output.log 2>&1

