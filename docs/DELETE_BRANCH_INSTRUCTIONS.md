# How to Delete the copilot/analyze-repo-documentation-strategy Branch

## Remote Branch Deletion

To delete the remote branch `copilot/analyze-repo-documentation-strategy`, run the following command:

```bash
git push origin --delete copilot/analyze-repo-documentation-strategy
```

## Local Branch Deletion (if it exists locally)

If you have the branch checked out locally, first switch to a different branch:

```bash
git checkout main
```

Then delete the local branch:

```bash
git branch -D copilot/analyze-repo-documentation-strategy
```

## Verification

After deletion, verify the branch no longer exists:

```bash
# Check remote branches
git ls-remote --heads origin | grep analyze

# Check local branches
git branch -a | grep analyze
```

## Alternative: Using GitHub Web Interface

1. Go to https://github.com/McMuff86/rhinomcp/branches
2. Find `copilot/analyze-repo-documentation-strategy` in the branch list
3. Click the trash/delete icon next to the branch name
4. Confirm the deletion

## Notes

- The branch `copilot/analyze-repo-documentation-strategy` was found on the remote repository
- The exact branch name `copilot/analyze-repo-documentation` was not found
- Make sure you don't need any code from this branch before deleting it
