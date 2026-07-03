# backend/services/database.py
# Database Service - Versi Fix untuk LanceDB Schema

import os
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging

import lancedb
import numpy as np
import pyarrow as pa  # <-- IMPORTANT: untuk schema

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Mengelola database ArsipCerdas"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Path database
        self.vector_path = self.data_dir / "lancedb"
        self.sqlite_path = self.data_dir / "metadata.db"
        
        # Inisialisasi
        self._init_sqlite()
        self._init_lancedb()
        
        logger.info(f"✅ Database siap di: {self.data_dir}")
    
    def _init_sqlite(self):
        """Buat tabel SQLite"""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        
        # Tabel dokumen
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                file_path TEXT UNIQUE,
                file_hash TEXT,
                total_pages INTEGER,
                indexed_at TIMESTAMP,
                file_size INTEGER,
                metadata TEXT
            )
        ''')
        
        # Tabel chunk
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                doc_id TEXT,
                text TEXT,
                page_num INTEGER,
                chunk_index INTEGER,
                FOREIGN KEY(doc_id) REFERENCES documents(id)
            )
        ''')
        
        # Tabel audit log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                query TEXT,
                results_count INTEGER,
                time_ms REAL
            )
        ''')
        
        # Index untuk performa
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_path ON documents(file_path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_doc_id ON chunks(doc_id)')
        
        conn.commit()
        conn.close()
        
        logger.info("✅ SQLite siap")
    
    def _init_lancedb(self):
        """Inisialisasi LanceDB untuk vector search"""
        try:
            # Koneksi ke LanceDB
            self.vector_db = lancedb.connect(str(self.vector_path))
            
            # Cek apakah table sudah ada
            tables = self.vector_db.table_names()
            
            if 'documents' not in tables:
                # Buat schema dengan PyArrow
                schema = pa.schema([
                    pa.field('id', pa.string()),
                    pa.field('text', pa.string()),
                    pa.field('vector', pa.list_(pa.float32(), 384)),
                    pa.field('file_path', pa.string()),
                    pa.field('page_num', pa.int32()),
                    pa.field('chunk_index', pa.int32()),
                    pa.field('metadata', pa.string()),
                    pa.field('tanggal', pa.string()),
                    pa.field('nomor_surat', pa.string())
                ])
                
                # Buat table dengan schema
                self.vector_db.create_table('documents', schema=schema)
                logger.info("✅ LanceDB table 'documents' dibuat")
            
            # Simpan referensi table
            self.doc_table = self.vector_db.open_table('documents')
            logger.info("✅ LanceDB siap")
            
        except Exception as e:
            logger.error(f"❌ Gagal inisialisasi LanceDB: {e}")
            # Fallback: hapus dan buat ulang
            import shutil
            if self.vector_path.exists():
                shutil.rmtree(self.vector_path)
                logger.info("🗑️ Data LanceDB lama dihapus")
            
            # Buat ulang
            self.vector_db = lancedb.connect(str(self.vector_path))
            
            # Schema dengan PyArrow
            schema = pa.schema([
                pa.field('id', pa.string()),
                pa.field('text', pa.string()),
                pa.field('vector', pa.list_(pa.float32(), 384)),
                pa.field('file_path', pa.string()),
                pa.field('page_num', pa.int32()),
                pa.field('chunk_index', pa.int32()),
                pa.field('metadata', pa.string()),
                pa.field('tanggal', pa.string()),
                pa.field('nomor_surat', pa.string())
            ])
            
            self.vector_db.create_table('documents', schema=schema)
            self.doc_table = self.vector_db.open_table('documents')
            logger.info("✅ LanceDB siap (dibuat ulang)")
    
    def save_document(self, parsed_doc, embeddings: List[np.ndarray]):
        """Simpan dokumen hasil parsing ke database"""
        
        doc_id = parsed_doc.file_hash
        
        # 1. Simpan ke SQLite
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        
        # Metadata sebagai JSON
        metadata = {}
        if hasattr(parsed_doc, 'metadata'):
            if hasattr(parsed_doc.metadata, '__dict__'):
                metadata = parsed_doc.metadata.__dict__
            else:
                metadata = parsed_doc.metadata
        
        cursor.execute('''
            INSERT OR REPLACE INTO documents 
            (id, file_path, file_hash, total_pages, indexed_at, file_size, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            doc_id,
            parsed_doc.file_path,
            parsed_doc.file_hash,
            parsed_doc.total_pages,
            datetime.now().isoformat(),
            os.path.getsize(parsed_doc.file_path),
            json.dumps(metadata, default=str)
        ))
        
        # 2. Simpan chunks ke SQLite
        for chunk in parsed_doc.chunks:
            chunk_id = f"{doc_id}_{chunk.chunk_index}"
            cursor.execute('''
                INSERT OR REPLACE INTO chunks
                (id, doc_id, text, page_num, chunk_index)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                chunk_id,
                doc_id,
                chunk.text,
                chunk.page_num,
                chunk.chunk_index
            ))
        
        conn.commit()
        conn.close()
        
        # 3. Simpan ke LanceDB
        data = []
        for chunk, emb in zip(parsed_doc.chunks, embeddings):
            # Ekstrak metadata dari chunk
            metadata = self._extract_metadata_from_text(chunk.text)
            
            # Pastikan vector dalam format list
            if hasattr(emb, 'tolist'):
                vector_list = emb.tolist()
            else:
                vector_list = emb
            
            data.append({
                'id': f"{doc_id}_{chunk.chunk_index}",
                'text': chunk.text,
                'vector': vector_list,
                'file_path': parsed_doc.file_path,
                'page_num': chunk.page_num,
                'chunk_index': chunk.chunk_index,
                'metadata': json.dumps(metadata),
                'tanggal': metadata.get('tanggal', ''),
                'nomor_surat': metadata.get('nomor', '')
            })
        
        if data:
            try:
                self.doc_table.add(data)
                logger.info(f"✅ {len(data)} chunk tersimpan di LanceDB")
            except Exception as e:
                logger.error(f"❌ Gagal simpan ke LanceDB: {e}")
                # Coba alternative: tambahkan satu per satu
                for item in data:
                    try:
                        self.doc_table.add([item])
                    except Exception as e2:
                        logger.error(f"❌ Gagal simpan chunk {item['id']}: {e2}")
        
        logger.info(f"✅ Dokumen tersimpan: {parsed_doc.file_path} ({len(embeddings)} chunk)")
    
    def _extract_metadata_from_text(self, text: str) -> Dict:
        """Ekstrak metadata dari teks chunk"""
        import re
        metadata = {}
        
        # Cari nomor surat
        nomor_pattern = r'(?:Nomor|No\.?)\s*[:;]\s*([^\n]+)'
        match = re.search(nomor_pattern, text, re.IGNORECASE)
        if match:
            metadata['nomor'] = match.group(1).strip()
        
        # Cari tanggal
        tanggal_pattern = r'(?:Tanggal|Tgl\.?)\s*[:;]\s*([^\n]+)'
        match = re.search(tanggal_pattern, text, re.IGNORECASE)
        if match:
            metadata['tanggal'] = match.group(1).strip()
        
        # Cari perihal
        perihal_pattern = r'(?:Perihal|Hal)\s*[:;]\s*([^\n]+)'
        match = re.search(perihal_pattern, text, re.IGNORECASE)
        if match:
            metadata['perihal'] = match.group(1).strip()
        
        return metadata
    
    def search(self, query_vector: np.ndarray, limit: int = 10) -> List[Dict]:
        """Cari dokumen dengan vector similarity"""
        try:
            # Pastikan query_vector dalam format list
            if hasattr(query_vector, 'tolist'):
                query_vector = query_vector.tolist()
            
            # Search di LanceDB
            results = self.doc_table.search(query_vector).limit(limit).to_list()
            
            return results
        except Exception as e:
            logger.error(f"❌ Gagal search: {e}")
            return []
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """Ambil dokumen dari SQLite"""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'file_path': row[1],
                'file_hash': row[2],
                'total_pages': row[3],
                'indexed_at': row[4],
                'file_size': row[5],
                'metadata': json.loads(row[6]) if row[6] else {}
            }
        return None
    
    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """Ambil log pencarian"""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, query, results_count, time_ms 
            FROM audit_log 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'timestamp': row[0],
                'query': row[1],
                'results_count': row[2],
                'time_ms': row[3]
            }
            for row in rows
        ]
    
    def log_search(self, query: str, results_count: int, time_ms: float):
        """Catat pencarian ke audit log"""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO audit_log (query, results_count, time_ms)
            VALUES (?, ?, ?)
        ''', (query, results_count, time_ms))
        
        conn.commit()
        conn.close()
    
    def get_stats(self) -> Dict:
        """Dapatkan statistik database"""
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        
        # Total dokumen
        cursor.execute('SELECT COUNT(*) FROM documents')
        total_docs = cursor.fetchone()[0]
        
        # Total chunks
        cursor.execute('SELECT COUNT(*) FROM chunks')
        total_chunks = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_documents': total_docs,
            'total_chunks': total_chunks
        }
    
    def clear_all(self):
        """Hapus semua data (hati-hati!)"""
        import shutil
        
        # Hapus SQLite
        if self.sqlite_path.exists():
            self.sqlite_path.unlink()
        
        # Hapus LanceDB
        if self.vector_path.exists():
            shutil.rmtree(self.vector_path)
        
        # Re-inisialisasi
        self._init_sqlite()
        self._init_lancedb()
        
        logger.warning("⚠️ Semua data database telah dihapus!")

# ============ FUNGSI TEST ============

def test_database():
    """Test database sederhana"""
    print("🧪 Testing Database...")
    
    # Buat database
    db = DatabaseManager("data_test")
    
    # Test stats
    stats = db.get_stats()
    print(f"✅ Stats: {stats}")
    
    # Test log
    db.log_search("test query", 10, 0.5)
    logs = db.get_audit_log(1)
    print(f"✅ Log: {logs}")
    
    # Hapus data test
    import shutil
    shutil.rmtree("data_test")
    
    print("✅ Database test selesai!")

if __name__ == "__main__":
    test_database()