# -*- coding: utf-8 -*-
import sys
import os
import traceback
import xbmc
import xbmcaddon
import xbmcvfs
import xbmcgui
import datetime

__addon__ = xbmcaddon.Addon(id='script.videoextras')
__version__ = __addon__.getAddonInfo('version')
__cwd__ = __addon__.getAddonInfo('path').decode("utf-8")
__resource__ = xbmc.translatePath(os.path.join(__cwd__, 'resources').encode("utf-8")).decode("utf-8")
__lib__ = xbmc.translatePath(os.path.join(__resource__, 'lib').encode("utf-8")).decode("utf-8")

sys.path.append(__resource__)
sys.path.append(__lib__)

# Import the common settings
from settings import log
from settings import os_path_join


# Ideally we would use an XML parser to do this like ElementTree
# However they all end up re-ordering the attributes, so doing a diff
# between changed files is very hard, so for this reason we do it
# all manually without the aid of an XML parser
#
# The names in the Windows XML files map as follows to the display names
# PosterWrapView            Poster Wrap          ViewVideoLibrary.xml    DONE
# PosterWrapView2_Fanart    Fanart               ViewVideoLibrary.xml    DONE
# MediaListView2            Media Info           ViewVideoLibrary.xml    TV left to do (E in wrong place)
# MediaListView3            Media Info 2         ViewVideoLibrary.xml    TV left to do
# MediaListView4            Media Info 3         ViewVideoLibrary.xml    TV left to do
# CommonRootView            List                 ViewFileMode.xml
# ThumbnailView             Thumbnail            ViewFileMode.xml
# WideIconView              Wide (TV Only)       ViewFileMode.xml
# FullWidthList             Big List             ViewFileMode.xml
class ConfUpdate():
    INCLUDE_CMD = '<include file="IncludesVideoExtras.xml"/>'

    DIALOG_VIDEO_INFO_ONLOAD = '<onload condition="System.HasAddon(script.videoextras)">XBMC.RunScript(script.videoextras,check,"$INFO[ListItem.FilenameAndPath]")</onload>'

    DIALOG_VIDEO_INFO_BUTTON = '''\t\t\t\t\t</control>\n\t\t\t\t\t<control type="button" id="%d">
\t\t\t\t\t\t<description>Extras</description>
\t\t\t\t\t\t<include>ButtonInfoDialogsCommonValues</include>
\t\t\t\t\t\t<label>$ADDON[script.videoextras 32001]</label>
\t\t\t\t\t\t<onclick>XBMC.RunScript(script.videoextras,display,"$INFO[ListItem.FilenameAndPath]")</onclick>
\t\t\t\t\t\t<visible>System.HasAddon(script.videoextras) + [Container.Content(movies) | Container.Content(episodes) | Container.Content(TVShows) | Container.Content(musicvideos)] + IsEmpty(Window(movieinformation).Property("HideVideoExtrasButton"))</visible>'''

    DIALOG_VIDEO_INFO_ICON = '''\t\t\t\t\t<!-- Add the Video Extras Icon -->\n\t\t\t\t\t<include>VideoExtrasLargeIcon</include>
\t\t\t\t</control>
\t\t\t\t<control type="grouplist">
\t\t\t\t\t<description>Add the Video Extras Icon</description>
\t\t\t\t\t<left>210</left>
\t\t\t\t\t<top>480</top>
\t\t\t\t\t<width>600</width>
\t\t\t\t\t<align>left</align>
\t\t\t\t\t<itemgap>2</itemgap>
\t\t\t\t\t<orientation>horizontal</orientation>
\t\t\t\t\t<include>VisibleFadeEffect</include>
\t\t\t\t\t<visible>!Control.IsVisible(50) + Container.Content(tvshows) + !Container.Content(Episodes)</visible>
\t\t\t\t\t<include>VideoExtrasLargeIcon</include>'''

    LARGE_ICON_INCLUDE = '''\t\t\t\t<!-- Add the Video Extras Icon -->\n\t\t\t\t<include>VideoExtrasLargeIcon</include>'''

    def __init__(self):
        # Find out where the confluence skin files are located
        confAddon = xbmcaddon.Addon(id='skin.confluence')
        self.confpath = xbmc.translatePath(confAddon.getAddonInfo('path'))
        self.confpath = os_path_join(self.confpath, '720p')
        log("Confluence Location: %s" % self.confpath)
        # Create the timestamp centrally, as we want all files changed for a single
        # run to have the same backup timestamp so it can be easily undone if the
        # user wishes to switch it back
        self.bak_timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self.errorToLog = False

    # Method to update all of the required Confluence files
    def updateSkin(self):
        # Update the files one at a time
        self._addIncludeFile()
        self._updateDialogVideoInfo()
        self._updateViewsVideoLibrary()

        # Now either print the complete message or the "check log" message
        if self.errorToLog:
            xbmcgui.Dialog().ok(__addon__.getLocalizedString(32001), __addon__.getLocalizedString(32157), __addon__.getLocalizedString(32152))
        else:
            xbmcgui.Dialog().ok(__addon__.getLocalizedString(32001), __addon__.getLocalizedString(32158))

    # Copies over the include file used for icon overlays
    def _addIncludeFile(self):
        # copy over the video extras include file
        skinsDir = xbmc.translatePath(os_path_join(__resource__, 'skins').encode("utf-8")).decode("utf-8")
        incFile = os_path_join(skinsDir, 'IncludesVideoExtras.xml')
        # Work out where it is going to go
        tgtFile = os_path_join(self.confpath, 'IncludesVideoExtras.xml')
        log("IncludesVideoExtras: Copy from %s to %s" % (incFile, tgtFile))
        xbmcvfs.copy(incFile, tgtFile)

    # Makes all the required changes to DialogVideoInfo.xml
    def _updateDialogVideoInfo(self):
        # Get the location of the information dialog XML file
        dialogXml = os_path_join(self.confpath, 'DialogVideoInfo.xml')
        log("DialogVideoInfo: Confluence dialog XML file: %s" % dialogXml)

        # Make sure the file exists (It should always exist)
        if not xbmcvfs.exists(dialogXml):
            log("DialogVideoInfo: Unable to find the file DialogVideoInfo.xml, skipping file", xbmc.LOGERROR)
            self.errorToLog = True
            return

        # Load the DialogVideoInfo.xml into a string
        dialogXmlFile = xbmcvfs.File(dialogXml, 'r')
        dialogXmlStr = dialogXmlFile.read()
        dialogXmlFile.close()

        # Now check to see if the skin file has already had the video extras bits added
        if 'script.videoextras' in dialogXmlStr:
            # Already have video extras referenced, so we do not want to do anything else
            # to this file
            log("DialogVideoInfo: Video extras already referenced in %s, skipping file" % dialogXml, xbmc.LOGINFO)
            self.errorToLog = True
            return

        # Now add the include link to the file
        dialogXmlStr = self._addIncludeToXml(dialogXmlStr)

        # Start by adding the onLoad section
        previousOnLoad = 'XBMC.RunScript(script.tvtunes,backend=True)</onload>'

        if previousOnLoad not in dialogXmlStr:
            # The file has had a standard component deleted, so quit
            log("DialogVideoInfo: Could not find TvTunes onLoad command, skipping file", xbmc.LOGERROR)
            self.errorToLog = True
            return

        # Now add the Video Extras onLoad command after the TvTunes one
        insertTxt = previousOnLoad + "\n\t" + ConfUpdate.DIALOG_VIDEO_INFO_ONLOAD
        dialogXmlStr = dialogXmlStr.replace(previousOnLoad, insertTxt)

        # Now we need to add the button after the TvTunes button
        previousButton = '"TvTunes_HideVideoInfoButton"))</visible>'

        if previousButton not in dialogXmlStr:
            # The file has had a standard component deleted, so quit
            log("DialogVideoInfo: Could not find TvTunes button, skipping file", xbmc.LOGERROR)
            self.errorToLog = True
            return

        # Check to make sure we use a unique ID value for the button
        idOK = False
        idval = 101
        while not idOK:
            idStr = "id=\"%d\"" % idval
            if idStr not in dialogXmlStr:
                idOK = True
            else:
                idval = idval + 1

        # Now add the Video Extras button after the TvTunes one
        insertTxt = previousButton + "\n" + (ConfUpdate.DIALOG_VIDEO_INFO_BUTTON % idval)
        dialogXmlStr = dialogXmlStr.replace(previousButton, insertTxt)

        # Now add the section for the icon overlay
        iconPrevious = 'VideoTypeHackFlaggingConditions</include>'
        if iconPrevious not in dialogXmlStr:
            log("DialogVideoInfo: Could not find point to add icon overlay, skipping overlay addition", xbmc.LOGERROR)
            self.errorToLog = True
            return

        insertTxt = iconPrevious + "\n" + ConfUpdate.DIALOG_VIDEO_INFO_ICON
        dialogXmlStr = dialogXmlStr.replace(iconPrevious, insertTxt)

        self._saveNewFile(dialogXml, dialogXmlStr)

    # Save the new contents, taking a backup of the old file
    def _saveNewFile(self, dialogXml, dialogXmlStr):
        log("SaveNewFile: New file content: %s" % dialogXmlStr)

        # Now save the file to disk, start by backing up the old file
        xbmcvfs.copy(dialogXml, "%s.videoextras-%s.bak" % (dialogXml, self.bak_timestamp))

        # Now save the new file
        dialogXmlFile = xbmcvfs.File(dialogXml, 'w')
        dialogXmlFile.write(dialogXmlStr)
        dialogXmlFile.close()

    def _updateViewsVideoLibrary(self):
        # Get the location of the information dialog XML file
        dialogXml = os_path_join(self.confpath, 'ViewsVideoLibrary.xml')
        log("ViewsVideoLibrary: Confluence dialog XML file: %s" % dialogXml)

        # Make sure the file exists (It should always exist)
        if not xbmcvfs.exists(dialogXml):
            log("ViewsVideoLibrary: Unable to find the file ViewsVideoLibrary.xml, skipping file", xbmc.LOGERROR)
            self.errorToLog = True
            return

        # Load the DialogVideoInfo.xml into a string
        dialogXmlFile = xbmcvfs.File(dialogXml, 'r')
        dialogXmlStr = dialogXmlFile.read()
        dialogXmlFile.close()

        # Now check to see if the skin file has already had the video extras bits added
        if 'IncludesVideoExtras' in dialogXmlStr:
            # Already have video extras referenced, so we do not want to do anything else
            # to this file
            log("ViewsVideoLibrary: Video extras already referenced in %s, skipping file" % dialogXml, xbmc.LOGINFO)
            self.errorToLog = True
            return

        # Update the PosterWrapView part
        dialogXmlStr = self._updatePosterWrapView(dialogXmlStr)
        # Update the MediaListView2 part
        dialogXmlStr = self._updateMediaListView2(dialogXmlStr)

        # Now add the include link to the file
        dialogXmlStr = self._addIncludeToXml(dialogXmlStr)

        # Now add the section for the icon overlay
        iconPrevious = 'VideoTypeHackFlaggingConditions</include>'
        if iconPrevious not in dialogXmlStr:
            log("DialogVideoInfo: Could not find point to add icon overlay, skipping overlay addition", xbmc.LOGERROR)
            self.errorToLog = True
            return

        insertTxt = iconPrevious + "\n" + ConfUpdate.LARGE_ICON_INCLUDE
        dialogXmlStr = dialogXmlStr.replace(iconPrevious, insertTxt)

        self._saveNewFile(dialogXml, dialogXmlStr)

    # Adds the line to the XML that imports the extras include file
    def _addIncludeToXml(self, xmlStr):
        updatedXml = xmlStr
        # First check if the include command is already in the XML
        if ConfUpdate.INCLUDE_CMD not in updatedXml:
            # We want the include at the top, so add it after the first window
            tag = '<window>'
            if tag not in updatedXml:
                tag = '<includes>'
            # Make sure the tagwe are about to use is still there
            if tag in updatedXml:
                insertTxt = tag + "\n\t" + ConfUpdate.INCLUDE_CMD
                updatedXml = updatedXml.replace(tag, insertTxt)
        return updatedXml

    # Update the PosterWrapView section of the ViewsVideoLibrary.xml file
    def _updatePosterWrapView(self, dialogXmlStr):
        log("ViewsVideoLibrary: Updating PosterWrapView")
        # Split the text up into lines, this will enable us to process each line
        # to insert the data expected
        lines = dialogXmlStr.splitlines(True)
        totalNumLines = len(lines)
        currentLine = 0

        log("ViewsVideoLibrary: File split into %d lines" % totalNumLines)

        # Go through each line of the original file until we get to the section
        # we are looking for
        while (currentLine < totalNumLines) and ('PosterWrapView' not in lines[currentLine]):
            currentLine = currentLine + 1

        # Now we have started the PosterWrapView we need to go until we get to the tag
        # that contains </itemlayout>
        while (currentLine < totalNumLines) and ('</itemlayout>' not in lines[currentLine]):
            # add the line to the newly created file
            currentLine = currentLine + 1

        if currentLine < totalNumLines:
            insertData = '''\t\t\t\t\t<!-- Add the Video Extras Icon -->
\t\t\t\t\t<control type="group">
\t\t\t\t\t\t<description>VideoExtras Flagging Images</description>
\t\t\t\t\t\t<left>10</left>
\t\t\t\t\t\t<top>310</top>
\t\t\t\t\t\t<include>VideoExtrasOverlayIcon</include>
\t\t\t\t\t</control>\n'''
            lines.insert(currentLine, insertData)
            totalNumLines = totalNumLines + 1
            currentLine = currentLine + 1

        # Now work until the end of the focus layout as we want to add something before it
        while (currentLine < totalNumLines) and ('</focusedlayout>' not in lines[currentLine]):
            # add the line to the newly created file
            currentLine = currentLine + 1

        if currentLine < totalNumLines:
            insertData = '''\t\t\t\t\t<!-- Add the Video Extras Icon -->
\t\t\t\t\t<control type="group">
\t\t\t\t\t\t<description>VideoExtras Flagging Images</description>
\t\t\t\t\t\t<left>10</left>
\t\t\t\t\t\t<top>300</top>
\t\t\t\t\t\t<include>VideoExtrasOverlayIcon</include>
\t\t\t\t\t\t<animation type="focus">
\t\t\t\t\t\t\t<effect type="fade" start="0" end="100" time="200"/>
\t\t\t\t\t\t\t<effect type="slide" start="0,0" end="-20,40" time="200"/>
\t\t\t\t\t\t</animation>
\t\t\t\t\t\t<animation type="unfocus">
\t\t\t\t\t\t\t<effect type="fade" start="100" end="0" time="200"/>
\t\t\t\t\t\t\t<effect type="slide" end="0,0" start="-20,40" time="200"/>
\t\t\t\t\t\t</animation>
\t\t\t\t\t</control>\n'''
            lines.insert(currentLine, insertData)

        # Now join all the data together
        return ''.join(lines)

    def _updateMediaListView2(self, dialogXmlStr):
        # TODO:
        return dialogXmlStr

#########################
# Main
#########################
if __name__ == '__main__':
    log("VideoExtras: Updating Confluence Skin (version %s)" % __version__)

    doUpdate = xbmcgui.Dialog().yesno(__addon__.getLocalizedString(32001), __addon__.getLocalizedString(32155))

    if doUpdate:
        try:
            confUp = ConfUpdate()
            confUp.updateSkin()
            del confUp
        except:
            log("VideoExtras: %s" % traceback.format_exc(), xbmc.LOGERROR)
            xbmcgui.Dialog().ok(__addon__.getLocalizedString(32001), __addon__.getLocalizedString(32156), __addon__.getLocalizedString(32152))