"""Added new column for ranked searching of terms and definitions

Revision ID: 201bae6698f6
Revises: 4614666a279f
Create Date: 2015-10-21 00:31:05.525848

"""

# revision identifiers, used by Alembic.
revision = '201bae6698f6'
down_revision = '4614666a279f'

from alembic import op
import sqlalchemy as sa

def upgrade():
    db_bind = op.get_bind()
    #
    # Replace the index for terms with one including varchar_pattern_ops
    #

    # drop the old index
    db_bind.execute(sa.sql.text('''
        DROP INDEX IF EXISTS ix_definitions_term;
    '''))
    # create the new index
    db_bind.execute(sa.sql.text('''
        CREATE INDEX ix_definitions_term ON definitions (term varchar_pattern_ops);
    '''))

    #
    # Support full-text search on terms and definitions
    #

    # add the tsv_search column to the definitions table
    db_bind.execute(sa.sql.text('''
        ALTER TABLE definitions ADD COLUMN tsv_search tsvector;
    '''))

    # set up a trigger to populate tsv_search when records are created or altered
    db_bind.execute(sa.sql.text('''
        DROP FUNCTION IF EXISTS definitions_search_trigger();
    '''))
    db_bind.execute(sa.sql.text('''
        CREATE FUNCTION definitions_search_trigger() RETURNS trigger AS $$
        begin
          new.tsv_search :=
             setweight(to_tsvector('pg_catalog.english', COALESCE(new.term,'')), 'A') ||
             setweight(to_tsvector('pg_catalog.english', COALESCE(new.definition,'')), 'B');
          return new;
        end
        $$ LANGUAGE plpgsql;
    '''))

    db_bind.execute(sa.sql.text('''
        DROP TRIGGER IF EXISTS tsvupdate_definitions_trigger ON definitions;
    '''))
    db_bind.execute(sa.sql.text('''
        CREATE TRIGGER tsvupdate_definitions_trigger BEFORE INSERT OR UPDATE ON definitions FOR EACH ROW EXECUTE PROCEDURE definitions_search_trigger();
    '''))

    # create an index for tsv_search
    db_bind.execute(sa.sql.text('''
        DROP INDEX IF EXISTS ix_definitions_tsv_search;
    '''))
    db_bind.execute(sa.sql.text('''
        CREATE INDEX ix_definitions_tsv_search ON definitions USING gin(tsv_search);
    '''))

    # populate tsv_search for existing records
    db_bind.execute(sa.sql.text('''
        UPDATE definitions SET tsv_search = setweight(to_tsvector('pg_catalog.english', COALESCE(term,'')), 'A') || setweight(to_tsvector('pg_catalog.english', COALESCE(definition,'')), 'B');
    '''))

def downgrade():
    db_bind = op.get_bind()
    #
    # Revert the terms index to the original style
    #

    # drop the varchar_pattern_ops index
    db_bind.execute(sa.sql.text('''
        DROP INDEX IF EXISTS ix_definitions_term;
    '''))
    # re-create the standard index
    db_bind.execute(sa.sql.text('''
        CREATE INDEX ix_definitions_term ON definitions(term);
    '''))

    #
    # Remove support for full-text search on terms and definitions
    #

    # drop the tsv_search column from the definitions table
    db_bind.execute(sa.sql.text('''
        ALTER TABLE definitions DROP COLUMN IF EXISTS tsv_search;
    '''))

    # drop the search trigger and function
    db_bind.execute(sa.sql.text('''
        DROP TRIGGER IF EXISTS tsvupdate_definitions_trigger ON definitions;
    '''))
    db_bind.execute(sa.sql.text('''
        DROP FUNCTION IF EXISTS definitions_search_trigger();
    '''))

    # drop the index
    db_bind.execute(sa.sql.text('''
        DROP INDEX IF EXISTS ix_definitions_tsv_search;
    '''))
