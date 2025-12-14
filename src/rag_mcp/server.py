import os
import json
import time
from typing import Optional
from mcp.server.fastmcp import FastMCP
from .config import load_config, AppConfig
from .storage import RAGStorage
from .state import StateManager
from .utils import read_file_content

from .logger import logger

def get_config() -> AppConfig:
    # Try to find config
    # 1. Env var
    # 2. Current dir
    config_path = os.environ.get("RAG_MCP_CONFIG", "config.yaml")
    return load_config(config_path)

def search_rag_impl(keyword: str, dir_path: Optional[str] = None) -> str:
    start_time = time.time()
    config = get_config()
    
    dirs_to_search = []

    # Check if we are in single-directory serve mode
    current_serve_dir = os.environ.get("RAG_MCP_SERVE_DIR")

    if current_serve_dir:
        # If serving a specific directory, we only search that one by default
        # In serve mode, we ignore dir_path parameter as requested
        dirs_to_search.append(current_serve_dir)
    elif dir_path:
        dirs_to_search.append(dir_path)
    else:
        dirs_to_search = StateManager.load_state()
        
    if not dirs_to_search:
        return json.dumps({
            "code": 500,
            "message": "No directories indexed or specified.",
            "data": None
        }, ensure_ascii=False)
        
    all_matches = []
    total_files = 0
    total_chunks = 0
    
    for d in dirs_to_search:
        if not os.path.exists(os.path.join(d, ".muxue_rag")):
            continue
            
        try:
            storage = RAGStorage(d, config)
            results = storage.search(keyword, n_results=5)
            
            # results is a dict: {'ids': [[]], 'documents': [[]], 'metadatas': [[]], 'distances': [[]]}
            if results and results['documents']:
                docs = results['documents'][0]
                metas = results['metadatas'][0]
                dists = results['distances'][0] if 'distances' in results else [0]*len(docs)
                
                for i, doc in enumerate(docs):
                    meta = metas[i]
                    dist = dists[i]
                    
                    all_matches.append({
                        "content": doc,
                        "match_degree": "high" if dist < 0.5 else "medium", # heuristic
                        "file_path": meta.get("file_path"),
                        "score": dist
                    })
        except Exception as e:
            logger.error(f"Error searching in {d}: {e}")
            
    # Sort by score (lower distance is better)
    all_matches.sort(key=lambda x: x['score'])
    
    # Format response
    match_content = []
    file_info = []
    
    for m in all_matches:
        match_content.append({
            "content": m['content'],
            "match_degree": m['match_degree']
        })
        file_info.append({
            "file_path": m['file_path']
        })
        
    stats = {
        "cost_time": round(time.time() - start_time, 3),
        "match_file_count": len(set(m['file_path'] for m in all_matches)),
        "match_chunk_count": len(all_matches)
    }
    
    if not all_matches:
        return json.dumps({
            "code": 200,
            "message": "未检索到与关键词相关的内容",
            "data": None
        }, ensure_ascii=False)
        
    return json.dumps({
        "code": 200,
        "message": "检索成功",
        "data": {
            "match_content": match_content,
            "file_info": file_info,
            "stats": stats
        }
    }, ensure_ascii=False)

def create_mcp_server() -> FastMCP:
    """创建并配置MCP服务器，根据环境动态注册工具"""
    # Check if we are in single-directory serve mode
    serve_dir = os.environ.get("RAG_MCP_SERVE_DIR")

    # Initialize FastMCP
    mcp = FastMCP("rag-mcp")

    if serve_dir:
        @mcp.tool()
        def search_rag(keyword: str) -> str:
            """
            Search for keyword in RAG database.
            Args:
                keyword: Search query.
            """
            return search_rag_impl(keyword, None)
    else:
        @mcp.tool()
        def search_rag(keyword: str, dir_path: Optional[str] = None) -> str:
            """
            Search for keyword in RAG database.
            Args:
                keyword: Search query.
                dir_path: Optional directory to search in. If None, searches all indexed directories.
            """
            return search_rag_impl(keyword, dir_path)

    @mcp.tool()
    def read_raw_file(file_path: str) -> str:
        """
        Read raw content of a file.
        Args:
            file_path: Absolute path to the file.
        """
        if not os.path.exists(file_path):
            return json.dumps({
                "code": 500,
                "message": "文件不存在，请检查路径是否正确",
                "data": None
            }, ensure_ascii=False)

        # Check if text file?
        # Requirement says: "If non-text, return error"
        # We can use our is_text_file util, but it's in utils.
        from .utils import is_text_file
        if not is_text_file(file_path):
             return json.dumps({
                "code": 500,
                "message": "无法读取非纯文本文件",
                "data": None
            }, ensure_ascii=False)

        try:
            content = read_file_content(file_path)
            stats = os.stat(file_path)

            return json.dumps({
                "code": 200,
                "message": "读取成功",
                "data": {
                    "raw_content": content
                },
                "file_info": {
                    "file_path": file_path,
                    "file_size": stats.st_size,
                    "modify_time": stats.st_mtime
                }
            }, ensure_ascii=False)
        except PermissionError:
            return json.dumps({
                "code": 500,
                "message": "无文件读取权限，请检查权限设置",
                "data": None
            }, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                "code": 500,
                "message": f"读取失败: {str(e)}",
                "data": None
            }, ensure_ascii=False)

    return mcp

def start_server():
    """启动MCP服务器"""
    mcp = create_mcp_server()
    mcp.run()
