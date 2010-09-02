# -*- coding: utf-8 -*-

# © Copyright 2010 Rob Miller. All Rights Reserved.
# Based on code from django-video:
# © Copyright 2009 Andre Engelbrecht. All Rights Reserved.
# This script is licensed under the BSD Open Source Licence
# Please see the text file LICENCE for more information
# If this script is distributed, it must be accompanied by the Licence

from django.core.management.base import NoArgsCommand
import os
from subprocess import Popen
from subprocess import PIPE

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        """ Encode all pending streams
        """
        from django.conf import settings
        from bm.gallery import models

        GALLERIES_ROOT = getattr(settings, 'GALLERIES_ROOT')
        GALLERIES_URL = getattr(settings, 'GALLERIES_URL')
        ENCODED_VIDEO_WIDTH = getattr(settings, 'VIDEO_WIDTH', '320')

        videos = models.Video.objects.all().filter(encode=True)
        for video in videos:
            infilefullpath = video.filefield.path
            scaledmediapath = models.get_scaled_media_path(video)
            scaledmediapath = '%s%s' % (GALLERIES_ROOT, scaledmediapath)
            flvfilename = "%s.flv" % video.slug
            flvfilefullpath = os.path.join(scaledmediapath, flvfilename)
            thumbnailfilename = "%s.png" % video.slug

            ### XXX STOPPED HERE XXX ###
            # ---- Final Results ----
            #flvurl = "videos/flv/%s" % flvfilename
            #thumburl = "videos/thumbnails/%s.png" % video.slug
            
            # Check if scaledmediapath folder exists and create if not
            if not(os.access(scaledmediapath, os.F_OK)):
                os.makedirs(scaledmediapath)

            # compute video size w/ preserved aspect ratio
            width, height = video.width, video.height
            if width > ENCODED_VIDEO_WIDTH:
                ratio = float(width) / height
                flvwidth = ENCODED_VIDEO_WIDTH
                flvheight = int(ENCODED_VIDEO_WIDTH / ratio)
                encoded_video_size = '%dx%d' % (ENCODED_VIDEO_WIDTH,
                                                encoded_video_height)
            else:
                flvwidth = width
                flvheight = height

            encoded_video_size = '%dx%d' % (flvwidth, flvheight)
            video.flvwidth = width
            video.flvheight = height
                        
            # ffmpeg command to create flv video
            ffmpeg = ['ffmpeg', '-y', '-i', infilefullpath, '-acodec',
                      'libmp3lame', '-ar', '22050',  '-ab', '32000', '-f',
                      'flv', '-s', encoded_video_size, '-b', '1000000',
                      flvfilefullpath]

            # ffmpeg command to create the video thumbnail
            getThumb = ['ffmpeg', '-y', '-i', infilefullpath, '-vframes',
                        '1', '-ss', '00:00:02', '-an', '-vcodec', 'png',
                        '-f', 'rawvideo', '-s', encoded_video_size,
                        os.path.join(scaledmediapath, thumbnailfilename)]

            # flvtool command to get the metadata
            flvtool = ['flvtool2', '-U', flvfilefullpath]

            print "Input File (full path): %s " % infilefullpath
            print "Output File (full path): %s " % flvfilefullpath
            print "Thumbnail Filename: %s" % thumbnailfilename
            print 80 * "-"
            print "ffmpeg Command: %s " % ' '.join(ffmpeg)
            print "Thumbnail Command: %s " % ' '.join(getThumb)
            print "flvTool Command: %s " % ' '.join(flvtool)
            print 80 * "-"
            
            # Lets do the conversion
            print "ffmpeg Result:"
            print 80 * "-"
            ffmpegresult = Popen(ffmpeg, stdout=PIPE).communicate()
            print ffmpegresult[0]
            if ffmpegresult[1]:
                print "STDERR:\n========\n%s\n" % ffmpegresult[1]

            if os.access(flvfilefullpath, os.F_OK): # File exists
                if (os.stat(flvfilefullpath).st_size==0):
                    # Outfile size is zero -> something went wrong, we remove
                    # the file so that it does not cause confusion
                    os.remove(flvfilefullpath) 
                else:
                    # It _seems_ to have worked, do the rest
                    print 80 * "-"
                    print "flvTool result: "
                    print 80 * "-"
                    flvtoolresult = Popen(flvtool, stdout=PIPE).communicate()
                    print flvtoolresult[0]
                    if flvtoolresult[1]:
                        print "STDERR:\n========\n%s\n" % flvtoolresult[1]

                    print 80 * "-"
                    print "Thumbnail Result"
                    print 80 * "-"
                    thumbresult = Popen(getThumb, stdout=PIPE).communicate()
                    print thumbresult[0]
                    if thumbresult[1]:
                        print "STDERR:\n========\n%s\n" % thumbresult[1]

                    video.encode = False
                    flvurl = ('%s%s'
                              % (GALLERIES_URL,
                                 models.get_scaled_media_path(video,
                                                              flvfilename))
                              )
                    thumburl = ('%s%s%s.png'
                                % (GALLERIES_URL,
                                   models.get_scaled_media_path(video),
                                   video.slug)
                                )
                    video.flvfile = flvurl
                    video.thumbnail = thumburl
            video.save()
