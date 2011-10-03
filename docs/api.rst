Burning Man Media Gallery API Documentation
===========================================

API Overview
------------

The Burning Man Media Gallery API is free for you to use and build with.

The API currently supports two formats, XML and JSON. By default it will return JSON. If you wish to consume XML, pass the API the keypair format=xml. If you want JSONP, provide the keypair callback=myclbk.

Methods
-------

The API supports the following methods to receive Media Gallery data.  Note that each example must have authentication as described below.

**Retrieve Image**

  This API method allows several options to be embedded in the query.  In each case, to use the option, simply add it to the query before calculating the signature (see Authentication below for how to do that):

  * **height**: parameter name: "h", default=0, if greater than 0 it will resize the image to be no larger than the specified height in pixels, keeping the same aspect ratio.
  * **width**: parameter name: "w", default=0, if greater than 0 it will resize the image to be no wider than the specified height in pixels, keeping the same aspect ratio.  If both height and width are greater than 0, then a "best fit" resize will be made to fit the image inside the box defined by both sizes.
  * **watermark**: paremeter name: "watermark", default="false", options="both|footer|extended|false".  This controls whether which copyright watermarks are placed on the image.  "footer" causes an overlay over the bottom part of the image, "extended" causes the full copyright disclaimer to be embedded below the image.
  * **crop**: parameter name: "crop", options="true|false", default="false", if true it causes the resize to be cropped at the height and width specified instead of resizing the whole thing.
  * **upscale**: parameter name: "crop", options="true|false", default="false", if true it causes the resize to allow the image to be scaled larger than the original.

  Simple Example

    ``http://galleries.burningman.com/api/photos/scottlondon/scottlondon.41818/image?AUTHENTICATION``

  Simple Example Response

    *raw image data* at full size

  This data can be used as the target of an <img> tag, for example:

  ``<img src="http://galleries.burningman.com/api/photos/scottlondon/scottlondon.41818/image?AUTHENTICATION">``

  Resized Example

    ``http://galleries.burningman.com/api/photos/scottlondon/scottlondon.41818/image?AUTHENTICATION&h=400&w=400``

  Resized Example Response

    *raw image data* resized to fit in a 400x400 box

  Resized with a Watermark Example:

    ``http://galleries.burningman.com/api/photos/scottlondon/scottlondon.41818/image?AUTHENTICATION&h=600&watermark=extended``

  Resized with a Watermark Example Response

    *raw image data* resized to be no more than 600 pixels high, including copyright text at the bottom of the image.


**Retrieve Image Caption**

  Example

    ``http://galleries.burningman.com/api/photos/scottlondon/scottlondon.41818/caption?AUTHENTICATION``

  Example Response

    ``"The Man Under a Red Sky"``

**Retrieve Image Metadata as JSON**

  Example

      ``http://galleries.burningman.com/api/photos/scottlondon/scottlondon.41818/json?AUTHENTICATION``

  Example Response::

   {
    "date_taken": null,
    "image": "photos/scottlondon/41418.jpg",
    "year": 2010,
    "_state": null,
    "height": 1536,
    "in_press_gallery": false,
    "moderator_id": null,
    "full_image_available": false,
    "id": 2,
    "date_approved": null,
    "view_count": 40,
    "title": "The Man Under a Red Sky",
    "width": 1024,
    "legacy_id": null,
    "child_attrpath": null,
    "status": "submitted",
    "date_submitted": null,
    "mediabase_ptr_id": 2,
    "imagebase_ptr_id": 2,
    "date_added": "2011-03-31 10:15:45",
    "slug": "bruce.2",
    "_owner_cache": null,
    "notes": "",
    "caption": "The Man Under a Red Sky",
    "owner_id": 2
   }

Authentication
--------------

Authentication is done via a simple "signature", which is then appended to the querystring of the API url.  We'll go into more detail below, but here is the basic scheme:

