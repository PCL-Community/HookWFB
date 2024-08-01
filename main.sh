#!/bin/bash

PORT=8080
GITHUB_TOKEN="your_github_token"
REPO_OWNER="PCL-Community"
REPO_NAME="PCL2-1930"

add_label() {
    local pr_number="$1"
    local label="$2"
    curl -s -H "Authorization: token $GITHUB_TOKEN" \
         -H "Content-Type: application/json" \
         -X POST \
         -d "{\"labels\": [\"$label\"]}" \
         "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/issues/$pr_number/labels"
}

remove_label() {
    local pr_number="$1"
    local label="$2"
    curl -s -H "Authorization: token $GITHUB_TOKEN" \
         -X DELETE \
         "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/issues/$pr_number/labels/$label"
}

handle_request() {
    local payload="$1"
    event=$(echo "$payload" | jq -r '.action')
    pr_number=$(echo "$payload" | jq -r '.pull_request.number')

    case "$event" in
        "closed")
            if echo "$payload" | jq -r '.pull_request.merged' | grep -q true; then
                add_label "$pr_number" "▲ 合并"
            fi
            ;;
        "submitted")
            review_state=$(echo "$payload" | jq -r '.review.state')
            reviewer=$(echo "$payload" | jq -r '.review.user.login')
            if [[ "$review_state" == "changes_requested" ]]; then
                add_label "$pr_number" "◈ 修正"
                remove_label "$pr_number" "⇵ 通过"
            elif [[ "$review_state" == "approved" && "$reviewer" == "WForst-Breeze" ]]; then
                add_label "$pr_number" "⇵ 通过"
                remove_label "$pr_number" "◈ 修正"
            fi
            ;;
        "labeled")
            label=$(echo "$payload" | jq -r '.label.name')
            if [[ "$label" == "× 拒绝" ]] || [[ "$label" == "× 无效" ]] || [[ "$label" == "× 重新编写" ]]; then
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
        while IFS= read -r line; do
            payload="$payload$line"
            [ "$line" == $'\r' ] && break
        done

        handle_request "$payload"
        echo -e "HTTP/1.1 200 OK\r\n"
    } | nc -l -p "$PORT"
done