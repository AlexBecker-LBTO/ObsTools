#!/usr/bin/env python3
import os, time
import argparse
import curses

global currdir
currdir = os.getcwd()
def main():
    '''
    
    Main function with the general program sequence that is called on init.
    
    '''    
    parser = argparse.ArgumentParser(description='Finds README files in current directory and all subdirectories.', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-d', '--display', type=str, help='How to display content of README file.', choices=['less', 'more'], default='less')
    parser.add_argument('-m', '--mode', type=str, help='If more than one readme file is found show most recent file or list of files.', choices=['list', 'recent'], default='recent')
    args = parser.parse_args()
    
    filelist = searchDir()
    if len(filelist) == 0:
        print('No readme file found!')
    elif len(filelist) == 1:
        os.system(f'{args.display} {filelist[0]}')
    elif len(filelist) > 1 and args.mode == 'recent':
        os.system(f'{args.display} {filelist[0]}')
    elif len(filelist) > 1 and args.mode == 'list':
        createSelectionMenu(filelist, args)


def createSelectionMenu(filelist, args):

    menu = {'title' : 'Select readme file',
            'type' : 'menu',
            'subtitle' : 'Readme files found:'}
    options = []
    longestabsolutepath = max([(len(x),x) for x in filelist])
    longestrelativepath = len(os.path.relpath(longestabsolutepath[1], currdir)) + 5
    for entry in filelist:
        relfile = os.path.relpath(entry, currdir)
        optionentry = {'title' : f'{relfile:<{longestrelativepath}} {time.ctime(os.path.getmtime(entry))}', 'type' : 'command', 'command': f'{args.display} {entry}'}
        options.append(optionentry)

    menu['options'] = options

    m = CursesMenu(menu)
    selected_action = m.display()

    if selected_action['type'] != 'exitmenu':
        os.system(selected_action['command'])

def searchDir():
    filelist = []
    for dirpath, dirnames, filenames in os.walk(currdir):
        for filename in [f for f in filenames if f.upper().startswith("READ") or f.upper().endswith("README") or f.upper().endswith("README.TXT") or f.upper().endswith(".ME")]:
            filelist.append(os.path.join(dirpath, filename))
    filelist.sort(key=lambda x: os.path.getmtime(x))
    filelist.reverse()
    return filelist


class CursesMenu(object):

    INIT = {'type' : 'init'}

    def __init__(self, menu_options):
        self.screen = curses.initscr()
        self.menu_options = menu_options
        self.selected_option = 0
        self._previously_selected_option = None
        self.running = True

        #init curses and curses input
        curses.noecho()
        curses.cbreak()
        curses.start_color()
        curses.curs_set(0) #Hide cursor
        self.screen.keypad(1)

        #set up color pair for highlighted option
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        self.hilite_color = curses.color_pair(1)
        self.normal_color = curses.A_NORMAL

    def prompt_selection(self, parent=None):
        if parent is None:
            lastoption = "Exit"
        else:
            lastoption = "Return to previous menu ({})".format(parent['title'])

        option_count = len(self.menu_options['options'])

        input_key = None

        ENTER_KEY = ord('\n')
        while input_key != ENTER_KEY:
            if self.selected_option != self._previously_selected_option:
                self._previously_selected_option = self.selected_option

            self.screen.border(0)
            self._draw_title()
            for option in range(option_count):
                if self.selected_option == option:
                    self._draw_option(option, self.hilite_color)
                else:
                    self._draw_option(option, self.normal_color)

            if self.selected_option == option_count:
                self.screen.addstr(5 + option_count, 4, "{:2} - {}".format(option_count+1,
                    lastoption), self.hilite_color)
            else:
                self.screen.addstr(5 + option_count, 4, "{:2} - {}".format(option_count+1,
                    lastoption), self.normal_color)

            max_y, max_x = self.screen.getmaxyx()
            if input_key is not None:
                self.screen.addstr(max_y-3, max_x - 5, "{:3}".format(self.selected_option))
            self.screen.refresh()


            input_key = self.screen.getch()
            down_keys = [curses.KEY_DOWN, ord('j')]
            up_keys = [curses.KEY_UP, ord('k')]
            exit_keys = [ord('q')]

            if input_key in down_keys:
                if self.selected_option < option_count:
                    self.selected_option += 1
                else:
                    self.selected_option = 0

            if input_key in up_keys:
                if self.selected_option > 0:
                    self.selected_option -= 1
                else:
                    self.selected_option = option_count

            if input_key in exit_keys:
                self.selected_option = option_count #auto select exit and return
                break

        return self.selected_option

    def _draw_option(self, option_number, style):
        self.screen.addstr(5 + option_number,
                           4,
                           "{:2} - {}".format(option_number+1, self.menu_options['options'][option_number]['title']),
                           style)

    def _draw_title(self):
        self.screen.addstr(2, 2, self.menu_options['title'], curses.A_STANDOUT)
        self.screen.addstr(4, 2, self.menu_options['subtitle'], curses.A_BOLD)

    def display(self):
        selected_option = self.prompt_selection()
        i, _ = self.screen.getmaxyx()
        curses.endwin()
        os.system('clear')
        if selected_option < len(self.menu_options['options']):
            selected_opt = self.menu_options['options'][selected_option]
            return selected_opt
        else:
            self.running = False
            return {'title' : 'Exit', 'type' : 'exitmenu'}


if __name__ == '__main__':
    main()
