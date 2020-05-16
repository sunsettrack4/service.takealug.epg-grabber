# -*- coding: utf-8 -*-
import xbmc
import xbmcaddon
import xbmcvfs
import xbmcgui
import time
from datetime import datetime#
import os
import json
import re
import socket
from collections import Counter
from resources.lib import xml_structure
from resources.providers import magenta_DE
from resources.providers import tvspielfilm_DE
from resources.providers import swisscom_CH
from resources.providers import horizon
import sys

## Python 3 Compatibility
if sys.version_info[0] > 2:
    # python 3
    pass
else:
    # python 2
    reload(sys)
    sys.setdefaultencoding('utf-8')

ADDON = xbmcaddon.Addon(id="service.takealug.epg-grabber")
addon_name = ADDON.getAddonInfo('name')
addon_version = ADDON.getAddonInfo('version')
loc = ADDON.getLocalizedString
datapath = xbmc.translatePath(ADDON.getAddonInfo('profile'))
temppath = os.path.join(datapath, "temp")
thread_temppath = os.path.join(temppath, "multithread")

## Read Global Settings
storage_path = ADDON.getSetting('storage_path')
auto_download = True if ADDON.getSetting('auto_download').lower() == 'true' else False
timeswitch_1 = int(ADDON.getSetting('timeswitch_1'))
timeswitch_2 = int(ADDON.getSetting('timeswitch_2'))
timeswitch_3 = int(ADDON.getSetting('timeswitch_3'))
enable_rating_mapper = True if ADDON.getSetting('enable_rating_mapper').upper() == 'TRUE' else False
use_local_sock = True if ADDON.getSetting('use_local_sock').upper() == 'TRUE' else False
tvh_local_sock = ADDON.getSetting('tvh_local_sock')
download_threads = int(ADDON.getSetting('download_threads'))
enable_multithread = True if ADDON.getSetting('enable_multithread').upper() == 'TRUE' else False

## Get Enabled Grabbers
enable_grabber_magentaDE = True if ADDON.getSetting('enable_grabber_magentaDE').upper() == 'TRUE' else False
enable_grabber_tvsDE = True if ADDON.getSetting('enable_grabber_tvsDE').upper() == 'TRUE' else False
enable_grabber_swcCH = True if ADDON.getSetting('enable_grabber_swcCH').upper() == 'TRUE' else False
enable_grabber_hznDE = True if ADDON.getSetting('enable_grabber_hznDE').upper() == 'TRUE' else False
enable_grabber_hznAT = True if ADDON.getSetting('enable_grabber_hznAT').upper() == 'TRUE' else False
enable_grabber_hznCH = True if ADDON.getSetting('enable_grabber_hznCH').upper() == 'TRUE' else False
enable_grabber_hznNL = True if ADDON.getSetting('enable_grabber_hznNL').upper() == 'TRUE' else False
enable_grabber_hznPL = True if ADDON.getSetting('enable_grabber_hznPL').upper() == 'TRUE' else False
enable_grabber_hznIE = True if ADDON.getSetting('enable_grabber_hznIE').upper() == 'TRUE' else False
enable_grabber_hznGB = True if ADDON.getSetting('enable_grabber_hznGB').upper() == 'TRUE' else False
enable_grabber_hznSK = True if ADDON.getSetting('enable_grabber_hznSK').upper() == 'TRUE' else False
enable_grabber_hznCZ = True if ADDON.getSetting('enable_grabber_hznCZ').upper() == 'TRUE' else False
enable_grabber_hznHU = True if ADDON.getSetting('enable_grabber_hznHU').upper() == 'TRUE' else False
enable_grabber_hznRO = True if ADDON.getSetting('enable_grabber_hznRO').upper() == 'TRUE' else False

# Check if any Grabber is enabled
if (enable_grabber_magentaDE or enable_grabber_tvsDE or enable_grabber_swcCH or enable_grabber_hznDE or enable_grabber_hznAT or enable_grabber_hznCH or enable_grabber_hznNL or enable_grabber_hznPL or enable_grabber_hznIE or enable_grabber_hznGB or enable_grabber_hznSK or enable_grabber_hznCZ or enable_grabber_hznHU or enable_grabber_hznRO):
    enabled_grabber = True
else:
    enabled_grabber = False

