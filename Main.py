import logging
from flask import Flask, request, jsonify
import requests
from random import randint
from config import *

app = Flask(__name__)

# 设置日志记录
logging.basicConfig(filename='app.log', level=logging.INFO, format='[%(asctime)s] %(levelname)s > %(message)s')

# 设置Webhook路由
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    payload = request.json
    action = payload.get('action')
    pr = payload.get('pull_request')

    if pr:
        pr_number = pr.get('number')
        pr_labels = [label['name'] for label in pr.get('labels', [])]
        pr_state = pr.get('state')

        # 记录接收到的Webhook
        tempid = randint(1, 10000)
        logging.log(logging.INFO, f'[#{tempid}] 接收到 PR WebHook: {action}')

        # 当PR被标记时
        if action == 'labeled':
            logging.log(logging.INFO, f'[#{tempid}] WebHook 类型为被标记')
            label_name = payload.get('label', {}).get('name')
            if label_name == '通过':
                logging.log(logging.INFO, f'[#{tempid}] 标记类型为 通过')
                approve_pr(pr_number, tempid)
            elif label_name == '拒绝' and pr_state != 'closed':
                logging.log(logging.INFO, f'[#{tempid}] 标记类型为 拒绝')
                close_pr(pr_number, tempid)
            else:
                logging.log(logging.INFO, f'[#{tempid}] 标记类型不是期望处理的')

        # 当PR被WForst-Breeze批准时
        if action == 'submitted' and payload.get('review', {}).get('user', {}).get('login') == 'WForst-Breeze':
            logging.log(logging.INFO, f'[#{tempid}] WebHook 类型为被 WForst-Breeze 批准')
            if payload.get('review', {}).get('state') == 'approved':
                add_label(pr_number, '⇵ 通过', tempid)

        # 一个PR被close后且没有被合并
        if action == 'closed' and pr_state == 'closed' and not pr.get('merged'):
            logging.log(logging.INFO, f'[#{tempid}] WebHook 类型为非合并的关闭')
            add_label(pr_number, '× 拒绝', tempid)

        # 一个PR被创建后
        if action == 'opened':
            logging.log(logging.INFO, f'[#{tempid}] WebHook 类型为新 PR')
            request_review(pr_number, 'WForst-Breeze', tempid)

        # 一个PR被合并以后
        if action == 'closed' and pr.get('merged'):
            logging.log(logging.INFO, f'[#{tempid}] WebHook 类型为合并')
            add_label(pr_number, '√ 完成', tempid)

    return jsonify({'status': 'success'}), 200

def add_label(pr_number, label, tempid):
    try:
        url = f'{GITHUB_API_URL}/repos/{GITHUB_USERNAME}/PCL2-1930/issues/{pr_number}/labels'
        headers = {'Authorization': f'token {GITHUB_TOKEN}'}
        data = {'labels': [label]}
        requests.post(url, headers=headers, json=data)
        logging.log(logging.INFO, f'[#{tempid}] 往第 {pr_number} 号 PR 添加标签 {label} 成功')
    except:
        logging.log(logging.ERROR, f'[#{tempid}] 往第 {pr_number} 号 PR 添加标签 {label} 失败')

def approve_pr(pr_number, tempid):
    try:
        url = f'{GITHUB_API_URL}/repos/{GITHUB_USERNAME}/PCL2-1930/pulls/{pr_number}/reviews'
        headers = {'Authorization': f'token {GITHUB_TOKEN}'}
        data = {'event': 'APPROVE'}
        requests.post(url, headers=headers, json=data)
        logging.log(logging.INFO, f'[#{tempid}] 批准第 {pr_number} 号 PR 成功')
    except:
        logging.log(logging.ERROR, f'[#{tempid}] 批准第 {pr_number} 号 PR 失败')

def close_pr(pr_number, tempid):
    try:
        url = f'{GITHUB_API_URL}/repos/{GITHUB_USERNAME}/PCL2-1930/pulls/{pr_number}'
        headers = {'Authorization': f'token {GITHUB_TOKEN}'}
        data = {'state': 'closed'}
        requests.patch(url, headers=headers, json=data)
        logging.log(logging.INFO, f'[#{tempid}] 关闭第 {pr_number} 号 PR 成功')
    except:
        logging.log(logging.ERROR, f'[#{tempid}] 关闭第 {pr_number} 号 PR 失败')

def request_review(pr_number, reviewer, tempid):
    try:
        url = f'{GITHUB_API_URL}/repos/{GITHUB_USERNAME}/PCL2-1930/pulls/{pr_number}/requested_reviewers'
        headers = {'Authorization': f'token {GITHUB_TOKEN}'}
        data = {'reviewers': [reviewer]}
        requests.post(url, headers=headers, json=data)
        logging.log(logging.INFO, f'[#{tempid}] 请求 {reviewer} 审查第 {pr_number} 号 PR 成功')
    except:
        logging.log(logging.ERROR, f'[#{tempid}] 请求 {reviewer} 审查第 {pr_number} 号 PR 失败')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=18000, debug=True)
