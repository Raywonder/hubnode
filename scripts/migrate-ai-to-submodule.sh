#!/bin/bash
# Migrate ai/ directory to proper git submodule
# Usage: ./scripts/migrate-ai-to-submodule.sh

set -e

REPO_ROOT="/home/devinecr/apps/hubnode"
SUBMODULE_PATH="ai"
SUBMODULE_REMOTE="git@github.com:Raywonder/hubnode-ai.git"
BACKUP_SUFFIX=$(date +%Y%m%d_%H%M%S)

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   Hubnode Git Submodule Migration Tool                  ║"
echo "║   Component: ai/                                         ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

cd "$REPO_ROOT"

# Safety check
if [ ! -d "$SUBMODULE_PATH/.git" ]; then
    echo "❌ Error: $SUBMODULE_PATH/.git not found!"
    echo "   This directory is not an embedded git repository."
    exit 1
fi

# Step 1: Create backup
echo "📦 Step 1: Creating backup..."
BACKUP_PATH="${SUBMODULE_PATH}.backup.${BACKUP_SUFFIX}"
cp -r "$SUBMODULE_PATH" "$BACKUP_PATH"
echo "✅ Backup created: $BACKUP_PATH"
echo ""

# Step 2: Remove from git index
echo "🗑️  Step 2: Removing from git index..."
git rm -rf --cached "$SUBMODULE_PATH" 2>/dev/null || true
echo "✅ Removed from git tracking"
echo ""

# Step 3: Remove embedded .git
echo "🧹 Step 3: Removing embedded .git directory..."
rm -rf "${SUBMODULE_PATH}/.git"
echo "✅ Embedded .git removed"
echo ""

# Step 4: Remove the directory entirely
echo "📂 Step 4: Preparing for submodule..."
rm -rf "$SUBMODULE_PATH"
echo "✅ Directory cleared"
echo ""

# Step 5: Add as submodule
echo "🔗 Step 5: Adding as git submodule..."
if git submodule add "$SUBMODULE_REMOTE" "$SUBMODULE_PATH"; then
    echo "✅ Submodule added successfully"
else
    echo "❌ Failed to add submodule!"
    echo "   Restoring from backup..."
    rm -rf "$SUBMODULE_PATH"
    cp -r "$BACKUP_PATH" "$SUBMODULE_PATH"
    exit 1
fi
echo ""

# Step 6: Update .gitignore
echo "📝 Step 6: Updating .gitignore..."
if ! grep -q "^# Submodule git directories" .gitignore 2>/dev/null; then
    cat >> .gitignore << 'EOF'

# Submodule git directories handled by .gitmodules
# Don't manually track submodule .git directories
EOF
    echo "✅ .gitignore updated"
else
    echo "ℹ️  .gitignore already configured"
fi
echo ""

# Step 7: Commit changes
echo "💾 Step 7: Committing changes..."
git add .gitmodules .gitignore "$SUBMODULE_PATH"
git commit -m "Convert ai/ to git submodule

- Migrated ai/ from embedded repository to proper submodule
- Remote: $SUBMODULE_REMOTE
- Enables proper version control and collaborative updates
- Backup created: $BACKUP_PATH

Benefits:
- Independent version control for AI components
- Proper dependency tracking
- Easier collaboration across teams
- Clean separation of concerns

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>"

if [ $? -eq 0 ]; then
    echo "✅ Changes committed successfully"
else
    echo "❌ Commit failed!"
    exit 1
fi
echo ""

# Step 8: Initialize and update
echo "🔄 Step 8: Initializing submodule..."
git submodule init
git submodule update
echo "✅ Submodule initialized"
echo ""

# Step 9: Verify
echo "✨ Step 9: Verification..."
echo ""
echo "Submodule status:"
git submodule status
echo ""
echo "Git status:"
git status --short
echo ""

# Final summary
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   ✅ Migration Complete!                                 ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "Summary:"
echo "  • Backup location: $BACKUP_PATH"
echo "  • Submodule: $SUBMODULE_PATH"
echo "  • Remote: $SUBMODULE_REMOTE"
echo ""
echo "Next steps:"
echo "  1. Test the submodule: cd $SUBMODULE_PATH && git status"
echo "  2. Push changes: git push origin main"
echo "  3. Update team about submodule usage"
echo ""
echo "To clone in future:"
echo "  git clone --recursive git@github.com:Raywonder/hubnode.git"
echo ""
echo "To update submodule:"
echo "  git submodule update --remote $SUBMODULE_PATH"
echo ""