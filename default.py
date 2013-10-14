# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with XBMC; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
import sys
import os
import re
import random
#Modules XBMC
import xbmcplugin
import xbmc
import xbmcgui
import xbmcvfs
import xbmcaddon

# Add JSON support for queries
if sys.version_info < (2, 7):
    import simplejson
else:
    import json as simplejson

__addon__     = xbmcaddon.Addon(id='script.videoextras')
__addonid__   = __addon__.getAddonInfo('id')

def log(txt):
    if __addon__.getSetting( "logEnabled" ) == "true":
        if isinstance (txt,str):
            txt = txt.decode("utf-8")
            message = u'%s: %s' % (__addonid__, txt)
            xbmc.log(msg=message.encode("utf-8"), level=xbmc.LOGDEBUG)

path = __addon__.getAddonInfo('path').decode("utf-8")
log("Path: " + path)

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
        return __addon__.getSetting( "extrasFileTag" )

    @staticmethod
    def isSearchNested():
        return __addon__.getSetting( "searchNested" ) == "true"

    @staticmethod
    def isMenuReturnVideoSelection():
        return __addon__.getSetting( "extrasReturn" ) == "Video Selection"

    @staticmethod
    def isMenuReturnHome():
        return __addon__.getSetting( "extrasReturn" ) == "Home"

    @staticmethod
    def isMenuReturnInformation():
        return __addon__.getSetting( "extrasReturn" ) == "Information"


########################################################
# Class to store all the details for a given extras file
########################################################
class ExtrasItem():
    def __init__( self, filename ):
        self.filename = filename
        # Get the ordering and display details
        (self.orderKey, self.displayName) = self._generateOrderAndDisplay(filename)

    # eq and lt defined for sorting order only
    def __eq__(self, other):
        # Check key, display then filename - all need to be the same for equals
        return ((self.orderKey, self.displayName, self.filename) ==
                (other.orderKey, other.displayName, other.filename))

    def __lt__(self, other):
        # Order in key, display then filename 
        return ((self.orderKey, self.displayName, self.filename) <
                (other.orderKey, other.displayName, other.filename))

    # Returns the name to display to the user for the file
    def getDisplayName(self):
        return self.displayName.replace(".sample","").replace("&#58;", ":")

    # Return the filename for the extra
    def getFilename(self):
        return self.filename


    def _generateOrderAndDisplay(self, filename):
        # First thing is to trim the display name from the filename
        # Get just the filename, don't need the full path
        displayName = os.path.split(filename)[1]
        # Remove the file extension (e.g .avi)
        displayName = os.path.splitext( displayName )[0]
        # Remove anything before the -extras- tag (if it exists)
        extrasTag = Settings.getExtrasFileTag()
        if (extrasTag != "") and (extrasTag in displayName):
            justDescription = displayName.split(extrasTag,1)[1]
            if len(justDescription) > 0:
                displayName = justDescription
        
        result = ( displayName, displayName )
        # Search for the order which will be written as [n]
        # Followed by the display name
        match = re.search("^\[(?P<order>.+)\](?P<Display>.*)", displayName)
        if match:
            orderKey = match.group('order')
            if orderKey != "":
                result = ( orderKey, match.group('Display') )
        return result


####################################################
# Class to control displaying and playing the extras
####################################################
class VideoExtrasWindow(xbmcgui.Window):
    def showList(self, exList):
        # Get the list of display names
        displayNameList = []
        for anExtra in exList:
            log("adding: " + anExtra.getDisplayName() + " filename: " + anExtra.getFilename())
            displayNameList.append(anExtra.getDisplayName())

        addPlayAll = (len(exList) > 1)
        if addPlayAll:
            displayNameList.insert(0, "Play All" )

        # Show the list to the user
        select = xbmcgui.Dialog().select('Extras', displayNameList)
        
        infoDialogId = xbmcgui.getCurrentWindowDialogId();
        # USer has made a selection, -1 is exit
        if select != -1:
            xbmc.executebuiltin("Dialog.Close(all, true)", True)
            extrasPlayer = xbmc.Player();
            waitLoop = 0
            while extrasPlayer.isPlaying() and waitLoop < 10:
                xbmc.sleep(100)
                waitLoop = waitLoop + 1
            extrasPlayer.stop()
            # Give anything that was already playing time to stop
            while extrasPlayer.isPlaying():
                xbmc.sleep(100)
            if select == 0 and addPlayAll == True:
                playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
                playlist.clear()
                for item in exList:
                    log( "Start playing " + item.getFilename() )
                    playlist.add( item.getFilename() )
                extrasPlayer.play( playlist )
            else:
                itemToPlay = select
                # If we added the PlayAll option to the list need to allow for it
                # in the selection, so add one
                if addPlayAll == True:
                    itemToPlay = itemToPlay - 1
                log( "Start playing " + exList[itemToPlay].getFilename() )
                extrasPlayer.play( exList[itemToPlay].getFilename() )
            while extrasPlayer.isPlayingVideo():
                xbmc.sleep(100)
            
            # The video selection will be the default return location
            if not Settings.isMenuReturnVideoSelection():
                if Settings.isMenuReturnHome():
                    xbmc.executebuiltin("xbmc.ActivateWindow(home)", True)
                else:
                    # Put the information dialog back up
                    xbmc.executebuiltin("xbmc.ActivateWindow(" + str(infoDialogId) + ")")
                    if not Settings.isMenuReturnInformation():
                        # Wait for the Info window to open, it can take a while
                        # this is to avoid the case where the exList dialog displays
                        # behind the info dialog
                        while( xbmcgui.getCurrentWindowDialogId() != infoDialogId):
                            xbmc.sleep(100)
                        # Allow time for the screen to load - this could result in an
                        # action such as starting TvTunes
                        xbmc.sleep(1000)
                        # Before showing the list, check if someone has quickly
                        # closed the info screen while it was opening and we were waiting
                        if xbmcgui.getCurrentWindowDialogId() == infoDialogId:
                            # Reshow the exList that was previously generated
                            self.showList(exList)

    def showError(self):
        xbmcgui.Dialog().ok("Info", "No extras found")


