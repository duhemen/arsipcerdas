# backend/core/workflow.py
# Integrasi semua service - VERSI FIXED

import sys
from pathlib import Path

# Tambahkan root project ke sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Sekarang import dengan benar
from backend.services.parser import DocumentParser
from backend.services.ai import AIService
from backend.services.database import DatabaseManager
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Workflow:
    """Alur kerja utama ArsipCerdas"""
    
    def __init__(self):
        self.parser = DocumentParser()
        self.ai = AIService()
        self.db = DatabaseManager("data")
        
        logger.info("✅ Workflow siap!")
    
    def process_document(self, filepath: str):
        """Proses satu dokumen: parse → embed → simpan"""
        logger.info(f"📄 Memproses: {filepath}")
        
        # 1. Parse dokumen
        parsed = self.parser.parse(filepath)
        logger.info(f"   ✅ Parsing selesai: {parsed.total_pages} halaman, {len(parsed.chunks)} chunk")
        
        # 2. Embed semua chunks
        texts = [chunk.text for chunk in parsed.chunks]
        embeddings = self.ai.embed(texts)
        logger.info(f"   ✅ Embedding selesai: {len(embeddings)} vektor")
        
        # 3. Simpan ke database
        self.db.save_document(parsed, embeddings)
        logger.info(f"   ✅ Dokumen tersimpan!")
        
        return parsed
    
    def search(self, query: str, limit: int = 10):
        """Cari dokumen"""
        logger.info(f"🔍 Mencari: '{query}'")
        
        # 1. Embed query
        query_vector = self.ai.embed_single(query)
        
        # 2. Cari di database
        results = self.db.search(query_vector, limit=limit)
        
        # 3. Catat log
        self.db.log_search(query, len(results), 0.5)
        
        return results
    
    def get_stats(self):
        """Dapatkan statistik"""
        return self.db.get_stats()

# ============ FUNGSI TEST ============

def test_workflow():
    """Test workflow lengkap"""
    print("=" * 60)
    print("🧪 TESTING WORKFLOW LENGKAP")
    print("=" * 60)
    
    # Buat workflow
    workflow = Workflow()
    
    # 1. Buat file test
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    
    test_files = []
    for i in range(3):
        filename = f"test_doc_{i+1}.pdf"
        c = canvas.Canvas(filename, pagesize=letter)
        c.drawString(100, 750, f"Dokumen Test {i+1}")
        c.drawString(100, 700, f"Nomor: 440/{i+1:03d}/2026")
        c.drawString(100, 675, f"Tanggal: {15+i} Juni 2026")
        c.drawString(100, 650, f"Perihal: Dokumen ke-{i+1}")
        c.save()
        test_files.append(filename)
    
    print("\n📄 File test dibuat:")
    for f in test_files:
        print(f"   - {f}")
    
    # 2. Proses semua file
    print("\n" + "=" * 60)
    print("📥 PROSES INGEST")
    print("=" * 60)
    
    for f in test_files:
        try:
            workflow.process_document(f)
        except Exception as e:
            logger.error(f"❌ Gagal proses {f}: {e}")
    
    # 3. Test search
    print("\n" + "=" * 60)
    print("🔍 TEST SEARCH")
    print("=" * 60)
    
    queries = [
        "nomor 440",
        "dokumen test",
        "Juni 2026"
    ]
    
    for query in queries:
        print(f"\n🔍 Mencari: '{query}'")
        try:
            results = workflow.search(query, limit=5)
            
            if results:
                print(f"   ✅ Ditemukan {len(results)} hasil:")
                for i, r in enumerate(results[:3], 1):
                    text = r.get('text', '')[:50]
                    print(f"   {i}. {text}...")
            else:
                print("   ❌ Tidak ada hasil")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # 4. Statistik
    print("\n" + "=" * 60)
    print("📊 STATISTIK")
    print("=" * 60)
    stats = workflow.get_stats()
    print(f"Total dokumen: {stats['total_documents']}")
    print(f"Total chunk: {stats['total_chunks']}")
    
    # 5. Cleanup
    print("\n" + "=" * 60)
    print("🧹 CLEANUP")
    print("=" * 60)
    for f in test_files:
        if os.path.exists(f):
            os.remove(f)
            print(f"   ✅ Hapus: {f}")
    
    print("\n✅ Workflow test selesai!")

if __name__ == "__main__":
    test_workflow()