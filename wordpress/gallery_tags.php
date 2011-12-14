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

/**
 * Wordpress shorttag function returning a properly formatted url for a gallery image.
 *
 * Can be called in any of these formats, all attributes except url are optional
 *
 * [bmimgs]gallery url[/bmimgs]
 * [bmimgs watermark='none|both|footer|extended' height=100 width=100 upscale=true crop=true img=true]gallery url[/bmimgs]
 * [bmimgs watermark='none|both|footer|extended' height=100 width=100 upscale=true crop=true url='gallery url']
 * [bmimgs json='true']gallery url[/bmimgs]
 * [bmimgs json='true']gallery url[/bmimgs]
 * [bmimgs xml='true']gallery url[/bmimgs]
 * [bmimgs xml='true' url='gallery url']
 *
 * Options descriptions:
 * - watermark: Default is none, can also be "both", "footer" or "extended"
 * - size: thumbnail | half | medium | large | full (default medium)
 * - height: Default 0 (ignored), the maximum height in pixels
 * - width: Default 0 (ignored), the minimum width
 * - upscale: Default false, if true, then the image will be allowed to resize larger than the original
 * - crop: Default false, if true then instead of resizing, the image will be cropped
 * - img: Default true, if not json or xml. If true, wrap the image in an img tag
 * - json: Default false, if true then return json metadata
 * - xml: Default false, if true then return xml metadata
 * - align: left|right|center (default left)
 * - caption: true|false|<some arbitrary caption that you want to supply> (default true)
 * - link: true|false|full (default false)
 *         if "true", generates a link to the media gallery,
 *         if "full", generates a link to the full-size image
 *
 * NOTES:
 * 		You cannot simultaneously resize and get metadata with json or xml.
 *		If you specify "true" for a caption, the caption data from the image gallery will be used/
 *		If you specify "size" then height and width values will be ignored.
 *
 *@param array $atts the shorttag attributes
 *@param string $content the url as returned when browsing the gallery.
 */

function register_bm_gallery_settings() {
	register_setting( 'bm-gallery-opts', 'bm_gallery_user' );
	register_setting( 'bm-gallery-opts', 'bm_gallery_key' );
} // register_bm_gallery_settings
add_action( 'admin_init', 'register_bm_gallery_settings' );

function gallery_tag($atts, $content=null) {
	$processed = shortcode_atts(
		array('watermark' => null,
		'height' => 0,
		'h' => 0,
		'width' => 0,
		'w' => 0,
		'size' => 'medium',
		'upscale' => null,
		'crop' => null,
		'json' => 'f',
		'xml' => 'f',
		'img' => 'true',
		'url' => $content,
		'caption' => 'true',
		'align' => '',
		'link' => 'f'),
		$atts);
	extract( $processed );

	if ( $url == null ) {
		return '<!-- Bad [bmimgs] tag, no url passed -->';
	}

	$urlinfo = parse_url( $url );

	$meta = FALSE;
	$action = 'image';

	if ( $json == 'true' || $json == 'yes' ) {
		$meta = TRUE;
		$action = 'json';
	}
	else {
		$json = FALSE;
		if ( $xml == 'true' || $xml == 'yes' ) {
			$meta = TRUE;
			$action = 'xml';
		}
	}

	$image_for_site = false;

	$apiatts = array();
	if ( $meta ) {
		$img = 'false';
	}
	else {
		if ( $width == 0 && $height == 0 ) {
			global $_wp_additional_image_sizes;
			if ( strcasecmp( $size, 'medium' ) == 0 )
				$width = get_option( 'medium_size_w' );
			else if ( strcasecmp( $size, 'large' ) == 0 )
				$width = get_option( 'large_size_w' );
			else if ( strcasecmp( $size, 'half' ) == 0 ) {
				global $_wp_additional_image_sizes;
				if ( isset( $_wp_additional_image_sizes[ 'half' ] ) ) {
					$image_size = $_wp_additional_image_sizes[ 'half' ];
					$width = $image_size[ 'width' ];
				}
			}
			else if ( strcasecmp( $size, 'thumbnail' ) == 0 )
				$width = get_option( 'thumbnail_size_w' );
			else if ( strcasecmp( $size, 'site_tall' ) == 0 ) {
				$width = 130;
				$image_for_site = true;
			}
			else if ( strcasecmp( $size, 'site_wide' ) == 0 ) {
				$width = 175;
				$image_for_site = true;
			}
		}
		else {
			if ( $height == 0 && $h > 0 ) {
				$height = $h;
			}
			if ( $width == 0 && $w > 0 ) {
				$width = $w;
			}
		}

		$apiatts[] = 'h=' . $height;
		$apiatts[] = 'w=' . $width;
		if ( $watermark != null ) {
			$apiatts[] = 'watermark=' . $watermark;
		}
		if ( $upscale == 'true' || $upscale == 'yes' ) {
			$apiatts[] = 'upscale=t';
		}
		if ( $crop == 'true' || $crop == 'yes' ) {
			$apiatts[] = 'crop=t';
		}
	}

	$has_capt = ( !$image_for_site && ( $caption=='true' || $caption=='yes' ) );
	if ( $has_capt ) {
		// go get caption, awkward
		$apiurl2 = '/api'. $urlinfo['path'] . '/caption';

		$apiatts2 = array();
		$apiurl2 = gallery_sign_url( $apiurl2, $apiatts2, $urlinfo );
		$ch = curl_init();

		// set url
		curl_setopt( $ch, CURLOPT_URL, $apiurl2 );

		//return the transfer as a string
		curl_setopt( $ch, CURLOPT_RETURNTRANSFER, 1 );

		// $output contains the output string
		$caption = curl_exec( $ch );

		// close curl resource to free up system resources
		curl_close( $ch );
	}
	else if ( trim( $caption ) !== '' ) {
		$has_capt = true;
		$caption = htmlspecialchars_decode( $caption );
	}

	$apiurl = '/api' . $urlinfo['path'] . '/' . $action;
	$apiurl = gallery_sign_url( $apiurl, $apiatts, $urlinfo );
	if ( $image_for_site || $img == 'true' || $img == 'yes' ) {
		$escaped_caption = addslashes( $caption );
		$ret = "<img src='$apiurl' alt='$escaped_caption' />";

		if ( $image_for_site || $link == 'true' ) {
			$ret = "<a href='$url'>$ret";
		}
		else if ( $link == 'full' ) {
			$fullatts = array();
			$fullurl = '/api' . $urlinfo['path'] . '/' . $action;
			$fullurl = gallery_sign_url( $fullurl, $fullatts, $urlinfo );
			$ret = "<a href='$fullurl'>$ret";
		}
	}
	else {
		$ret = $apiurl;
	}

	if ( !empty( $align ) || $has_capt ) {
		$classes = array();
		if ( !empty( $align ) ) {
			$classes[] = "align$align";
			$classes[] = "images$align";
		}
		if ( $has_capt ) {
			$classes[] = 'wp-caption';
		}
		$cl = implode( ' ', $classes );
		$wp_image_div_width = $width . 'px';
		$ret = "<div class='$cl' style='width:$wp_image_div_width'>$ret";

		if ( $image_for_site == true ) {
			$ret .= '<span style="float:right"><img src="' . get_bloginfo( 'stylesheet_directory' ) . '/images/about_this_photo.gif"/></span></a>';
		}
		else if ( $has_capt ) {
			if ($link == 'true' || $link == 'full') {
				$ret .= "</a>";
			}
			$ret .= '<p class="wp-caption-text">' . $caption . '</p>';
		}
		else if ($link == 'true' || $link == 'full') {
			$ret .= "</a>";
		}
		$ret .= '</div>';
	}
	else if ($link == 'true' || $link == 'full') {
		$ret .= "</a>";
	}

  return $ret;
} // gallery_tag
add_shortcode( 'bmimgs', 'gallery_tag' );

