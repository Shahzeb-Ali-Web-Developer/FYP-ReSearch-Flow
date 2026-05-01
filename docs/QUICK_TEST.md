# Quick Test Guide - Citation Mesh

## ✅ Servers Should Be Running

I've started both servers in separate command windows. You should see:
- **Backend Server** window (port 8000)
- **Frontend Server** window (port 5173)

## 🧪 Test It Now

### Step 1: Open Your Browser
Go to: **http://localhost:5173**

### Step 2: Search for Papers
1. Type a topic in the search box (e.g., "machine learning", "deep learning", "neural networks")
2. Press Enter or click Search
3. Wait for results to load

### Step 3: Open Citation Mesh
1. Look at the **Works** section (left side)
2. Find the **"Citation Mesh"** button (black button with network icon) in the top-right
3. Click it!

### Step 4: See the Graph
You should see:
- A full-screen overlay
- Interactive graph with nodes (papers) and edges (citations)
- Toolbar with zoom, layout options, export

## ✅ What You Should See

**On Results Page:**
- Black "Citation Mesh" button appears when papers are loaded

**When You Click It:**
- Full-screen graph visualization
- Papers shown as circles (nodes)
- Citation relationships shown as arrows (edges)
- Root papers (your search results) are larger and darker
- Referenced papers are smaller and gray

**You Can:**
- Zoom in/out
- Change layouts (Dagre, Breadthfirst, Force-Directed)
- Click nodes to see paper details
- Export as PNG
- Close the overlay

## 🐛 If It Doesn't Work

### Check Backend (http://localhost:8000)
1. Open http://localhost:8000/health
   - Should show: `{"status":"healthy"}`
2. Open http://localhost:8000/docs
   - Should show API documentation
   - Look for "Citation Network" section

### Check Frontend (http://localhost:5173)
1. Open http://localhost:5173
   - Should show homepage
2. Open browser DevTools (F12)
   - Check Console tab for errors
   - Check Network tab for failed requests

### Common Issues

**"Citation Mesh" button doesn't appear:**
- Make sure you have search results loaded
- Check browser console for errors

**Graph shows "No citation connections found":**
- Try searching for more popular topics
- Some papers may not have citation data

**Backend errors:**
- Check the Backend Server window for error messages
- Make sure all dependencies are installed

## 📊 Success Indicators

✅ Backend responds at http://localhost:8000/health
✅ Frontend loads at http://localhost:5173
✅ Search returns results
✅ "Citation Mesh" button appears
✅ Graph visualization shows up
✅ You can interact with the graph

---

**🎉 If all these work, your Citation Mesh feature is complete and working!**
