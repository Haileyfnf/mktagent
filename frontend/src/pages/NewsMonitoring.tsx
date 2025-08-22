import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import './NewsMonitoring.css';
import Toast from '../components/Toast';
import ConfirmModal from '../components/ConfirmModal';

interface Keyword {
  id: number;
  keyword: string;
  type: string;
  group_name?: string;
}

interface Stats {
  total_count: number;
  week_articles: number;
  week_press_releases: number;
  week_organic_articles: number;
}

interface MonthlyStats {
  keyword: string;
  type: string;
  group_name: string;
  total_articles: number;
  press_releases: number;
  mention_rate: number;
}

const NewsMonitoring: React.FC = () => {
  const navigate = useNavigate();
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [stats, setStats] = useState<Stats | null>(null); // 키워드 수
  const [summaryStats, setSummaryStats] = useState<any>(null); // 주간 기사 등
  const [showModal, setShowModal] = useState(false);
  const [newKeyword, setNewKeyword] = useState('');
  const [newGroupName, setNewGroupName] = useState('');
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editKeywordId, setEditKeywordId] = useState<number | null>(null);
  const [editKeyword, setEditKeyword] = useState('');
  const [editType, setEditType] = useState('');
  const [editGroupName, setEditGroupName] = useState('');
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [deleteTargetId, setDeleteTargetId] = useState<number | null>(null);
  const [monthlyStats, setMonthlyStats] = useState<MonthlyStats[]>([]);

  const loadKeywords = useCallback(async () => {
    console.log('키워드 목록 요청:', 'http://localhost:5000/api/keywords');
    try {
      const response = await fetch('http://localhost:5000/api/keywords');
      const data = await response.json();
      if (data.keywords) {
        setKeywords(sortKeywords(data.keywords));
        console.log('키워드 목록 응답:', data);
      }
    } catch (error) {
      console.error('키워드 로드 실패:', error);
      console.log('키워드 목록 에러:', error);
    }
  }, []);

  useEffect(() => {
    loadStats();
    loadSummaryStats();
    loadKeywords();
    loadMonthlyStats();
  }, [loadKeywords]);

  const loadStats = async () => {
    console.log('통계 요청:', 'http://localhost:5000/api/keywords/stats');
    try {
      const response = await fetch('http://localhost:5000/api/keywords/stats');
      const data = await response.json();
      if (data.success) {
        setStats(data.data);
        console.log('통계 응답:', data);
      }
    } catch (error) {
      console.error('통계 로드 실패:', error);
      console.log('통계 에러:', error);
    }
  };

  const loadSummaryStats = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/dashboard/summary');
      const data = await response.json();
      if (data.success) setSummaryStats(data.data);
    } catch (error) {
      console.error('요약 통계 로드 실패:', error);
    }
  };

  const loadMonthlyStats = async () => {
    console.log('월간 통계 요청:', 'http://localhost:5000/api/keywords/monthly_stats');
    try {
      const response = await fetch('http://localhost:5000/api/keywords/monthly_stats');
      const data = await response.json();
      if (data.success) {
        setMonthlyStats(data.data);
        console.log('월간 통계 응답:', data);
      }
    } catch (error) {
      console.error('월간 통계 로드 실패:', error);
      console.log('월간 통계 에러:', error);
    }
  };

  const addKeyword = async () => {
    console.log('addKeyword 요청:', 'http://localhost:5000/api/keywords', { keyword: newKeyword, group_name: newGroupName });
    if (!newKeyword.trim()) {
      showMessage('키워드를 입력해주세요.', 'error');
      return;
    }

    if (keywords.some(k => k.keyword === newKeyword)) {
      showMessage('이미 존재하는 키워드입니다.', 'error');
      return;
    }

    try {
      const response = await fetch('http://localhost:5000/api/keywords', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ keyword: newKeyword, group_name: newGroupName })
      });

      const data = await response.json();
      if (data.success) {
        showMessage(data.message, 'success');
        setNewKeyword('');
        setNewGroupName('');
        setShowModal(false);
        loadKeywords();
        loadStats();
        console.log('addKeyword 응답:', data);
      } else {
        showMessage('오류: ' + data.error, 'error');
      }
    } catch (error) {
      showMessage('서버 연결에 실패했습니다.', 'error');
      console.log('addKeyword 에러:', error);
    }
  };

  const deleteKeyword = async (id: number) => {
    setDeleteTargetId(id);
    setShowConfirmModal(true);
  };

  const confirmDelete = async () => {
    if (!deleteTargetId) return;

    try {
      const response = await fetch(`http://localhost:5000/api/keywords/${deleteTargetId}`, {
        method: 'DELETE'
      });

      const data = await response.json();
      if (data.success) {
        showMessage(data.message, 'success');
        loadKeywords();
        loadStats();
      } else {
        showMessage('오류: ' + data.error, 'error');
      }
    } catch (error) {
      showMessage('서버 연결에 실패했습니다.', 'error');
    } finally {
      setShowConfirmModal(false);
      setDeleteTargetId(null);
    }
  };

  const openEditModal = (keywordObj: Keyword) => {
    setEditKeywordId(keywordObj.id);
    setEditKeyword(keywordObj.keyword);
    setEditType(keywordObj.type);
    setEditGroupName(keywordObj.group_name || '');
    setEditModalOpen(true);
  };

  const updateKeyword = async () => {
    if (!editKeywordId) return;
    if (keywords.some(k => k.keyword === editKeyword && k.id !== editKeywordId)) {
      showMessage('이미 존재하는 키워드입니다.', 'error');
      return;
    }
    try {
      const response = await fetch(`http://localhost:5000/api/keywords/${editKeywordId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ keyword: editKeyword, type: editType, group_name: editGroupName, is_active: 1 })
      });
      const data = await response.json();
      if (data.success) {
        showMessage(data.message, 'success');
        setEditModalOpen(false);
        loadKeywords();
        loadStats();
      } else {
        showMessage('오류: ' + data.error, 'error');
      }
    } catch (error) {
      showMessage('서버 연결에 실패했습니다.', 'error');
    }
  };

  const showMessage = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const sortKeywords = (keywords: Keyword[]) => {
    return [...keywords].sort((a, b) => {
      // 1순위: 자사 우선
      if (a.type !== b.type) {
        return a.type === '자사' ? -1 : 1;
      }
      // 2순위: 그룹명 가나다순
      if (a.group_name !== b.group_name) {
        return (a.group_name || '').localeCompare(b.group_name || '', 'ko');
      }
      // 3순위: 키워드 가나다순
      return a.keyword.localeCompare(b.keyword, 'ko');
    });
  };

  // group_name 단위로 월간 통계 합산
  const groupMonthlyStats = monthlyStats.reduce((acc: Record<string, any>, item) => {
    const key = item.group_name;
    if (!acc[key]) {
      acc[key] = {
        group_name: item.group_name,
        type: item.type,
        total_articles: 0,
        press_releases: 0,
        mention_rate: 0,
      };
    }
    acc[key].total_articles += item.total_articles;
    acc[key].press_releases += item.press_releases;
    return acc;
  }, {});

  // 전체 보도자료 수 계산 (모든 그룹의 보도자료 합계)
  const totalPressReleases = Object.values(groupMonthlyStats).reduce((sum: number, item: any) => sum + item.press_releases, 0);

  // 보도자료 비중 = (각 그룹 보도자료 수 / 전체 보도자료 수) × 100
  const groupMonthlyStatsArr = Object.values(groupMonthlyStats).map((item: any) => ({
    ...item,
    mention_rate: totalPressReleases ? Math.round((item.press_releases / totalPressReleases) * 100) : 0
  }));

  return (
    <div className="news-monitoring-content">
      {/* Toast 알림 */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      {/* Confirm Modal */}
      {showConfirmModal && (
        <ConfirmModal
          title="키워드 삭제"
          message="이 키워드를 삭제하시겠습니까?"
          onConfirm={confirmDelete}
          onCancel={() => {
            setShowConfirmModal(false);
            setDeleteTargetId(null);
          }}
        />
      )}

      {/* 통계 카드 대시보드 */}
      <div className="dashboard-stats">
        <div className="stat-card">
          <h3>모니터링 브랜드</h3>
          <div className="value" style={{ color: '#4285f4' }}>{stats ? stats.total_count : 0}</div>
        </div>
        <div className="stat-card">
          <h3>이번 달 수집된 기사</h3>
          <div className="value" style={{ color: '#4285f4' }}>{summaryStats ? summaryStats.month_articles : 0}</div>
        </div>
        <div className="stat-card">
          <h3>보도자료</h3>
          <div className="value" style={{ color: '#4285f4' }}>{summaryStats ? summaryStats.month_press_releases : 0}</div>
        </div>
        <div className="stat-card">
          <h3>오가닉 기사</h3>
          <div className="value" style={{ color: '#4285f4' }}>{summaryStats ? summaryStats.month_organic_articles : 0}</div>
        </div>
      </div>

      {/* 월간 통계 카드 */}
      <div className="section">
        <div className="section-header">
          <h2 className="section-title">월간 통계</h2>
        </div>
        <div className="monitoring-status">
          {groupMonthlyStatsArr.map((item) => (
            <div 
              key={item.group_name} 
              className="status-card clickable" 
              onClick={() => navigate(`/keyword-dashboard/${encodeURIComponent(item.group_name)}`)}
            >
                             <div className="status-header">
                 <h3 className="status-title" title={item.group_name}>{item.group_name}</h3>
                 <span className={`brand-type ${item.type === '경쟁사' ? 'competitor' : 'company'}`}>{item.type}</span>
               </div>
              <div className="status-metrics">
                                 <div className="metric">
                   <div className="metric-label">전체 기사<br/>&nbsp;</div>
                   <div className="metric-value">{item.total_articles}</div>
                 </div>
                 <div className="metric">
                   <div className="metric-label">보도 자료<br/>&nbsp;</div>
                   <div className="metric-value">{item.press_releases}</div>
                 </div>
                                   <div className="metric">
                    <div className="metric-label">보도자료<br/>커버리지</div>
                    <div className="metric-value">{item.mention_rate}%</div>
                  </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 브랜드 관리 */}
      <div className="section">
        <div className="section-header">
          <h2 className="section-title">모니터링 키워드</h2>
          <button className="btn-primary" onClick={() => setShowModal(true)}>
            + 키워드 추가
          </button>
        </div>
        <div className="brand-list">
          {keywords.map((keyword) => (
            <div key={keyword.id} className="brand-item">
              <div className="brand-info">
                <span className={`brand-type ${keyword.type === '경쟁사' ? 'competitor' : 'company'}`}>{keyword.type || '자사'}</span>
                <span className="brand-name">{keyword.keyword}</span>
                <span className="group-name" style={{ marginLeft: '10px', color: '#888', fontSize: '13px' }}>
                  그룹: {keyword.group_name}
                </span>
              </div>
              <div className="brand-actions">
                <button className="btn-icon" onClick={() => openEditModal(keyword)}>
                  <svg width="16" height="16" fill="#666" viewBox="0 0 24 24">
                    <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
                  </svg>
                </button>
                <button className="btn-icon" onClick={() => deleteKeyword(keyword.id)}>
                  <svg width="16" height="16" fill="#666" viewBox="0 0 24 24">
                    <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 알림 설정 */}
      <div className="section">
        <div className="section-header">
          <h2 className="section-title">알림 설정</h2>
        </div>
        <div className="notification-settings">
          <div className="setting-item">
            <div className="setting-info">
              <h4>일일 리포트</h4>
              <p>매일 오전 9시에 전일 모니터링 결과를 이메일로 전송</p>
            </div>
            <label className="toggle-switch">
              <input type="checkbox" defaultChecked />
              <span className="toggle-slider"></span>
            </label>
          </div>

          <div className="setting-item">
            <div className="setting-info">
              <h4>실시간 알림</h4>
              <p>중요 이슈 발생 시 즉시 알림</p>
            </div>
            <label className="toggle-switch">
              <input type="checkbox" defaultChecked />
              <span className="toggle-slider"></span>
            </label>
          </div>

          <div className="setting-item">
            <div className="setting-info">
              <h4>주간 분석 리포트</h4>
              <p>매주 월요일 오전 10시에 주간 트렌드 분석 리포트 전송</p>
            </div>
            <label className="toggle-switch">
              <input type="checkbox" />
              <span className="toggle-slider"></span>
            </label>
          </div>
        </div>
      </div>

      {/* 브랜드 추가 모달 */}
      {showModal && (
        <div className="modal" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">키워드 추가</h3>
              <button className="close-btn" onClick={() => setShowModal(false)}>
                &times;
              </button>
            </div>
            
            <div className="brand-form">
              <div className="form-group">
                <label>키워드명</label>
                <input
                  type="text"
                  placeholder="키워드명 입력"
                  value={newKeyword}
                  onChange={(e) => setNewKeyword(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter') {
                      addKeyword();
                    }
                  }}
                />
              </div>
              <div className="form-group">
                <label>유형</label>
                <div style={{ color: '#888', fontSize: '13px', marginTop: '8px' }}>
                  유형은 AI가 자동 분류할 예정입니다
                </div>
              </div>
              <div className="form-group">
                <label>그룹명</label>
                <div style={{ color: '#888', fontSize: '13px', marginTop: '8px' }}>
                  그룹명은 AI가 자동 분류할 예정입니다
                </div>
              </div>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '30px' }}>
              <button 
                type="button" 
                className="btn-primary" 
                style={{ background: '#e1e4e8', color: '#666' }} 
                onClick={() => setShowModal(false)}
              >
                취소
              </button>
              <button type="button" className="btn-primary" onClick={addKeyword}>
                추가
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 키워드 수정 모달 */}
      {editModalOpen && (
        <div className="modal" onClick={() => setEditModalOpen(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">키워드 수정</h3>
              <button className="close-btn" onClick={() => setEditModalOpen(false)}>&times;</button>
            </div>
            <div className="brand-form">
              <div className="form-group">
                <label>키워드명</label>
                <input type="text" value={editKeyword} onChange={e => setEditKeyword(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') { updateKeyword(); } }} />
              </div>
              <div className="form-group">
                <label>유형</label>
                <select value={editType} onChange={e => setEditType(e.target.value)} style={{ padding: '12px', border: '1px solid #e1e4e8', borderRadius: '6px', fontSize: '14px', width: '100%' }} onKeyDown={e => { if (e.key === 'Enter') { updateKeyword(); } }}>
                  <option value="자사">자사</option>
                  <option value="경쟁사">경쟁사</option>
                </select>
              </div>
              <div className="form-group">
                <label>그룹명</label>
                <input type="text" value={editGroupName} onChange={e => setEditGroupName(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') { updateKeyword(); } }} />
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '30px' }}>
              <button type="button" className="btn-primary" style={{ background: '#e1e4e8', color: '#666' }} onClick={() => setEditModalOpen(false)}>
                취소
              </button>
              <button type="button" className="btn-primary" onClick={updateKeyword}>
                저장
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default NewsMonitoring; 