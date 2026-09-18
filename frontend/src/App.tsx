import { lazy, Suspense } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import Layout from './components/layout/Layout';
import ProtectedRoute from './components/layout/ProtectedRoute';
import { LoadingState } from './components/common/states';
const Home = lazy(() => import('./pages/Home'));
const MapPage = lazy(() => import('./pages/MapPage'));
const AreaDetail = lazy(() => import('./pages/AreaDetail'));
const Compare = lazy(() => import('./pages/Compare'));
const Advisory = lazy(() => import('./pages/Advisory'));
const AuthPage = lazy(() => import('./pages/AuthPage'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Profile = lazy(() => import('./pages/Profile'));
const ReportPage = lazy(() => import('./pages/ReportPage'));
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'));
const Awareness = lazy(() => import('./pages/Awareness'));
const DesignSystem = lazy(() => import('./pages/DesignSystem'));
const NotFound = lazy(() => import('./pages/NotFound'));
export default function App() {
  return <Suspense fallback={<div className="app-loading">
    <LoadingState />
  </div>}>
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="map" element={<MapPage />} />
        <Route path="areas/:id" element={<AreaDetail />} />
        <Route path="compare" element={<Compare />} />
        <Route path="advisory" element={<Advisory />} />
        <Route path="awareness" element={<Awareness />} />
        <Route path="community" element={<ReportPage />} />
        <Route path="reports" element={<Navigate to="/community" replace />} />
        <Route path="login" element={<AuthPage />} />
        <Route path="register" element={<AuthPage register />} />
        <Route path="design-system" element={<DesignSystem />} />
        <Route element={<ProtectedRoute />}>
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="profile" element={<Profile />} />
        </Route>
        <Route element={<ProtectedRoute admin />}>
          <Route path="admin" element={<AdminDashboard />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  </Suspense>;
}