guide_temp = os.path.join(datapath, 'guide.xml')
guide_dest = os.path.join(storage_path, 'guide.xml')
grabber_cron = os.path.join(datapath, 'grabber_cron.json')
grabber_cron_tmp = os.path.join(temppath, 'grabber_cron.json')

## Make a debug logger
def log(message, loglevel=xbmc.LOGDEBUG):
    xbmc.log('[{} {}] {}'.format(addon_name, addon_version, message), loglevel)

## Make OSD Notify Messages
OSD = xbmcgui.Dialog()

## MAKE an Monitor
Monitor = xbmc.Monitor()

def notify(title, message, icon=xbmcgui.NOTIFICATION_INFO):
    OSD.notification(title, message, icon)

def copy_guide_to_destination():
    done = xbmcvfs.copy(guide_temp, guide_dest)
    if done:
        ## Write new setting last_download
        with open(grabber_cron, 'r') as f:
            data = json.load(f)
            data['last_download'] = str(int(time.time()))

        with open(grabber_cron_tmp, 'w') as f:
            json.dump(data, f, indent=4)
        ## rename temporary file replacing old file
        xbmcvfs.copy(grabber_cron_tmp, grabber_cron)
        xbmcvfs.delete(grabber_cron_tmp)
        f.close()
        xbmc.sleep(3000)
        notify(addon_name, loc(32350), icon=xbmcgui.NOTIFICATION_INFO)
        log(loc(32350), xbmc.LOGNOTICE)

    else:
        notify(addon_name, loc(32351), icon=xbmcgui.NOTIFICATION_ERROR)
        log(loc(32351), xbmc.LOGERROR)

def check_channel_dupes():
    with open(guide_temp) as f:
        c = Counter(c.strip().lower() for c in f if c.strip())  # for case-insensitive search
        dupe = []
        for line in c:
            if c[line] > 1:
                if ('display-name' in line or 'icon src' in line or '</channel' in line):
                    pass
                else:
                    dupe.append(line + '\n')
        dupes = ''.join(dupe)

        if (not dupes == ''):
            log('{} {}'.format(loc(32400),dupes), xbmc.LOGERROR)
            dialog = xbmcgui.Dialog()
            ok = dialog.ok('-]ERROR[- {}'.format(loc(32400)), dupes)
            if ok:
                exit()

def run_grabber():
    check_startup()
    xml_structure.xml_start()
    ## Check Provider , Create XML Channels
    if enable_grabber_magentaDE:
        magenta_DE.startup()
        magenta_DE.create_xml_channels()
    if enable_grabber_tvsDE:
        tvspielfilm_DE.startup()
        tvspielfilm_DE.create_xml_channels()
    if enable_grabber_swcCH:
        swisscom_CH.startup()
        swisscom_CH.create_xml_channels()
    if enable_grabber_hznDE:
        horizon.startup('de')
        horizon.create_xml_channels('de')
    if enable_grabber_hznAT:
        horizon.startup('at')
        horizon.create_xml_channels('at')
    if enable_grabber_hznCH:
        horizon.startup('ch')
        horizon.create_xml_channels('ch')
    if enable_grabber_hznNL:
        horizon.startup('nl')
        horizon.create_xml_channels('nl')
    if enable_grabber_hznPL:
        horizon.startup('pl')
        horizon.create_xml_channels('pl')
    if enable_grabber_hznIE:
        horizon.startup('ie')
        horizon.create_xml_channels('ie')
    if enable_grabber_hznGB:
        horizon.startup('gb')
        horizon.create_xml_channels('gb')
    if enable_grabber_hznSK:
        horizon.startup('sk')
        horizon.create_xml_channels('sk')
    if enable_grabber_hznCZ:
        horizon.startup('cz')
        horizon.create_xml_channels('cz')
    if enable_grabber_hznHU:
        horizon.startup('hu')
        horizon.create_xml_channels('hu')
    if enable_grabber_hznRO:
        horizon.startup('ro')
        horizon.create_xml_channels('ro')

    # Check for Channel Dupes
    check_channel_dupes()

    ## Create XML Broadcast
    if enable_grabber_magentaDE:
        magenta_DE.create_xml_broadcast(enable_rating_mapper, thread_temppath, download_threads)
    if enable_grabber_tvsDE:
        tvspielfilm_DE.create_xml_broadcast(enable_rating_mapper, thread_temppath, download_threads)
    if enable_grabber_swcCH:
        swisscom_CH.create_xml_broadcast(enable_rating_mapper, thread_temppath, download_threads)
    if enable_grabber_hznDE:
        horizon.create_xml_broadcast('de', enable_rating_mapper, thread_temppath, download_threads)
    if enable_grabber_hznAT:
        horizon.create_xml_broadcast('at', enable_rating_mapper, thread_temppath, download_threads)
    if enable_grabber_hznCH:
        horizon.create_xml_broadcast('ch', enable_rating_mapper, thread_temppath, download_threads)
    if enable_grabber_hznNL:
        horizon.create_xml_broadcast('nl', enable_rating_mapper, thread_temppath, download_threads)
    if enable_grabber_hznPL:
        horizon.create_xml_broadcast('pl', enable_rating_mapper, thread_temppath, download_threads)
    if enable_grabber_hznIE:
        horizon.create_xml_broadcast('ie', enable_rating_mapper, thread_temppath, download_threads)
    if enable_grabber_hznGB:
        horizon.create_xml_broadcast('gb', enable_rating_mapper, thread_temppath, download_threads)
    if enable_grabber_hznSK:
        horizon.create_xml_broadcast('sk', enable_rating_mapper, thread_temppath, download_threads)
    if enable_grabber_hznCZ:
        horizon.create_xml_broadcast('cz', enable_rating_mapper, thread_temppath, download_threads)
    if enable_grabber_hznHU:
        horizon.create_xml_broadcast('hu', enable_rating_mapper, thread_temppath, download_threads)
    if enable_grabber_hznRO:
        horizon.create_xml_broadcast('ro', enable_rating_mapper, thread_temppath, download_threads)

    ## Finish XML
    xml_structure.xml_end()
    copy_guide_to_destination()

    ## Write Guide in TVH Socked
    if use_local_sock:
        write_to_sock()

