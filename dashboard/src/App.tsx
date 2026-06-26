
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout/Layout';

import { Overview } from './pages/Overview';
import { SecurityCenter } from './pages/SecurityCenter';

import { AIReviewCenter } from './pages/AIReviewCenter';
import { RuleManagement } from './pages/RuleManagement';
import { Analytics } from './pages/Analytics';
import { DocGen } from './pages/DocGen';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Overview />} />
          <Route path="security" element={<SecurityCenter />} />

          <Route path="ai-review" element={<AIReviewCenter />} />
          <Route path="rules" element={<RuleManagement />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="doc-gen" element={<DocGen />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
