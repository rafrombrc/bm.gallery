from bm.gallery import models 
from django.db import connection
from django.db import transaction
from django.db.models import signals
from django.db.utils import DatabaseError

# ensure permissions module gets loaded when we run syncdb
import bm.gallery.permissions

sqls = [
    """
    CREATE LANGUAGE plpgsql;
    """,

    """
    CREATE TABLE gallery_searchable_text (
        mediabase_ptr_id INTEGER REFERENCES gallery_mediabase(id),
        title VARCHAR(300),
        caption VARCHAR(500),
        notes TEXT,
        owner_username VARCHAR(30),
        owner_first_name VARCHAR(30),
        owner_last_name VARCHAR(30),
        tags VARCHAR(500) NOT NULL DEFAULT '',
        tsv TSVECTOR
        );
    """,

    """
    CREATE INDEX gallery_searchable_text_owner_username_idx
        ON gallery_searchable_text(owner_username);
    """,

    """
    CREATE INDEX gallery_searchable_text_tsv_idx ON gallery_searchable_text
        USING gin(tsv);
    """,

    """
    CREATE TRIGGER text_tsv_update BEFORE INSERT OR UPDATE
        ON gallery_searchable_text FOR EACH ROW EXECUTE PROCEDURE
        tsvector_update_trigger('tsv', 'pg_catalog.english',
                                'title', 'caption', 'notes',
                                'owner_username', 'owner_first_name',
                                'owner_last_name', 'tags');
    """,

    """
    CREATE OR REPLACE FUNCTION mediabase_search_update() RETURNS trigger AS $$
        DECLARE
            changed boolean; 
        BEGIN
            IF (tg_op = 'DELETE') THEN
                DELETE FROM gallery_searchable_text
                WHERE mediabase_ptr_id = old.id;
            ELSIF (tg_op = 'INSERT') THEN
                INSERT INTO gallery_searchable_text (mediabase_ptr_id,
                                                     title, caption,
                                                     notes)
                VALUES (new.id, new.title, new.caption, new.notes);
                
                UPDATE gallery_searchable_text SET
                    owner_username = auth_user.username,
                    owner_first_name = auth_user.first_name,
                    owner_last_name = auth_user.last_name
                    FROM auth_user
                WHERE auth_user.id = new.owner_id
                AND mediabase_ptr_id = new.id;
            ELSIF (tg_op = 'UPDATE') THEN
                changed := FALSE;
                IF new.title != old.title OR new.caption != old.caption
                OR new.notes != old.notes THEN
                    changed := TRUE;
                END IF;
                IF changed THEN
                    UPDATE gallery_searchable_text SET
                        title = new.title,
                        caption = new.caption,
                        notes = new.notes
                    WHERE mediabase_ptr_id = new.id;
                END IF;
            END IF;
            RETURN new;
        END
    $$ LANGUAGE plpgsql;
    """,

    """
    CREATE TRIGGER mediabase_search_update AFTER INSERT OR UPDATE OR DELETE
        ON gallery_mediabase FOR EACH ROW EXECUTE PROCEDURE
        mediabase_search_update();
        
    """,
    
    """
    CREATE OR REPLACE FUNCTION user_search_update() RETURNS trigger AS $$
        DECLARE
            changed boolean; 
        BEGIN
            changed := FALSE;
            IF new.username != old.username
            OR new.first_name != old.first_name
            OR new.last_name != old.last_name THEN
                changed := TRUE;
            END IF;
            IF changed THEN
                UPDATE gallery_searchable_text SET
                    owner_username = new.username,
                    owner_first_name = new.first_name,
                    owner_last_name = new.last_name
                WHERE owner_username = old.username;
            END IF;
            RETURN new;
        END
    $$ LANGUAGE plpgsql;
    """,

    """
    CREATE TRIGGER user_search_update AFTER UPDATE
        ON auth_user FOR EACH ROW EXECUTE PROCEDURE
        user_search_update();
        
    """,

    """
    CREATE OR REPLACE FUNCTION tag_search_update() RETURNS trigger AS $$
        DECLARE
            tag_name text;
            concat_tags text;
            pos integer;
            len integer;
        BEGIN
            IF (tg_op = 'INSERT') THEN
                SELECT INTO tag_name name FROM tagging_tag WHERE id = new.tag_id;
                SELECT INTO concat_tags tags FROM gallery_searchable_text WHERE
                    mediabase_ptr_id = new.object_id;
                pos := POSITION(tag_name IN concat_tags);
                IF (pos = 0) THEN
                    UPDATE gallery_searchable_text
                        SET tags = tag_name || ' ' || coalesce(concat_tags, '')
                        WHERE mediabase_ptr_id = new.object_id;
                END IF;
            ELSIF (tg_op = 'DELETE') THEN
                SELECT INTO tag_name name FROM tagging_tag WHERE id = old.tag_id;
                SELECT INTO concat_tags tags FROM gallery_searchable_text WHERE
                    mediabase_ptr_id = old.object_id;
                len := CHAR_LENGTH(tag_name);
                pos := POSITION(tag_name IN concat_tags);
                IF (pos != 0) THEN
                    UPDATE gallery_searchable_text SET
                        tags = TRIM(OVERLAY(concat_tags PLACING ''
                                            FROM pos FOR len))
                        WHERE mediabase_ptr_id = old.object_id;
                END IF;
            END IF;
            RETURN new;
        END
    $$ LANGUAGE plpgsql
    """,

    """
    CREATE TRIGGER tag_search_update AFTER INSERT OR DELETE
        ON tagging_taggeditem FOR EACH ROW EXECUTE PROCEDURE
        tag_search_update();
    """,

    ]

def execute_sql(cursor, sql):
    try:
        cursor.execute(sql)
        transaction.commit_unless_managed()
    except DatabaseError, e:
        if 'already exists' in e.message:
            transaction.rollback()
        else:
            raise

def tsearch_init(**kwargs):
    cursor = connection.cursor()
    for sql in sqls:
        execute_sql(cursor, sql)

signals.post_syncdb.connect(tsearch_init, sender=models)
