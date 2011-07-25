Burning Man Media Gallery Wordpress Tag
=======================================

Description
-----------

This tag adds the ability for a Wordpress installation to use the Burning Man Media Gallery API via a convenient "short tag".

Installation
------------

#. Copy the file "gallery_tags.php" from the "wordpress" directory of the sourcecode to your "wp-content/plugins" directory.
#. Activate the plugin from your admin page.
#. Login to the admin of your Wordpress blog, and look on the admin navbar under "settings" for "BM Gallery Settings".  Fill in your username and API key, then click "save".

Usage
-----

In any post or page, you can use the shorttag "[gallery]" to refer to gallery images, with all the signing taken care of for you.

It can be called in any of these formats, all attributes except url are optional:

* [gallery]gallery url[/gallery]
* [gallery watermark='none|both|footer|extended' height=100 width=100 upscale=true crop=true img=true]gallery url[/gallery]
* [gallery watermark='none|both|footer|extended' height=100 width=100 upscale=true crop=true url='gallery url']
* [gallery json='true']gallery url[/gallery]
* [gallery json='true']gallery url[/gallery]
* [gallery xml='true']gallery url[/gallery]
* [gallery xml='true' url='gallery url']

Options descriptions:

 * watermark: Default is none, can alsp be "both", "footer" or "extended"
 * height: Default 0 (ignored), the maximum height in pixels
 * width: Default 0 (ignored), the minimum width
 * upscale: Default false, if true, then the image will be allowed to resize larger than the original
 * crop: Default false, if true then instead of resizing, the image will be cropped
 * img: Default true, if not json or xml. If true, wrap the image in an img tag
 * json: Default false, if true then return json metadata
 * xml: Default false, if true then return xml metadata
 * align: left|right|center
 * caption: true|false
 * link: true|false|full (default false). If "true", generates a link to the media gallery, if "full", generates a link to the full-size image

*Note that you cannot simultaneously resize and get metadata with json or xml.*

