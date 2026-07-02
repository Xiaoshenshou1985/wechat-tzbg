#!/usr/bin/env python3
"""
统一上传脚本 - 将指定文件提交并推送到 wechat-tzbg 仓库
用法: python upload.py <文件名> [提交消息]
示例: python upload.py a-stock.html "A股盘前日报 2026-06-19"
"""

import subprocess
import sys
import os
import json
from datetime import datetime

REPO = os.path.expanduser('~/wechat-tzbg')
TZ = '+0800'

def run(cmd, capture=True):
    result = subprocess.run(cmd, capture_output=capture, text=True, cwd=REPO)
    return result

def upload(filename, msg=''):
    if not os.path.exists(os.path.join(REPO, filename)):
        print(f"❌ 文件不存在: {filename}")
        return False
    
    # 1. 确保工作目录干净（备份未追踪文件）
    bak_files = []
    for f in ['index.html', 'auth_qr.png']:
        path = os.path.join(REPO, f)
        if os.path.exists(path) and f != filename:
                bak = path + '.bak'
                os.rename(path, bak)
                bak_files.append((f, bak))
    
    try:
        # 2. 拉取远程最新
        r = run(['git', 'pull', '--rebase', 'origin', 'main'])
        if r.returncode != 0:
            print(f"⚠️ 拉取失败，尝试强制同步: {r.stderr[:100]}")
            run(['git', 'rebase', '--abort'])
            r = run(['git', 'fetch', 'origin', 'main'])
        
        # 3. 更新 timestamps.json（把 .html 后缀去掉就是 key）
        page_key = filename.replace('.html', '') if filename.endswith('.html') else filename
        ts_path = os.path.join(REPO, 'timestamps.json')
        ts = {}
        if os.path.exists(ts_path):
            with open(ts_path) as f:
                ts = json.load(f)
        now_local = datetime.now().strftime('%Y-%m-%d %H:%M')
        if filename.endswith('.html'):
            ts[page_key] = now_local
            with open(ts_path, 'w') as f:
                json.dump(ts, f, indent=2, ensure_ascii=False)
                f.write('\n')
            print(f"🕒 timestamps.json: {page_key} → {now_local}")
        
        # 4. 添加 timestamps.json 和报告文件
        run(['git', 'add', filename])
        run(['git', 'add', 'timestamps.json'])
        commit_msg = msg or f"Update {filename}"
        r = run(['git', 'commit', '-m', commit_msg])
        if 'nothing to commit' in r.stderr:
            print(f"ℹ️ {filename} 无变化，跳过")
            return True
        
        # 4. 推送
        r = run(['git', 'push', 'origin', 'main', '--force-with-lease'])
        if r.returncode != 0:
            print(f"❌ 推送失败: {r.stderr[:200]}")
            return False
        
        print(f"✅ {filename} 已上传: {commit_msg}")
        return True
        
    finally:
        # 恢复备份文件
        for f, bak in bak_files:
                if os.path.exists(bak):
                    os.rename(bak, os.path.join(REPO, f))

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python upload.py <文件名> [提交消息]")
        sys.exit(1)
    
    filename = sys.argv[1]
    msg = sys.argv[2] if len(sys.argv) > 2 else f"Update {filename}"
    upload(filename, msg)
