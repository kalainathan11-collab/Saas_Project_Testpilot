import { lazy, Suspense } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { ProjectProvider } from './context/ProjectContext'
import { AuthProvider } from './context/AuthContext'
import { ProtectedRoute, PublicOnlyRoute } from './components/auth/ProtectedRoute'
import { AppShell } from './components/layout/AppShell'
import { AuthLayout } from './components/layout/AuthLayout'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import { PageFallback } from './components/ui/PageFallback'

const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const ReportsPage = lazy(() => import('./pages/ReportsPage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));
const ProjectListPage = lazy(() => import('./pages/ProjectListPage'));
const ProjectFormPage = lazy(() => import('./pages/ProjectFormPage'));
const ProjectDetailPage = lazy(() => import('./pages/ProjectDetailPage'));
const RequirementListPage = lazy(() => import('./pages/RequirementListPage'));
const RequirementFormPage = lazy(() => import('./pages/RequirementFormPage'));
const RequirementDetailPage = lazy(() => import('./pages/RequirementDetailPage'));
const TestCaseListPage = lazy(() => import('./pages/TestCaseListPage'));
const TestCaseFormPage = lazy(() => import('./pages/TestCaseFormPage'));
const TestCaseDetailPage = lazy(() => import('./pages/TestCaseDetailPage'));
const TestRunListPage = lazy(() => import('./pages/TestRunListPage'));
const TestRunFormPage = lazy(() => import('./pages/TestRunFormPage'));
const TestRunExecutionPage = lazy(() => import('./pages/TestRunExecutionPage'));
const DefectListPage = lazy(() => import('./pages/DefectListPage'));
const DefectFormPage = lazy(() => import('./pages/DefectFormPage'));
const DefectDetailPage = lazy(() => import('./pages/DefectDetailPage'));
const AuthCallbackPage = lazy(() => import('./pages/AuthCallbackPage'))

export default function App() {
  return (
    <AuthProvider>
    <ProjectProvider>
      <BrowserRouter>
        <Suspense fallback={<PageFallback />}>
        <Routes>
          <Route path="/auth/callback" element={<AuthCallbackPage />} />

          <Route element={<PublicOnlyRoute />}>
            <Route element={<AuthLayout />}>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
            </Route>
          </Route>

          <Route element={<ProtectedRoute />}>
          <Route element={<AppShell />}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/profile" element={<ProfilePage />} />

            <Route path="/projects" element={<ProjectListPage />} />
            <Route path="/projects/new" element={<ProjectFormPage />} />
            <Route path="/projects/:id/edit" element={<ProjectFormPage />} />
            <Route path="/projects/:id" element={<ProjectDetailPage />} />

            <Route path="/requirements" element={<RequirementListPage />} />
            <Route path="/requirements/new" element={<RequirementFormPage />} />
            <Route path="/requirements/:id/edit" element={<RequirementFormPage />} />
            <Route path="/requirements/:id" element={<RequirementDetailPage />} />

            <Route path="/testcases" element={<TestCaseListPage />} />
            <Route path="/testcases/new" element={<TestCaseFormPage />} />
            <Route path="/testcases/:id/edit" element={<TestCaseFormPage />} />
            <Route path="/testcases/:id" element={<TestCaseDetailPage />} />

            <Route path="/testruns" element={<TestRunListPage />} />
            <Route path="/testruns/new" element={<TestRunFormPage />} />
            <Route path="/testruns/:id/edit" element={<TestRunFormPage />} />
            <Route path="/testruns/:id" element={<TestRunExecutionPage />} />

            <Route path="/defects" element={<DefectListPage />} />
            <Route path="/defects/new" element={<DefectFormPage />} />
            <Route path="/defects/:id/edit" element={<DefectFormPage />} />
            <Route path="/defects/:id" element={<DefectDetailPage />} />

            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
          </Route>

          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
        </Suspense>
      </BrowserRouter>
    </ProjectProvider>
    </AuthProvider>
  )
}
