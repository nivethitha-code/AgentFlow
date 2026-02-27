import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from 'next-themes';
import { Layout } from './components/Layout';
import { Home } from './components/Home';
import { WorkflowEditor } from './components/WorkflowEditor';
import { RunViewer } from './components/RunViewer';
import { History } from './components/History';

function App() {
  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/builder" element={<WorkflowEditor />} />
            <Route path="/run/:runId" element={<RunViewer />} />
            <Route path="/history" element={<History />} />
          </Routes>
        </Layout>
      </Router>
    </ThemeProvider>
  );
}

export default App;
