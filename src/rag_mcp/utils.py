import os
import mimetypes

def is_text_file(file_path: str) -> bool:
    """
    Check if a file is a text file based on extension and content.
    """
    # Skip hidden files/dirs (except if explicitly handled, but usually we skip .git etc)
    if os.path.basename(file_path).startswith('.'):
        return False
        
    # Extensions to skip
    skip_exts = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg',
        '.mp4', '.avi', '.mov', '.flv', '.mkv',
        '.mp3', '.wav', '.flac', '.aac',
        '.zip', '.rar', '.tar', '.gz', '.7z',
        '.exe', '.dll', '.sh', '.bat', '.apk',
        '.pdf', '.docx', '.xlsx', '.bin', '.pyc'
    }
    
    ext = os.path.splitext(file_path)[1].lower()
    if ext in skip_exts:
        return False
        
    # Extensions to include
    text_exts = {
        '.txt', '.md', '.json', '.yaml', '.xml', '.csv', '.log', '.ini', '.conf', '.py', '.js', '.html', '.css'
    }
    
    if ext in text_exts:
        return True
        
    # Heuristic check for other files
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)
            return True
    except UnicodeDecodeError:
        return False
    except Exception:
        return False

def read_file_content(file_path: str) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""

def chunk_text(text: str, chunk_count: int) -> list[str]:
    """
    Split text into approximately `chunk_count` parts, respecting boundaries.
    """
    if not text:
        return []
        
    if chunk_count <= 1:
        return [text]
        
    total_len = len(text)
    target_size = total_len // chunk_count
    
    if target_size == 0:
        return [c for c in text] # Very small text
        
    chunks = []
    current_pos = 0
    
    # Simple recursive splitter logic simulation
    # We want to find a split point near current_pos + target_size
    
    for _ in range(chunk_count - 1):
        if current_pos >= total_len:
            break
            
        search_start = current_pos + target_size
        # Look for a good split point around search_start
        # Priorities: \n\n, \n, space
        
        split_point = -1
        
        # Search window: +/- 20% of target size? Or just look forward/backward
        # Let's look forward for the nearest newline
        
        # Try to find \n in the next chunk
        # We want to split roughly at `current_pos + target_size`
        
        candidate = min(current_pos + target_size, total_len)
        
        # If we are at the end, just take the rest
        if candidate == total_len:
            chunks.append(text[current_pos:])
            current_pos = total_len
            break
            
        # Look for \n around candidate
        # Search range: [candidate - target_size/2, candidate + target_size/2]
        # But we must advance.
        
        # Let's just find the nearest newline after candidate, or before if it's too far.
        # Simple approach: Find last \n before candidate + margin?
        
        # Let's use a simpler approach:
        # Just split at `target_size` but back off to nearest newline.
        
        end = min(current_pos + target_size, total_len)
        
        # Try to extend to next newline if it's close
        next_newline = text.find('\n', end)
        prev_newline = text.rfind('\n', current_pos, end)
        
        if next_newline != -1 and next_newline - end < 100:
             split_point = next_newline + 1
        elif prev_newline != -1 and end - prev_newline < 100:
             split_point = prev_newline + 1
        else:
            # Try space
            next_space = text.find(' ', end)
            if next_space != -1 and next_space - end < 50:
                split_point = next_space + 1
            else:
                split_point = end
                
        chunks.append(text[current_pos:split_point])
        current_pos = split_point
        
    # Last chunk
    if current_pos < total_len:
        chunks.append(text[current_pos:])
        
    return chunks
