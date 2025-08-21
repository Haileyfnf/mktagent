#!/usr/bin/env python3
"""
AI 분석 서비스 테스트 스크립트
"""
import os
import sys
from pathlib import Path

    # services 디렉토리를 Python 경로에 추가
current_dir = Path(__file__).parent
services_dir = current_dir.parent / "src" / "services"
sys.path.append(str(services_dir))

print("🚀 AI 분석 서비스 테스트 시작...")

try:
    # AI 분석 서비스 import
    print("📦 모듈 import 중...")
    from ai_analysis_service import get_ai_analysis_service
    
    # 서비스 초기화
    print("🔧 AI 분석 서비스 초기화 중...")
    service = get_ai_analysis_service()
    print("✅ AI 분석 서비스 초기화 완료")
    
    # Claude API 키 확인
    claude_api_key = os.getenv("CLAUDE_API_KEY")
    if not claude_api_key:
        print("⚠️  경고: CLAUDE_API_KEY가 설정되지 않았습니다!")
        print("   .env 파일에 CLAUDE_API_KEY=your_key_here 를 추가해주세요.")
        sys.exit(1)
    
    print(f"🔑 Claude API 키: {'*' * 20}...{claude_api_key[-4:] if len(claude_api_key) > 4 else '****'}")
    
    # 캠페인 성과 분석 실행 (2025년 7월 데이터)
    print("📊 캠페인 성과 분석 시작 - 2025년 7월 데이터...")
    print("   (이 과정은 1-3분 정도 소요될 수 있습니다)")
    
    # 2025년 7월 특정 월 분석
    report = service.analyze_campaign_performance(
        days_back=30,  # 이 값은 specific_month가 있으면 무시됨
        brand_id=None,  # 모든 브랜드
        specific_month="2025-07"  # 2025년 7월
    )
    
    print("\n✅ 2025년 7월 분석 완료!")
    print(f"📄 보고서 제목: {report.title}")
    print(f"📅 분석 기간: 2025년 7월 (특정 월 분석)")
    print(f"📅 생성 시간: {report.generated_at}")
    print(f"📁 저장 위치: {service.output_dir}")
    print(f"🔍 핵심 인사이트 수: {len(report.key_insights)}")
    print(f"💡 권장사항 수: {len(report.recommendations)}")
    
    # 저장된 파일 확인
    reports_dir = service.output_dir
    if reports_dir.exists():
        md_files = list(reports_dir.glob("*.md"))
        if md_files:
            print(f"\n📂 생성된 보고서 파일들:")
            for file in sorted(md_files, key=lambda x: x.stat().st_mtime, reverse=True)[:3]:
                size_kb = round(file.stat().st_size / 1024, 2)
                print(f"   📄 {file.name} ({size_kb} KB)")
        else:
            print("⚠️  reports 디렉토리에 .md 파일이 없습니다.")
    else:
        print("⚠️  reports 디렉토리가 생성되지 않았습니다.")
    
except ImportError as e:
    print(f"❌ Import 에러: {e}")
    print("   필요한 패키지를 설치해주세요: pip install anthropic loguru")
    
except Exception as e:
    print(f"❌ 에러 발생: {e}")
    import traceback
    traceback.print_exc()

print("\n🏁 테스트 완료")
