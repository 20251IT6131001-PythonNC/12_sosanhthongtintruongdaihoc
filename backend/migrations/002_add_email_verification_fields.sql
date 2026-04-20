-- Migration: Add email verification fields to users table
-- Date: 2026-04-19
-- Description: Add email verification support for user signup flow

ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN email_verification_token VARCHAR(255) NULL;
ALTER TABLE users ADD COLUMN verification_token_expiry DATETIME NULL;

CREATE INDEX idx_verification_token ON users(email_verification_token);
