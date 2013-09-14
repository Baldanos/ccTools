import sys
import urwid
from ccTalk import *


#ccParse, a ccTalk data viewer
#Copyright (C) 2012 Nicolas Oberli
#
#This program is free software; you can redistribute it and/or
#modify it under the terms of the GNU General Public License
#as published by the Free Software Foundation; either version 2
#of the License, or (at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

keys = []
data = ""


class Label (urwid.Text):

    def selectable(self):
        return True

    def keypress(self,  size,  key):
        return key



def reloadContent():
    content = [urwid.AttrMap(w, None, 'focus') for w in keys]
    return content

def main ():

    content = urwid.SimpleListWalker(reloadContent())
    messagesList = urwid.ListBox(content)

    palette = [
        ('body','dark cyan', '', 'standout'),
        ('focus','dark red', '', 'standout'),
        ('head','light red', 'black'),
        ]

    menutxt = urwid.Text("Menu bar")
    menufill = urwid.Filler(menutxt)

    infoTxt = urwid.Text("Info panel")
    infoFill = urwid.Filler(infoTxt)

    def keystroke (kinput):

        if kinput is 'r':
            infoTxt.set_text(str(len(messages)))
            reloadContent()

        if kinput in ('q', 'Q'):
            raise urwid.ExitMainLoop()

        if kinput is 'enter':
            focus, pos = messagesList.get_focus()
            if messages[pos].payload.data != "":
                if messages[pos].payload.header == 0:
                    text = "\n= In response to : " +\
                            messages[pos-1].payload.headerType + "\n" +\
                            str(messages[pos-1]) + "\n"
                    text = text + "\n= Payload decoding \n" +\
                            messages[pos].payload.parsePayload(
                                    messages[pos-1].payload.header) + "\n"
                else:
                    text = "\n= Header " + str(messages[pos].payload.header) +\
                            " (" + messages[pos].payload.headerType + ")\n"
                    text = text + "= Payload decoding \n" +\
                            messages[pos].payload.parsePayload(
                                    messages[pos].payload.header) + "\n"
            else:
                if messages[pos].payload.header == 0:
                    text = "\n= In response to : " +\
                            messages[pos-1].payload.headerType + "\n" +\
                            str(messages[pos-1]) + "\n"
                else:
                    text = "\n= Header " + str(messages[pos].payload.header) +\
                            " (" + messages[pos].payload.headerType + ")\n"
            text = text + "\n= Raw dump of packet \n" +\
                    messages[pos].raw().encode('hex')
            infoTxt.set_text(text)

    liste = urwid.Pile(
                       [(urwid.LineBox(messagesList)),
                        ('fixed',17,(urwid.LineBox(infoFill))),
                        ])

    header = urwid.AttrMap(urwid.Text('ccParse 0.2 - ' + str(len(keys)) +\
            ' messages'), 'head')
    view = urwid.Frame(liste,  header=header)
    loop = urwid.MainLoop(view, palette, unhandled_input=keystroke)
    loop.run()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage : "+sys.argv[0]+" <filename>"
        sys.exit()
    else:
        f = open(sys.argv[1],"rb")
        data = f.read()
        f.close()
        data, messages = parseMessages(data)
        keys = []
        for message in messages:
            keys.append(Label(str(message)))
        reloadContent()
    main()
