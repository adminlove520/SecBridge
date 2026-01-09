import git
import os
import logging

class GitManager:
    def __init__(self, repo_path):
        self.repo_path = repo_path
        try:
            self.repo = git.Repo(repo_path)
        except git.exc.InvalidGitRepositoryError:
            logging.error(f"路径 {repo_path} 不是一个有效的 Git 仓库")
            raise

    def pull_changes(self):
        """
        拉取最新更改并返回 (old_commit_sha, new_commit_sha)
        """
        origin = self.repo.remotes.origin
        
        # 获取拉取前的 HEAD
        old_commit = self.repo.head.commit.hexsha
        
        logging.info("正在拉取最新代码...")
        try:
            origin.pull()
        except Exception as e:
            logging.warning(f"Git pull failed: {e}")
        
        # 获取拉取后的 HEAD
        new_commit = self.repo.head.commit.hexsha
        
        return old_commit, new_commit

    def get_changed_files(self, old_commit, new_commit):
        """
        获取两个 commit 之间的差异文件列表
        只返回新增或修改的 .md 文件
        """
        if old_commit == new_commit:
            return []

        changed_files = []
        # diff 格式: compare old to new
        diffs = self.repo.commit(old_commit).diff(self.repo.commit(new_commit))

        for diff in diffs:
            # item.a_path 是旧路径, item.b_path 是新路径
            # 我们关心的是新增 (A) 或 修改 (M) 的文件
            # diff.change_type: 'A' for added, 'D' for deleted, 'R' for renamed, 'M' for modified
            
            if diff.change_type in ['A', 'M']:
                file_path = diff.b_path
                if file_path and file_path.endswith('.md'):
                    full_path = os.path.join(self.repo_path, file_path)
                    changed_files.append(full_path)
        
        return changed_files

    def get_all_markdown_files(self):
        """
        获取仓库中所有的 Markdown 文件
        注意: 为保证稳定性，回退使用 os.walk 遍历文件系统
        """
        md_files = []
        for root, dirs, files in os.walk(self.repo_path):
            if '.git' in root:
                continue
            for file in files:
                if file.endswith('.md'):
                    md_files.append(os.path.join(root, file))
        return md_files
