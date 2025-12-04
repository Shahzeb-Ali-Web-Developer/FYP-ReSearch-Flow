import {Routes, Route} from "react-router-dom";
import Home from './pages/Home';
import AuthPage from './pages/AuthPage';
import MainLayout from './layouts/MainLayout';
import AuthLayout from './layouts/AuthLayout';
import AuthCallback from './pages/AuthCallBack';
import Results from './pages/Results';
import SavedSearches from './pages/SavedSearches';


function App() {

  return (
    <>
      <Routes>
        {/* Pages with Navbar */}
        <Route element={<MainLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/results" element={<Results />} />
          <Route path="/saved-searches" element={<SavedSearches />} />
        </Route>
        
        {/* Auth pages without Navbar */}
        <Route element={<AuthLayout />}>
          <Route path="/auth" element={<AuthPage />} />
          <Route path="/auth/callback" element={<AuthCallback />} />
        </Route>
      </Routes>
    
    </>
  )
}

export default App
