import os
import uvicorn
import webbrowser
import threading
import time

def open_browser():
    time.sleep(2) # Wait for server to start
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    print("🚀 Starting Gesture Control Suite...")
    
    # Check if frontend is built
    if not os.path.exists("frontend/dist"):
        print("⚠️ Warning: Frontend build not found. Please run 'cd frontend & npm run build' first.")
    
    # Start browser thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Start server
    from server import app
    uvicorn.run(app, host="0.0.0.0", port=8000)
