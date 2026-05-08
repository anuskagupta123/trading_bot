# Secret rotation and post-filter-repo steps

This file documents the local rotation performed and steps you must complete in production.

## Local actions performed
- Generated new credentials and wrote them to `backend/.env.local` (ignored).
- Moved previous `backend/.env` to `backend/.env.local` before rotation.
- Removed `backend/.env` from git history and pushed cleaned history. A backup branch `backup-before-filter-repo` exists on remote.

## Required production steps
1. **Rotate Postgres password**
   - Example (psql):
     ```bash
     psql -U postgres -d trading_db -c "ALTER USER postgres WITH PASSWORD '<new_password>'"
     ```
2. **Update deployment environment**
   - Set `DATABASE_URL` to include the new password.
   - Set `ADMIN_TOKEN` to the new token value.
   - Set `WEBHOOK_SECRET` to the new secret value.
3. **Restart backend service** and verify `/health` and logs show migrations succeeded.

## Cleanup and collaborator instructions
- After rotation and verification, delete remote backup branch:
  ```bash
  git push origin --delete backup-before-filter-repo
  ```
- Inform collaborators to re-clone or run:
  ```bash
  git fetch origin
  git reset --hard origin/main
  ```

## Note
New secret values are only stored locally in `backend/.env.local` and were not pushed to remote.
