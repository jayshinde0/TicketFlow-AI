import React from 'react';
import Navbar from '../components/landing/Navbar';
import Hero from '../components/landing/Hero';
import Features from '../components/landing/Features';
import HowItWorks from '../components/landing/HowItWorks';
import PipelineSimulation from '../components/landing/PipelineSimulation';
import Footer from '../components/landing/Footer';

export default function Home() {
  return (
    <div className="font-sans antialiased text-white bg-surface selection:bg-brand-500/30 selection:text-white">
      {/* Navigation */}
      <Navbar />

      <main>
        {/* Main Hero Section with animated background */}
        <Hero />
        
        {/* Key Features Section */}
        <Features />
        
        {/* How It Works Steps */}
        <HowItWorks />
        
        {/* Interactive Interactive Flowchart */}
        <PipelineSimulation />
      </main>

      {/* Footer Area */}
      <Footer />
    </div>
  );
}
