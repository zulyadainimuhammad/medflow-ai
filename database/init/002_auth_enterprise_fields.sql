-- MedFlow AI
-- Authentication model enterprise upgrade
-- Adds security, profile, organizational, and audit fields to users table.

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS employee_id VARCHAR(64),
    ADD COLUMN IF NOT EXISTS middle_name VARCHAR(100),
    ADD COLUMN IF NOT EXISTS job_title VARCHAR(120),
    ADD COLUMN IF NOT EXISTS department_id UUID,
    ADD COLUMN IF NOT EXISTS organization_id UUID,
    ADD COLUMN IF NOT EXISTS profile_photo_url VARCHAR(500),
    ADD COLUMN IF NOT EXISTS preferred_language VARCHAR(10) NOT NULL DEFAULT 'en',
    ADD COLUMN IF NOT EXISTS timezone VARCHAR(64) NOT NULL DEFAULT 'UTC',
    ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS account_locked_until TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS last_failed_login TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS two_factor_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS two_factor_secret VARCHAR(255),
    ADD COLUMN IF NOT EXISTS refresh_token_version INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS created_by UUID,
    ADD COLUMN IF NOT EXISTS updated_by UUID,
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'uq_users_employee_id'
    ) THEN
        ALTER TABLE users
            ADD CONSTRAINT uq_users_employee_id UNIQUE (employee_id);
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_users_created_by_users'
    ) THEN
        ALTER TABLE users
            ADD CONSTRAINT fk_users_created_by_users
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_users_updated_by_users'
    ) THEN
        ALTER TABLE users
            ADD CONSTRAINT fk_users_updated_by_users
            FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL;
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS ix_users_employee_id ON users (employee_id);
CREATE INDEX IF NOT EXISTS ix_users_department_id ON users (department_id);
CREATE INDEX IF NOT EXISTS ix_users_organization_id ON users (organization_id);
CREATE INDEX IF NOT EXISTS ix_users_deleted_at ON users (deleted_at);
