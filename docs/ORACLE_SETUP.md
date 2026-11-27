# Oracle Cloud setup for M1

Checked against official Oracle documentation on 26 November 2026. Account signup,
capacity, limits and billing must be verified in your own console. No infrastructure
has been provisioned by this repository.

1. Sign in to the [OCI console](https://cloud.oracle.com/). If you need an account,
   start with [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/). Complete
   identity/payment verification yourself; keep those details outside this project.
2. Find Autonomous AI Database, then Create Autonomous AI Database. Select
   **Always Free** explicitly, and **26ai** rather than 19c. Use a project name such
   as `ragv1`. Choose the Transaction Processing workload if available; our app
   uses ordinary relational tables with a VECTOR column. Confirm the summary shows
   Always Free before creation. If it only offers paid resources or unavailable
   capacity, stop and report that blocker rather than changing tiers.
3. Set the ADMIN password locally. Use ADMIN only for setup. Follow the networking
   choices supported by your tier; restrict access to your client IP when supported.
   Keep mTLS enabled for the wallet path. Wait for status Available.
4. Open Database Actions → Administration → Database Users (labels may vary).
   Create `RAG_APP` with its own password, CREATE SESSION and CREATE TABLE, and
   a bounded quota on DATA (for example 100 MB for this small experiment).
   Do not grant DBA or unrestricted tablespace privileges. If the user wizard
   assigns broader roles, review them before using that user for the app.
5. Open DB Connection and download an instance wallet, setting a local wallet
   password. Extract under this project's ignored `wallet/` directory. The Python
   Thin driver needs `ewallet.pem`; the connection alias comes from `tnsnames.ora`.
   Choose the `_low` service alias for this single-process experiment if provided.
6. Copy `.env.example` to `.env`. Set the project user/password, the alias as
   ORACLE_DSN, the absolute wallet directory as ORACLE_WALLET_DIR, and wallet
   password as ORACLE_WALLET_PASSWORD. Quote values with special characters as
   appropriate for dotenv. Never paste the file or wallet into chat.
7. Tell Codex the local configuration is ready. M1 then runs the explicit schema
   initializer once and the real rollback-only vector smoke. A failure is not a
   passed milestone. Schema DDL commits and must be inspected if partially applied.

The local demo was verified with the project schema owner. For a release
runtime, an authorized administrator creates a dedicated user (e.g. RAG_READER)
with a password set locally, no quota or writer roles, and `CREATE SESSION`.
The table owner then grants only these object privileges.

```sql
GRANT READ ON documents TO RAG_READER;
GRANT READ ON document_chunks TO RAG_READER;
```

Configure the API with that account and `ORACLE_DATA_SCHEMA=RAG_APP` (or the
actual owner identifier). This changes name resolution only. It does not grant
privileges. Keep owner credentials for the ingest and rollback smoke commands.
Connect as the runtime account and run these read-only verification queries.

```sql
SELECT privilege FROM session_privs ORDER BY privilege;
SELECT owner, table_name, privilege FROM user_tab_privs_recd
WHERE table_name IN ('DOCUMENTS', 'DOCUMENT_CHUNKS');
SELECT COUNT(*) FROM RAG_APP.document_chunks;
```

Expect CREATE SESSION and READ on the two tables with no DML grants or broad
privileges. Then verify `/health/ready` and `/api/v1/search` as that account.
No runtime user was provisioned during M3. See [Oracle object privileges](https://docs.oracle.com/en/database/oracle/oracle-database/26/dbseg/managing-object-privileges.html).

For M3.1, stop the local API and apply `002_library.sql` as the corpus owner
with `.venv/Scripts/python -m app.migrate_library`. The repeatable script
adds metadata and a nullable page field without changing existing vectors.
Startup never migrates the database automatically.

Keep the existing reader grants. Have an authorized admin provision a
separate writer with CREATE SESSION, no schema ownership, and no broad role.
An authorized database administrator runs the following in the target PDB.
Replace each example password locally with a different strong password.

```sql
CREATE USER RAG_READER IDENTIFIED BY "<reader-password-set-locally>";
CREATE USER RAG_WRITER IDENTIFIED BY "<writer-password-set-locally>";
GRANT CREATE SESSION TO RAG_READER;
GRANT CREATE SESSION TO RAG_WRITER;
```

Connect as the owner and grant these object privileges.

```sql
GRANT READ ON documents TO RAG_READER;
GRANT READ ON document_chunks TO RAG_READER;
GRANT READ, INSERT, DELETE ON documents TO RAG_WRITER;
GRANT UPDATE (external_ok) ON documents TO RAG_WRITER;
GRANT INSERT, DELETE ON document_chunks TO RAG_WRITER;
```

Set `ORACLE_WRITE_USER` and `ORACLE_WRITE_PASSWORD` locally alongside the
reader configuration and owner schema. The application prevents lifecycle
changes to seeds, but direct writer DELETE privileges are table-level.
Restrict the writer credential and consider a definer-rights package for
database-side enforcement before public deployment. Reader/writer grants
still need a real validation session with the separate accounts.

Verify both identities and effective rights from their own Oracle sessions.
Do not enable new broad roles to make a failed check pass.

```sql
SELECT SYS_CONTEXT('USERENV', 'SESSION_USER') AS session_user FROM dual;
SELECT privilege FROM session_privs ORDER BY privilege;
SELECT role FROM session_roles ORDER BY role;
SELECT owner, table_name, privilege FROM user_tab_privs_recd
WHERE table_name IN ('DOCUMENTS', 'DOCUMENT_CHUNKS');
SELECT owner, table_name, column_name, privilege FROM user_col_privs_recd
WHERE table_name = 'DOCUMENTS';
```

Run the API with the reader in `ORACLE_USER`/`ORACLE_PASSWORD`, the writer
pair in `ORACLE_WRITE_USER`/`ORACLE_WRITE_PASSWORD`, and `ORACLE_DATA_SCHEMA`
set to the existing owner. Keep owner DDL credentials in a separate local
configuration. Verify reader search and permission denial on an attempted
no-row update, and verify the writer upload, eligibility change and confirmed
deletion against a disposable fixture. The reader must have no DML and the
writer must have no schema-DDL privilege. A table-level writer credential is
not itself constrained to the app's seed-deletion guard.

### Pre-frontend operator handoff

1. Open SQL Worksheet as ADMIN on the same Autonomous database used by the
   demo. Use the same wallet and low service. Check whether either account
   already exists before running the two CREATE USER statements above.
   Inspect any pre-existing grants before reusing an account.

   ```sql
   SELECT username, account_status FROM dba_users
   WHERE username IN ('RAG_READER', 'RAG_WRITER');
   ```

2. As the existing table owner, apply the object grants above. Leave owner
   objects and data in place. Create neither additional tablespace quota nor
   roles for the two service accounts. In a private local configuration set
   `ORACLE_USER` and `ORACLE_PASSWORD` to the reader, the two
   `ORACLE_WRITE_*` settings to the writer, and `ORACLE_DATA_SCHEMA` to
   the existing owner (normally `RAG_APP`). Retain the same DSN and wallet.
   Keep owner credentials separately for maintenance.
3. Compare the following in the original app's Oracle session and the
   diagnostic session locally. Record only match flags and row counts.
   Substitute the actual owner for `RAG_APP` in the second query if needed.
   Bind the two document titles locally in lowercase.

   ```sql
   SELECT SYS_CONTEXT('USERENV','SERVICE_NAME') AS service_name,
          SYS_CONTEXT('USERENV','CURRENT_SCHEMA') AS current_schema,
          SYS_CONTEXT('USERENV','SESSION_USER') AS session_user
   FROM dual;
   SELECT title, COUNT(*) FROM RAG_APP.documents
   WHERE document_type = 'pdf'
     AND LOWER(TRIM(title)) IN (:title_one, :title_two)
   GROUP BY title;
   ```

4. Verify the session/role/grant queries above separately for each identity.
   Reader should have only the two READ grants and no DML. Writer should
   have precisely the grants listed above and no schema DDL. Run the
   following checks as separate statements. Both updates should be denied
   for the reader. Only the first update should succeed for the writer,
   affecting zero rows.

   ```sql
   UPDATE RAG_APP.documents SET external_ok = 0 WHERE 1 = 0;
   UPDATE RAG_APP.documents SET title = 'permission probe' WHERE 1 = 0;
   SELECT COUNT(*) FROM RAG_APP.document_chunks;
   ROLLBACK;
   ```

   The reader's third statement should **succeed**. The writer's should be
   denied because its chunk grants permit insert and delete only.
5. After both account pairs are configured, verify readiness and library
   behavior using the host application's normal launch. Run the opt-in
   library integration only for its disposable test fixture, with separate
   authorization for the fixture mutation. Send no credentials through chat.

Sources: [provisioning steps and versions](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/autonomous-provision.html),
[Always Free limitations](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/autonomous-always-free.html),
[connection overview](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/connect-introduction.html),
[Python wallet parameters](https://python-oracledb.readthedocs.io/en/v3.4.1/api_manual/connect_params.html).
