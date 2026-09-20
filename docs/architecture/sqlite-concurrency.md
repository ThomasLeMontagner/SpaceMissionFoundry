# Local SQLite concurrency

File-backed SQLite connections use write-ahead logging (WAL) and a 30-second busy timeout. WAL lets readers retain a consistent snapshot while another connection commits. SQLite still permits only one writer at a time. The application does not lower SQLite's synchronous durability setting. In-memory databases retain their memory journal mode; PostgreSQL connection configuration is unchanged.

Every new application connection checks the journal mode and enables WAL when needed. Restart existing app processes to apply the connection policy. No table migration is required; migrations still run before API startup. WAL is intended for a database on the same machine, not a database file shared across hosts on a network filesystem. Its `.db-wal` and `.db-shm` sidecars are ignored by Git. Do not remove sidecars or copy only the main database file while the app is running; use SQLite's backup facilities or stop the app cleanly before backing up the database.

Mission changes still use a conditional UPDATE against the expected revision. The mission, history, relationships and any baseline snapshot commit together. Concurrent requests based on the same revision produce one accepted update and one stale-revision rejection; no workflow action is silently replayed.

SQLite does not implement row-level `SELECT FOR UPDATE`. Saving a sensitivity study therefore starts `BEGIN IMMEDIATE` before reading the mission's source revision and archive flag. That write reservation prevents a design update or archive from committing between validation and study insertion. Calculations take place before this short transaction. PostgreSQL retains its existing row lock. Saving a study does not change mission revisions or baseline snapshots.

If SQLite still reports BUSY or LOCKED after its wait, the API returns HTTP 503 with `Retry-After: 1` and asks the user to reload and retry. The failed transaction rolls back. There is no automatic replay of engineering approvals; a changed mission revision must be reviewed again. Other database operational errors retain their normal failure behavior rather than being mislabeled as contention. This handler covers ordinary API responses; an already-started event stream cannot change its HTTP status.

The regression suite uses separate Store instances against temporary files to check reader/writer overlap, competing updates, study-save races with edits and archiving, bounded lock exhaustion, safe retry, unchanged history/baselines, and in-memory compatibility. This is not a multi-user throughput guarantee or a replacement for PostgreSQL when sustained concurrent writes are required.

References: [SQLite isolation](https://www.sqlite.org/isolation.html), [WAL behavior and constraints](https://www.sqlite.org/wal.html), and [busy timeout](https://www.sqlite.org/pragma.html#pragma_busy_timeout).
