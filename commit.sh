git add .
echo "Commit Message:"
read commitmessage
git commit --allow-empty -m "$commitmessage"
git push origin
