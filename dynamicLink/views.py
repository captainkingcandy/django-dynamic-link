#!/usr/bin/python
# -*- coding:utf-8 -*-
# This Python file uses the following encoding: utf-8

__author__ = "Andreas Fritz - sources.e-blue.eu"
__copyright__ = "Copyright (c) " + "28.08.2010" + " Andreas Fritz"
__licence__ = """New BSD Licence"""

import os
from .presettings import DYNAMIC_LINK_URL_BASE_COMPONENT, TEXT_REQUEST_IS_EXPIRED, TEXT_REQUEST_DOES_NOT_EXIST, DYNAMIC_LINK_MEDIA
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render
from django.template import RequestContext
import mimetypes
from django.views.decorators.cache import cache_control
from django.utils.translation import ugettext_lazy as _
from .models import Download, IsExpiredError


def expired(key):
    expired_objects = Download.objects.filter(active=False)
    # check expired objects
    for obj in expired_objects:
        if key == obj.link_key:
            return obj


def active(key):
    active_objects = Download.objects.filter(active=True)
    # check active objects
    for obj in active_objects:
        if key == obj.link_key:
            return obj


def error(request, text=_(u'Sorry, your request is not available')):
    """returns the error page"""
    extra_context = {'message': text}
    template = 'dynamicLink/not_avallible.html'
    return render(
                 request, template,
                 extra_context
                 )


def site(request, offset):
    """process site requests"""
    offset = offset.split('-')  # turn offset to keylist
    obj = {'actives': [], 'expired': [], 'notexist': []}

    # Test if keys are valid
    for key in offset:
        if active(key):
            obj['actives'].append(active(key))
        elif expired(key):
            obj['expired'].append(expired(key))
        else:
            obj['notexist'].append(key)

    template = 'dynamicLink/provide.html'
    extra_context = {
                     'basepath': DYNAMIC_LINK_URL_BASE_COMPONENT,
                     'downloads': obj
                     }
    return render(
                 request,
                 template,
                 extra_context
                 )


def fetch(request, offset):
    """process link requests. make desissions for every single download link"""
    if active(offset):
        return provide(request, offset)
    elif expired(offset):
        return error(request, TEXT_REQUEST_IS_EXPIRED)
    else:
        return error(request, TEXT_REQUEST_DOES_NOT_EXIST)


@cache_control(private=True)
def provide(request, key):
    """
    Return a download without the rael path to the served file.
    The content will served by a stream.

    The file will read in byte code to a socket wich will be
    used in the response object. Headers in the response will
    set for the specific served content referable to its type.
    """
    # Read database

#     # This code runs only with python >= 2.6
#     stored_file_obj = Download.objects.get(link_key=key)
#     try:
#         # we use a model method to validate and
#         # deliver the path
#         filepath = stored_file_obj.get_path()
#     except IsExpiredError as e:
#         return error(request, e.value)

    # alternate code that also run in older python before 2.6
    stored_file_obj = Download.objects.get(link_key=key)
    try:
        # we use a model method to validate and
        # deliver the path
        filepath = stored_file_obj.get_path()
    except IsExpiredError:
        return error(request)

    # make file path suitable for different installations
    delimiter = DYNAMIC_LINK_MEDIA.strip('/').split('/')[-1]
    # now we use the objects get_paht() method to be sure
    # the object instance keep up to date.
    file_path = os.path.normpath(
        DYNAMIC_LINK_MEDIA + '/' + filepath.split(delimiter)[-1]
                                )

    # read file as binary
    try:
        fsocket = open(file_path, 'rb')  # garbage collector will deal with
        # not closed fsocket
    except IOError:
        stored_file_obj.active = False
        stored_file_obj.save()  # only raise the following once
        return HttpResponseNotFound(unicode(_(u'File not found!')))  # admin
        # will get informed by mail

#     # read file as binary
#     try:
#         f = open(file_path, 'rb')
#     except IOError:
#         stored_file_obj.active = False
#         stored_file_obj.save()  # only raise the following once
#         return HttpResponseNotFound(unicode(_(u'File not found!')))  # admin
#         # will get informed by mail
#     fsocket = f.read()
#     f.close()

    # get file parameters
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    # specify mimetype and encoding
    auto_mimetype, auto_encoding = mimetypes.guess_type(file_path)
    if not auto_mimetype:  # for unknown types use stream
        auto_mimetype = 'application/octet-stream'

    # response object
    response = HttpResponse(fsocket, content_type=auto_mimetype)  # object instance
    # with mimetype and file

    # set headers in the response object
    # a list of headers:
    # http://en.wikipedia.org/wiki/List_of_HTTP_header_fields
    # encode('utf-8') assuming you're running on a server with UTF-8 as
    # the file system encoding.
    response['Content-Disposition'] = 'attachment; filename=%s' \
            % file_name  # add correct filename

# for python2 put above " % file_name.encode('utf-8')"

    if auto_encoding and auto_encoding is not 'gzip':
        # set encoding but exclude gzip from encoding headers
        # GZip uses zlib, but on its own zlib produces content that's
        # improperly encoded for a browser seeing 'gzip' as the content
        # encoding.
        response['Content-Encoding'] = auto_encoding
    # set response file size for the browsers progress bar
    response['Content-Length'] = file_size

    return response
