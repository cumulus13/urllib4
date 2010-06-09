#!/usr/bin/env python
from __future__ import with_statement

import sys, os, os.path
from datetime import datetime, timedelta
import logging

try:
    from gurl import Url as urlparse
except ImportError:
    from urlparse import urlparse

import urllib4

DEFAULT_LOG_LEVEL = logging.WARN
DEFAULT_LOG_FORMAT = '%(asctime)s %(levelname)s [%(process)d:%(thread)d] %(module)s.%(name)s: %(message)s'

PROGRESS_BAR_LENGTH = 40

def parse_cmdline():
    from optparse import OptionParser
    
    parser = OptionParser("Usage: %prog [options] <url> ...")
    
    parser.add_option('-v', '--verbose', action='store_const',
                      const=logging.INFO, dest='log_level', default=DEFAULT_LOG_LEVEL,
                      help='Show the verbose information')
    parser.add_option('-d', '--debug', action='store_const',
                      const=logging.DEBUG, dest='log_level',
                      help='Show the debug information')    
    parser.add_option('--log-format', dest='log_format',
                      metavar='FMT', default=DEFAULT_LOG_FORMAT,
                      help='Format to output the log')
    parser.add_option('--log-file', dest='log_file', metavar='FILE',
                      help='File to write log to. Default is `stdout`.')
    
    opts, args = parser.parse_args()

    logging.basicConfig(level=opts.log_level,
                        format=opts.log_format,
                        filename=opts.log_file,
                        stream=sys.stdout)
    
    return opts, args

def size_pretty(size):
    KB = 1024
    MB = KB * 1024
    GB = MB * 1024
    
    if size > GB:
        return "%.1fG" % (size / GB)
    if size > MB:
        return "%.1fM" % (size / MB)
    if size > KB:
        return "%.1fK" % (size / KB)
    
    return "%dB" % int(size)
    
def timedelta_prettry(delta):
    MINUTE = 60
    HOUR = MINUTE * 60    
    
    s = ""
    
    if delta.days > 0:
        s += '%d d' % delta.days
        
    if delta.seconds > HOUR:
        s += '%d h' % (delta.seconds / HOUR)
        
    if (delta.seconds % HOUR) > MINUTE:
        s += '%d h' % (delta.seconds / MINUTE)
        
    s += '%d s' % (delta.seconds % MINUTE)
    
    return s
        
def update_status(str):
    if sys.platform == 'win32':
        import win32console 
        
        buf = win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE)
        pos = buf.GetConsoleScreenBufferInfo()['CursorPosition']
        size = buf.GetConsoleScreenBufferInfo()['MaximumWindowSize']        
        buf.SetConsoleCursorPosition(win32console.PyCOORDType(0, pos.Y))
        buf.WriteConsole(str+' '*(size.X-len(str)-1))
    else:
        print str

if __name__ == '__main__':
    opts, args = parse_cmdline()

    c = urllib4.HttpClient();
    
    for url in args:
        print "--%s-- %s" % (datetime.now(), url)
        
        o = urlparse(url)
        
        filename = os.path.basename(o.path)
        
        print "HTTP request sent, awaiting response...",
        
        download_records = []
                
        def onprogress(download_total, downloaded, upload_total, uploaded):
            if download_total > 0:            
                if len(download_records) == 0:
                    print c.status
                    print "Length: %d (%s) [%s]" % (int(download_total), size_pretty(download_total), c.headers.get('Content-Type'))
                    
                    print "Saving to: `%s`" % filename
                    print
                
                download_records.append([datetime.now(), downloaded])
                
                download_percent = downloaded/download_total if download_total else 0
                download_progress = '='*int(download_percent * PROGRESS_BAR_LENGTH)
                
                if len(download_progress) < PROGRESS_BAR_LENGTH:
                    download_progress += '>'
                    download_progress += ' '*(PROGRESS_BAR_LENGTH-len(download_progress))
                
                download_status = "%3d%% [%s] %-10d" % (download_percent*100, download_progress, downloaded)
                
                download_time = (datetime.now() - download_records[0][0]).seconds
                
                if download_time > 0:
                    download_speed = downloaded/download_time
                    download_expect = timedelta(seconds=(download_total - downloaded) / download_speed)
                    
                    download_status += " %s/s eta %s" % (size_pretty(download_speed), timedelta_prettry(download_expect))
                
                update_status(download_status)
                
            return urllib4.PROGRESS_CALLBACK_CONTINUE
                    
        with open(filename, 'wb') as f:
            c.download(url, f, progress_callback=onprogress)