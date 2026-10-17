# Backups & Recovery

## What is backed up

`hacklab backup` (or `backend.app.maintenance.backup.create_backup`) produces a
timestamped, checksummed `.tar.gz` containing:

- the **database** (a consistent copy via SQLite's online backup API, safe to
  run while the server is active);
- **configuration** (`secret_key`, `.env`);
- a **manifest** with per-file SHA-256 checksums.

A `.sha256` sidecar is written and the archive is verified on creation.

Course content, profile definitions and learning paths live in the versioned
catalogue (in the repo), so they are recovered by redeploying the code and
running `hacklab init`. Image *metadata* is in the database; the large image
*bytes* are reproducible via `hacklab images fetch`/build and are excluded by
default.

Disposable VM overlays are **excluded by default** (they are reproducible from
golden images). Persistent VM definitions are recorded in the database and thus
captured. Set `backup.include_disposable_disks = true` to include overlays.

## Creating a backup

```bash
hacklab backup                       # writes to <data>/backups/
hacklab backup --output /mnt/backup  # custom location
```

Schedule it with cron/systemd timers on the host.

## Verifying

```python
from backend.app.maintenance import backup
assert backup.verify_backup("/path/hacklab-backup-YYYYMMDD-HHMMSS.tar.gz")
```

## Restoring

1. Stop the service: `sudo systemctl stop hacklab`.
2. Extract the archive; it contains a `hacklab-backup/` folder.
3. Copy `hacklab.db`, `secret_key` and `.env` back into `HACKLAB_DATA_DIR`.
4. `alembic upgrade head` (in case the code is newer than the backup).
5. Start the service and run `hacklab doctor`.

## Backing up active VM disks

For persistent guest disks, prefer libvirt-consistent snapshots
(`virsh snapshot-create-as` / external snapshots) or back up overlays while the
guest is shut down. Disposable lab disks do not need backing up — reset rebuilds
them from the golden image.
