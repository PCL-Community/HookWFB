from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

GITHUB_TOKEN = 'yuanshen'
GITHUB_USERNAME = 'PCL-Community'

GITHUB_API_URL = 'https://api.github.com'

# 设置Webhook路由
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    payload = request.json
    action = payload.get('action')
    pr = payload.get('pull_request')

    if pr:
        pr_number = pr.get('number')
        pr_labels = [label['name'] for label in pr.get('labels', [])]
        pr_user = pr.get('user', {}).get('login')
        pr_state = pr.get('state')

        # 当PR被标记时
        if action == 'labeled':
            label_name = payload.get('label', {}).get('name')
            if label_name == '通过':
                approve_pr(pr_number)
            elif label_name == '× 拒绝' and pr_state != 'closed':
                close_pr(pr_number)

        # 当PR被WForst-Breeze批准时
        if action == 'submitted' and payload.get('review', {}).get('user', {}).get('login') == 'WForst-Breeze':
            if payload.get('review', {}).get('state') == 'approved':
                add_label(pr_number, '通过')

        # 一个PR被close后且没有被合并
        if action == 'closed' and pr_state == 'closed' and not pr.get('merged'):
            add_label(pr_number, '× 拒绝')

        # 一个PR被创建后
        if action == 'opened':
            request_review(pr_number, 'WForst-Breeze')

        # 一个PR被合并以后
        if action == 'closed' and pr.get('merged'):
            add_label(pr_number, '完成')

    return jsonify({'status': 'success'}), 200
    
    add_label(pr_number, label):
    url = f'{GITHUB_API_URL}/repos/{GITHUB_USERNAME}/PCL2-1930/issues/{pr_number}/labels'
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    data = {'labels': [label]}
    requests.post(url, headers=headers, json=data)

def approve_pr(pr_number):
    url = f'{GITHUB_API_URL}/repos/{GITHUB_USERNAME}/PCL2-1930/pulls/{pr_number}/reviews'
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    data = {'event': 'APPROVE'}
    requests.post(url, headers=headers, json=data)

def close_pr(pr_number):
    url = f'{GITHUB_API_URL}/repos/{GITHUB_USERNAME}/PCL2-1930/pulls/{pr_number}'
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    data = {'state': 'closed'}
    requests.patch(url, headers=headers, json=data)

def request_review(pr_number, reviewer):
    url = f'{GITHUB_API_URL}/repos/{GITHUB_USERNAME}/PCL2-1930/pulls/{pr_number}/requested_reviewers'
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    data = {'reviewers': [reviewer]}
    requests.post(url, headers=headers, json=data)

if __name__ == '__main__':
    app.run(debug=True)
