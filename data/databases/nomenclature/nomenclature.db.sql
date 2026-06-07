BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "metadata" (
	"key"	TEXT,
	"value"	TEXT,
	"updated_at"	DATETIME DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY("key")
);
CREATE TABLE IF NOT EXISTS "spare_parts" (
	"id"	INTEGER,
	"article"	TEXT NOT NULL UNIQUE,
	"name"	TEXT,
	"barcodes"	TEXT,
	"unit"	TEXT,
	"last_updated"	DATETIME DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE INDEX IF NOT EXISTS "idx_article" ON "spare_parts" (
	"article"
);
COMMIT;
