# Database Migration Fix - October 24, 2024

## Issue Found and Fixed

**Error when running migration:**
```
ERROR:  42804: foreign key constraint "extension_profiles_assessment_id_fkey" cannot be implemented
DETAIL:  Key columns "assessment_id" and "id" are of incompatible types: uuid and integer.
```

## Root Cause

The `candidate_assessments` table (existing table) uses `SERIAL PRIMARY KEY`, which is an `INTEGER` type in PostgreSQL. However, the new `extension_profiles` table was trying to reference it with a `UUID` type foreign key.

**Existing table schema:**
```sql
CREATE TABLE candidate_assessments (
    id SERIAL PRIMARY KEY,  -- This is INTEGER, not UUID
    linkedin_url TEXT NOT NULL,
    ...
);
```

**Original migration (incorrect):**
```sql
ALTER TABLE extension_profiles
ADD COLUMN assessment_id UUID REFERENCES candidate_assessments(id);  -- WRONG TYPE
```

## Fix Applied

**Updated migration (correct):**
```sql
ALTER TABLE extension_profiles
ADD COLUMN assessment_id INTEGER REFERENCES candidate_assessments(id);  -- CORRECT TYPE
```

## File Updated

- `backend/migrations/add_assessment_fields.sql` (line 8)
  - Changed `assessment_id UUID` → `assessment_id INTEGER`

## What You Need to Do

**If you already tried running the migration and got the error:**

1. Drop the problematic column (if it was partially created):
```sql
-- In Supabase SQL Editor:
ALTER TABLE extension_profiles DROP COLUMN IF EXISTS assessment_id;
```

2. Re-run the updated migration file:
```sql
-- Copy and paste the entire contents of:
-- backend/migrations/add_assessment_fields.sql
-- Into Supabase SQL Editor and run it
```

**If you haven't run the migration yet:**
- Just run the migration as instructed in START_HERE.md
- The fix is already applied, so it will work correctly

## Verification

After running the migration, verify the column type is correct:
```sql
-- In Supabase SQL Editor:
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'extension_profiles'
  AND column_name = 'assessment_id';

-- Should show:
-- column_name    | data_type
-- assessment_id  | integer
```

## Impact

- ✅ Migration now runs without errors
- ✅ Foreign key constraint works correctly
- ✅ Assessment linking will work as expected
- ✅ No changes needed to application code (app.py already handles integers)

## Commit

Fixed in commit: `356a0b8`
- Branch: `dev/enhancements`
- File: `backend/migrations/add_assessment_fields.sql`

---

**Status:** ✅ Fixed - Migration ready to run
