#!/usr/bin/python
# -*- coding:utf-8 -*-
# This Python file uses the following encoding: utf-8

__author__ = "Andreas Fritz - sources.e-blue.eu"
__copyright__ = "Copyright (c) " + "28.08.2010" + " Andreas Fritz"
__licence__ = """New BSD Licence"""

from django.contrib import admin
from .models import Download
from django.utils.translation import ugettext_lazy as _
from .api import DownloadSiteUrl, file_link_url 
from .presettings import DYNAMIC_LINK_MEDIA 


class DownLinkAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        """catch the request object for list pages"""
        self.request = request
        return super(DownLinkAdmin, self).get_queryset(request)

    list_display = ('slug', 'active', 'file', 'valid', 'clicks',
                    'timestamp_creation', 'link')
    actions = ['make_link']
    search_fields = ['slug', 'file_path', 'timestamp_creation', 'link_key']
    list_per_page = 50
    fieldsets = (
                 (_(u'Link'), {
                 'fields': ('slug', 'file_path')
                 }),
                 (_(u'Additional values'), {
                 'classes': ('collapse',),
                 'fields': ('active', 'current_clicks', 'timeout_hours',
                            'max_clicks')
                 }),
                 )

    def valid(self, obj):
        """Shows time stamp expired or active time"""
        diff = str(obj.get_timout_time()).split('.')[0]
        if obj.timeout_time():
            if obj.active:
                # set active to false
                obj.active = False
                obj.save()
            return '<span style="color: #FF7F00; ">%s</span>:<br/> ' \
            % (str(_(u'timeout'))) + diff
        else:
            return diff
    valid.allow_tags = True
    valid.short_description = _(u'valid')

    def file(self, obj):
        """Shows truncated filename on platform independent length."""
        return str(obj.file_path).split(DYNAMIC_LINK_MEDIA)[-1]
    file.allow_tags = True
    file.short_description = _(u'file')

    def clicks(self, obj):
        """Shows current and max allowed clicks in the list display"""
        txt = '%s %s %s' % (obj.current_clicks, str(_(u'from')),
                            obj.max_clicks)
        if obj.timeout_clicks():
            if obj.active == True:
                # set active to false
                obj.active = False
                obj.save()
            return '<span style="color: #FF7F00; ">%s</span><br/>%s' \
            % (str(_('max clicks reached')), txt)
        elif obj.max_clicks == 0:
            return '%s %s <span style="color: #FF7F00; ">%s</span>' \
            % (obj.current_clicks, str(_(u'from')),
               str(_(u'unlimited')))
        else:
            return txt
    clicks.allow_tags = True
    clicks.short_description = _(u'clicks')

    def link(self, obj):
        """Generate site and download url from link object"""

        # download site with link
        siteurl = DownloadSiteUrl([obj.link_key])
        sitelink = siteurl.get_site_url(self.request)
        sitelink = u'<span style="color: #FF7F00; ">%s:</span> \
        <a target="new" href="%s/">%s/</a><br/>' \
        % (str(_(u'Site')), sitelink, sitelink)

        # direct accessable link
        filelink = file_link_url(self.request, obj)
        filelink = '<span style="color: #FF7F00; ">%s:</span> %s' \
        % (str(_(u'File')), filelink)

        return sitelink + filelink
    link.allow_tags = True
    link.short_description = _(u'link')

    def make_link(modeladmin, request, queryset):
        """Action method. Make site url from many singles objects."""
        li = []
        for obj in queryset:
            li.append(obj.link_key)
        siteurl = DownloadSiteUrl(li)
        sitelink = siteurl.get_site_url(request)
        # response
        from django.http import HttpResponse
        return HttpResponse('<a target="new" href="%s/">%s/</a><br/>' \
                            % (sitelink, sitelink))
    make_link.short_description = _("Make from selected a download site link")

admin.site.register(Download, DownLinkAdmin)
