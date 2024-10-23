git add .
read -p "Enter commit message: " commit_message
git commit -m "$commit_message"

read -p "Enter branch name: " branch_name
git push origin "$branch_name"