# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Category'
        db.create_table('gallery_category', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=25)),
        ))
        db.send_create_signal('gallery', ['Category'])

        # Adding model 'Profile'
        db.create_table('gallery_profile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=300, null=True, blank=True)),
        ))
        db.send_create_signal('gallery', ['Profile'])

        # Adding model 'MediaBase'
        db.create_table('gallery_mediabase', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=100, db_index=True)),
            ('caption', self.gf('django.db.models.fields.CharField')(max_length=500, null=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
            ('date_added', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('year', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('view_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('status', self.gf('django.db.models.fields.CharField')(default='uploaded', max_length=15)),
            ('child_attrpath', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('height', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('width', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('date_submitted', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('date_approved', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('moderator', self.gf('django.db.models.fields.related.ForeignKey')(related_name='mediabase_moderator_set', null=True, to=orm['auth.User'])),
            ('notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('gallery', ['MediaBase'])

        # Adding M2M table for field categories on 'MediaBase'
        db.create_table('gallery_mediabase_categories', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('mediabase', models.ForeignKey(orm['gallery.mediabase'], null=False)),
            ('category', models.ForeignKey(orm['gallery.category'], null=False))
        ))
        db.create_unique('gallery_mediabase_categories', ['mediabase_id', 'category_id'])

        # Adding model 'ImageBase'
        db.create_table('gallery_imagebase', (
            ('mediabase_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['gallery.MediaBase'], unique=True, primary_key=True)),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True)),
            ('date_taken', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('full_image_available', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('gallery', ['ImageBase'])

        # Adding model 'Photo'
        db.create_table('gallery_photo', (
            ('imagebase_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['gallery.ImageBase'], unique=True, primary_key=True)),
            ('legacy_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, db_index=True)),
            ('in_press_gallery', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
        ))
        db.send_create_signal('gallery', ['Photo'])

        # Adding model 'Artifact'
        db.create_table('gallery_artifact', (
            ('imagebase_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['gallery.ImageBase'], unique=True, primary_key=True)),
            ('legacy_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, db_index=True)),
        ))
        db.send_create_signal('gallery', ['Artifact'])

        # Adding model 'Video'
        db.create_table('gallery_video', (
            ('mediabase_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['gallery.MediaBase'], unique=True, primary_key=True)),
            ('filefield', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('flvfile', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True, blank=True)),
            ('thumbnail', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('flvheight', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('flvwidth', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('encode', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('gallery', ['Video'])

        # Adding model 'FeaturedMedia'
        db.create_table('gallery_featuredmedia', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('media', self.gf('django.db.models.fields.related.ForeignKey')(related_name='media', to=orm['gallery.MediaBase'])),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('gallery', ['FeaturedMedia'])


    def backwards(self, orm):
        
        # Deleting model 'Category'
        db.delete_table('gallery_category')

        # Deleting model 'Profile'
        db.delete_table('gallery_profile')

        # Deleting model 'MediaBase'
        db.delete_table('gallery_mediabase')

        # Removing M2M table for field categories on 'MediaBase'
        db.delete_table('gallery_mediabase_categories')

        # Deleting model 'ImageBase'
        db.delete_table('gallery_imagebase')

        # Deleting model 'Photo'
        db.delete_table('gallery_photo')

        # Deleting model 'Artifact'
        db.delete_table('gallery_artifact')

        # Deleting model 'Video'
        db.delete_table('gallery_video')

        # Deleting model 'FeaturedMedia'
        db.delete_table('gallery_featuredmedia')


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
            'imagebase_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['gallery.ImageBase']", 'unique': 'True', 'primary_key': 'True'}),
            'legacy_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'db_index': 'True'})
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
            'mediabase_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['gallery.MediaBase']", 'unique': 'True', 'primary_key': 'True'})
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
