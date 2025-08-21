#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Marketing AI Agent Web Application
실행 파일
"""

import argparse
import os
import sys
from dotenv import load_dotenv
import subprocess
from threading import Thread
from backend.src.flask.app import create_app

# 환경 변수 로드
load_dotenv()

# 프로젝트 경로 설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend', 'src'))

def run_flask():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="Marketing AI Agent Web Application")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="서버 호스트 주소")
    parser.add_argument("--port", type=int, default=5000, help="서버 포트")
    parser.add_argument("--debug", action="store_true", help="디버그 모드")
    
    args = parser.parse_args()
    
    # Flask 앱 생성
    app = create_app()
    
    print("🚀 Marketing AI Agent 웹앱을 시작합니다...")
    print(f"📍 URL: http://{args.host}:{args.port}")
    print("📊 API 문서: http://localhost:5000/api/health")
    
    # 웹앱 실행
    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug
    )

def run_react():
    frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
    subprocess.run(['npm', 'start'], cwd=frontend_dir, shell=True)

if __name__ == '__main__':
    flask_thread = Thread(target=run_flask)
    # react_thread = Thread(target=run_react)

    flask_thread.start()
    # react_thread.start()

    flask_thread.join()
    # react_thread.join()
