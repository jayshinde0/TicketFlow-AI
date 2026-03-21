import React, { useEffect, useRef, useState } from 'react';
import { motion, useScroll, useTransform, useMotionValueEvent } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ArrowRight, Sparkles, Bot, AlertTriangle, CheckCircle2, Route } from 'lucide-react';

const FRAME_COUNT = 192;
const FOLDER_PATH = '/Ticket/';

export default function Hero() {
  const containerRef = useRef(null);
  const canvasRef = useRef(null);
  const imagesRef = useRef([]);
  const [imagesLoaded, setImagesLoaded] = useState(false);
  const currentFrameRef = useRef(-1);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.15, delayChildren: 0.2 } }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] } }
  };

  // Prevent multiple image load calls
  useEffect(() => {
    let isMounted = true;
    let loaded = 0;
    
    for (let i = 1; i <= FRAME_COUNT; i++) {
      const img = new Image();
      img.src = `${FOLDER_PATH}${i.toString().padStart(5, '0')}.jpg`;
      img.onload = () => {
        if (!isMounted) return;
        loaded++;
        if (loaded === FRAME_COUNT) {
          setImagesLoaded(true);
          // Initial Draw
          requestAnimationFrame(() => drawFrame(1));
        }
      };
      img.onerror = () => {
        if (!isMounted) return;
        loaded++;
        if (loaded === FRAME_COUNT) {
          setImagesLoaded(true);
        }
      };
      imagesRef.current[i] = img;
    }

    return () => {
      isMounted = false;
    };
  }, []);

  const drawFrame = (frameIndex) => {
    if (frameIndex === currentFrameRef.current) return;
    
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const img = imagesRef.current[frameIndex];
    
    if (img && img.complete && img.width > 0) {
      const ratio = window.devicePixelRatio || 1;
      const cw = canvas.parentElement.clientWidth;
      const ch = canvas.parentElement.clientHeight;

      if (canvas.width !== cw * ratio || canvas.height !== ch * ratio) {
        canvas.width = cw * ratio;
        canvas.height = ch * ratio;
        ctx.scale(ratio, ratio);
      }

      ctx.clearRect(0, 0, cw, ch);

      const imgRatio = img.width / img.height;
      const canvasRatio = cw / ch;

      // "Contain" scaling logic so the entire image is visible
      let drawW, drawH, offsetX, offsetY;

      if (imgRatio > canvasRatio) {
        // Image is wider than canvas -> bind to width
        drawW = cw;
        drawH = cw / imgRatio;
        offsetX = 0;
        offsetY = (ch - drawH) / 2;
      } else {
        // Image is taller than canvas -> bind to height
        drawH = ch;
        drawW = ch * imgRatio;
        offsetX = (cw - drawW) / 2;
        offsetY = 0;
      }

      // Shift it slightly down so the navbar doesn't cover the top frames
      offsetY += ch * 0.05; 

      ctx.drawImage(img, offsetX, offsetY, drawW, drawH);
      currentFrameRef.current = frameIndex;
    }
  };

  // Scroll logic for Hero background
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start start', 'end start'] // Maps 0 to 1 as hero scrolls out of view
  });

  const frameIndex = useTransform(scrollYProgress, [0, 1], [1, FRAME_COUNT]);

  useMotionValueEvent(frameIndex, 'change', (latest) => {
    if (!imagesLoaded) return;
    const index = Math.min(FRAME_COUNT, Math.max(1, Math.floor(latest)));
    // Draw via rAF for performance
    requestAnimationFrame(() => drawFrame(index));
  });

  // Handle Resize Recalculation
  useEffect(() => {
    const handleResize = () => {
      if (!imagesLoaded) return;
      currentFrameRef.current = -1;
      drawFrame(Math.min(FRAME_COUNT, Math.max(1, Math.floor(frameIndex.get()))));
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [imagesLoaded, frameIndex]);

  // Mock data for scrolling tickets based on Stitch MCP generated content
  const tickets = [
    {
      id: '#TK-8821', title: 'API Rate Limit spikes detected in production environment.',
      status: 'Urgent', statusColor: 'text-danger', statusBg: 'bg-danger',
      confidence: '98.4%', badge: 'AI Triaged', icon: Sparkles
    },
    {
      id: '#TK-8822', title: 'Customer requesting refund for duplicate subscription billing.',
      status: 'Resolved', statusColor: 'text-gray-400', statusBg: 'bg-gray-400',
      confidence: '100%', badge: 'AI Solved', icon: CheckCircle2
    },
    {
      id: '#TK-8823', title: 'New integration request: OAuth2 support for custom CRM.',
      status: 'Assigned', statusColor: 'text-brand-400', statusBg: 'bg-brand-400',
      confidence: '92.1%', badge: 'Triaged', icon: Route
    },
    {
      id: '#TK-8824', title: 'Payment gateway timeout reported across 12 unique accounts.',
      status: 'Escalated', statusColor: 'text-danger', statusBg: 'bg-danger',
      confidence: '99.9%', badge: 'Priority Case', icon: AlertTriangle
    }
  ];

  return (
    <section ref={containerRef} className="relative h-[250vh] bg-surface">
      <div className="sticky top-0 h-screen w-full overflow-hidden flex flex-col pt-24 pb-4 md:pb-8">
        
        {/* Background Video/Canvas Loop */}
      <div className="absolute inset-0 z-0 overflow-hidden mix-blend-screen opacity-40">
        <canvas 
          ref={canvasRef}
          className="w-full h-full object-cover blur-[2px]" 
        />
        {/* Dark overlay to ensure text remains perfectly readable */}
        <div className="absolute inset-0 bg-gradient-to-b from-surface/80 via-surface/60 to-surface pointer-events-none" />
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-10 mix-blend-overlay pointer-events-none" />
      </div>

      <style>{`
        @keyframes scroll {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
        .animate-scroll {
          display: flex;
          width: max-content;
          animation: scroll 40s linear infinite;
        }
        .animate-scroll:hover {
          animation-play-state: paused;
        }
      `}</style>
      
      {/* Additional Glows */}
      <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[10%] left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-brand-600/10 rounded-full blur-[120px]" />
      </div>

      {/* Text Container */}
      <div className="flex-1 flex flex-col justify-center w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="max-w-4xl mx-auto space-y-8"
        >
          {/* Badge */}
          <motion.div variants={itemVariants} className="flex justify-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-surface-card/80 backdrop-blur-md border border-brand-500/30 text-brand-300 text-sm font-medium shadow-[0_0_15px_rgba(65,105,255,0.15)]">
              <Sparkles className="w-4 h-4" />
              <span>Supercharging support with AI</span>
            </div>
          </motion.div>

          {/* Headline */}
          <motion.h1 
            variants={itemVariants} 
            className="text-5xl md:text-7xl font-extrabold tracking-tight text-white leading-[1.1]"
          >
            Resolve tickets faster with <br className="hidden md:block" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-400 to-accent-400 drop-shadow-sm">
              Intelligent Automation
            </span>
          </motion.h1>

          {/* Subheadline */}
          <motion.p 
            variants={itemVariants} 
            className="text-lg md:text-xl text-gray-300 max-w-2xl mx-auto leading-relaxed drop-shadow-sm font-medium"
          >
            Ticket Flow AI automatically triages, routes, and helps agents answer support tickets. Build a world-class customer experience with fewer escalations and zero bottlenecks.
          </motion.p>

          {/* CTAs */}
          <motion.div 
            variants={itemVariants} 
            className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4"
          >
            <Link
              to="/dashboard"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3.5 text-base font-semibold text-white transition-all duration-300 bg-gradient-brand rounded-xl shadow-glow hover:shadow-[0_0_25px_rgba(65,105,255,0.5)] hover:-translate-y-1"
            >
              Start for free
              <ArrowRight className="w-5 h-5" />
            </Link>
            <a
              href="#how-it-works"
              className="w-full sm:w-auto inline-flex items-center justify-center px-8 py-3.5 text-base font-semibold text-gray-300 transition-all duration-300 bg-surface-card/80 backdrop-blur-md border border-surface-border rounded-xl hover:bg-surface-hover hover:text-white hover:-translate-y-1"
            >
              See how it works
            </a>
          </motion.div>
        </motion.div>
      </div>

      {/* Scrolling Tickets Component (From Stitch MCP) */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1, delay: 0.8 }}
        className="relative w-full overflow-hidden -rotate-2 z-10 mt-auto"
      >
        {/* Edge Fades for smooth infinite scroll illusion */}
        <div className="absolute left-0 top-0 bottom-0 w-32 bg-gradient-to-r from-surface to-transparent z-20 pointer-events-none" />
        <div className="absolute right-0 top-0 bottom-0 w-32 bg-gradient-to-l from-surface to-transparent z-20 pointer-events-none" />

        <div className="animate-scroll gap-6 py-10 flex">
          {/* Render tickets thrice to create the infinite loop effect seamlessly across 100vw */}
          {[...tickets, ...tickets, ...tickets].map((ticket, i) => (
            <div
              key={i}
              className="w-[380px] flex-shrink-0 p-6 rounded-2xl bg-surface-card/60 backdrop-blur-md border border-surface-border shadow-[0_8px_30px_rgba(0,0,0,0.12)] hover:border-brand-500/50 hover:shadow-glow-sm transition-all flex flex-col gap-4 text-left"
            >
              <div className="flex justify-between items-start">
                <div className="px-3 py-1 rounded-full bg-brand-900/40 text-[10px] font-bold text-brand-300 uppercase tracking-wider flex items-center gap-1.5 border border-brand-500/20">
                  <ticket.icon className="w-3 h-3" />
                  {ticket.badge}
                </div>
                <span className="text-gray-500 text-[10px] font-mono tracking-wide">{ticket.id}</span>
              </div>
              
              <h3 className="font-bold text-lg text-white leading-snug">
                {ticket.title}
              </h3>
              
              <div className="mt-auto pt-2 flex items-center justify-between border-t border-surface-border/50">
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${ticket.statusBg} ${ticket.status === 'Urgent' ? 'animate-pulse' : ''}`} />
                  <span className={`text-xs font-semibold ${ticket.statusColor} uppercase`}>
                    {ticket.status}
                  </span>
                </div>
                <div className="text-right">
                  <div className="text-[10px] text-gray-500 uppercase tracking-widest font-semibold mb-0.5">Confidence</div>
                  <div className="text-accent-400 font-extrabold">{ticket.confidence}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </motion.div>
      </div>
    </section>
  );
}
