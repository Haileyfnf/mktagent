import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import Layout from './components/Layout';
import PageTitle from './components/PageTitle';
import NewsMonitoring from './pages/NewsMonitoring';
import ChinaSNSTrends from './pages/ChinaSNSTrends';
import KeywordDashboard from './pages/KeywordDashboard';
import InfluencerMonitoring from './pages/InfluencerMonitoring';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/news-monitoring" replace />} />
          <Route 
            path="/news-monitoring" 
            element={
              <>
                <PageTitle title="뉴스 모니터링" />
                <NewsMonitoring />
              </>
            } 
          />
          <Route 
            path="/china-sns-trends" 
            element={
              <>
                <PageTitle title="중국 SNS 트렌드" />
                <ChinaSNSTrends />
              </>
            } 
          />
          <Route 
            path="/keyword-dashboard/:groupName" 
            element={<KeywordDashboard />} 
          />
          <Route 
            path="/influencer-monitoring" 
            element={
              <>
                <PageTitle title="인플루언서 모니터링" />
                <InfluencerMonitoring />
              </>
            } 
          />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
