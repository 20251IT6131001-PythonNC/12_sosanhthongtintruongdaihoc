-- Migration: Add is_active and reason fields to users table
-- Date: 2026-04-30
-- Description: Support account closure - track active status and closure reason

ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE users ADD COLUMN reason VARCHAR(250) NULL;
