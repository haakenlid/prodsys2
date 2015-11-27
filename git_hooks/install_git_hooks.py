#!/usr/bin/env python
"""Symlink git hooks from version control source to local .git/hooks/"""
import os
hooks = [  # valid git hook filenames
    'applypatch-msg',
    'pre-applypatch',
    'post-applypatch',
    'pre-commit',
    'prepare-commit-msg',
    'commit-msg',
    'post-commit',
    'pre-rebase',
    'post-checkout',
    'post-merge',
    'pre-receive',
    'update',
    'post-receive',
    'post-update',
    'pre-auto-gc',
    'post-rewrite',
    'pre-push', ]


def symlink_to_git_folder():
    """Create symlinks if they don't exist"""
    src_dir = os.path.abspath(os.path.dirname(__file__))
    dest_dir = os.path.abspath(os.path.join(src_dir, '..', '.git', 'hooks'))
    for filename in os.listdir(src_dir):
        if filename in hooks:
            try:
                os.symlink(
                    os.path.join(src_dir, filename),
                    os.path.join(dest_dir, filename)
                )
            except OSError:
                pass

if __name__ == '__main__':
    symlink_to_git_folder()
