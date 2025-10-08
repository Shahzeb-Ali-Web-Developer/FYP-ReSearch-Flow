import { useState } from 'react'
import {Routes, Route} from "react-router-dom";
import Home from './pages/Home';
import Navbar from './components/Navbar';
import AuthPage from './pages/AuthPage';
import MainLayout from './layouts/MainLayout';
import AuthLayout from './layouts/AuthLayout';
import AuthCallback from './pages/AuthCallBack';


function App() {

  return (
    <>
      <Routes>
        <Route element={<MainLayout />} ><Route path="/" element={<Home />}  /></Route>
        <Route element={<AuthLayout />}>
        <Route path="/auth" element={<AuthPage />} />
        <Route path="/auth/callback" element={<AuthCallback />} />

        </Route>
      </Routes>
    
    </>
  )
}

export default App
