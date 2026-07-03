# main.py - Aplikasi ArsipCerdas FULL v0.3
# Dengan semua fitur: PDF Preview, Drag & Drop, Bulk Indexing, Export

import sys
import os
import socket
import webbrowser
import time
import logging
import json
from pathlib import Path
from typing import Optional, List
import shutil

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Tambahkan path project
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def find_free_port():
    """Cari port kosong"""
    for port in range(52341, 52441):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except:
                continue
    return 52341

def run_fastapi():
    """Jalankan FastAPI server"""
    try:
        import uvicorn
        from fastapi import FastAPI, HTTPException, UploadFile, File
        from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
        from fastapi.staticfiles import StaticFiles
        from pydantic import BaseModel
        
        # Import services
        from backend.services.parser import DocumentParser
        from backend.services.ai import AIService
        from backend.services.database import DatabaseManager
        
        # Inisialisasi services
        parser = DocumentParser()
        ai = AIService()
        db = DatabaseManager("data")
        
        # Buat FastAPI app
        app = FastAPI(title="ArsipCerdas API", version="0.3.0")
        
        # Models untuk API
        class SearchQuery(BaseModel):
            query: str
            limit: Optional[int] = 10
        
        class IngestRequest(BaseModel):
            file_path: str
        
        class ExportRequest(BaseModel):
            results: List[dict]
            format: str = "csv"
        
        # Path frontend
        frontend_path = Path(__file__).parent / "frontend"
        
        # Mount static files jika frontend ada
        if frontend_path.exists():
            app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
        
        # ==================== API ENDPOINTS ====================
        
        @app.get("/")
        async def root():
            """Halaman utama"""
            index_path = frontend_path / "index.html"
            if index_path.exists():
                return HTMLResponse(content=index_path.read_text(encoding='utf-8'))
            
            # Fallback jika frontend belum ada
            return HTMLResponse("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>ArsipCerdas</title>
                    <style>
                        body { font-family: 'Segoe UI', Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; background: #f5f5f5; }
                        .container { background: white; border-radius: 10px; padding: 40px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                        h1 { color: #2563eb; margin-top: 0; }
                        .status { background: #dcfce7; padding: 10px 20px; border-radius: 5px; color: #166534; }
                        .endpoint { background: #f8fafc; padding: 10px 15px; margin: 10px 0; border-radius: 5px; font-family: monospace; }
                        .method { display: inline-block; padding: 2px 10px; border-radius: 3px; font-weight: bold; margin-right: 10px; }
                        .get { background: #dbeafe; color: #1e40af; }
                        .post { background: #d1fae5; color: #065f46; }
                        .footer { margin-top: 30px; color: #6b7280; font-size: 14px; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>🚀 ARSIP CERDAS</h1>
                        <div class="status">✅ Aplikasi berjalan dengan baik!</div>
                        <h2>📡 API Endpoints</h2>
                        <div class="endpoint"><span class="method get">GET</span> <code>/api/status</code> - Cek status server</div>
                        <div class="endpoint"><span class="method post">POST</span> <code>/api/search</code> - Cari dokumen</div>
                        <div class="endpoint"><span class="method post">POST</span> <code>/api/ingest</code> - Index dokumen</div>
                        <div class="endpoint"><span class="method post">POST</span> <code>/api/ingest-folder</code> - Index folder</div>
                        <div class="endpoint"><span class="method post">POST</span> <code>/api/upload</code> - Upload PDF</div>
                        <div class="endpoint"><span class="method get">GET</span> <code>/api/stats</code> - Statistik database</div>
                        <div class="endpoint"><span class="method get">GET</span> <code>/api/logs</code> - Audit log</div>
                        <div class="endpoint"><span class="method get">GET</span> <code>/api/preview</code> - Preview PDF</div>
                        <div class="endpoint"><span class="method post">POST</span> <code>/api/export</code> - Export hasil</div>
                        <div class="footer">ArsipCerdas v0.3.0 | 100% Offline</div>
                    </div>
                </body>
                </html>
            """)
        
        @app.get("/api/status")
        async def status():
            """Cek status server"""
            return {
                "status": "running",
                "version": "0.3.0",
                "timestamp": time.time()
            }
        
        @app.post("/api/search")
        async def search(query: SearchQuery):
            """Cari dokumen berdasarkan query"""
            try:
                start_time = time.time()
                
                # 1. Embed query
                query_vector = ai.embed_single(query.query)
                
                # 2. Search di database
                results = db.search(query_vector, limit=query.limit)
                
                # 3. Log
                elapsed_ms = (time.time() - start_time) * 1000
                db.log_search(query.query, len(results), elapsed_ms)
                
                return {
                    "query": query.query,
                    "results": results,
                    "total": len(results),
                    "time_ms": elapsed_ms
                }
            except Exception as e:
                logger.error(f"Search error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/api/ingest")
        async def ingest(request: IngestRequest):
            """Index satu dokumen"""
            try:
                # Parse dokumen
                parsed = parser.parse(request.file_path)
                
                # Embed
                texts = [chunk.text for chunk in parsed.chunks]
                embeddings = ai.embed(texts)
                
                # Simpan
                db.save_document(parsed, embeddings)
                
                return {
                    "status": "success",
                    "file": request.file_path,
                    "chunks": len(parsed.chunks),
                    "pages": parsed.total_pages
                }
            except Exception as e:
                logger.error(f"Ingest error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/api/ingest-folder")
        async def ingest_folder(folder_path: str):
            """Index seluruh folder PDF"""
            try:
                folder = Path(folder_path)
                if not folder.exists():
                    raise HTTPException(status_code=404, detail="Folder tidak ditemukan")
                
                pdf_files = list(folder.glob("**/*.pdf"))
                total = len(pdf_files)
                
                results = {
                    'total': total,
                    'processed': 0,
                    'failed': 0,
                    'files': []
                }
                
                for idx, pdf_file in enumerate(pdf_files):
                    try:
                        # Parse dokumen
                        parsed = parser.parse(str(pdf_file))
                        
                        # Embed
                        texts = [chunk.text for chunk in parsed.chunks]
                        embeddings = ai.embed(texts)
                        
                        # Simpan
                        db.save_document(parsed, embeddings)
                        
                        results['processed'] += 1
                        results['files'].append({
                            'name': pdf_file.name,
                            'status': 'success'
                        })
                    except Exception as e:
                        results['failed'] += 1
                        results['files'].append({
                            'name': pdf_file.name,
                            'status': 'failed',
                            'error': str(e)
                        })
                
                return results
                
            except Exception as e:
                logger.error(f"Ingest folder error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/api/upload")
        async def upload_file(file: UploadFile = File(...)):
            """Upload dan index PDF"""
            try:
                # Simpan file sementara
                temp_dir = Path("temp_uploads")
                temp_dir.mkdir(exist_ok=True)
                
                file_path = temp_dir / file.filename
                with open(file_path, "wb") as f:
                    content = await file.read()
                    f.write(content)
                
                # Index file
                parsed = parser.parse(str(file_path))
                texts = [chunk.text for chunk in parsed.chunks]
                embeddings = ai.embed(texts)
                db.save_document(parsed, embeddings)
                
                # Hapus file sementara
                file_path.unlink()
                
                return {
                    "status": "success",
                    "file": file.filename,
                    "chunks": len(parsed.chunks),
                    "pages": parsed.total_pages
                }
            except Exception as e:
                logger.error(f"Upload error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/api/stats")
        async def stats():
            """Statistik database"""
            return db.get_stats()
        
        @app.get("/api/logs")
        async def logs(limit: int = 50):
            """Audit log pencarian"""
            logs = db.get_audit_log(limit)
            return {"logs": logs}
        
        @app.get("/api/preview")
        async def preview(file: str):
            """Stream PDF untuk preview"""
            try:
                file_path = Path(file)
                if not file_path.exists():
                    raise HTTPException(status_code=404, detail="File tidak ditemukan")
                
                return FileResponse(
                    path=file_path,
                    media_type='application/pdf',
                    filename=file_path.name
                )
            except Exception as e:
                logger.error(f"Preview error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/api/download")
        async def download(file: str):
            """Download PDF"""
            try:
                file_path = Path(file)
                if not file_path.exists():
                    raise HTTPException(status_code=404, detail="File tidak ditemukan")
                
                return FileResponse(
                    path=file_path,
                    media_type='application/pdf',
                    filename=file_path.name
                )
            except Exception as e:
                logger.error(f"Download error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/api/upload")
        async def upload_file(file: UploadFile = File(...)):
            """Upload dan index berbagai format file"""
            try:
                # Validasi ekstensi
                allowed_extensions = ['.pdf', '.docx', '.pptx', '.xlsx', '.txt']
                file_ext = Path(file.filename).suffix.lower()
        
                if file_ext not in allowed_extensions:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Format tidak didukung. Gunakan: {', '.join(allowed_extensions)}"
                    )
        
                # Simpan file sementara
                temp_dir = Path("temp_uploads")
                temp_dir.mkdir(exist_ok=True)
        
                file_path = temp_dir / file.filename
                with open(file_path, "wb") as f:
                    content = await file.read()
                    f.write(content)
        
                # Parse file
                parsed = parser.parse_any(str(file_path))
        
                # Embed
                texts = [chunk.text for chunk in parsed.chunks]
                embeddings = ai.embed(texts)
        
                # Simpan
                db.save_document(parsed, embeddings)
        
                # Hapus file sementara
                file_path.unlink()
        
                return {
                    "status": "success",
                    "file": file.filename,
                    "type": file_ext,
                    "chunks": len(parsed.chunks),
                    "pages": parsed.total_pages
                }
            except Exception as e:
                logger.error(f"Upload error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # ==================== START SERVER ====================
        
        # Jalankan server
        port = find_free_port()
        logger.info(f"🚀 FastAPI berjalan di http://localhost:{port}")
        
        # Buka browser
        webbrowser.open(f"http://localhost:{port}")
        
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
        
    except Exception as e:
        logger.error(f"❌ Gagal menjalankan FastAPI: {e}")

def main():
    """Main function"""
    print("=" * 60)
    print("🚀 ARSIP CERDAS v0.3.0")
    print("=" * 60)
    print("📡 Mencari port kosong...")
    
    port = find_free_port()
    print(f"✅ Port ditemukan: {port}")
    
    print("🚀 Menjalankan server...")
    print("🌐 Browser akan terbuka otomatis")
    print("\n📋 API Endpoints:")
    print(f"   http://localhost:{port}/api/status")
    print(f"   http://localhost:{port}/api/stats")
    print(f"   http://localhost:{port}/api/logs")
    print("\n💡 Fitur:")
    print("   - 🔍 Search dokumen dengan AI")
    print("   - 📄 Preview PDF di browser")
    print("   - 📤 Drag & Drop upload")
    print("   - 📁 Bulk indexing folder")
    print("   - 📊 Export hasil (CSV/PDF)")
    print("\n   Tekan Ctrl+C untuk berhenti\n")
    
    # Jalankan FastAPI
    try:
        run_fastapi()
    except KeyboardInterrupt:
        print("\n👋 Sampai jumpa!")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()