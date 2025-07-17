#!/bin/bash

# Script to archive remote branches by creating tags
# This preserves the branch history as tags before deletion

echo "📦 Archiving remote branches..."
echo "📋 This will create tags for each remote branch"
echo ""

# Get all remote branches except master and main
REMOTE_BRANCHES=$(git branch -r | grep "origin/" | grep -v "origin/master" | grep -v "origin/main" | sed 's/origin\///')

if [ -z "$REMOTE_BRANCHES" ]; then
    echo "✅ No remote branches to archive (only master/main exist)"
    exit 0
fi

echo "📦 Remote branches to archive:"
echo "$REMOTE_BRANCHES" | while read branch; do
    echo "   - $branch"
done

echo ""
read -p "❓ Do you want to create archive tags for these remote branches? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📦 Creating archive tags for remote branches..."
    echo "$REMOTE_BRANCHES" | while read branch; do
        echo "Creating archive tag: archive/remote/$branch"
        git tag "archive/remote/$branch" "origin/$branch"
    done
    
    echo ""
    echo "✅ Remote branch archiving completed!"
    echo "📋 You can view archived remote branches with: git tag | grep 'archive/remote/'"
    echo "📋 To restore a remote branch: git checkout -b branch_name archive/remote/branch_name"
    echo ""
    
    read -p "❓ Do you also want to delete the remote branches? (y/N): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Deleting remote branches..."
        echo "$REMOTE_BRANCHES" | while read branch; do
            echo "Deleting remote branch: origin/$branch"
            git push origin --delete "$branch"
        done
        echo "✅ Remote branch deletion completed!"
    else
        echo "📦 Remote branches kept (only archived as tags)"
    fi
else
    echo "❌ Operation cancelled"
fi 