# Citation Mesh Testing Guide

## ✅ What Was Implemented

The citation mesh feature is now complete! Here's what was added:

### Backend
- ✅ `backend/src/app/services/citation_network_service.py` - Service to build citation networks
- ✅ `backend/src/app/api/v1/routes/citation.py` - API endpoint for citation networks
- ✅ Updated `backend/src/app/api/v1/api_router.py` - Added citation router

### Frontend
- ✅ `frontend/src/components/CitationMesh.jsx` - Interactive graph visualization component
- ✅ Updated `frontend/src/pages/Results.jsx` - Added "Citation Mesh" button
- ✅ Updated `frontend/src/services/api.js` - Added `getCitationNetwork()` method

### Dependencies
- ✅ `cytoscape` - Graph visualization library
- ✅ `react-cytoscapejs` - React wrapper for Cytoscape
- ✅ `cytoscape-dagre` - Hierarchical layout algorithm

---

## 🚀 Step 1: Start Your Servers

### Option A: Use the Script (Easiest)
```powershell
.\run-servers.ps1
```

### Option B: Manual Start

**Terminal 1 - Backend:**
```powershell
cd backend
C:\Users\HP\AppData\Local\Programs\Python\Python312\python.exe -m uvicorn src.app.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 - Frontend:**
```powershell
cd frontend
npm run dev
```

**Verify servers are running:**
- Backend: http://localhost:8000/health → Should show `{"status":"healthy"}`
- Frontend: http://localhost:5173 → Should show homepage

---

## 🧪 Step 2: Test the Backend API

### Test 1: Check API Documentation
1. Open http://localhost:8000/docs in your browser
2. Look for **"Citation Network"** section in the API docs
3. You should see a `POST /api/v1/citation/network` endpoint

### Test 2: Test the Endpoint Directly
Open http://localhost:8000/docs and:
1. Find `POST /api/v1/citation/network`
2. Click "Try it out"
3. Use this test payload:
```json
{
  "papers": [
    {
      "paperId": "https://openalex.org/W2741809807",
      "title": "Test Paper",
      "referencedWorks": ["https://openalex.org/W1234567890"]
    }
  ],
  "max_depth": 1,
  "max_nodes": 50
}
```
4. Click "Execute"
5. **Expected Result:** You should get a response with `nodes` and `edges` arrays

---

## 🎨 Step 3: Test the Frontend Feature

### Test 1: Search for Papers
1. Go to http://localhost:5173
2. Search for a topic (e.g., "machine learning", "deep learning")
3. Wait for results to load

### Test 2: Open Citation Mesh
1. On the Results page, look for the **"Citation Mesh"** button in the top-right of the Works section
2. Click the button
3. **Expected Result:** A full-screen overlay should appear with:
   - Header showing "Citation Network"
   - Loading spinner (briefly)
   - Graph visualization showing nodes (papers) and edges (citations)

### Test 3: Interact with the Graph
1. **Zoom:** Use the zoom in/out buttons or mouse wheel
2. **Layout:** Try different layouts from the dropdown (Dagre, Breadthfirst, Force-Directed)
3. **Click Nodes:** Click on any paper node
   - **Expected:** The detail panel should open showing that paper's information
4. **Export:** Click the download button to export as PNG
5. **Close:** Click the X button to close the mesh

---

## ✅ Verification Checklist

Use this checklist to confirm everything works:

### Backend ✅
- [ ] Backend server starts without errors
- [ ] API docs show `/api/v1/citation/network` endpoint
- [ ] Endpoint accepts POST requests with papers array
- [ ] Returns network data with nodes and edges

### Frontend ✅
- [ ] Frontend server starts without errors
- [ ] No console errors in browser DevTools
- [ ] "Citation Mesh" button appears on Results page
- [ ] Button is clickable when papers are loaded
- [ ] Citation mesh overlay opens
- [ ] Graph renders with nodes and edges
- [ ] Can interact with graph (zoom, pan, click)
- [ ] Layout changes work
- [ ] Clicking nodes opens paper details
- [ ] Export button works
- [ ] Close button works

### Integration ✅
- [ ] No CORS errors in browser console
- [ ] Network requests succeed (check Network tab)
- [ ] Graph shows actual citation relationships
- [ ] Root papers (from search) are highlighted differently

---

## 🐛 Troubleshooting

### Issue: "Citation Mesh" button doesn't appear
**Solution:**
- Make sure you have search results loaded
- Check browser console for errors
- Verify `CitationMesh` component is imported in `Results.jsx`

### Issue: Graph shows "No citation connections found"
**Possible Causes:**
- Papers don't have `referencedWorks` data
- OpenAlex API didn't return citation data
- Papers are too new/obscure to have citations

**Solution:**
- Try searching for more popular topics (e.g., "machine learning", "neural networks")
- Check if papers have `referencedWorks` in the API response

### Issue: Backend returns 500 error
**Check:**
1. Backend logs for error messages
2. OpenAlex API is accessible
3. `citation_network_service.py` is in the correct location

### Issue: Graph doesn't render
**Check:**
1. Browser console for JavaScript errors
2. Cytoscape dependencies are installed: `npm list cytoscape react-cytoscapejs cytoscape-dagre`
3. Network requests are successful (check Network tab)

### Issue: Layout dropdown is empty or missing Dagre
**Solution:**
- This is normal if `cytoscape-dagre` didn't install properly
- Breadthfirst and Cose layouts should still work
- Reinstall: `cd frontend && npm install cytoscape-dagre`

---

## 📊 What Success Looks Like

When everything works correctly, you should see:

1. **On Results Page:**
   - A black "Citation Mesh" button with network icon
   - Button appears next to other action buttons

2. **When Clicked:**
   - Full-screen overlay opens
   - Shows "Citation Network" header
   - Graph visualization appears with:
     - **Nodes:** Circles representing papers
     - **Edges:** Arrows showing citation relationships
     - **Root nodes:** Larger, darker circles (your search results)
     - **Citation nodes:** Smaller, gray circles (referenced papers)

3. **Interactions Work:**
   - Can zoom in/out
   - Can change layouts
   - Can click nodes to see paper details
   - Can export as PNG
   - Can close the overlay

---

## 🎯 You're Done When...

✅ All items in the Verification Checklist are checked
✅ You can successfully:
   - Search for papers
   - Click "Citation Mesh" button
   - See the graph visualization
   - Interact with the graph
   - Click nodes to see paper details

---

## 📝 Next Steps (Optional Enhancements)

If you want to improve the feature further:

1. **Add more citation depth** - Explore 2-3 levels deep
2. **Add node tooltips** - Show paper info on hover
3. **Add filtering** - Filter by year, venue, etc.
4. **Add search** - Search for specific papers in the graph
5. **Add clustering** - Group related papers together
6. **Performance optimization** - Handle large networks better

---

## 🆘 Still Having Issues?

1. **Check the logs:**
   - Backend: Look at terminal output
   - Frontend: Open browser DevTools (F12) → Console tab

2. **Verify dependencies:**
   ```powershell
   # Backend
   cd backend
   pip list | findstr requests
   
   # Frontend
   cd frontend
   npm list cytoscape react-cytoscapejs cytoscape-dagre
   ```

3. **Test API directly:**
   - Use Postman or curl to test the endpoint
   - Check http://localhost:8000/docs for interactive testing

4. **Common fixes:**
   - Restart both servers
   - Clear browser cache
   - Reinstall dependencies if needed

---

**🎉 Congratulations!** If all tests pass, your citation mesh feature is complete and working!
