import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Bot, Menu, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled ? 'bg-surface/80 backdrop-blur-md shadow-sm border-b border-surface-border' : 'bg-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group">
            <div className="bg-gradient-brand p-2 rounded-xl group-hover:scale-105 transition-transform duration-300 shadow-glow">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold text-white">
              TicketFlow AI
            </span>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-8">
            <a href="/#features" className="text-sm font-medium text-gray-400 hover:text-white transition-colors">Features</a>
            <a href="/#how-it-works" className="text-sm font-medium text-gray-400 hover:text-white transition-colors">How it works</a>
            <a href="/#pricing" className="text-sm font-medium text-gray-400 hover:text-white transition-colors">Pricing</a>
            <a href="/#contact" className="text-sm font-medium text-gray-400 hover:text-white transition-colors">Contact</a>
          </div>

          {/* CTAs */}
          <div className="hidden md:flex items-center gap-4">
            <Link to="/login" className="text-sm font-medium text-gray-400 hover:text-white transition-colors">
              Log in
            </Link>
            <Link
              to="/dashboard"
              className="inline-flex items-center justify-center px-5 py-2.5 text-sm font-medium text-white transition-all duration-300 bg-gradient-brand rounded-lg hover:shadow-glow hover:-translate-y-0.5"
            >
              Get Started
            </Link>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="text-gray-400 hover:text-white focus:outline-none p-2"
            >
              {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Nav */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden bg-surface-card border-b border-surface-border"
          >
            <div className="px-4 pt-2 pb-6 space-y-1">
              <a href="/#features" onClick={() => setMobileMenuOpen(false)} className="block px-3 py-2 text-base font-medium text-gray-300 hover:bg-surface-hover hover:text-white rounded-md">Features</a>
              <a href="/#how-it-works" onClick={() => setMobileMenuOpen(false)} className="block px-3 py-2 text-base font-medium text-gray-300 hover:bg-surface-hover hover:text-white rounded-md">How it works</a>
              <a href="/#pricing" onClick={() => setMobileMenuOpen(false)} className="block px-3 py-2 text-base font-medium text-gray-300 hover:bg-surface-hover hover:text-white rounded-md">Pricing</a>
              <div className="mt-4 pt-4 border-t border-surface-border flex flex-col gap-3">
                <Link to="/login" onClick={() => setMobileMenuOpen(false)} className="block w-full text-center px-4 py-2 text-base font-medium text-gray-300 bg-surface-hover rounded-md hover:text-white outline-none border border-surface-border">
                  Log in
                </Link>
                <Link to="/dashboard" onClick={() => setMobileMenuOpen(false)} className="block w-full text-center px-4 py-2 text-base font-medium text-white bg-gradient-brand rounded-md shadow-glow">
                  Get Started
                </Link>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.nav>
  );
}
