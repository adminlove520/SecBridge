import os
import re

def extract_info_from_path(file_path, repo_root, source_config=None):
    """
    根据文件路径和仓库配置提取标题、标签和内容
    """
    source_config = source_config or {}
    source_type = source_config.get('type', 'generic')
    tag_rules = source_config.get('tag_rules', {})
    
    rel_path = os.path.relpath(file_path, repo_root)
    parts = rel_path.split(os.sep)
    
    final_title = os.path.basename(file_path).replace('.md', '')
    tags = set()
    skip = False

    # ---内容读取 ---
    full_text = ""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            full_text = f.read()
    except Exception as e:
        full_text = f"无法读取内容: {str(e)}"

    # --- 1. 过滤逻辑: 识别导航类 README ---
    if final_title.lower() == 'readme':
        # 启发式判断：链接密度
        links = re.findall(r'\[.*?\]\(.*?\)', full_text)
        text_no_links = re.sub(r'\[.*?\]\(.*?\)', '', full_text)
        # 如果链接数量多且剩余文本较少，则认为是导航
        if len(links) > 5 and len(text_no_links.strip()) < 300:
            skip = True

    # --- 2. 标签生成算法 ---
    
    # A. 路径匹配逻辑
    path_mapping = tag_rules.get('path_mapping', {})
    for path_part in parts:
        if path_part in path_mapping:
            tags.add(path_mapping[path_part])
    
    # B. Frontmatter 提取 (如 tag: xxx)
    if tag_rules.get('extract_frontmatter'):
        # 兼容 --- \n tag: xxx \n ---
        fm_match = re.search(r'^---\s*\n(.*?)\n---\s*\n', full_text, re.DOTALL)
        if fm_match:
            fm_content = fm_match.group(1)
            # 简单正则匹配 tag/tags
            tag_val = re.search(r'^tags?:\s*(.*)$', fm_content, re.MULTILINE | re.IGNORECASE)
            if tag_val:
                t_str = tag_val.group(1).strip()
                # 处理 [tag1, tag2] 格式或单字符串
                if t_str.startswith('[') and t_str.endswith(']'):
                    t_list = [t.strip().strip('"').strip("'") for t in t_str[1:-1].split(',')]
                    tags.update(t_list)
                else:
                    tags.add(t_str)

    # C. 自动目录标签 (Redteam 风格: "1. 信息收集")
    if tag_rules.get('use_folder_as_tag') and len(parts) >= 2:
        folder_tag = parts[-2]
        # 去掉数字前缀（如 1. ）
        folder_tag = re.sub(r'^\d+[\.\s\-]+', '', folder_tag)
        if folder_tag and folder_tag.lower() not in ['source', 'poc', 'readme']:
            tags.add(folder_tag)

    # D. PoC 特定规则
    if source_type == 'poc':
        if len(parts) >= 1 and re.match(r'^\d{4}$', parts[0]):
            tags.add(parts[0])
        vuln_dir_name = parts[-2] if len(parts) >= 2 else ""
        if vuln_dir_name and final_title.lower() in ['readme', 'index', 'poc']:
            final_title = vuln_dir_name
        year = parts[0] if len(parts) >= 1 and parts[0].isdigit() else ""
        if year and not final_title.startswith(year):
            final_title = f"{year}-{final_title}"

    # E. 正则提取 (如 CVE)
    if tag_rules.get('extract_cve'):
        cve_match = re.search(r'CVE-\d{4}-\d{4,}', final_title, re.IGNORECASE)
        if cve_match:
            tags.add("CVE")

    # --- 3. 内容提取与清洗 ---
    content_body = ""
    # 移除 YAML Frontmatter
    clean_text = re.sub(r'^---\s+.*?\s+---\s+', '', full_text, flags=re.DOTALL).strip()
    
    if source_type == 'poc':
        pattern = re.compile(r'(?:^|\n)(?:#+\s*|\*\*)(漏洞复现|POC|EXP|漏洞POC)(?:\*\*|:)?.*?\n(.*?)(?:(?=\n#)|$)', re.IGNORECASE | re.DOTALL)
        match = pattern.search(clean_text)
        if match:
            content_body = match.group(2).strip()
    
    if not content_body:
        # 取首个非标题段落
        paragraphs = [p.strip() for p in clean_text.split('\n\n') if p.strip() and not p.strip().startswith('#')]
        if paragraphs:
            content_body = paragraphs[0]
            if len(content_body) < 100 and len(paragraphs) > 1:
                content_body += "\n\n" + paragraphs[1]

    # 4. 关键词嗅探 (排除 Frontmatter)
    keywords_to_check = tag_rules.get('keywords', ["RCE", "免杀", "权限维持", "内网渗透", "应急响应", "溯源"])
    for kw in keywords_to_check:
        if kw.lower() in clean_text.lower():
            if source_type == 'wiki' and kw == "面试":
                tags.add("面试与成长")
            else:
                tags.add(kw)

    # 智能截断
    max_len = 1500
    if len(content_body) > max_len:
        content_body = content_body[:max_len] + "\n\n> ...... (提示: 内容已截断，请查看附件 `Markdown` 获取完整细节)"
    
    # 动态前缀
    prefix = "💡"
    tags_str = "".join(list(tags))
    if source_type == 'poc': prefix = "🛡️ [PoC]"
    elif "面试" in tags_str: prefix = "👨‍💻 [面试]"
    elif "工具" in tags_str: prefix = "🛠️ [工具]"
    elif "红蓝对抗" in tags_str or "红队" in tags_str: prefix = "⚔️ [红蓝]"
    elif "提权" in tags_str: prefix = "🚀 [提权]"
    elif "信息收集" in tags_str: prefix = "🔍 [信息收集]"
    
    formatted_content = f"{prefix}\n\n{content_body}"

    # 附件处理
    attachments = [file_path]
    dir_path = os.path.dirname(file_path)
    if os.path.exists(dir_path):
        for f in os.listdir(dir_path):
            if f.lower().endswith(('.pdf', '.docx', '.doc')) and os.path.join(dir_path, f) != file_path:
                attachments.append(os.path.join(dir_path, f))

    return {
        "title": final_title,
        "tags": list(tags),
        "content_path": file_path,
        "content_body": formatted_content,
        "attachments": attachments,
        "skip": skip
    }
