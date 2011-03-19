# -*- coding: utf-8 -*-
"""Provides log utility methods, mostly useful for getting and instantiating a log easily.

:Authors:
    - Bruce Kroeze
"""
"""
New BSD License
===============
Copyright (c) 2008, Bruce Kroeze http://solidsitesolutions.com

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.
    * Neither the name of SolidSiteSolutions LLC, Zefamily LLC nor the names of its 
      contributors may be used to endorse or promote products derived from this 
      software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
__docformat__="restructuredtext"


import os, os.path, logging, logging.config, logging.handlers

DEBUG=logging.DEBUG
INFO=logging.INFO
WARN=logging.WARN

_ROOT = None
_ONCE = {}

def getLogger(target, ini = None, streaming = True, level = logging.DEBUG, 
    outfile = None, format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    rotation_count = 0, rotation_max=0):
    """Returns the requested logger, loading the base config from the spec'd
    ini file if not already loaded.

    Note that there can be several nominees for an inifile by delimiting with
    a semicolon.
    
    If no root, and no configfile is found, then load from the kwargs:
    
    streaming - true if errors should print to the console
    level - default log level
    format - output format
    outfile - output filename (Format with a leading "/" for an absolute path, else relative to the current working dir, format like so for RotatingFileHandler fname:maxsize:maxcount)
    rotation_ct - number of rotations to keep, 0 disables
    rotation_max - megabytes per rotating file
    """

    global _ROOT

    if _ROOT is None:
        if ini:
            for inifile in ini.split(";"):
                inifile = resolve_path(inifile)
                if os.path.exists(inifile):
                    logging.config.fileConfig(inifile)
                    _ROOT = logging.root
                    _ROOT.debug("loaded from %s", inifile)
                    
    if _ROOT is None:
        
        if isinstance(level, dict):
            levels = level
            level = levels.pop('root', logging.DEBUG)
        else:
            levels = {}
                
        _ROOT = logging.root
        _ROOT.setLevel(level)
        formatter = logging.Formatter(format)
        
        if streaming:
            streamout = logging.StreamHandler()
            streamout.setLevel(level)
            streamout.setFormatter(formatter)
            maybe_add_handler(_ROOT, streamout)
            
        if outfile:
            if rotation_count > 0:
                fileout = logging.handlers.RotatingFileHandler(
                    outfile, 
                    maxBytes=rotation_max*1024*1024, 
                    backupCount=rotation_count)
            else:
                fileout = logging.FileHandler(outfile)
                
            fileout.setLevel(level)
            fileout.setFormatter(formatter)
            maybe_add_handler(_ROOT, fileout)

        for key in levels:
            l = getLogger(key)
            l.setLevel(levels[key])
            
        _ROOT.debug("loaded config")

    return logging.getLogger(target)

def maybe_add_handler(logger, handler):
    ok = True
    hc = handler.__class__
    for h in logger.handlers:
        if h.__class__ == hc:
            ok = False
            break
    if ok:
        logger.addHandler(handler)

def resolve_path(fname):
    """Expands all environment variables and tildes, returning the absolute path."""
    fname = os.path.expandvars(fname)
    fname = os.path.expanduser(fname)
    if fname.startswith("./"):
        fname = "%s%s" % (os.getcwd(), fname[1:])
    return os.path.abspath(fname)

def warn_once(logger, key, *args):
    global _ONCE
    if not _ONCE.get(key, False):
        _ONCE[key] = True
        logger.warn(*args)