def write_to_sock():
    if check_startup():
        if (use_local_sock and os.path.isfile(guide_temp)):
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            epg = open(guide_temp, 'rb')
            epg_data = epg.read()
            try:
                log('{} {}'.format(loc(32380), tvh_local_sock), xbmc.LOGNOTICE)
                notify(addon_name, loc(32380), icon=xbmcgui.NOTIFICATION_INFO)
                sock.connect(tvh_local_sock)
                sock.send(epg_data)
                log('{} {}'.format(sock.recv, tvh_local_sock), xbmc.LOGNOTICE)
            except socket.error as e:
                notify(addon_name, loc(32379), icon=xbmcgui.NOTIFICATION_ERROR)
                log('{} {}'.format(loc(32379), e), xbmc.LOGERROR)
            finally:
                sock.close()
        else:
            ok = dialog.ok(loc(32119), loc(32409))
            if ok:
                log(loc(32409), xbmc.LOGERROR)

def worker():
    initiate_download = False

    ## Read Settings for last / next_download
    with open(grabber_cron, 'r') as j:
        cron = json.load(j)
        next_download = int(cron['next_download'])
        last_download = int(cron['last_download'])
    j.close()

    log('{} {}'.format(loc(32352), datetime.fromtimestamp(last_download).strftime('%d.%m.%Y %H:%M')), xbmc.LOGDEBUG)

    if (int(next_download) > int(last_download)):
        log('{} {}'.format(loc(32353), datetime.fromtimestamp(next_download).strftime('%d.%m.%Y %H:%M')), xbmc.LOGDEBUG)

    if next_download < int(time.time()):
        # suggested download time has passed (e.g. system was offline) or time is now, download epg
        # and set a new timestamp for the next download
        log('{} {}'.format(loc(32352), datetime.fromtimestamp(last_download).strftime('%d.%m.%Y %H:%M')), xbmc.LOGNOTICE)
        log('{} {}'.format(loc(32353), datetime.fromtimestamp(next_download).strftime('%d.%m.%Y %H:%M')), xbmc.LOGNOTICE)
        log('{}'.format(loc(32356)), xbmc.LOGNOTICE)
        initiate_download = True

    ## If next_download < last_download, initiate an Autodownload
    if initiate_download:
        notify(addon_name, loc(32357), icon=xbmcgui.NOTIFICATION_INFO)
        run_grabber()

    ## Calculate the next_download Setting

    # get Settings for daily_1, daily_2, daily_3
    today = datetime.today()
    now = int(time.time())
    calc_daily_1 = datetime(today.year, today.month, day=today.day, hour=timeswitch_1, minute=0, second=0)
    calc_daily_2 = datetime(today.year, today.month, day=today.day, hour=timeswitch_2, minute=0, second=0)
    calc_daily_3 = datetime(today.year, today.month, day=today.day, hour=timeswitch_3, minute=0, second=0)

    try:
        daily_1 = int(calc_daily_1.strftime("%s"))
        daily_2 = int(calc_daily_2.strftime("%s"))
        daily_3 = int(calc_daily_3.strftime("%s"))
    except ValueError:
        daily_1 = int(time.mktime(calc_daily_1.timetuple()))
        daily_2 = int(time.mktime(calc_daily_2.timetuple()))
        daily_3 = int(time.mktime(calc_daily_3.timetuple()))

    ## If sheduleplan for daily 1,2,3 is in the past, plan it for next day
    if daily_1 <= now:
        daily_1 += int(86400)
    if daily_2 <= now:
        daily_2 += int(86400)
    if daily_3 <= now:
        daily_3 += int(86400)

    ## Find the lowest Integer for next download
    next_download = min([int(daily_1), int(daily_2), int(daily_3)])

    ## Write new setting next_download
    with open(grabber_cron, 'r') as f:
        data = json.load(f)
        data['next_download'] = str(int(next_download))

    with open(grabber_cron_tmp, 'w') as f:
        json.dump(data, f, indent=4)
    ## rename temporary file replacing old file
    xbmcvfs.copy(grabber_cron_tmp, grabber_cron)
    xbmcvfs.delete(grabber_cron_tmp)
    f.close()

