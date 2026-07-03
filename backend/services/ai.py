# backend/services/ai.py
# AI Service - Mengubah teks menjadi vektor

import logging
import numpy as np
from typing import List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class AIService:
    """Service untuk embedding teks"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Model default: all-MiniLM-L6-v2 (ukuran 80MB, ringan)
        Alternatif: multilingual-e5-small (420MB, lebih akurat)
        """
        self.model_name = model_name
        self.model = None
        self.is_loaded = False
        
        logger.info(f"🤖 AI Service siap dengan model: {model_name}")
    
    def load_model(self):
        """Load model (lazy loading)"""
        if self.is_loaded:
            return
        
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"⏳ Loading model {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)
            self.is_loaded = True
            logger.info("✅ Model siap!")
        except Exception as e:
            logger.error(f"❌ Gagal load model: {e}")
            raise
    
    def embed(self, texts: List[str]) -> np.ndarray:
        """Ubah teks menjadi vektor"""
        if not texts:
            return np.array([])
        
        # Load model jika belum
        if not self.is_loaded:
            self.load_model()
        
        # Embedding
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,  # Normalisasi untuk cosine similarity
            show_progress_bar=False
        )
        
        return embeddings
    
    def embed_single(self, text: str) -> np.ndarray:
        """Ubah satu teks menjadi vektor"""
        return self.embed([text])[0]

# ============ FUNGSI TEST ============

def test_ai():
    """Test AI service"""
    print("🧪 Testing AI Service...")
    
    # Buat service
    ai = AIService()
    
    # Test teks
    texts = [
        "Surat cuti tahunan Pak Budi",
        "Nomor surat 440/012/2026",
        "Perihal: Pengajuan cuti"
    ]
    
    # Embed
    embeddings = ai.embed(texts)
    
    print(f"✅ Jumlah teks: {len(texts)}")
    print(f"✅ Dimensi vektor: {embeddings.shape}")
    print(f"✅ Tipe data: {embeddings.dtype}")
    
    # Test similarity
    from sklearn.metrics.pairwise import cosine_similarity
    
    # Cari teks yang paling mirip dengan "cuti"
    query = "cuti tahunan"
    query_emb = ai.embed_single(query)
    
    similarities = cosine_similarity([query_emb], embeddings)[0]
    
    print(f"\n🔍 Mencari: '{query}'")
    for text, sim in zip(texts, similarities):
        print(f"   {text[:50]}... -> {sim:.3f}")
    
    print("\n✅ AI Service test selesai!")

if __name__ == "__main__":
    test_ai()