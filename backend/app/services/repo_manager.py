import os
import shutil
import stat
import subprocess
import urllib.parse
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import git
from app.core.config import settings
from app.core.logging import logger
from app.core.security import is_safe_repo_url, sanitize_path


def _remove_readonly(func, path, excinfo):
    """Clear read-only bit on Windows and retry removal."""
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


class RepoManager:
    """
    Manages safe repository cloning, caching, metadata extraction,
    and filesystem isolation for security scanning.
    """

    @staticmethod
    def parse_repo_info(url: str) -> Tuple[str, str]:
        """
        Extract (owner, repo_name) from URL or SSH string.
        """
        url_clean = url.strip()
        if url_clean.endswith(".git"):
            url_clean = url_clean[:-4]
            
        if url_clean.startswith("git@"):
            parts = url_clean.split(":")
            if len(parts) == 2:
                sub_parts = parts[1].strip("/").split("/")
                if len(sub_parts) >= 2:
                    return sub_parts[0], sub_parts[1]
        else:
            parsed = urllib.parse.urlparse(url_clean)
            path_parts = [p for p in parsed.path.strip("/").split("/") if p]
            if len(path_parts) >= 2:
                return path_parts[0], path_parts[1]
            elif len(path_parts) == 1:
                return "unknown", path_parts[0]
                
        return "owner", "repository"

    @staticmethod
    def get_repo_target_dir(repository_id: str) -> str:
        """Returns safe target directory for repository clone inside base storage."""
        os.makedirs(settings.REPOSITORIES_BASE_DIR, exist_ok=True)
        return os.path.join(settings.REPOSITORIES_BASE_DIR, repository_id)

    @classmethod
    def clone_or_fetch(
        cls,
        url: str,
        repository_id: str,
        branch: Optional[str] = None,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Safely clones the repository with shallow depth and size limits.
        """
        is_safe, err_msg = is_safe_repo_url(url)
        if not is_safe:
            raise ValueError(f"Security error: {err_msg}")

        target_dir = cls.get_repo_target_dir(repository_id)
        
        # Clean existing dir completely before fresh clone
        if os.path.exists(target_dir):
            try:
                shutil.rmtree(target_dir, onerror=_remove_readonly)
            except Exception as e:
                logger.warning(f"Failed to clear directory {target_dir}: {e}")

        # Inject auth token if provided for private repos
        clone_url = url
        if auth_token and url.startswith("https://"):
            parsed = urllib.parse.urlparse(url)
            clone_url = f"https://x-access-token:{auth_token}@{parsed.netloc}{parsed.path}"

        logger.info(f"Cloning {url} into {target_dir} (shallow clone depth=1)")

        # Prepare non-interactive environment
        clone_env = os.environ.copy()
        clone_env["GIT_TERMINAL_PROMPT"] = "0"
        clone_env["GIT_ASKPASS"] = ""
        clone_env["GCM_INTERACTIVE"] = "never"

        # Attempt shallow clone with specified branch or fallback to default remote HEAD
        clone_cmd = ["git", "clone", "--depth", "1"]
        if branch and branch.lower() not in ("main", "master", "default"):
            clone_cmd.extend(["--branch", branch])
        clone_cmd.extend([clone_url, target_dir])

        try:
            res = subprocess.run(
                clone_cmd,
                capture_output=True,
                text=True,
                env=clone_env,
                timeout=settings.ANALYSIS_TIMEOUT_SECONDS
            )
            if res.returncode != 0:
                err_lower = (res.stderr or "").lower()
                if "could not read username" in err_lower or "authentication failed" in err_lower or "not found" in err_lower:
                    raise RuntimeError(
                        "Depo bulunamadı veya gizli (private) bir repo. Gizli depolar için lütfen GitHub Access Token girin."
                    )

                # If specific branch failed, retry without branch flag to get default branch
                logger.warning(f"Branch clone attempt failed: {res.stderr}. Retrying default branch...")
                if os.path.exists(target_dir):
                    shutil.rmtree(target_dir, onerror=_remove_readonly)
                
                fallback_cmd = ["git", "clone", "--depth", "1", clone_url, target_dir]
                fallback_res = subprocess.run(
                    fallback_cmd,
                    capture_output=True,
                    text=True,
                    env=clone_env,
                    timeout=settings.ANALYSIS_TIMEOUT_SECONDS
                )
                if fallback_res.returncode != 0:
                    fb_err = (fallback_res.stderr or "").lower()
                    if "could not read username" in fb_err or "authentication failed" in fb_err or "not found" in fb_err:
                        raise RuntimeError(
                            "Depo bulunamadı veya gizli (private) bir repo. Gizli depolar için lütfen GitHub Access Token girin."
                        )
                    raise RuntimeError(f"Git clone failed: {fallback_res.stderr or res.stderr}")

            repo = git.Repo(target_dir)
            commit_hash = repo.head.commit.hexsha
            active_branch = branch or (repo.active_branch.name if not repo.head.is_detached else "default")

            # Check repository size limit
            total_size_mb = cls.calculate_dir_size_mb(target_dir)
            if total_size_mb > settings.MAX_REPO_SIZE_MB:
                shutil.rmtree(target_dir, onerror=_remove_readonly)
                raise ValueError(
                    f"Repository size ({total_size_mb:.1f} MB) exceeds maximum allowed limit of {settings.MAX_REPO_SIZE_MB} MB"
                )

            return {
                "target_dir": target_dir,
                "commit_hash": commit_hash,
                "branch": active_branch,
                "size_mb": total_size_mb,
            }
        except subprocess.TimeoutExpired:
            shutil.rmtree(target_dir, onerror=_remove_readonly)
            raise TimeoutError("Depo klonlama işlemi zaman aşımına uğradı (Timeout).")
        except Exception as e:
            logger.error(f"Error during repository clone: {e}")
            raise

    @staticmethod
    def calculate_dir_size_mb(path: str) -> float:
        total = 0
        for root, dirs, files in os.walk(path):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    total += os.path.getsize(fp)
                except OSError:
                    pass
        return total / (1024 * 1024)

    @classmethod
    def cleanup_repo(cls, repository_id: str) -> None:
        """Removes cloned repository from disk after indexing if needed."""
        target_dir = os.path.join(settings.REPOSITORIES_BASE_DIR, repository_id)
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir, onerror=_remove_readonly)
            logger.info(f"Cleaned up repository directory: {target_dir}")
