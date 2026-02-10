def read_first_lines(file_path: str, max_lines: int = 10):
    """读取指定文件的前 max_lines 行，返回行内容列表"""
    lines = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for _ in range(max_lines):
                line = f.readline()
                if not line:
                    break
                lines.append(line.rstrip('\n'))
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
    return lines
