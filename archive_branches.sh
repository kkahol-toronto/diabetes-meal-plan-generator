#!/bin/bash

# Script to archive branches by creating tags before deletion
# This preserves the branch history as tags

echo "📦 Archiving branches..."
echo "📋 This will create tags for each branch before deletion"
echo ""

# Get all local branches except master
LOCAL_BRANCHES=$(git branch | grep -v "master" | sed 's/^[ *]*//')

if [ -z "$LOCAL_BRANCHES" ]; then
    echo "✅ No local branches to archive (only master exists)"
    exit 0
fi

echo "📦 Branches to archive:"
echo "$LOCAL_BRANCHES" | while read branch; do
    echo "   - $branch"
done

echo ""
read -p "❓ Do you want to archive these branches as tags? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📦 Creating archive tags..."
    echo "$LOCAL_BRANCHES" | while read branch; do
        echo "Creating archive tag: archive/$branch"
        git tag "archive/$branch" "$branch"
    done
    
    echo ""
    echo "🗑️  Now deleting local branches..."
    echo "$LOCAL_BRANCHES" | while read branch; do
        echo "Deleting branch: $branch"
        git branch -D "$branch"
    done
    
    echo ""
    echo "✅ Branch archiving completed!"
    echo "📋 You can view archived branches with: git tag | grep 'archive/'"
    echo "📋 To restore a branch: git checkout -b branch_name archive/branch_name"
else
    echo "❌ Operation cancelled"
fi 