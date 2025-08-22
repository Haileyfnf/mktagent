import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import './KeywordDashboard.css';
import Toast from '../components/Toast';

interface Article {
  id: number;
  title: string;
  press: string;
  pub_date: string;
  url: string;
  classification_result: '보도자료' | '오가닉' | '해당없음' | 'unknown';
  confidence_score: number;
}

interface KeywordStats {
  keyword: string;
  type: string;
  total_articles: number;
  press_releases: number;
  organic_articles: number;
  mention_rate: number;
}

const KeywordDashboard: React.FC = () => {
  const { groupName } = useParams<{ groupName: string }>();
  const navigate = useNavigate();
  
  const [articles, setArticles] = useState<Article[]>([]);
  const [stats, setStats] = useState<KeywordStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | '보도자료' | '오가닉'>('all');
  const [sortBy, setSortBy] = useState<'date' | 'title' | 'press'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [selectedMonth, setSelectedMonth] = useState<string>('');
  const [availableMonths, setAvailableMonths] = useState<string[]>([]);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);
  const [showReasonModal, setShowReasonModal] = useState(false);
  const [reasonData, setReasonData] = useState<{
    title: string;
    classification_result: string;
    confidence_score: number;
    reason: string;
    created_at: string;
    article_id: number; // Added for update
  } | null>(null);
  const [editingArticleId, setEditingArticleId] = useState<number | null>(null);
  const [editingInModal, setEditingInModal] = useState(false);
  const [editClassification, setEditClassification] = useState('');
  const [editReason, setEditReason] = useState('');

  // reasonData가 바뀔 때만 초기화
  useEffect(() => {
    setEditReason(reasonData?.reason || '');
  }, [reasonData]);

  const loadKeywordData = useCallback(async () => {
    try {
      setLoading(true);
      
      // 통계 데이터 로드
      const statsResponse = await fetch(`http://localhost:5000/api/keywords/group/${groupName}/stats`);
      const statsData = await statsResponse.json();
      if (statsData.success) {
        setStats(statsData.data);
      }

      // 기사 데이터 로드
      const articlesResponse = await fetch(`http://localhost:5000/api/keywords/group/${groupName}/articles`);
      const articlesData = await articlesResponse.json();
      if (articlesData.success) {
        setArticles(articlesData.data);
        
        // 사용 가능한 월 목록 생성
        const months = new Set<string>();
        articlesData.data.forEach((article: Article) => {
          const date = new Date(article.pub_date);
          const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
          months.add(monthKey);
        });
        
        const sortedMonths = Array.from(months).sort().reverse(); // 최신 월 먼저
        setAvailableMonths(sortedMonths);
        
        // 기본값을 현재 월로 설정 (초기 로드 시에만)
        if (selectedMonth === '') {
          const currentMonth = new Date().toISOString().slice(0, 7); // YYYY-MM 형식
          if (sortedMonths.includes(currentMonth)) {
            setSelectedMonth(currentMonth);
          } else if (sortedMonths.length > 0) {
            setSelectedMonth(sortedMonths[0]); // 데이터가 있는 가장 최신 월
          }
        }
      }
    } catch (error) {
      console.error('키워드 데이터 로드 실패:', error);
      showMessage('데이터를 불러오는데 실패했습니다.', 'error');
    } finally {
      setLoading(false);
    }
  }, [groupName, selectedMonth]);

  useEffect(() => {
    if (groupName) {
      loadKeywordData();
    }
  }, [groupName, loadKeywordData]);

  const showMessage = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const filteredArticles = articles.filter(article => {
    // 분류 필터
    const classificationMatch = filter === 'all' || article.classification_result === filter;
    
    // 월 필터
    let monthMatch = true;
    if (selectedMonth && selectedMonth !== 'all') {
      const articleDate = new Date(article.pub_date);
      const articleMonth = `${articleDate.getFullYear()}-${String(articleDate.getMonth() + 1).padStart(2, '0')}`;
      monthMatch = articleMonth === selectedMonth;
    }
    
    return classificationMatch && monthMatch;
  });

  const sortedArticles = [...filteredArticles].sort((a, b) => {
    let result = 0;
    
    switch (sortBy) {
      case 'date':
        result = new Date(a.pub_date).getTime() - new Date(b.pub_date).getTime();
        break;
      case 'title':
        result = a.title.localeCompare(b.title, 'ko');
        break;
      case 'press':
        result = a.press.localeCompare(b.press, 'ko');
        break;
    }
    
    return sortOrder === 'desc' ? -result : result;
  });

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const updateClassification = async (articleId: number, newClassification: string) => {
    try {
      const response = await fetch(`http://localhost:5000/api/keywords/article/${articleId}/classification`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ classification: newClassification }),
      });
      
      const data = await response.json();
      
      if (data.success) {
        // 기사 목록 업데이트
        setArticles(prevArticles => 
          prevArticles.map(article => 
            article.id === articleId 
              ? { ...article, classification_result: newClassification as any, confidence_score: 1.0 }
              : article
          )
        );
        setEditingArticleId(null);
        showMessage('분류가 성공적으로 업데이트되었습니다.', 'success');
      } else {
        showMessage(data.message || '분류 업데이트에 실패했습니다.', 'error');
      }
    } catch (error) {
      console.error('분류 업데이트 실패:', error);
      showMessage('분류 업데이트에 실패했습니다.', 'error');
    }
  };

  // 수정 버튼 클릭 시 초기값 세팅 (최적화)
  const handleEditClick = () => {
    setEditClassification(reasonData?.classification_result || '');
    setEditReason(reasonData?.reason || '');
    setEditingInModal(true);
  };

  // 분류 수정 저장 함수
  const handleSaveClassification = async () => {
    await updateClassificationInModal(editClassification, editReason);
    setEditingInModal(false);
  };

  // updateClassificationInModal 함수 수정
  const updateClassificationInModal = async (newClassification: string, newReason: string) => {
    if (!reasonData) return;
    if (!newClassification || newClassification.trim() === '') return;
    try {
      const response = await fetch(`http://localhost:5000/api/keywords/article/${reasonData.article_id}/classification`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ classification: newClassification, reason: newReason }),
      });
      const data = await response.json();
      if (data.success) {
        setArticles(prevArticles => 
          prevArticles.map(article => 
            article.id === reasonData.article_id 
              ? { ...article, classification_result: newClassification as any, confidence_score: 1.0 }
              : article
          )
        );
        setReasonData(prev => prev ? {
          ...prev,
          classification_result: newClassification,
          confidence_score: 1.0,
          reason: newReason,
          created_at: new Date().toISOString().replace('T', ' ').substring(0, 19)
        } : null);
        showMessage('분류가 성공적으로 업데이트되었습니다.', 'success');
      } else {
        showMessage(data.message || '분류 업데이트에 실패했습니다.', 'error');
      }
    } catch (error) {
      console.error('분류 업데이트 실패:', error);
      showMessage('분류 업데이트에 실패했습니다.', 'error');
    }
  };

  const showClassificationReason = async (articleId: number) => {
    try {
      const response = await fetch(`http://localhost:5000/api/keywords/article/${articleId}/classification-reason`);
      const data = await response.json();
      
      if (data.success) {
        setReasonData({...data.data, article_id: articleId});
        setShowReasonModal(true);
        setEditingInModal(false);
      } else {
        showMessage('분류 이유를 불러올 수 없습니다.', 'error');
      }
    } catch (error) {
      console.error('분류 이유 로드 실패:', error);
      showMessage('분류 이유를 불러오는데 실패했습니다.', 'error');
    }
  };

  const getClassificationBadge = (classification: string, confidence: number, articleId: number) => {
    const badgeClass = classification === '보도자료' ? 'press-release' : 
                      classification === '오가닉' ? 'organic' : 'unknown';
    
    // 편집 모드인 경우 드롭다운 표시
    if (editingArticleId === articleId) {
      return (
        <select 
          className="classification-edit-select"
          value={classification}
          onChange={(e) => updateClassification(articleId, e.target.value)}
          onBlur={() => setEditingArticleId(null)}
          autoFocus
        >
          <option value="보도자료">보도자료</option>
          <option value="오가닉">오가닉</option>
          <option value="해당없음">해당없음</option>
        </select>
      );
    }
    
    return (
      <span 
        className={`classification-badge ${badgeClass} clickable`}
        onClick={() => showClassificationReason(articleId)}
        title="클릭하여 분류 이유 보기"
      >
        {classification === '보도자료' ? '보도자료' : 
         classification === '오가닉' ? '오가닉' : 
         classification === '해당없음' ? '해당없음' : '미분류'}
        <small className="confidence">({Math.round(confidence * 100)}%)</small>
      </span>
    );
  };

  if (loading) {
    return (
      <>
        <div className="custom-page-title">
          <button className="page-title-back-button" onClick={() => navigate(-1)}>
            <span className="icon">←</span>
            뒤로가기
          </button>
        </div>
        <div className="keyword-dashboard">
          <div className="dashboard-header">
            <div className="header-info">
              <h1>{groupName}</h1>
            </div>
          </div>
          <div className="loading">데이터를 불러오는 중...</div>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="custom-page-title">
        <button className="page-title-back-button" onClick={() => navigate(-1)}>
          <span className="icon">←</span>
          뒤로가기
        </button>
      </div>
      <div className="keyword-dashboard">
        {/* Toast 알림 */}
        {toast && (
          <Toast
            message={toast.message}
            type={toast.type}
            onClose={() => setToast(null)}
          />
        )}

        {/* 분류 수정 모달 */}
        {showReasonModal && reasonData && (
          <div className="modal-overlay" onClick={() => setShowReasonModal(false)}>
            <div className="reason-modal" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h3>분류</h3>
                <button className="close-btn" onClick={() => setShowReasonModal(false)}>
                  ×
                </button>
              </div>
              <div className="modal-content">
                <div className="reason-item">
                  <strong>기사 제목:</strong>
                  <p>{reasonData.title}</p>
                </div>
                <div className="reason-item">
                  <strong>분류 결과:</strong>
                  <div className="classification-edit-container" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: 8 }}>
                    {editingInModal ? (
                      <>
                        <select
                          className="classification-modal-select"
                          value={editClassification}
                          onChange={e => setEditClassification(e.target.value)}
                          autoFocus
                        >
                          <option value="">선택하세요</option>
                          <option value="보도자료">보도자료</option>
                          <option value="오가닉">오가닉</option>
                          <option value="해당없음">해당없음</option>
                        </select>
                        <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
                          <button className="edit-classification-btn" onClick={handleSaveClassification}>
                            저장
                          </button>
                          <button className="edit-classification-btn" style={{ background: '#e1e4e8', color: '#666' }} onClick={() => setEditingInModal(false)}>
                            취소
                          </button>
                        </div>
                      </>
                    ) : (
                      <div className="classification-display">
                        <span className={`classification-result ${reasonData.classification_result}`}>
                          {reasonData.classification_result === '보도자료' ? '보도자료' : 
                           reasonData.classification_result === '오가닉' ? '오가닉' : 
                           reasonData.classification_result === '해당없음' ? '해당없음' : '미분류'}
                        </span>
                        <button 
                          className="edit-classification-btn"
                          onClick={handleEditClick}
                        >
                          수정
                        </button>
                      </div>
                    )}
                  </div>
                </div>
                <div className="reason-item">
                  <strong>신뢰도:</strong>
                  <span>{Math.round(reasonData.confidence_score * 100)}%</span>
                </div>
                <div className="reason-item">
                  <strong>분류 이유:</strong>
                  {editingInModal ? (
                    <textarea
                      value={editReason}
                      onChange={e => setEditReason(e.target.value)}
                      placeholder="분류 이유를 입력하세요"
                      rows={3}
                      style={{ width: '100%' }}
                    />
                  ) : (
                    <p className="reason-text">{reasonData.reason}</p>
                  )}
                </div>
                <div className="reason-item">
                  <strong>분류 일시:</strong>
                  <span>
                    {reasonData.created_at && reasonData.created_at !== '1970-01-01 09:00:00' && reasonData.created_at !== null
                      ? new Date(reasonData.created_at).toLocaleString('ko-KR')
                      : '-'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 헤더 */}
        <div className="dashboard-header">
          <div className="header-info">
            <h1>{groupName}</h1>
            {stats && (
              <span className={`keyword-type ${stats.type === '경쟁사' ? 'competitor' : 'company'}`}>
                {stats.type}
              </span>
            )}
          </div>
        </div>

      {/* 통계 카드 */}
      {stats && (
        <div className="stats-overview">
          <div className="stat-card">
            <h3>이번 달 기사</h3>
            <div className="value">{stats.total_articles || 0}</div>
          </div>
          <div className="stat-card">
            <h3>보도자료</h3>
            <div className="value">{stats.press_releases || 0}</div>
          </div>
          <div className="stat-card">
            <h3>오가닉 기사</h3>
            <div className="value">{stats.organic_articles || 0}</div>
          </div>
          <div className="stat-card">
            <h3>보도자료 커버리지</h3>
            <div className="value">{stats.mention_rate || 0}%</div>
          </div>
        </div>
      )}

      {/* 데이터가 없을 때 기본 통계 카드 표시 */}
      {!loading && !stats && (
        <div className="stats-overview">
          <div className="stat-card">
            <h3>전체 기사</h3>
            <div className="value">0</div>
          </div>
          <div className="stat-card">
            <h3>보도자료</h3>
            <div className="value">0</div>
          </div>
          <div className="stat-card">
            <h3>오가닉 기사</h3>
            <div className="value">0</div>
          </div>
          <div className="stat-card">
            <h3>보도자료 커버리지</h3>
            <div className="value">0%</div>
          </div>
        </div>
      )}

      {/* 필터 및 정렬 */}
      <div className="controls">
        <div className="filters">
          <label>분류:</label>
          <select value={filter} onChange={(e) => setFilter(e.target.value as any)}>
            <option value="all">전체</option>
            <option value="보도자료">보도자료</option>
            <option value="오가닉">오가닉</option>
          </select>
          
          <label style={{ marginLeft: '20px' }}>월별:</label>
          <select value={selectedMonth} onChange={(e) => setSelectedMonth(e.target.value)}>
            <option value="all">전체 기간</option>
            {availableMonths.map(month => (
              <option key={month} value={month}>
                {new Date(month + '-01').toLocaleDateString('ko-KR', { 
                  year: 'numeric', 
                  month: 'long' 
                })}
              </option>
            ))}
          </select>
        </div>
        
        <div className="sorting">
          <label>정렬:</label>
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value as any)}>
            <option value="date">게재일</option>
            <option value="title">제목</option>
            <option value="press">언론사</option>
          </select>
          <button 
            className={`sort-order ${sortOrder === 'desc' ? 'desc' : 'asc'}`}
            onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
          >
            {sortOrder === 'desc' ? '↓' : '↑'}
          </button>
        </div>
      </div>

      {/* 기사 리스트 */}
      <div className="articles-section">
        <div className="section-header">
          <h2>수집된 기사 ({sortedArticles.length}건)</h2>
        </div>
        
        <div className="articles-table">
          <div className="table-header">
            <div className="col-date">게재일</div>
            <div className="col-title">제목</div>
            <div className="col-press">언론사</div>
            <div className="col-classification">분류</div>
            <div className="col-actions">링크</div>
          </div>
          
          <div className="table-body">
            {sortedArticles.map((article) => (
              <div key={article.id} className="table-row">
                <div className="col-date">
                  {formatDate(article.pub_date)}
                </div>
                <div className="col-title">
                  <span className="article-title" title={article.title}>
                    {article.title}
                  </span>
                </div>
                <div className="col-press">
                  {article.press}
                </div>
                <div className="col-classification">
                  {getClassificationBadge(article.classification_result, article.confidence_score, article.id)}
                </div>
                <div className="col-actions">
                  <a 
                    href={article.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="link-button"
                  >
                    보기
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>

        {sortedArticles.length === 0 && (
          <div className="no-articles">
            선택한 필터에 해당하는 기사가 없습니다.
          </div>
        )}
      </div>
      </div>
    </>
  );
};

export default KeywordDashboard; 