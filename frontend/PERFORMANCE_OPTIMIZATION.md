# React App Performance Optimization Guide

## 🐌 **Why Your React App Might Be Slow**

Your app is likely slow due to one or more of these common issues:

---

## 🔍 **Diagnosis & Solutions**

### **1. Initial Load Speed (Development Mode)**

#### ❌ **Problem:** Development server is slow
**Symptoms:**
- Takes 30+ seconds to start
- Hot reload is slow
- Browser takes time to load

#### ✅ **Solutions:**

**A. Disable Source Maps (Quick Fix)**

Edit `frontend/package.json`:
```json
{
  "scripts": {
    "start": "GENERATE_SOURCEMAP=false react-scripts start",
    "build": "GENERATE_SOURCEMAP=false react-scripts build"
  }
}
```

**B. Enable Fast Refresh**

Create `frontend/.env`:
```env
FAST_REFRESH=true
GENERATE_SOURCEMAP=false
ESLINT_NO_DEV_ERRORS=true
TSC_COMPILE_ON_ERROR=true
```

**C. Reduce Bundle Size**

Your `node_modules` is **802 MB** - this is normal but can be optimized:

```bash
# Remove unused dependencies
npm prune

# Clear cache
npm cache clean --force

# Reinstall
rm -rf node_modules package-lock.json
npm install
```

---

### **2. Runtime Performance (While Using App)**

#### ❌ **Problem:** App is laggy during use
**Symptoms:**
- Slow page transitions
- Delayed button clicks
- Choppy animations

#### ✅ **Solutions:**

**A. Optimize Re-renders**

Create `frontend/src/utils/performance.js`:
```javascript
import { memo, useCallback, useMemo } from 'react';

// Memoize expensive components
export const MemoizedComponent = memo(YourComponent);

// Memoize callbacks
export const useOptimizedCallback = (fn, deps) => useCallback(fn, deps);

// Memoize computed values
export const useOptimizedValue = (fn, deps) => useMemo(fn, deps);
```

**B. Add React DevTools Profiler**

Install extension:
- Chrome: React Developer Tools
- Check "Highlight updates when components render"
- Profile your app to find slow components

**C. Optimize Images**

Replace large images with compressed versions:
```bash
# Install image optimizer
npm install --save-dev imagemin imagemin-webp
```

---

### **3. Network Performance (API Calls)**

#### ❌ **Problem:** Slow API responses
**Symptoms:**
- Dashboard takes long to load
- Ticket list is slow
- Analytics page hangs

#### ✅ **Solutions:**

**A. Add Request Caching**