def check_startup():
    #Create Tempfolder if not exist
    if not os.path.exists(temppath):
        os.makedirs(temppath)
    if not os.path.exists(thread_temppath):
        os.makedirs(thread_temppath)

    if storage_path == 'choose':
        notify(addon_name, loc(32359), icon=xbmcgui.NOTIFICATION_ERROR)
        log(loc(32359), xbmc.LOGERROR)
        return False

    if not enabled_grabber:
        notify(addon_name, loc(32360), icon=xbmcgui.NOTIFICATION_ERROR)
        log(loc(32360), xbmc.LOGERROR)
        return False

    if use_local_sock:
        socked_string = '.sock'
        if not re.search(socked_string, tvh_local_sock):
            notify(addon_name, loc(32378), icon=xbmcgui.NOTIFICATION_ERROR)
            log(loc(32378), xbmc.LOGERROR)
            return False

    ## create Crontab File which not exists at first time
    if (not os.path.isfile(grabber_cron)):
        with open(grabber_cron, 'w') as downloads:
            downloads.write(json.dumps({}))
            downloads.close()

        # Write Setting last_download and next_download which not exist first Time
        with open(grabber_cron, 'r') as f:
            data = json.load(f)
            if 'last_download' not in data:
                data['last_download'] = str(int(time.time()))
            ## Push next_download to tomorrow (prevent instant grabbing if auto_download = true)
            if 'next_download' not in data:
                data['next_download'] = str(int(time.time() + int(86400)))

            with open(grabber_cron_tmp, 'w') as f:
                json.dump(data, f, indent=4)
            ## rename temporary file replacing old file
            xbmcvfs.copy(grabber_cron_tmp, grabber_cron)
            xbmcvfs.delete(grabber_cron_tmp)
            f.close()

    ## Clean Tempfiles
    for file in os.listdir(temppath):
        xbmcvfs.delete(os.path.join(temppath, file))
    return True

if check_startup():
    try:
        dialog = xbmcgui.Dialog()
        if sys.argv[1] == 'manual_download':
            ret = dialog.yesno('Takealug EPG Grabber', loc(32401))
            if ret:
                manual = True
                notify(addon_name, loc(32376), icon=xbmcgui.NOTIFICATION_INFO)
                run_grabber()
        if sys.argv[1] == 'write_to_sock':
            ret = dialog.yesno(loc(32119), loc(32408))
            if ret:
                write_to_sock()
    except IndexError:
        pass

    while not Monitor.waitForAbort(60):
        if auto_download:
            worker()
