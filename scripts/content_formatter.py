import os
import re

def extract_info_from_path(file_path, repo_root):
    """
    根据文件路径提取标题、标签和相关附件
    结构: 年份/漏洞名称文件夹/Markdown文件
    例如: 2025/1Panel-CVE-2025-54424-远程命令执行/1Panel-CVE-2025-54424-远程命令执行.md
    
    返回:
    {
        "title": "2025-1Panel-CVE-2025-54424-远程命令执行",
        "tags": ["2025"],
        "content_path": file_path,
        "attachments": [file_path, pdf_path]
    }
    """
    # 获取相对于仓库根目录的路径
    rel_path = os.path.relpath(file_path, repo_root)
    parts = rel_path.split(os.sep)
    
    # 默认值
    year_tag = "Unknown"
    title = os.path.basename(file_path).replace('.md', '')
    vuln_dir_name = ""
    
    # 策略：从后往前找
    # -1 是文件名
    # -2 通常是漏洞目录名
    # 如果存在月份层级 (2026/01/VulnDir/File.md)，则 -2 依然是 VulnDir
    # 但如果只有 (2026/01/README.md)，则 -2 是 01，这时候应该忽略或作为特殊情况
    
    if len(parts) >= 2:
        # 尝试提取年份（通常在第一层）
        if re.match(r'^\d{4}$', parts[0]):
            year_tag = parts[0]
        
        # 确定漏洞目录
        # 忽略掉月份目录 (纯数字 01-12)
        candidate_dir = parts[-2]
        if re.match(r'^\d{1,2}$', candidate_dir):
            # 如果倒数第二层是月份，说明可能是直接在月份下的文件，或者结构异常
            # 这种情况下通常不是有效的 PoC 目录，或者我们往上找一层？
            # 针对 PoC 结构：Year/Vuln/File.md (parts=3) 或 Year/Month/Vuln/File.md (parts=4)
            # 如果 parts[-2] 是月份，那 parts[-1] 是文件。说明没有 VulnDir。
            # 这种文件 (如 2026/02/README.md) 我们可能作为 General 处理，或跳过提取复杂标签
            vuln_dir_name = title # Fallback
        else:
            vuln_dir_name = candidate_dir

    # 优化标题: 优先使用目录名 (因为文件名有时很随意)
    if vuln_dir_name and title.lower() in ['readme', 'index', 'poc']:
        final_title = vuln_dir_name
    elif vuln_dir_name:
        final_title = vuln_dir_name
    else:
        final_title = title

    # 组合年份 (如果标题没包含)
    if year_tag != "Unknown" and not final_title.startswith(year_tag):
        final_title = f"{year_tag}-{final_title}"

    # --- 提取漏洞复现/摘要内容 ---
    content_body = "New PoC Alert!" # 默认值
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            full_text = f.read()
            
        # 策略 1: 匹配 "漏洞复现" / "POC" / "EXP" 章节
        # 匹配 # 漏洞复现 或 **漏洞复现** (忽略大小写)
        # (?:^|\n) 确保匹配行首
        pattern = re.compile(r'(?:^|\n)(?:#+\s*|\*\*)(漏洞复现|POC|EXP|漏洞POC)(?:\*\*|:)?.*?\n(.*?)(?:(?=\n#)|$)', re.IGNORECASE | re.DOTALL)
        match = pattern.search(full_text)
        
        extracted_text = ""
        if match:
            extracted_text = match.group(2).strip()
        else:
            # 策略 2: 如果没找到特定标题，尝试跳过前面可能的元数据/无关信息
            # 简单的取前 500 字符作为预览
            # 找第一个代码块之前的内容？或者直接截断
            if len(full_text) > 200:
                extracted_text = full_text[:500]
            else:
                extracted_text = full_text

        if extracted_text:
            # 限制长度，防止 Discord 报错 (Content limit 2000, 留点余量给标题)
            max_len = 1800
            if len(extracted_text) > max_len:
                extracted_text = extracted_text[:max_len] + "\n... (详见附件)"
            content_body = extracted_text
            
    except Exception as e:
        print(f"Error reading content for {file_path}: {e}")



    # --- 简化标签提取: 直接使用目录名/标题 (用户建议) ---
    tags = [year_tag] if year_tag != "Unknown" else []
    
    if vuln_dir_name:
        # 1. 移除年份前缀 (避免重复)
        clean_name = vuln_dir_name
        if clean_name.startswith(f"{year_tag}-"):
             clean_name = clean_name[len(year_tag)+1:]
        elif clean_name.startswith(year_tag):
             clean_name = clean_name[len(year_tag):]
        
        # 2. 直接作为标签 (截断以适配 Discord 20字符限制)
        # 优先去空格
        tag_candidate = clean_name.strip()
        if tag_candidate:
            # 如果太长，取前20个字符
            if len(tag_candidate) > 20:
                tag_candidate = tag_candidate[:20]
            
            # [USER REQUEST] 暂时禁用由于截断带来的 Bug (e.g. "WordPress S")
            # 避免与 Year 重复
            # if tag_candidate != year_tag:
            #     tags.append(tag_candidate)
                
    dir_path = os.path.dirname(file_path)
    attachments = [file_path] # Markdown 本身
    
    if os.path.exists(dir_path):
        for f in os.listdir(dir_path):
            if f.lower().endswith('.pdf'):
                attachments.append(os.path.join(dir_path, f))
    
    return {
        "title": final_title,
        "tags": tags,
        "content_path": file_path,
        "content_body": content_body,
        "attachments": attachments
    }
