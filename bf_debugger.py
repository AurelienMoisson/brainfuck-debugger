#! /usr/bin/python3
'''you can see how rotate.bf works by using the following commands :
echo -e '\x01\x02\x03\x04\x05\x06' > test_input
./bf_debugger.py rotate.bf test_input "r r r g g b m y y r r r m y y y y r r r m y y y y r r r m y y y y"

(you can also play around with the input values in the first command)
in the above command, 3 byte variables are shown in red,
the 1s and 0s used for carry checks are in magenta and yellow
the bytes where are put every small multiplication inputs are in green
and the byte for small multiplication outputs are in blue

to use the debugger :
    - you can use the down arrow key to execute the code until the executer
     arrives on a line below.
    - you can use [ to go to the next loop start
    - you can use ] to go exit the loop the code currently is in
    - you can press any other key to execute one character
'''
import curses
import sys
import time
from math import ceil

class Interpret:
    def __init__(self, file_name, mem_size, get_input = lambda: sys.stdin.read(1)):
        f = open(file_name, "r")
        self.lines = [line.split('#')[0] for line in f.read().split("\n")]
        self.pos = [0,0]#line, column
        self.loop_starts = []
        self.data = bytearray(mem_size)
        self.head_pos = 0
        self.mem_size = mem_size
        self.out = ""
        self.get_input = get_input
        self.correct_pos()
    def correct_pos(self):
        while self.pos[1]>=len(self.lines[self.pos[0]]):
            self.pos = [self.pos[0]+1, self.pos[1]-len(self.lines[self.pos[0]])]
            if self.pos[0]>=len(self.lines):
                raise EOFError()
    def step(self):
        char = self.lines[self.pos[0]][self.pos[1]]
        if char == '[':
            if self.data[self.head_pos]:
                self.loop_starts.append(self.pos[:])
            else:
                depth = 1
                while depth > 0:
                    self.pos[1] += 1
                    self.correct_pos()
                    if self.lines[self.pos[0]][self.pos[1]] == "[":
                        depth += 1
                    if self.lines[self.pos[0]][self.pos[1]] == "]":
                        depth -= 1
        if char == ']':
            if self.data[self.head_pos]:
                self.pos = self.loop_starts[-1][:]
            else:
                self.loop_starts.pop(-1)
        if char == '>':
            self.head_pos += 1
            self.head_pos %= self.mem_size
        if char == '<':
            self.head_pos -= 1
            self.head_pos %= self.mem_size
        if char == '+':
            self.data[self.head_pos] = (self.data[self.head_pos] + 1)%256
        if char == '-':
            self.data[self.head_pos] = (self.data[self.head_pos] - 1)%256
        if char == '.':
            self.out += chr(self.data[self.head_pos])
        if char == ',':
            self.data[self.head_pos] = ord(self.get_input())
        self.pos[1] += 1
        self.correct_pos()

    def next_loop_start(self):
        depth = len(self.loop_starts)
        while len(self.loop_starts) <= depth:
            depth = len(self.loop_starts)
            self.step()

    def exit_loop(self):
        depth = len(self.loop_starts)
        if depth == 0:
            return
        while len(self.loop_starts) >= depth:
            self.step()

    def run_loop(self):
        depth = len(self.loop_starts)
        if depth == 0:
            return
        while len(self.loop_starts) >= depth:
            self.step()
            if len(self.loop_starts) == depth and self.lines[self.pos[0]][self.pos[1]] == ']':
                return

    def get_output(self):
        out = self.out
        self.out = ""
        return out

    def set_input(self, string):
        self.input += string

