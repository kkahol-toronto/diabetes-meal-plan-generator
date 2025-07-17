#!/bin/bash

# Script to delete remote branches except master and main
# This will affect the remote repository - use with caution!

echo "🧹 Cleaning up remote branches..."
echo "⚠️  This will delete remote branches from origin"
echo "📋 Branches to keep: master, main"
echo ""

# Get all remote branches except master and main
REMOTE_BRANCHES=$(git branch -r | grep "origin/" | grep -v "origin/master" | grep -v "origin/main" | sed 's/origin\///')

if [ -z "$REMOTE_BRANCHES" ]; then
    echo "✅ No remote branches to delete (only master/main exist)"
    exit 0
fi

echo "🗑️  Branches to be deleted:"
echo "$REMOTE_BRANCHES" | while read branch; do
    echo "   - $branch"
done

echo ""
read -p "❓ Do you want to proceed? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Deleting remote branches..."
    echo "$REMOTE_BRANCHES" | while read branch; do
        echo "Deleting origin/$branch..."
        git push origin --delete "$branch"
    done
    echo "✅ Remote branch cleanup completed!"
else
    echo "❌ Operation cancelled"
fi 