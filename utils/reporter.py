import os
import logging
from typing import List, Set, Dict

class Reporter:
    def __init__(self, repo_path: str, db_manager):
        self.repo_path = repo_path
        self.db_manager = db_manager
        self.success_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        self.failed_items: List[str] = []
        self.unclassified_items: List[str] = []

    def record_success(self):
        self.success_count += 1

    def record_failure(self, item_name: str, reason: str = ""):
        self.failed_count += 1
        self.failed_items.append(f"{item_name} ({reason})")

    def record_skip(self):
        self.skipped_count += 1

    def scan_orphans(self) -> List[str]:
        """
        Scan for 'orphan' files: Files in year directories that are not in the processed list
        and haven't been picked up by the main logic (e.g. standalone docx/pdf or misnamed folders).
        """
        logging.info("开始扫描未分类(孤儿)文件...")
        processed_files = self.db_manager.get_all_processed_files() # We need this method in DBManager
        processed_set = set(processed_files)
        
        orphans = []
        
        # Assume directories like 2024, 2025...
        for root, dirs, files in os.walk(self.repo_path):
            # Skip .git directory
            if '.git' in root:
                continue
                
            rel_root = os.path.relpath(root, self.repo_path)
            
            # Simple heuristic: Only look inside Year directories (20xx)
            parts = rel_root.split(os.sep)
            if not (len(parts) >= 1 and parts[0].isdigit() and len(parts[0]) == 4):
                 continue

            for file in files:
                if file.lower().endswith('.md') or file.lower() == 'readme.md':
                    # Main logic handles MD files, we check if they were processed
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.repo_path)
                    
                    if rel_path not in processed_set:
                        # Ensure it's not a false positive (e.g. just queued but failed?)
                        # But for now, if not in DB, it's pending/orphan
                        orphans.append(rel_path)
                
                elif file.lower().endswith(('.pdf', '.docx', '.doc')):
                    # Non-MD files. Check if they are attachments of any processed file?
                    # This is hard because DB only stores unique 'file_path' of the MD.
                    # Simplified logic: If a directory contains NO processed MD files, 
                    # then everything in it is likely an orphan.
                    pass 
                    
        # Improved Strategy:
        # 1. Start from Year directories.
        # 2. Iterate all subdirectories.
        # 3. If a directory contains NO .md file, OR contains .md files but NONE are in DB -> Orphan Dir
        
        self.unclassified_items = orphans
        logging.info(f"扫描完成，发现 {len(orphans)} 个未分类/未处理项目")
        return orphans

    def generate_report(self, output_path: str = "report_latest.md"):
        logging.info(f"正在生成运行报告: {output_path}")
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# SecPoster 运行报告\n\n")
            from datetime import datetime
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"**生成时间**: {current_time}\n\n")
            
            f.write("## 1. 运行摘要\n\n")
            f.write(f"- ✅ **成功发送**: {self.success_count}\n")
            f.write(f"- ❌ **发送失败**: {self.failed_count}\n")
            f.write(f"- ⏭️ **跳过/重复**: {self.skipped_count}\n\n")
            
            if self.failed_items:
                f.write("## 2. 失败列表\n\n")
                for item in self.failed_items:
                    f.write(f"- [ ] {item}\n")
                f.write("\n")
            
            if self.unclassified_items:
                f.write("## 3. 未分类/遗漏文件 (Orphans)\n\n")
                f.write("> 以下文件存在于目录但未被记录在已发送数据库中，可能需要人工检查结构。\n\n")
                # Group by Year for better readability
                files_by_year = {}
                for item in self.unclassified_items:
                    year = item.split(os.sep)[0]
                    if year not in files_by_year:
                        files_by_year[year] = []
                    files_by_year[year].append(item)
                
                for year, items in sorted(files_by_year.items(), reverse=True):
                    f.write(f"### {year} ({len(items)})\n")
                    for item in items[:50]: # Limit report size
                        f.write(f"- {item}\n")
                    if len(items) > 50:
                        f.write(f"- ... (还有 {len(items)-50} 个)\n")
                    f.write("\n")

        logging.info("报告生成完毕")
