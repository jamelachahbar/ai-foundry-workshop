import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from './components/theme-provider'
import { MainLayout } from './components/layout/main-layout'
import { Toaster } from './components/ui/toaster'
import FinOpsExpert from './pages/FinOpsExpert'

// Placeholder components until we implement them
const AskPage = () => <div>Ask Page</div>;
const HistoryPage = () => <div>History Page</div>;
const TestingPage = () => <div>Testing Page</div>;

function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="finops-ui-theme">
      <Router>
        <MainLayout>
          <Routes>
            <Route path="/" element={<Navigate to="/finops-expert" replace />} />
            <Route path="/ask" element={<AskPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/testing" element={<TestingPage />} />
            <Route path="/finops-expert" element={<FinOpsExpert />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </MainLayout>
        <Toaster />
      </Router>
    </ThemeProvider>
  )
}

export default App 