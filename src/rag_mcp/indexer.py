import os
import time
import uuid
from typing import List, Dict, Set
from .config import AppConfig
from .storage import RAGStorage
from .utils import is_text_file, read_file_content, chunk_text

from .logger import logger

class Indexer:
    def __init__(self, target_dir: str, config: AppConfig):
        self.target_dir = os.path.abspath(target_dir)
        self.config = config
        self.storage = RAGStorage(self.target_dir, config)

    def index(self):
        logger.info(f"Indexing directory: {self.target_dir}")
        self.storage.initialize()
        
        # Get existing files in DB
        existing_data = self.storage.collection.get(include=['metadatas'])
        
        existing_files: Dict[str, float] = {} # path -> mtime
        file_ids: Dict[str, List[str]] = {} # path -> list of chunk ids
        
        if existing_data and existing_data['ids']:
            for i, meta in enumerate(existing_data['metadatas']):
                if meta and 'file_path' in meta:
                    fpath = meta['file_path']
                    fmtime = meta.get('mtime', 0)
                    existing_files[fpath] = fmtime
                    if fpath not in file_ids:
                        file_ids[fpath] = []
                    file_ids[fpath].append(existing_data['ids'][i])

        # Walk directory
        current_files: Set[str] = set()
        files_to_process = []
        
        for root, dirs, files in os.walk(self.target_dir):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
                
            for file in files:
                file_path = os.path.join(root, file)
                if not is_text_file(file_path):
                    continue
                    
                current_files.add(file_path)
                mtime = os.path.getmtime(file_path)
                
                # Check if needs update
                # Use a small epsilon for float comparison
                if file_path not in existing_files or abs(existing_files[file_path] - mtime) > 1e-6:
                    files_to_process.append(file_path)

        # Identify deleted files
        files_to_delete = []
        for fpath in existing_files:
            if fpath not in current_files:
                files_to_delete.append(fpath)

        # Delete removed files
        if files_to_delete:
            logger.info(f"Removing {len(files_to_delete)} deleted files from index...")
            all_ids_to_delete = []
            for fpath in files_to_delete:
                if fpath in file_ids:
                    all_ids_to_delete.extend(file_ids[fpath])
            if all_ids_to_delete:
                self.storage.collection.delete(ids=all_ids_to_delete)

        # Process new/modified files
        # First, delete old chunks for modified files
        ids_to_remove_for_update = []
        for fpath in files_to_process:
            if fpath in file_ids:
                ids_to_remove_for_update.extend(file_ids[fpath])
        
        if ids_to_remove_for_update:
             self.storage.collection.delete(ids=ids_to_remove_for_update)

        logger.info(f"Processing {len(files_to_process)} files...")
        
        for i, file_path in enumerate(files_to_process):
            try:
                content = read_file_content(file_path)
                if not content:
                    continue
                    
                chunks = chunk_text(content, self.config.processing.chunk_count)
                
                if not chunks:
                    continue
                    
                mtime = os.path.getmtime(file_path)
                file_name = os.path.basename(file_path)
                
                doc_ids = [str(uuid.uuid4()) for _ in chunks]
                metadatas = []
                for chunk in chunks:
                    metadatas.append({
                        "file_path": file_path,
                        "file_name": file_name,
                        "mtime": mtime,
                        "chunk_index": chunks.index(chunk),
                        "total_chunks": len(chunks)
                    })
                
                self.storage.add_documents(chunks, metadatas, doc_ids)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1}/{len(files_to_process)} files")
                    
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                
        logger.info("Indexing complete.")

    def clean(self):
        self.storage.clear()
