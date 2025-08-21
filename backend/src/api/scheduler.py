from apscheduler.schedulers.background import BackgroundScheduler
from .naver_news_api import run_news_collection
import sqlite3
import os
import logging
from datetime import datetime
import requests
from dotenv import load_dotenv
load_dotenv()

# 로깅 설정
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'news_collection.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'db.sqlite')

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("텔레그램 토큰 또는 채팅 ID가 설정되지 않았습니다.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        response = requests.post(url, data=data, timeout=5)
        if response.status_code != 200:
            logging.error(f"텔레그램 전송 실패: {response.text}")
    except Exception as e:
        logging.error(f"텔레그램 전송 중 오류: {e}")

def scheduled_news_fetch():
    """매일 배치로 뉴스 수집을 실행하는 함수"""
    try:
        logging.info("🚀 매일 뉴스 수집 배치 작업 시작")
        
        # run_news_collection 함수 호출 (이미 구현되어 있음)
        result = run_news_collection()
        
        if result['success']:
            logging.info(f"✅ 뉴스 수집 완료 - 총 {result['total_articles']}개 검색, {result['saved_articles']}개 저장")
            logging.info(f"📊 저장 성공률: {result['success_rate']:.1f}%")
            
            if result.get('failed_keywords'):
                logging.warning(f"⚠️ 실패한 키워드: {result['failed_keywords']}")
            # 텔레그램 알림 전송
            msg = (
                f"✅ 뉴스 수집 완료!\n"
                f"총 {result['total_articles']}개 검색, {result['saved_articles']}개 저장\n"
                f"성공률: {result['success_rate']:.1f}%"
            )
            if result.get('failed_keywords'):
                msg += f"\n⚠️ 실패 키워드: {result['failed_keywords']}"
            send_telegram_message(msg)
        else:
            logging.error(f"❌ 뉴스 수집 실패: {result.get('error', '알 수 없는 오류')}")
            send_telegram_message(f"❌ 뉴스 수집 실패: {result.get('error', '알 수 없는 오류')}")
        
    except Exception as e:
        logging.error(f"❌ 스케줄러 실행 중 오류 발생: {str(e)}")
        send_telegram_message(f"❌ 스케줄러 실행 중 오류 발생: {str(e)}")

def start_scheduler():
    """스케줄러 시작"""
    try:
        scheduler = BackgroundScheduler()
        
        # 매일 오전 9시에 실행 (cron 형식)
        scheduler.add_job(
            scheduled_news_fetch, 
            'cron', 
            hour=9,   # 오전 9시
            minute=0, # 0분
            id='daily_news_collection',
            name='매일 오전 9시 뉴스 수집'
        )
        
        # 테스트용: 1분마다 실행 (개발 시에만 사용)
        # scheduler.add_job(scheduled_news_fetch, 'interval', minutes=1, id='test_news_collection')
        
        scheduler.start()
        logging.info("📅 뉴스 수집 스케줄러가 시작되었습니다.")
        logging.info("⏰ 매시 정시마다 뉴스 수집이 실행됩니다.")
        
        return scheduler
        
    except Exception as e:
        logging.error(f"❌ 스케줄러 시작 실패: {str(e)}")
        return None

def stop_scheduler(scheduler):
    """스케줄러 중지"""
    if scheduler:
        scheduler.shutdown()
        logging.info("🛑 뉴스 수집 스케줄러가 중지되었습니다.")

# 수동 실행용 함수
def run_manual_news_collection():
    """수동으로 뉴스 수집 실행"""
    logging.info("🔧 수동 뉴스 수집 시작")
    result = run_news_collection()
    
    if result['success']:
        print(f"✅ 수동 뉴스 수집 완료!")
        print(f"   총 검색된 기사: {result['total_articles']}개")
        print(f"   총 저장된 기사: {result['saved_articles']}개")
        print(f"   저장 성공률: {result['success_rate']:.1f}%")
    else:
        print(f"❌ 수동 뉴스 수집 실패: {result.get('error', '알 수 없는 오류')}")
    
    return result 