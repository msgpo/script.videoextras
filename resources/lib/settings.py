# -*- coding: utf-8 -*-
import xbmc
import xbmcaddon
import os

__addon__     = xbmcaddon.Addon(id='script.videoextras')
__addonid__   = __addon__.getAddonInfo('id')


# Common logging module
def log(txt):
    if __addon__.getSetting( "logEnabled" ) == "true":
        if isinstance (txt,str):
            txt = txt.decode("utf-8")
        message = u'%s: %s' % (__addonid__, txt)
        xbmc.log(msg=message.encode("utf-8"), level=xbmc.LOGDEBUG)


# There has been problems with calling join with non ascii characters,
# so we have this method to try and do the conversion for us
def os_path_join( dir, file ):
    # Convert each argument - if an error, then it will use the default value
    # that was passed in
    try:
        dir = dir.decode("utf-8")
    except:
        pass
    try:
        file = file.decode("utf-8")
    except:
        pass
    return os.path.join(dir, file)

# Splits a path the same way as os.path.split but supports paths of a different
# OS than that being run on
def os_path_split( fullpath ):
    
    # Check if it ends in a slash
    if fullpath.endswith("/") or fullpath.endswith("\\"):
        # Remove the slash character
        fullpath = fullpath[:-1]

    if "/" in fullpath:
        return fullpath.rsplit("/", 1)
    
    return fullpath.rsplit("\\", 1)

##############################
# Stores Various Settings
##############################
class Settings():
    @staticmethod
    def getExcludeFiles():
        return __addon__.getSetting( "excludeFiles" )

    @staticmethod
    def getExtrasDirName():
        return __addon__.getSetting( "extrasDirName" )

    @staticmethod
    def getExtrasFileTag():
        if  __addon__.getSetting( "enableFileTag" ) != "true":
            return ""
        return __addon__.getSetting( "extrasFileTag" )

    @staticmethod
    def isSearchNested():
        return __addon__.getSetting( "searchNested" ) == "true"

    @staticmethod
    def isDetailedListScreen():
        return __addon__.getSetting( "detailedList" ) == "true"

    @staticmethod
    def isMenuReturnVideoSelection():
        settingsSelect = "extrasReturn"
        if Settings.isDetailedListScreen():
            settingsSelect = "detailedReturn"
        return __addon__.getSetting( settingsSelect ) == __addon__.getLocalizedString(32007)

    @staticmethod
    def isMenuReturnHome():
        settingsSelect = "extrasReturn"
        if Settings.isDetailedListScreen():
            settingsSelect = "detailedReturn"
        return __addon__.getSetting( settingsSelect ) == __addon__.getLocalizedString(32009)

    @staticmethod
    def isMenuReturnInformation():
        settingsSelect = "extrasReturn"
        if Settings.isDetailedListScreen():
            settingsSelect = "detailedReturn"
        return __addon__.getSetting( settingsSelect ) == __addon__.getLocalizedString(32008)

    @staticmethod
    def isMenuReturnExtras():
        if Settings.isDetailedListScreen():
            return False
        return __addon__.getSetting( "extrasReturn" ) == __addon__.getLocalizedString(32001)

    @staticmethod
    def isForceButtonDisplay():
        return __addon__.getSetting( "forceButtonDisplay" ) == "true"

    @staticmethod
    def isServiceEnabled():
        return __addon__.getSetting( "serviceEnabled" ) == "true"

    @staticmethod
    def getAddonVersion():
        return __addon__.getAddonInfo('version')

    @staticmethod
    def isDatabaseEnabled():
        return __addon__.getSetting( "enableDB" ) == "true"

    @staticmethod
    def isCustomPathEnabled():
        return __addon__.getSetting("custom_path_enable") == 'true'
    
    @staticmethod
    def getCustomPath():
        if Settings.isCustomPathEnabled():
            return __addon__.getSetting("custom_path")
        else:
            return None

    @staticmethod
    def getCustomPathMoviesDir():
        if Settings.isCustomPathEnabled():
            return __addon__.getSetting("custom_path_movies")
        else:
            return ""

    @staticmethod
    def getCustomPathTvShowsDir():
        if Settings.isCustomPathEnabled():
            return __addon__.getSetting("custom_path_tvshows")
        else:
            return ""