/**
 * Sign an url for use by the Gallery API
 *
 * @param string $apiurl the url fragment to sign, it should not contain the scheme or server
 * @param array $apiatts list of options
 * @param array $urlinfo the url of the originial gallery link as parsed by parse_url
 * @return string url
 */
function gallery_sign_url( $apiurl, &$apiatts, $urlinfo ) {
	$gallery_key = get_option( 'bm_gallery_key' );
	$gallery_user = get_option( 'bm_gallery_user' );

	$apiurl = str_replace( '//', '/', $apiurl );
	if ( !empty( $gallery_key ) && !empty( $gallery_user ) ) {
		$apiatts[] = 'user=' . $gallery_user;
		$apiurl .= '?' . implode( '&', $apiatts );
		$seed = time();
		$n = rand( 10e16, 10e20 );
		$seed .= base_convert( $n, 10, 36 );
		$sig = md5( $apiurl . $seed . $gallery_key );
		$apiurl .= "&seed=$seed&sig=$sig";
	}
	elseif ( count( $apiatts ) > 0 ) {
		$apiurl .= '?' . implode( '&', $apiatts );
	}
	$signed = $urlinfo['scheme'] . '://' . $urlinfo['host'];
	if ( !empty( $urlinfo['port']) && $urlinfo['port'] <> 80 ) {
		$signed .= ':' . $urlinfo['port'];
	}
	$signed .= $apiurl;
	return $signed;
} // gallery_sign_url
add_action( 'admin_menu', 'bm_gallery_create_menu' );

function bm_gallery_create_menu() {
	//create new top-level menu
	add_options_page( 'BM Gallery Settings', 'BM Gallery Settings', 'administrator', 'bm.gallery', 'bm_gallery_settings_page' );
} // bm_gallery_create_menu

function bm_gallery_settings_page() {
?>
	<div class="wrap">
		<h2>BM Gallery</h2>
		<form method="post" action="options.php">
			<?php
			$user = get_option( 'bm_gallery_user' );
			$key = get_option( 'bm_gallery_key' );
			?>

			<table class="form-table">
				<tr valign="top">
					<th scope="row">Gallery Username</th>
					<td><input type="text" name="bm_gallery_user" value="<?php echo $user; ?>" /></td>
				</tr>
				<tr valign="top">
					<th scope="row">Gallery User Key</th>
					<td><input type="text" name="bm_gallery_key" value="<?php echo $key; ?>" /></td>
				</tr>
			</table>

			<p class="submit">
				<input type="submit" class="button-primary" value="<?php _e('Save Changes') ?>" />
			</p>
			<?php
			settings_fields( 'bm-gallery-opts' );
			do_settings( 'bm-gallery-opts' );
			?>
		</form>
	</div>
<?php
}
?>
