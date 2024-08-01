#!/bin/bash

PORT=8080
GITHUB_TOKEN="your_github_token"
REPO_OWNER="PCL-Community"
REPO_NAME="PCL2-1930"

handle_request() {
    local payload="$1"
    event=$(echo "$payload" | jq -r '.action')
    pr_number=$(echo "$payload" | jq -r '.pull_request.number')

    case "$event" in
        "closed")
            if echo "$payload" | jq -r '.pull_request.merged' | grep -q true; then
                curl -s -H "Authorization: token $GITHUB_TOKEN" \
                     -H "Content-Type: application/json" \
                     -X POST \
                     -d '{"labels": ["▲ 合并"]}' \
                     "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/issues/$pr_number/labels"
            fi
            ;;
        "review_requested")
            reviewer=$(echo "$payload" | jq -r '.requested_reviewer.login')
            if [[ "$reviewer" == "WForst-Breeze" ]]; then
                curl -s -H "Authorization: token $GITHUB_TOKEN" \
                     -H "Content-Type: application/json" \
                     -X POST \
                     -d '{"labels": ["⇵ 通过"]}' \
                     "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/issues/$pr_number/labels"
            fi
            ;;
        "labeled")
            label=$(echo "$payload" | jq -r '.label.name')
            if [[ "$label" == "× 拒绝" ]] || [[ "$label" == "× 无效" ]]; then
                curl -s -H "Authorization: token $GITHUB_TOKEN" \
                     -H "Content-Type: application/json" \
                     -X PATCH \
                     -d '{"state": "closed"}' \
                     "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/pulls/$pr_number"
            fi
            ;;
        "opened")
            curl -s -H "Authorization: token $GITHUB_TOKEN" \
                 -H "Content-Type: application/json" \
                 -X POST \
                 -d '{"reviewers":["WForst-Breeze"]}' \
                 "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/pulls/$pr_number/requested_reviewers"
            ;;
    esac
}

while true; do
    { 
        payload=""
        while read -r line; do
            payload="$payload$line"
        done

        handle_request "$payload"
        echo -e "HTTP/1.1 200 OK\r\n"
    } | nc -l -p "$PORT"
done
