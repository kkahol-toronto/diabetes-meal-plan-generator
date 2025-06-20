from datetime import datetime

def up():
    """
    Migration to add consent fields to users table.
    This will be executed when the migration is applied.
    """
    return """
    ALTER TABLE users
      ADD COLUMN consent_given BOOLEAN NOT NULL DEFAULT FALSE,
      ADD COLUMN consent_timestamp TIMESTAMP WITH TIME ZONE,
      ADD COLUMN policy_version VARCHAR(20);
    """

def down():
    """
    Rollback migration to remove consent fields from users table.
    This will be executed when the migration is rolled back.
    """
    return """
    ALTER TABLE users
      DROP COLUMN consent_given,
      DROP COLUMN consent_timestamp,
      DROP COLUMN policy_version;
    """ 