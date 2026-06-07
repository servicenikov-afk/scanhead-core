BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "spare_parts" (
	"product_model"	TEXT,
	"position"	TEXT,
	"art_no"	TEXT,
	"name"	TEXT,
	"usage_path"	TEXT,
	"category1"	TEXT,
	"category2"	TEXT,
	"category3"	TEXT,
	"production_date_from"	TEXT,
	"production_date_to"	TEXT,
	"serial_from"	TEXT,
	"serial_to"	TEXT
);
CREATE INDEX IF NOT EXISTS "idx_art_no" ON "spare_parts" (
	"art_no"
);
CREATE INDEX IF NOT EXISTS "idx_category1" ON "spare_parts" (
	"category1"
);
CREATE INDEX IF NOT EXISTS "idx_model" ON "spare_parts" (
	"product_model"
);
COMMIT;
