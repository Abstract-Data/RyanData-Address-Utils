# Conflict Resolution Scripts

This directory contains automated scripts to resolve merge conflicts in pull requests.

## Quick Start

```bash
# Resolve PR #2
./resolve-pr2.sh

# Resolve PR #4
./resolve-pr4.sh
```

## What These Scripts Do

### `resolve-pr2.sh`
Resolves conflicts in **PR #2: Improve CI workflow with dependency caching and Python version matrix**

**Actions:**
1. Checks out branch `copilot/sub-pr-1`
2. Merges `ci/add-github-workflows` (creates expected conflicts)
3. Removes old `ci.yml` file
4. Creates new split workflow files with these improvements:
   - `enable-cache: true` for faster CI runs
   - `permissions: contents: read` for security
   - Python version matrix (3.12, 3.13) in tests
5. Commits and pushes the resolution

### `resolve-pr4.sh`
Resolves conflicts in **PR #4: Extract duplicated CI setup steps into composite action**

**Actions:**
1. Checks out branch `copilot/sub-pr-1-another-one`
2. Merges `ci/add-github-workflows` (creates expected conflicts)
3. Removes old `ci.yml` file
4. Creates composite action `.github/actions/setup-python-uv/`
5. Creates new split workflow files using the composite action
6. Includes all improvements from PR #2
7. Commits and pushes the resolution

## Prerequisites

- Git repository cloned locally
- Write access to push to `copilot/sub-pr-1` and `copilot/sub-pr-1-another-one` branches
- All remote branches fetched (`git fetch --all`)

## Error Handling

Both scripts include robust error handling:
- ✅ Verbose logging of each step
- ✅ Verification that expected conflicts exist
- ✅ Graceful handling of missing files
- ✅ Automatic rollback on unexpected conditions
- ✅ Clear error messages for debugging

## Troubleshooting

### "Could not reset to origin"
This warning is informational. The script will use the current HEAD instead. This happens if you haven't fetched the remote branch.

**Solution:**
```bash
git fetch --all
```

### "Error: Expected conflicts but none found"
This means the branches have already been merged or the conflict was already resolved.

**Solution:** Check the PR status on GitHub. If it's already mergeable, you don't need to run the script.

### "Error: Merge completed without conflicts"
This is unexpected and suggests the branches are already compatible.

**Solution:** Check if the PR was already resolved manually.

### "Authentication failed"
The scripts require push permissions to the repository.

**Solution:** Ensure you have write access and your Git credentials are configured.

## Manual Alternative

If you prefer not to use the scripts, see:
- `PR_CONFLICT_RESOLUTION.md` for step-by-step manual instructions
- `resolved-workflows/` for pre-resolved workflow files you can copy

## Testing the Scripts

To test the scripts without pushing:

1. Comment out the `git push` line in the script
2. Run the script
3. Review the changes with `git diff --cached`
4. If satisfied, manually push with `git push origin <branch-name>`

## What Happens After Running

After running the scripts:
1. Check the PR on GitHub - conflicts should be resolved
2. The PR should show as "mergeable"
3. Review the changes in the PR
4. Merge when ready

## Script Output Example

```
Resolving conflicts in PR #2 (copilot/sub-pr-1)...
Resetting branch to clean state...
Reset to origin/copilot/sub-pr-1
Merging ci/add-github-workflows...
Merge conflicts detected (expected). Proceeding with resolution...
Conflicted files: .github/workflows/ci.yml
Removing conflicted ci.yml...
Creating resolved workflow files...
Staging changes...
Committing resolution...
Pushing to origin...
PR #2 conflicts resolved and pushed successfully!
```

## Support

If you encounter issues:
1. Check the error message for specific guidance
2. Review `SUMMARY.md` for overall context
3. See `PR_CONFLICT_RESOLUTION.md` for manual steps
4. Open an issue in the repository
