find .git/hooks -type l -exec rm {} \;
find .githooks -type f -exec ln -sf ../../{} .git/hooks/ \;
echo "=== Githooks installed ==="
echo "testing pre-commit hook by calling "
echo "  .git/hooks/pre-commit"
echo "=========================="
.git/hooks/pre-commit
