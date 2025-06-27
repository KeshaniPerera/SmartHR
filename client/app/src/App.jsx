import './App.css'
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { useState } from 'react'
import Home from "./assets/pages/Home";
import Login from './assets/pages/SignIn.jsx';
import NavBar from './assets/components/NavBar.jsx'; 
import Footer from './assets/components/Footer.jsx';

function App() {
  return <Router>
    <NavBar />
    <Routes>
       <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />

    </Routes>
     <Footer />
   

  </Router>;
}

export default App;