BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "storage_locations" (
	"id"	INTEGER,
	"article"	TEXT NOT NULL UNIQUE,
	"locations"	TEXT NOT NULL,
	"alternative_names"	TEXT,
	"notes"	TEXT,
	"created_at"	DATETIME DEFAULT CURRENT_TIMESTAMP,
	"updated_at"	DATETIME DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE INDEX IF NOT EXISTS "idx_article" ON "storage_locations" (
	"article"
);
CREATE TRIGGER update_storage_locations_timestamp 
        AFTER UPDATE ON storage_locations
        BEGIN
            UPDATE storage_locations 
            SET updated_at = CURRENT_TIMESTAMP 
            WHERE id = NEW.id;
        END;
COMMIT;
