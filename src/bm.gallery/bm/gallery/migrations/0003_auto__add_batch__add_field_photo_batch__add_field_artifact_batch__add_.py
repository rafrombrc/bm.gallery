# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Batch'
        db.create_table('gallery_batch', (
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=36, primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('date_added', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal('gallery', ['Batch'])

        # Adding field 'Photo.batch'
        db.add_column('gallery_photo', 'batch', self.gf('django.db.models.fields.related.ForeignKey')(related_name='photos', null=True, to=orm['gallery.Batch']), keep_default=False)

        # Adding field 'Artifact.batch'
        db.add_column('gallery_artifact', 'batch', self.gf('django.db.models.fields.related.ForeignKey')(related_name='artifacts', null=True, to=orm['gallery.Batch']), keep_default=False)

        # Adding field 'Video.batch'
        db.add_column('gallery_video', 'batch', self.gf('django.db.models.fields.related.ForeignKey')(related_name='videos', null=True, to=orm['gallery.Batch']), keep_default=False)


    def backwards(self, orm):
        
        # Deleting model 'Batch'
        db.delete_table('gallery_batch')

        # Deleting field 'Photo.batch'
        db.delete_column('gallery_photo', 'batch_id')

        # Deleting field 'Artifact.batch'
        db.delete_column('gallery_artifact', 'batch_id')

        # Deleting field 'Video.batch'
        db.delete_column('gallery_video', 'batch_id')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'gallery.artifact': {
            'Meta': {'object_name': 'Artifact', '_ormbases': ['gallery.ImageBase']},
            'batch': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'artifacts'", 'null': 'True', 'to': "orm['gallery.Batch']"}),
            'imagebase_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['gallery.ImageBase']", 'unique': 'True', 'primary_key': 'True'}),
            'legacy_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'db_index': 'True'})
        },
        'gallery.batch': {
            'Meta': {'object_name': 'Batch'},
            'date_added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '36', 'primary_key': 'True'})
        },
        'gallery.category': {
            'Meta': {'object_name': 'Category'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '25'})
        },
        'gallery.featuredmedia': {
            'Meta': {'object_name': 'FeaturedMedia'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'media': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'media'", 'to': "orm['gallery.MediaBase']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'gallery.imagebase': {
            'Meta': {'object_name': 'ImageBase', '_ormbases': ['gallery.MediaBase']},
            'date_taken': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'full_image_available': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True'}),
            'mediabase_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['gallery.MediaBase']", 'unique': 'True', 'primary_key': 'True'}),
            'textheight': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'gallery.mediabase': {
            'Meta': {'object_name': 'MediaBase'},
            'caption': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True'}),
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['gallery.Category']", 'symmetrical': 'False'}),
            'child_attrpath': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'date_added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'date_approved': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'date_submitted': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'height': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'moderator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'mediabase_moderator_set'", 'null': 'True', 'to': "orm['auth.User']"}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '100', 'db_index': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'uploaded'", 'max_length': '15'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'view_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'width': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'year': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'})
        },
        'gallery.photo': {
            'Meta': {'object_name': 'Photo', '_ormbases': ['gallery.ImageBase']},
            'batch': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'photos'", 'null': 'True', 'to': "orm['gallery.Batch']"}),
            'imagebase_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['gallery.ImageBase']", 'unique': 'True', 'primary_key': 'True'}),
            'in_press_gallery': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'legacy_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'db_index': 'True'})
        },
        'gallery.profile': {
            'Meta': {'object_name': 'Profile'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'gallery.video': {
            'Meta': {'object_name': 'Video', '_ormbases': ['gallery.MediaBase']},
            'batch': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'videos'", 'null': 'True', 'to': "orm['gallery.Batch']"}),
            'encode': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'filefield': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'flvfile': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'flvheight': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'flvwidth': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'mediabase_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['gallery.MediaBase']", 'unique': 'True', 'primary_key': 'True'}),
            'thumbnail': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['gallery']
