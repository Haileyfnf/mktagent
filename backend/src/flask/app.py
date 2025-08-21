from flask import Flask
from backend.src.api.keywords_api import keywords_bp
from backend.src.api.naver_news_api import naver_news_bp
from backend.src.api.articles_api import articles_bp
from backend.src.api.dashboard_summary_api import dashboard_bp
from backend.src.api.keyword_dashboard_api import keyword_dashboard_bp
#from backend.src.api.ml_classification_api import ml_classification_bp
from flask_cors import CORS
from backend.src.api.scheduler import start_scheduler, stop_scheduler
import atexit

# 전역 스케줄러 변수
scheduler = None

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Blueprint 등록
    app.register_blueprint(keywords_bp, url_prefix='/api')
    app.register_blueprint(naver_news_bp, url_prefix='/api')
    app.register_blueprint(articles_bp, url_prefix='/api')
    app.register_blueprint(dashboard_bp, url_prefix='/api')
    app.register_blueprint(keyword_dashboard_bp, url_prefix='/api')
    #app.register_blueprint(ml_classification_bp, url_prefix='/api')
    
    # 스케줄러 시작
    global scheduler
    scheduler = start_scheduler()
    
    # 앱 종료 시 스케줄러 정리
    atexit.register(lambda: stop_scheduler(scheduler))
    
    return app 