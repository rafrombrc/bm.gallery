<?php
/* Plugin Name: bm.gallery shortcodes
 * Plugin URI: http://earth.burningman.com/api/gallery/wordpress/
 * Description: Adds a gallery tag to Wordpress, interfacing with the bm.gallery API
 * Author: Bruce Kroeze
 * Version: 0.1
 * Author URI: http://ecomsmith.com
 *
 * Copyright 2011 Black Rock City LLC
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
 * MA 02110-1301, USA.
 *
 */

//Allow text widgets to use shortcodes
add_filter('widget_text', 'do_shortcode');

#$GALLERY_KEY = '6FwUn9c2X6MX2c3LH0EzQUqC4HyreC2xZe3DAaqTMiE=';
#$GALLERY_USER = 'bkroeze';

$GALLERY_KEY = '/Z+17Dql1Ar1sDXrpP9BZkBC4z+8xMcO+3GuLLAXCbU=';
$GALLERY_USER = 'bruce';

/**
 * Wordpress shorttag function returning a properly formatted url for a gallery image.
 *
 * Can be called in any of these formats, all attributes except url are optional
 *
 * [gallery]gallery url[/gallery]
 * [gallery watermark='none|both|footer|extended' height=100 width=100 upscale=true crop=true img=true]gallery url[/gallery]
 * [gallery watermark='none|both|footer|extended' height=100 width=100 upscale=true crop=true url='gallery url']
 * [gallery json='true']gallery url[/gallery]
 * [gallery json='true']gallery url[/gallery]
 * [gallery xml='true']gallery url[/gallery]
 * [gallery xml='true' url='gallery url']
 *
 * Options descriptions:
 * - watermark: Default is none, can alsp be "both", "footer" or "extended"
 * - height: Default 0 (ignored), the maximum height in pixels
 * - width: Default 0 (ignored), the minimum width
 * - upscale: Default false, if true, then the image will be allowed to resize larger than the original
 * - crop: Default false, if true then instead of resizing, the image will be cropped
 * - img: Default true, if not json or xml. If true, wrap the image in an img tag
 * - json: Default false, if true then return json metadata
 * - xml: Default false, if true then return xml metadata
 *
 *
 * Note that you cannot simultanesouly resize and get metadata with json or xml.
 *
 *@param array $atts the shorttag attributes
 *@param string $content the url as returned when browsing the gallery.
 */
function gallery_tag($atts, $content=null) {

  $processed = shortcode_atts(
    array('watermark' => null,
          'height' => 0,
          'h' => 0,
          'width' => 0,
          'w' => 0,
          'upscale' => null,
          'crop' => null,
          'json' => 'f',
          'xml' => 'f',
          'img' => 'true',
          'url' => $content),
    $atts);

  extract($processed);

  if ($url == null) {
    return '<!-- Bad [gallery] tag, no url passed -->';
  }

  $urlinfo = parse_url($url);

  $meta = FALSE;
  $action = 'image';

  if ($json == 'true' || $json == 'yes') {
    $meta = TRUE;
    $action = 'json';
  }
  else {
    $json = FALSE;
    if ($xml == 'true' || $xml == 'yes') {
      $meta = TRUE;
      $action = 'xml';
    }
  }

  $apiatts = array();
  if ($meta) {
    $img = 'false';
  }
  else {
    if ($height == 0 && $h > 0) {
      $height = $h;
    }
    if ($width == 0 && $w > 0) {
      $width = $w;
    }

    $apiatts[] = 'h=' . $height;
    $apiatts[] = 'w=' . $width;
    if ($watermark != null) {
      $apiatts[] = 'watermark=' . $watermark;
    }
    if ($upscale == 'true' || $upscale == 'yes') {
      $apiatts[] = 'upscale=t';
    }
    if ($crop == 'true' || $crop == 'yes') {
      $apiatts[] = 'crop=t';
    }
  }

  $apiurl = '/api' . $urlinfo['path'] . '/' . $action;

  $apiurl = gallery_sign_url($apiurl, $apiatts, $urlinfo);
  if ($img == 'true' || $img == 'yes') {
    return "<img src='$apiurl' />";
  }
  return $apiurl;
}

add_shortcode('gallery', 'gallery_tag');

/**
 * Sign an url for use by the Gallery API
 *
 * @param string $apiurl the url fragment to sign, it should not contain the scheme or server
 * @param array $apiatts list of options
 * @param array $urlinfo the url of the originial gallery link as parsed by parse_url
 * @return string url
 */
function gallery_sign_url($apiurl, &$apiatts, $urlinfo) {
  global $GALLERY_KEY, $GALLERY_USER;

  $apiurl = str_replace('//', '/', $apiurl);
  if (!empty($GALLERY_KEY) && !empty($GALLERY_USER)) {
    $apiatts[] = 'user=' . $GALLERY_USER;
    $apiurl .= '?' . implode('&',$apiatts);
    $seed = time();
    $sig = md5($apiurl . $seed . $GALLERY_KEY);
    $apiurl .= "&seed=$seed&sig=$sig";
  }
  elseif (count($apiatts) > 0) {
    $apiurl .= '?' . implode('&',$apiatts);
  }
  $signed = $urlinfo['scheme'] . '://' . $urlinfo['host'];
  if (!empty($urlinfo['port']) && $urlinfo['port'] <> 80) {
    $signed .= ':' . $urlinfo['port'];
  }
  $signed .= $apiurl;
  return $signed;
}