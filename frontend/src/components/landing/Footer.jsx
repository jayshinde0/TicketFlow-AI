import React from 'react';
import { Link } from 'react-router-dom';
import { Bot, Github, Twitter, Linkedin } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-surface border-t border-surface-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 md:py-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 md:gap-12">
          {/* Brand & Social */}
          <div className="col-span-1 md:col-span-1">
            <Link to="/" className="flex items-center gap-2 mb-4 group">
              <div className="bg-gradient-brand p-1.5 rounded-lg shadow-glow group-hover:scale-105 transition-transform duration-300">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <span className="text-lg font-bold text-white">
                TicketFlow AI
              </span>
            </Link>
            <p className="text-sm text-gray-400 mb-6 max-w-xs leading-relaxed">
              Next-generation customer support platform powered by advanced artificial intelligence.
            </p>
            <div className="flex items-center gap-4">
              <a href="#" className="text-gray-500 hover:text-brand-400 transition-colors">
                <Twitter className="w-5 h-5" />
              </a>
              <a href="#" className="text-gray-500 hover:text-brand-400 transition-colors">
                <Github className="w-5 h-5" />
              </a>
              <a href="#" className="text-gray-500 hover:text-brand-400 transition-colors">
                <Linkedin className="w-5 h-5" />
              </a>
            </div>
          </div>

          {/* Links */}
          <div>
            <h3 className="text-sm font-semibold text-white tracking-wider uppercase mb-4">Product</h3>
            <ul className="space-y-3">
              <li><a href="#features" className="text-sm text-gray-400 hover:text-brand-400 transition-colors">Features</a></li>
              <li><a href="#how-it-works" className="text-sm text-gray-400 hover:text-brand-400 transition-colors">How it works</a></li>
              <li><a href="#pricing" className="text-sm text-gray-400 hover:text-brand-400 transition-colors">Pricing</a></li>
              <li><Link to="/login" className="text-sm text-gray-400 hover:text-brand-400 transition-colors">Log in</Link></li>
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-white tracking-wider uppercase mb-4">Resources</h3>
            <ul className="space-y-3">
              <li><a href="#" className="text-sm text-gray-400 hover:text-brand-400 transition-colors">Documentation</a></li>
              <li><a href="#" className="text-sm text-gray-400 hover:text-brand-400 transition-colors">Help Center</a></li>
              <li><a href="#" className="text-sm text-gray-400 hover:text-brand-400 transition-colors">Blog</a></li>
              <li><a href="#" className="text-sm text-gray-400 hover:text-brand-400 transition-colors">Case Studies</a></li>
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-white tracking-wider uppercase mb-4">Company</h3>
            <ul className="space-y-3">
              <li><a href="#" className="text-sm text-gray-400 hover:text-brand-400 transition-colors">About</a></li>
              <li><a href="#contact" className="text-sm text-gray-400 hover:text-brand-400 transition-colors">Contact</a></li>
              <li><a href="#" className="text-sm text-gray-400 hover:text-brand-400 transition-colors">Privacy</a></li>
              <li><a href="#" className="text-sm text-gray-400 hover:text-brand-400 transition-colors">Terms</a></li>
            </ul>
          </div>
        </div>

        <div className="mt-12 pt-8 border-t border-surface-border flex flex-col md:flex-row items-center justify-between">
          <p className="text-sm text-gray-500">
            &copy; {new Date().getFullYear()} TicketFlow AI. All rights reserved.
          </p>
          <div className="flex items-center gap-4 mt-4 md:mt-0">
            <span className="flex items-center gap-1.5 text-sm font-medium text-gray-400 bg-surface-card px-3 py-1.5 rounded-full border border-surface-border shadow-sm">
               <div className="w-2 h-2 rounded-full bg-success animate-pulse"></div> All systems operational
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