def interactive_mode(stdscr, code_name, input_name, mem_size, delay, mem_colors = []):
    '''Displays the brainfuck code and the memory with curses
    and enables the user to interract with the code.
    '''
    curses.curs_set(0)

    curses.init_pair(1, curses.COLOR_RED, 0)
    curses.init_pair(2, curses.COLOR_GREEN, 0)
    curses.init_pair(3, curses.COLOR_BLUE, 0)
    curses.init_pair(4, curses.COLOR_MAGENTA, 0)
    curses.init_pair(5, curses.COLOR_CYAN, 0)
    curses.init_pair(6, curses.COLOR_YELLOW, 0)

    colors = {'w':curses.color_pair(0),
              'r':curses.color_pair(1),
              'g':curses.color_pair(2),
              'b':curses.color_pair(3),
              'm':curses.color_pair(4),
              'c':curses.color_pair(5),
              'y':curses.color_pair(6)}

    def get_char(k):
        char = chr(k).__repr__().strip("'")[-2:]
        char = ' '*(len(char)==1) + char
        return char
    mem_prints_functions = {
        'x': lambda k: hex(k)[-2:].replace('x', ' ').upper(),
        'c': lambda k: get_char(k)
        }
    global mem_print_type
    mem_print_type = []

    height, width = stdscr.getmaxyx()
    if (input_name != None):
        input_file = open(input_name, 'rb')
    else:
        input_file = None
    program = Interpret(code_name, mem_size, lambda : input_file.read(1))
    def get_input():
        global mem_print_type
        k = program.head_pos
        if k >= len(mem_print_type):
            mem_print_type += ['x'] * (k-len(mem_print_type)-1)
            mem_print_type += ['c']
        else:
            mem_print_type[k] = 'c'
        return input_file.read(1)
    program.get_input = get_input
    block_width = 2
    if width <= 2*block_width+2:
        raise StandardError("terminal too thin for interactive mode")

    code_width = max(len(l) for l in program.lines)
    code_height = len(program.lines)
    mem_width = max(width/2, width-code_width)
    mem_col = max(1,int(mem_width/(block_width+1)))
    mem_width = mem_col*(block_width+1)-1
    mem_height = ceil(mem_size/mem_col)
    mem_pad = curses.newpad(mem_height, mem_width)
    terminal_height = max(5, height-mem_height)
    code_pad = curses.newpad(code_height, code_width)
    
    for l,line in enumerate(program.lines):
        if l == program.pos[0]:
            for c in range(len(line)):
                if c == program.pos[1]:
                    code_pad.addstr(l,c, line[c], curses.A_REVERSE)
                else:
                    code_pad.addstr(l,c, line[c])
        else:
            code_pad.addstr(l,0,line)
    
    def redraw_mem(start = 0, end = -1):
        for k in range(start%mem_size, end%mem_size):
            l, c = divmod(k, mem_col)
            c *= block_width +1
            if k < len(mem_colors):
                color = colors[mem_colors[k]]
            else:
                color = colors['w']
            to_print = ''
            if k < len(mem_print_type):
                to_print = mem_prints_functions[mem_print_type[k]](program.data[k])
            else:
                to_print = mem_prints_functions['x'](program.data[k])
            if k == program.head_pos:
                mem_pad.addstr(l, c, to_print, color + curses.A_REVERSE)
            else:
                mem_pad.addstr(l, c, to_print, color)
    
    redraw_mem()

    last_pos = program.pos[:]
    last_head_pos = program.head_pos


    while True:
        redraw_mem(last_head_pos, last_head_pos+1)
        redraw_mem(program.head_pos, program.head_pos+1)

        code_pad.addstr(last_pos[0], last_pos[1], program.lines[last_pos[0]][last_pos[1]])
        code_pad.addstr(program.pos[0], program.pos[1], program.lines[program.pos[0]][program.pos[1]], curses.A_REVERSE)
        stdscr.refresh()
        code_pad_start_l = max(0, min(code_height-height, program.pos[0]-height//2))
        code_pad_start_c = max(0, min(code_width-width+mem_width, program.pos[1]-(width-mem_width)//2))
        code_pad.noutrefresh(code_pad_start_l,code_pad_start_c, 0,0, height-1, width-mem_width-1)

        mem_pad_start_l = max(0, min(mem_height-(height-terminal_height), program.head_pos//mem_col-(height-terminal_height)//2))
        mem_pad.noutrefresh(mem_pad_start_l,0, terminal_height, width-mem_width, height-1, width-1)
        curses.doupdate()
        last_pos = program.pos[:]
        last_head_pos = program.head_pos
        time.sleep(delay)
        k = stdscr.getkey()
        if k == "[":
            try:
                program.next_loop_start()
            except EOFError:
                return
            redraw_mem()
        elif k == "]":
            program.exit_loop()
            redraw_mem()
        elif k == "KEY_DOWN":
            line = program.pos[0]
            while program.pos[0] <= line:
                try:
                    program.step()
                except EOFError:
                    return
            redraw_mem()
        elif k == "\n":
            program.run_loop()
            redraw_mem()
        else:
            try:
                program.step()
            except EOFError:
                return
        stdscr.nodelay(1)
        while stdscr.getch() != -1:
            pass
        stdscr.nodelay(0)

mem_size = 65536
delay = 0
if len(sys.argv) > 3:
    curses.wrapper(interactive_mode, sys.argv[1], sys.argv[2], mem_size, delay, sys.argv[3].strip('\'"').split(' '))
elif len(sys.argv) > 2:
    curses.wrapper(interactive_mode, sys.argv[1], sys.argv[2], mem_size, delay)
else:
    curses.wrapper(interactive_mode, sys.argv[1], None, mem_size, delay)
