import React, { useEffect, useRef, useState, useMemo } from 'react';
import { motion, useScroll, useTransform, useMotionValueEvent } from 'framer-motion';

const FRAME_COUNT = 192;
const FOLDER_PATH = '/Ticket/';

export default function TicketScroll() {
  const containerRef = useRef(null);
  const canvasRef = useRef(null);
  
  const [imagesLoading, setImagesLoading] = useState(true);
  const [loadedCount, setLoadedCount] = useState(0);
  
  // Preloaded image objects
  const imagesRef = useRef([]);
  // Optimization: track the last rendered frame format to prevent redundant draw calls
  const currentFrameRef = useRef(-1);

  // Pad number to 5 digits e.g., 00001
  const getFrameDataUrl = (index) => {
    return `${FOLDER_PATH}${index.toString().padStart(5, '0')}.jpg`;
  };

  // 1. Preload Images
  useEffect(() => {
    let isMounted = true;
    let loaded = 0;
    
    // We preload all images
    for (let i = 1; i <= FRAME_COUNT; i++) {
      const img = new Image();
      img.src = getFrameDataUrl(i);
      img.onload = () => {
        if (!isMounted) return;
        loaded++;
        setLoadedCount(loaded);
        if (loaded === FRAME_COUNT) {
          setImagesLoading(false);
          // Initial draw
          requestAnimationFrame(() => drawFrame(1));
        }
      };
      
      // Error handling to prevent freezing if an image is missing
      img.onerror = () => {
        if (!isMounted) return;
        loaded++;
        setLoadedCount(loaded);
        if (loaded === FRAME_COUNT) setImagesLoading(false);
      };
      
      imagesRef.current[i] = img;
    }

    return () => {
      isMounted = false;
    };
  }, []);

  // 2. Canvas Drawing Function
  const drawFrame = (frameIndex) => {
    if (frameIndex === currentFrameRef.current) return; // Prevent duplicate drawing
    
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const image = imagesRef.current[frameIndex];
    if (!image || !image.complete) return;
    
    // Handle Retina / High DPI
    const ratio = window.devicePixelRatio || 1;
    // We keep internal resolution high based on client rect
    const container = canvas.parentElement;
    const cw = container.clientWidth;
    const ch = container.clientHeight;
    
    // Resize canvas to match actual css size * dpr if needed
    if (canvas.width !== cw * ratio || canvas.height !== ch * ratio) {
      canvas.width = cw * ratio;
      canvas.height = ch * ratio;
      ctx.scale(ratio, ratio);
    }

    // Clear canvas before drawing
    ctx.clearRect(0, 0, cw, ch);
    
    // Contain Object scaling logic (no cropping)
    const imgRatio = image.width / image.height;
    const canvasRatio = cw / ch;
    
    let drawW = cw;
    let drawH = ch;
    let offsetX = 0;
    let offsetY = 0;

    if (imgRatio > canvasRatio) {
      drawH = cw / imgRatio;
      offsetY = (ch - drawH) / 2;
    } else {
      drawW = ch * imgRatio;
      offsetX = (cw - drawW) / 2;
    }
    
    // Draw image centered
    ctx.drawImage(image, offsetX, offsetY, drawW, drawH);
    currentFrameRef.current = frameIndex;
  };

  // 3. Scroll hook binding
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start start', 'end end'] // Track the full 400vh explicitly
  });

  // Convert scroll ratio (0-1) to frame index (1-192)
  const frameIndex = useTransform(scrollYProgress, [0, 1], [1, FRAME_COUNT]);

  // Use the event listener instead of a React effect to guarantee strict synced updates to canvas
  useMotionValueEvent(frameIndex, 'change', (latest) => {
    if (imagesLoading) return;
    const index = Math.min(FRAME_COUNT, Math.max(1, Math.floor(latest)));
    // Draw via rAF for performance
    requestAnimationFrame(() => drawFrame(index));
  });

  // Handle Resize recalculations
  useEffect(() => {
    const handleResize = () => {
       if(!imagesLoading) {
           // force redraw on resize
           currentFrameRef.current = -1;
           drawFrame(Math.min(FRAME_COUNT, Math.max(1, Math.floor(frameIndex.get()))));
       }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [imagesLoading, frameIndex]);


  // Text Overlay Opacity mappings
  // 0% -> Text 1 (Center) -> 0 to 0.1
  const t1Opacity = useTransform(scrollYProgress, [0, 0.05, 0.12, 0.17], [0, 1, 1, 0]);
  const t1Y = useTransform(scrollYProgress, [0, 0.05, 0.17], [20, 0, -20]);

  // 20% -> Text 2 (Left) -> 0.18 to 0.35
  const t2Opacity = useTransform(scrollYProgress, [0.18, 0.23, 0.3, 0.35], [0, 1, 1, 0]);
  const t2Y = useTransform(scrollYProgress, [0.18, 0.23, 0.35], [20, 0, -20]);

  // 40% -> Text 3 (Right) -> 0.38 to 0.55
  const t3Opacity = useTransform(scrollYProgress, [0.38, 0.43, 0.5, 0.55], [0, 1, 1, 0]);
  const t3Y = useTransform(scrollYProgress, [0.38, 0.43, 0.55], [20, 0, -20]);

  // 60% -> Text 4 (Left) -> 0.58 to 0.75
  const t4Opacity = useTransform(scrollYProgress, [0.58, 0.63, 0.70, 0.75], [0, 1, 1, 0]);
  const t4Y = useTransform(scrollYProgress, [0.58, 0.63, 0.75], [20, 0, -20]);

  // 80% -> Text 5 (Center) -> 0.78 to 0.95
  const t5Opacity = useTransform(scrollYProgress, [0.78, 0.83, 0.95, 1], [0, 1, 1, 1]); // Stays visible
  const t5Y = useTransform(scrollYProgress, [0.78, 0.83, 1], [20, 0, 0]);

  return (
    <section 
      ref={containerRef} 
      className="relative h-[400vh] bg-gradient-to-b from-[#0B1120] to-[#1A1F3A]"
    >
      {/* Grid Overlay inside section limits */}
      <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none mix-blend-overlay"></div>
      
      {/* Sticky wrapper for canvas and text */}
      <div className="sticky top-0 h-screen w-full flex items-center justify-center overflow-hidden">
        
        {imagesLoading ? (
           <div className="absolute z-50 flex flex-col items-center gap-4">
             <div className="w-12 h-12 border-4 border-brand-500/20 border-t-brand-500 rounded-full animate-spin"></div>
             <p className="text-white font-medium text-lg bg-clip-text text-transparent bg-gradient-to-r from-brand-400 to-accent-400">
               Loading TicketFlow AI pipeline... {Math.round((loadedCount / FRAME_COUNT) * 100)}%
             </p>
           </div>
        ) : (
          <canvas 
            ref={canvasRef} 
            className="absolute inset-0 w-full h-full object-contain pointer-events-none opacity-90"
          />
        )}

        {/* Story Text Overlays */}
        <div className="relative z-10 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-full flex flex-col justify-center pointer-events-none">
          
          {/* T1: 0% - Center */}
          <motion.div 
            style={{ opacity: t1Opacity, y: t1Y }}
            className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center"
          >
            <h2 className="text-5xl md:text-7xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-brand-400 to-purple-400 mb-4 tracking-tight drop-shadow-sm">
              TicketFlow AI
            </h2>
            <p className="text-2xl text-gray-300 font-medium tracking-wide">
              From chaos to clarity
            </p>
          </motion.div>

          {/* T2: 20% - Left */}
          <motion.div 
            style={{ opacity: t2Opacity, y: t2Y }}
            className="absolute top-1/2 left-4 md:left-12 -translate-y-1/2 max-w-sm"
          >
            <div className="p-8 rounded-2xl bg-surface-card/40 backdrop-blur-xl border border-white/5 shadow-2xl">
                <h3 className="text-3xl font-bold text-white mb-3 tracking-tight">AI Classifies Instantly</h3>
                <p className="text-lg text-gray-400 leading-relaxed">Understands intent, priority, and urgency.</p>
            </div>
          </motion.div>

          {/* T3: 40% - Right */}
          <motion.div 
            style={{ opacity: t3Opacity, y: t3Y }}
            className="absolute top-1/2 right-4 md:right-12 -translate-y-1/2 max-w-sm"
          >
            <div className="p-8 rounded-2xl bg-surface-card/40 backdrop-blur-xl border border-white/5 shadow-2xl">
                <h3 className="text-3xl font-bold text-white mb-3 tracking-tight">Finds Relevant Solutions</h3>
                <p className="text-lg text-gray-400 leading-relaxed">Powered by semantic search and embeddings.</p>
            </div>
          </motion.div>

          {/* T4: 60% - Left */}
          <motion.div 
            style={{ opacity: t4Opacity, y: t4Y }}
            className="absolute top-1/2 left-4 md:left-12 -translate-y-1/2 max-w-sm"
          >
            <div className="p-8 rounded-2xl bg-surface-card/40 backdrop-blur-xl border border-white/5 shadow-2xl">
                <h3 className="text-3xl font-bold text-white mb-3 tracking-tight">Smart Decision Engine</h3>
                <p className="text-lg text-gray-400 leading-relaxed">Auto-resolve or escalate with confidence.</p>
            </div>
          </motion.div>

          {/* T5: 80% - Center CTA style */}
          <motion.div 
            style={{ opacity: t5Opacity, y: t5Y }}
            className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center w-full"
          >
            <div className="inline-block p-10 rounded-3xl bg-surface-card/60 backdrop-blur-2xl border border-brand-500/20 shadow-[0_0_50px_rgba(99,102,241,0.15)] max-w-2xl mx-auto">
                <h2 className="text-5xl md:text-6xl font-extrabold text-white mb-4 tracking-tight">
                  Continuously Learning
                </h2>
                <p className="text-2xl text-brand-300 font-medium">
                  Improves with every interaction.
                </p>
                <div className="mt-8 flex justify-center">
                   <button className="px-8 py-4 bg-gradient-brand text-white font-bold rounded-xl shadow-glow hover:-translate-y-1 transition-transform pointer-events-auto">
                      Explore the Platform
                   </button>
                </div>
            </div>
          </motion.div>

        </div>
      </div>
    </section>
  );
}