#. Find the URL you want to sign.  For example, let's say you want to sign the url for ``http://galleries.burningman.com/photos/scottlondon/scottlondon.41818/?mediattype=photo#pastheader``
#. Strip off the domain name and any query arguments, so for this example we'd have ``/photos/scottlondon/scottlondon.41818/``
#. Add the url path argument for the specific API command you want.  For example, if we wanted the raw image, we'd append "/image/", ending up with ``/photos/scottlondon/scottlondon.41818/image/``
#. Add any API arguments or options to the querystring.  For example, if we wanted the image to be a max height of 600 pixels, the url to be signed would be ``/photos/scottlondon/scottlondon.41818/image?h=600``
#. Get your API key.  You must be authorized to use API functions, which you can do by using the contact page on http://playaevents.burningman.com, once approved, you can get the API key from your profile page at http://playaevents.burningman.com/accounts/profile/
#. Make a random "seed" for signing.  The easiest "seed" is to simply take the timestamp of today, expressed as seconds.  Anything at all will be fine, but there are two caveats.  First, the seed can't ever be reused, and second, it needs to be less than 40 characters.
#. Add your username to the querystring.  For example, if my username was "example", the url to be signed would be: ``/photos/scottlondon/scottlondon.41818/?h=600&user=example``
#. Make a signature by taking an MD5 of the url, your seed, and your key, in that order. (code examples below)
#. Add the seed and your signature to the url.  For example, if your seed was "1302229284" and your MD5 signature was "5de4fce4f3135424be0a63db8f3ef20c", your final url would look like this: ``/photos/scottlondon/scottlondon.41818/?h=600&user=example&seed=1302229284&sig=5de4fce4f3135424be0a63db8f3ef20c``
#. That's it. Call the url and if you are authorized, you'll get the image data. It will only work once for that seed and signature.

Authentication Code Examples
----------------------------

**Python**

Python example code::

    import hashlib
    import time
    import types
    import urllib
    import urlparse

    def _add_query_param(query, param, val):
        """Add a querystring parameter to the url"""

        last = '%s=%s' % (param, urllib.quote_plus(val))
        if query:
            return "%s&%s" % (query, last)
        else:
            return last

    def _remove_query_param(query, param):
        """Removes a query param, leaving the querystring in order"""
        parts = query.split('&')
        look = "%s=" % param
        for ix in range(len(parts)-1, -1, -1):
            if parts[ix].startswith(look):
                del parts[ix]

        return '&'.join(parts)

    def _replace_query_param(query, param, val):
        """Replaces a query param, leaving the querystring in order"""
        parts = query.split('&')
        look = "%s=" % param
        for ix in range(0, len(parts)):
            if parts[ix].startswith(look):
                parts[ix] = "%s=%s" % (param, urllib.quote_plus(val))
                break
        return '&'.join(parts)

    def sign_url(url, key, user=None, seed=None):
        """Sign an url.

        Args:
            url: An url to sign.  It can have query parameters which will be preserved.
                 If there is no "seed" provided as a keyword arg, it will look in the
                 query params for it before finally simply giving up and using the
                 current timestamp as the seed.

            key: a key to sign with

        Kwargs:
            user: a user to sign with
            seed: An explicit seed string to use for signing.

        Returns:
            The same url, with its signature added to the querystring.
        """
        origurl = url
        parsed = urlparse.urlsplit(url)
        query = parsed.query
        qs = parse_qs(query)


        if not seed:
            # first look at query
            if 'seed' in qs:
                seed = qs['seed']
                query = _remove_query_param(query,'seed')
            else:
                timestamp = datetime.datetime.now()
                timestamp = time.mktime(timestamp.timetuple())
                seed = str(int(timestamp))
                log.debug('sign_url: no seed, using timestamp %s', seed)

        if user is not None:
            if 'user' in qs:
                username = qs['user']
                if type(username) is types.ListType:
                    username = username[0]
                if username != user.username:
                    query = _replace_query_param(query, 'user', self.user.username)
        else:
            if 'user' in qs:
                query = _remove_query_param(query, 'user')

        url = urlparse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, query, parsed.fragment))

        processor = hashlib.md5(work)
        processor.update(seed)
        processor.update(key)
        sig = processor.hexdigest()
        query = _add_query_param(query, 'seed', seed)
        query = _add_query_param(query, 'sig', sig)

        url = urlparse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, query, parsed.fragment))
        return url

**PHP**

PHP Example code::

    /**
     * Sign an url for use by the Gallery API
     *
     * @param string $apiurl the url fragment to sign, it should not contain the scheme or server
     * @param string $key the user key
     * @param string $user the user name for the key
     * @param array $apiatts array of options with key=value
     * @param array $urlinfo the url of the originial gallery link as parsed by parse_url
     * @return string url
     */
    function gallery_sign_url($apiurl, $key, $user, &$apiatts, $urlinfo) {

      $apiurl = str_replace('//', '/', $apiurl);
      if (!empty($key) && !empty($user)) {
        $apiatts[] = 'user=' . $user;
        $apiurl .= '?' . implode('&',$apiatts);
        $seed = time();
        $n = rand(10e16, 10e20);
        $seed .= base_convert($n, 10, 36);
        $sig = md5($apiurl . $seed . $key);
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