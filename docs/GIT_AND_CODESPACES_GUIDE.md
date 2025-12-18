# Git & Codespaces Quick Reference Guide

> **Goal:** Understand Git workflow, avoid mistakes, and keep your work safe.

---

## Table of Contents
1. [Golden Rules](#1-golden-rules)
2. [Git Basics](#2-git-basics)
3. [Branch Workflow](#3-branch-workflow)
4. [Saving Your Work](#4-saving-your-work)
5. [Codespaces Commands](#5-codespaces-commands)
6. [Migration Safety](#6-migration-safety)
7. [Recovery Commands](#7-recovery-commands)
8. [Ready-to-Use Templates](#8-ready-to-use-templates)

---

## 1. Golden Rules

```
✅ ALWAYS commit before switching branches
✅ ALWAYS pull before starting new work
✅ ALWAYS create a new branch for new features
✅ ALWAYS backup (zip) before risky operations
❌ NEVER force push to master without team agreement
❌ NEVER delete migrations that are already in production
❌ NEVER work directly on master for features
```

---

## 2. Git Basics

### What is What?

| Term | Meaning |
|------|---------|
| **Repository** | Your project folder tracked by Git |
| **Branch** | A separate line of development |
| **Commit** | A saved snapshot of your changes |
| **Push** | Upload your commits to GitHub |
| **Pull** | Download commits from GitHub |
| **Merge** | Combine two branches together |
| **Clone** | Download a repository for the first time |

### The Flow

```
Your PC (Local) ←→ GitHub (Remote)
     ↓                    ↓
  You work here    Backup & sharing
```

---

## 3. Branch Workflow

### Starting New Work

```bash
# 1. Make sure you're on master and up-to-date
git checkout master
git pull origin master

# 2. Create your feature branch
git checkout -b feature/your-feature-name

# 3. Work... make changes... then save
git add -A
git commit -m "feat: describe what you did"

# 4. Push to GitHub
git push -u origin feature/your-feature-name
```

### Switching Between Branches

```bash
# ALWAYS save first!
git add -A
git commit -m "wip: saving before switch"

# Then switch
git checkout branch-name
```

### Merging Your Work to Master

```bash
# Option A: Merge locally
git checkout master
git pull origin master
git merge feature/your-feature-name
git push origin master

# Option B: Create Pull Request on GitHub (safer, recommended)
# Just push your branch, then go to GitHub and click "New Pull Request"
```

### Deleting a Branch (after merged)

```bash
# Delete local branch
git branch -d feature/your-feature-name

# Delete remote branch
git push origin --delete feature/your-feature-name
```

---

## 4. Saving Your Work

### Quick Save (Commit)

```bash
git add -A && git commit -m "wip: saving progress"
```

### Full Backup to GitHub

```bash
git add -A && git commit -m "backup: saving all work" && git push
```

### Emergency Backup (Zip File)

Before risky operations, always zip your folder manually:
1. Right-click project folder
2. Send to → Compressed (zipped) folder
3. Name it with date: `project_backup_2025-12-19.zip`

### When to Backup (Zip)?

- Before force push (`git push -f`)
- Before deleting branches
- Before resetting (`git reset`)
- Before migration squash
- After completing a major feature

---

## 5. Codespaces Commands

### Starting Fresh in Codespaces

```bash
# Clear → Setup → Migrate → Run Server

# 1. Pull latest code
git pull origin master

# 2. Install dependencies (if requirements changed)
pip install -r requirements.txt

# 3. Run migrations (safe - only applies if needed)
python manage.py migrate

# 4. Run server
python manage.py runserver
```

### After Pulling New Code

```bash
# Template: Pull → Install → Migrate → Run
git pull origin master && pip install -r requirements.txt && python manage.py migrate && python manage.py runserver
```

### Rebuild Container (when Dockerfile changed)

In Codespaces:
1. Press `F1` or `Ctrl+Shift+P`
2. Type: `Codespaces: Rebuild Container`
3. Select it and wait

Or from command line:
```bash
# This will rebuild everything
gh codespace rebuild
```

### Testing Without Server

```bash
# For quick checks
python manage.py check

# For running tests
python manage.py test

# For checking migrations
python manage.py showmigrations
```

### Fetch Data for Debugging

```bash
# Check what's in database
python manage.py shell -c "from apps.inventory.models import InventoryItem; print(InventoryItem.objects.count())"

# Run seed data
python manage.py seed_all
```

---

## 6. Migration Safety

### Check Before Creating Migrations

```bash
# See what migrations exist
python manage.py showmigrations

# Preview what would be created (dry run)
python manage.py makemigrations --dry-run

# Check for problems
python manage.py check
```

### Safe Migration Workflow

```bash
# Template: Check → Make → Review → Apply

# 1. Check current state
python manage.py showmigrations

# 2. Create migrations
python manage.py makemigrations

# 3. Review what was created (read the file!)
# Look in apps/yourapp/migrations/

# 4. Apply migrations
python manage.py migrate
```

### Avoiding Duplicate Migrations

**Problem:** Two branches create migrations with same number (0007_xxx.py)

**Solution:** Always pull master before creating migrations

```bash
# Before making migrations
git checkout master
git pull origin master
git checkout your-branch
git merge master
# NOW make migrations
python manage.py makemigrations
```

### Fixing Migration Conflicts

```bash
# If you see "Conflicting migrations detected"

# Option 1: Merge migrations (Django does it)
python manage.py makemigrations --merge

# Option 2: If tables already exist (use carefully!)
python manage.py migrate --fake app_name migration_name
```

### Migration Cheat Sheet

| Situation | Command |
|-----------|---------|
| See all migrations | `python manage.py showmigrations` |
| Create new migration | `python manage.py makemigrations` |
| Apply migrations | `python manage.py migrate` |
| Preview only | `python manage.py makemigrations --dry-run` |
| Merge conflicts | `python manage.py makemigrations --merge` |
| Skip if exists | `python manage.py migrate --fake` |
| Rollback one | `python manage.py migrate app_name previous_migration` |

---

## 7. Recovery Commands

### Undo Last Commit (keep changes)

```bash
git reset --soft HEAD~1
```

### Undo Last Commit (discard changes)

```bash
git reset --hard HEAD~1
```

### Discard All Local Changes

```bash
git checkout -- .
```

### Get Back to Clean State

```bash
git fetch origin
git reset --hard origin/master
```

### Recover Deleted Branch

```bash
# Find the commit
git reflog

# Recreate branch from commit
git checkout -b recovered-branch abc1234
```

---

## 8. Ready-to-Use Templates

### Template A: Start New Feature

```bash
# Copy-paste this block
git checkout master && \
git pull origin master && \
git checkout -b feature/NEW_FEATURE_NAME
```

### Template B: Save and Push Work

```bash
# Copy-paste this block
git add -A && \
git commit -m "feat: YOUR_MESSAGE_HERE" && \
git push -u origin $(git branch --show-current)
```

### Template C: Codespaces Daily Start

```bash
# Copy-paste this block
git pull origin master && \
pip install -r requirements.txt && \
python manage.py migrate && \
python manage.py runserver
```

### Template D: Safe Migration Creation

```bash
# Copy-paste this block
python manage.py check && \
python manage.py makemigrations --dry-run && \
read -p "Continue? (y/n) " confirm && \
[ "$confirm" = "y" ] && python manage.py makemigrations && python manage.py migrate
```

### Template E: Full Reset to Master

```bash
# WARNING: This discards ALL local changes!
git fetch origin && \
git checkout master && \
git reset --hard origin/master && \
pip install -r requirements.txt && \
python manage.py migrate
```

### Template F: Quick Debug Check

```bash
# Copy-paste this block
python manage.py check && \
python manage.py showmigrations | grep -E "\[ \]|X" | head -20
```

---

## Quick Decision Tree

```
What do you want to do?
│
├─► Start new feature?
│   └─► Template A, then work, then Template B
│
├─► Continue work in Codespaces?
│   └─► Template C
│
├─► Create migrations?
│   └─► Template D
│
├─► Something broke, reset everything?
│   └─► ZIP BACKUP FIRST! Then Template E
│
├─► Check if everything is OK?
│   └─► Template F
│
└─► Save work before leaving?
    └─► Template B
```

---

## Common Mistakes & Fixes

| Mistake | Fix |
|---------|-----|
| Forgot to pull before work | `git stash && git pull && git stash pop` |
| Committed to wrong branch | `git reset --soft HEAD~1` then switch branch |
| Migration conflict | `python manage.py makemigrations --merge` |
| Pushed secret file | Remove, add to .gitignore, commit |
| Lost changes | Check `git reflog` for recovery |
| Codespace won't start | Rebuild container |

---

## For Claude Web Agent

When asking agent to do Git operations, be specific:

```
Good: "Create a new branch called feature/add-login from master"
Bad: "Save my work"

Good: "Commit all changes with message 'fix: login validation'"
Bad: "Push everything"

Good: "Pull master and merge into current branch"
Bad: "Update my code"
```

---

*Last Updated: December 19, 2025*