Edit `frontend/src/services/api.js` (or create if doesn't exist):
```javascript
import axios from 'axios';

// Simple in-memory cache
const cache = new Map();
const CACHE_DURATION = 60000; // 1 minute

const cachedAxios = {
  get: async (url, config) => {
    const cacheKey = url + JSON.stringify(config?.params || {});
    const cached = cache.get(cacheKey);
    
    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
      console.log('Cache hit:', url);
      return cached.data;
    }
    
    const response = await axios.get(url, config);
    cache.set(cacheKey, { data: response, timestamp: Date.now() });
    return response;
  }
};

export default cachedAxios;
```

**B. Implement Pagination**

For ticket lists, load in batches:
```javascript
const [tickets, setTickets] = useState([]);
const [page, setPage] = useState(1);
const LIMIT = 20;

useEffect(() => {
  fetch(`/api/tickets?page=${page}&limit=${LIMIT}`)
    .then(res => res.json())
    .then(data => setTickets(prev => [...prev, ...data]));
}, [page]);
```

**C. Add Loading States**

Show skeletons instead of blank screens:
```javascript
{loading ? <SkeletonLoader /> : <TicketList tickets={tickets} />}
```

---

### **4. Memory Leaks**

#### ❌ **Problem:** App gets slower over time
**Symptoms:**
- Fast initially, slow after 10 minutes
- Browser tab uses lots of RAM
- Eventually crashes

#### ✅ **Solutions:**

**A. Clean Up WebSocket Connections**

Edit `frontend/src/contexts/NotificationContext.jsx`:
```javascript
useEffect(() => {
  const ws = new WebSocket(url);
  
  return () => {
    console.log('Cleaning up WebSocket');
    ws.close(); // ✅ Always cleanup!
  };
}, [url]);
```

**B. Cancel Pending Requests**

```javascript
useEffect(() => {
  const controller = new AbortController();
  
  fetch('/api/tickets', { signal: controller.signal })
    .then(res => res.json())
    .then(data => setTickets(data))
    .catch(err => {
      if (err.name === 'AbortError') return;
      console.error(err);
    });
  
  return () => controller.abort(); // ✅ Cancel on unmount
}, []);
```

**C. Clear Intervals/Timeouts**

```javascript
useEffect(() => {
  const interval = setInterval(() => {
    fetchUpdates();
  }, 5000);
  
  return () => clearInterval(interval); // ✅ Always cleanup!
}, []);
```

---

### **5. Large Component Trees**

#### ❌ **Problem:** Too many components rendering
**Symptoms:**
- Opening Dashboard is slow
- Scrolling is janky
- React DevTools shows 1000+ components

#### ✅ **Solutions:**

**A. Implement Virtual Scrolling**

For long ticket lists:
```bash
npm install react-window
```

```javascript
import { FixedSizeList } from 'react-window';

function TicketList({ tickets }) {
  const Row = ({ index, style }) => (
    <div style={style}>
      <TicketCard ticket={tickets[index]} />
    </div>
  );
  
  return (
    <FixedSizeList
      height={600}
      itemCount={tickets.length}
      itemSize={100}
      width="100%"
    >
      {Row}
    </FixedSizeList>
  );
}
```

**B. Code Split Routes** (Already done! ✅)

Your `App.jsx` already uses `lazy()` - this is good!

**C. Avoid Inline Functions**

❌ Bad:
```javascript
<button onClick={() => handleClick(id)}>Click</button>
```

✅ Good:
```javascript
const onClick = useCallback(() => handleClick(id), [id]);
<button onClick={onClick}>Click</button>
```

---

### **6. Framer Motion Animations**

#### ❌ **Problem:** Animations are laggy
**Symptoms:**
- Page transitions stutter
- Hover effects lag

#### ✅ **Solutions:**

**A. Reduce Animation Complexity**

Edit components with `framer-motion`:
```javascript
// ❌ Too complex
<motion.div
  initial={{ opacity: 0, x: -100, y: -100, scale: 0 }}
  animate={{ opacity: 1, x: 0, y: 0, scale: 1 }}
/>

// ✅ Simpler
<motion.div
  initial={{ opacity: 0 }}
  animate={{ opacity: 1 }}
/>
```

**B. Use `will-change` CSS**

Add to `index.css`:
```css
.animated-element {
  will-change: transform, opacity;
}
```

**C. Disable Animations on Low-End Devices**

```javascript
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

<motion.div
  animate={prefersReducedMotion ? {} : { opacity: 1 }}
/>
```

---

## 🚀 **Quick Wins (Do These First!)**

### **1. Add .env File**

Create `frontend/.env`:
```env
# Speed up development
FAST_REFRESH=true
GENERATE_SOURCEMAP=false
ESLINT_NO_DEV_ERRORS=true

# Backend URL
REACT_APP_API_URL=http://localhost:8000
```

### **2. Update package.json**

```json
{
  "scripts": {
    "start": "GENERATE_SOURCEMAP=false react-scripts start",
    "build": "GENERATE_SOURCEMAP=false react-scripts build"
  }
}
```

### **3. Add React.memo to Heavy Components**

Find your slowest components (Dashboard, Analytics, TicketList) and wrap them:

```javascript
import { memo } from 'react';

const Dashboard = memo(function Dashboard() {
  // ... existing code
});

export default Dashboard;
```

### **4. Optimize Recharts (Analytics Page)**

If Analytics page is slow:

```javascript
import { LineChart, Line, ResponsiveContainer } from 'recharts';

// ✅ Add isAnimationActive={false}
<LineChart data={data}>
  <Line 
    type="monotone" 
    dataKey="value" 
    isAnimationActive={false}  // ← Disable animation
  />
</LineChart>
```

---

## 🔥 **Production Build Optimization**

### **1. Build for Production**

```bash
npm run build
```

This creates optimized production build that's **much faster** than development.

### **2. Analyze Bundle Size**

```bash
npm install --save-dev webpack-bundle-analyzer
```

Add to `package.json`:
```json
{
  "scripts": {
    "analyze": "source-map-explorer 'build/static/js/*.js'"
  }
}
```

Run:
```bash
npm install --save-dev source-map-explorer
npm run build
npm run analyze
```

### **3. Serve Production Build Locally**

```bash
npm install -g serve
serve -s build -p 3000
```

Test speed - should be **much faster**!

---

## 📊 **Measure Performance**

### **1. React DevTools Profiler**

1. Install React DevTools extension
2. Open DevTools → Profiler tab
3. Click Record
4. Navigate your app
5. Stop recording
6. See which components are slow

### **2. Chrome DevTools Performance**

1. Open Chrome DevTools → Performance tab
2. Click Record
3. Navigate your app
4. Stop recording
5. Look for:
   - Long tasks (yellow/red bars)
   - Layout shifts
   - Large JavaScript execution times

### **3. Lighthouse Audit**

1. Open Chrome DevTools → Lighthouse tab
2. Select "Performance"
3. Click "Generate report"
4. Fix issues with score < 90

---

## 🎯 **Expected Performance Targets**

| Metric | Target | Your Goal |
|--------|--------|-----------|
| **Initial Load** | < 3 seconds | ✅ Check with build |
| **Time to Interactive** | < 5 seconds | ✅ Lighthouse score |
| **Largest Contentful Paint** | < 2.5s | ✅ Lighthouse |
| **First Input Delay** | < 100ms | ✅ Smooth clicks |
| **Cumulative Layout Shift** | < 0.1 | ✅ No jumping |

---

## 🐛 **Debug Specific Slowness**

### **Dashboard is slow?**
- Too many API calls on mount
- Large data fetching
- **Fix:** Add loading states, pagination

### **Ticket List is slow?**
- Rendering 100+ tickets at once
- **Fix:** Virtual scrolling, pagination

### **Analytics page is slow?**
- Recharts animations
- Large datasets
- **Fix:** Disable animations, aggregate data

### **Page transitions are slow?**
- Framer Motion complexity
- **Fix:** Simplify animations

### **WebSocket causing issues?**
- Too many messages
- **Fix:** Throttle updates, batch changes

---

## ✅ **Checklist for Optimization**

- [ ] Add `.env` with `GENERATE_SOURCEMAP=false`
- [ ] Wrap heavy components in `React.memo`
- [ ] Add `useCallback` to event handlers
- [ ] Add `useMemo` to computed values
- [ ] Implement pagination for lists
- [ ] Add loading states everywhere
- [ ] Clean up useEffect dependencies
- [ ] Remove unused npm packages
- [ ] Disable Recharts animations
- [ ] Test production build
- [ ] Run Lighthouse audit
- [ ] Check React DevTools Profiler

---

## 🆘 **If Still Slow**

### **Last Resort: Upgrade React**

```bash
npm install react@latest react-dom@latest
npm install react-scripts@latest
```

### **Consider Vite Instead of CRA**

Create React App (CRA) is slow. Vite is much faster:

```bash
# Migration guide
npm create vite@latest my-app -- --template react
# Copy your src/ folder
# Update imports
```

---

## 📝 **Quick Commands**

```bash
# Clean install
rm -rf node_modules package-lock.json
npm install

# Clear cache
npm cache clean --force

# Production build
npm run build

# Test production locally
npx serve -s build

# Check bundle size
npm run analyze
```

---

**Start with the Quick Wins section and let me know which specific area is slowest!** 🚀
