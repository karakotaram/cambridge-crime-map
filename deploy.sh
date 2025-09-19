#!/bin/bash

# Cambridge Statistics Auto-Deploy Script
# Run this script to automatically deploy changes to cambridgestatistics.com

set -e

echo "🔄 Cambridge Statistics Auto-Deploy"
echo "=================================="

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Check if there are any changes
if git diff-index --quiet HEAD --; then
    echo "ℹ️  No changes detected"
    read -p "Deploy anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled"
        exit 0
    fi
else
    echo "📝 Changes detected:"
    git diff --name-only HEAD
    echo
fi

# Add all changes
echo "📦 Staging changes..."
git add .

# Commit with timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
COMMIT_MSG="Auto-deploy: Updates from $TIMESTAMP

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

echo "💾 Committing changes..."
git commit -m "$COMMIT_MSG" || echo "No changes to commit"

# Push to GitHub (triggers Netlify deploy)
echo "🚀 Pushing to GitHub..."
git push origin main

echo "✅ Deploy complete!"
echo "🌐 Changes will be live on cambridgestatistics.com in ~2 minutes"
echo "🔗 https://cambridgestatistics.com"