################################################
# Class to control Searching for the extra files
################################################
class VideoExtrasFinder():
    # Searches a given path for extras files
    def findExtras(self, path, filename):
        # Get the extras that are stored in the extras directory i.e. /Extras/
        files = self.getExtrasDirFiles(path)
        # Then add the files that have the extras tag in the name i.e. -extras-
        files.extend( self.getExtrasFiles( path, filename ) )
        if Settings.isSearchNested():
            files.extend( self._getNestedExtrasFiles( path, filename ) )
        files.sort()
        return files

    # Gets any extras files that are in the given extras directory
    def getExtrasDirFiles(self, basepath):
        # Add the name of the extras directory to the end of the path
        extrasDir = os.path.join( basepath, Settings.getExtrasDirName() )
        log( "Checking existence for " + extrasDir )
        extras = []
        # Check if the extras directory exists
        if xbmcvfs.exists( extrasDir ):
            # lest everything in the extras directory
            dirs, files = xbmcvfs.listdir( extrasDir )
            for filename in files:
                log( "found file: " + filename)
                # Check each file in the directory to see if it should be skipped
                if( Settings.getExcludeFiles() != "" ):
                    m = re.search(Settings.getExcludeFiles(), filename )
                else:
                    m = ""
                if m:
                    log( "Skiping file: " + filename)
                else:
                    extrasFile = os.path.join( extrasDir, filename )
                    extraItem = ExtrasItem(extrasFile)
                    extras.append(extraItem)
        return extras

    def _getNestedExtrasFiles(self, basepath, filename):
        extras = []
        if xbmcvfs.exists( basepath ):
            dirs, files = xbmcvfs.listdir( basepath )
            for dirname in dirs:
                dirpath = os.path.join( basepath, dirname )
                log( "Nested check in directory: " + dirpath )
                if( dirname != Settings.getExtrasDirName() ):
                    log( "Check directory: " + dirpath )
                    extras.extend( self.getExtrasDirFiles(dirpath) )
                    extras.extend( self.getExtrasFiles( dirpath, filename ) )
                    extras.extend( self._getNestedExtrasFiles( dirpath, filename ) )
        return extras

    # Search for files with the same name as the original video file
    # but with the extras tag on, this will not recurse directories
    # as they must exist in the same directory
    def getExtrasFiles(self, filepath, filename):
        extras = []
        extrasTag = Settings.getExtrasFileTag()

        # If there was no filename given, nothing to do
        if (filename == None) or (filename == "") or (extrasTag == ""):
            return extras
        directory = filepath
        dirs, files = xbmcvfs.listdir(directory)

        for aFile in files:
            if extrasTag in aFile:
                extrasFile = os.path.join( directory, aFile )
                extraItem = ExtrasItem(extrasFile)
                extras.append(extraItem)
        return extras

#################################
# Main Class to control the work
#################################
class VideoExtras():
    def __init__( self, inputArg ):
        log( "Finding extras for " + inputArg )
        self.baseDirectory = inputArg
        if self.baseDirectory.startswith("stack://"):
            self.baseDirectory = self.baseDirectory.replace("stack://", "")
        # If this is a file, then get it's parent directory
        if os.path.isfile(self.baseDirectory):
            self.baseDirectory = os.path.dirname(self.baseDirectory)
            self.filename = (os.path.split(inputArg))[1]
        else:
            self.filename = None
        log( "Root directory: " + self.baseDirectory )

    def run(self):
        # Display the busy icon while searching for files
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        extrasFinder = VideoExtrasFinder()
        files = extrasFinder.findExtras(self.baseDirectory, self.filename )
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )
        
        # All the files have been retrieved, now need to display them
        extrasWindow = VideoExtrasWindow()
        if not files:
            error = True
        else:
            error = extrasWindow.showList( files )
        if error:
            extrasWindow.showError()


#########################
# Main
#########################
if len(sys.argv) > 1:
    videoExtras = VideoExtras(sys.argv[1])
    videoExtras.run()
