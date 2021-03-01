#!/usr/bin/env python3
import os, sys, glob, pwd, mimetypes, time, shutil, rlcompleter, readline, signal


class Colour:
    DEFAULT = "\033[39m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    LIGHTGRAY = "\033[37m"
    DARKGRAY = "\033[90m"
    LIGHTRED = "\033[91m"
    LIGHTGREEN = "\033[92m"
    LIGHTYELLOW = "\033[93m"
    LIGHTBLUE = "\033[94m"
    LIGHTMAGENTA = "\033[95m"
    LIGHTCYAN = "\033[96m"
    WHITE = "\033[97m"


class PySh:
    STDIN = sys.stdin.fileno()
    STDOUT = sys.stdout.fileno()
    STDERR = sys.stderr.fileno()
    
    meta_args = ["python3", __file__]
    cmds = {"info": 1,
           "files": 0,
           "delete": 1,
           "copy": 2,
           "where": 0,
           "down": 1,
           "up": 0,
           "finish": 0,
           "source": 0,
           "help": 0,
           "hostname": 0,
           "username": 0,
           "dirname": 0
           }

    def __init__(self):
        pass

    def run(self, argv):
        cmd = argv[0]
        exc = self.build_path(cmd)
        args = [exc]+argv[1:]
        if not exc:
            sys.stderr.write(f'{cmd}: not found\n')
            return
        try:
            pid = os.fork()
            if pid == 0:
                if "|" in args:
                    args[0] = cmd
                    args = ' '.join(args)
                    self.open_pipe(args)
                else:
                    os.execv(exc, args)
                    os._exit(0)
            else:
                _, status = os.waitpid(0, 0)
                exitc = os.WEXITSTATUS(status)
        except OSError as e:
            sys.stderr.write(str(e)+'\n')
            os._exit(1)

    def build_path(self, cmd):
        for path in os.environ['PATH'].split(":"):
            exc = path+"/"+cmd
            if os.path.isfile(exc) and os.access(exc, os.X_OK):
                return exc
        return ""

    def sigint_handler(self, signal, frame):
        print("\n^C Keyboard interrupt\nBye!") # optionally, os.system("clear")
        sys.exit(0)

    def start_proc(self, fdin, fdout, exc, flags):
        pid = os.fork()
        if pid == 0:
            if fdin:
                os.dup2(fdin, self.STDIN)
                os.close(fdin)
            if fdout:
                os.dup2(fdout, self.STDOUT)
                os.close(fdout)
            return os.execv(exc, flags)
        return pid

    def open_pipe(self, args):
        args = args.split('|')
        fdin = 0
        for i in range(len(args)-1):
            r, w = os.pipe()
            cmd = args[i].split()
            exc = self.build_path(cmd[0])
            flags = [exc]+cmd[1:]
            self.start_proc(fdin, w, exc, flags)
            os.close(w)
            fdin = r
        if fdin:
            os.dup2(fdin, self.STDIN)
        cmd = args[-1].split()
        exc = self.build_path(cmd[0])
        flags = [exc]+cmd[1:]
        return os.execv(exc, flags)

    def source(self):
        try:
            print("\033[H\033[J")
            os.execv(sys.executable, self.meta_args)
        except OSError as e:
            os._exit(1)

    def files(self):
        for file in os.listdir('.'):
            st = ""
            fpath = os.path.abspath(file)
            if os.path.isdir(fpath):
                st = f'{file}/: directory'
            elif os.path.isfile(fpath):
                st = f'{file:2}: {mimetypes.guess_type(fpath)[0]}'
            print(st)
            
    
    def info(self, argv):
        if os.path.exists(argv[0]):
            file = argv[0]
            fpath = os.path.abspath(file)
            st = ""
            if os.path.isdir(fpath):
                st = f'{file:2}:'
            elif os.path.isfile(fpath):
                st = f'{file:2}: '
                if os.path.islink(fpath):
                    st += f' symbolic link to {os.readlink(fpath)}'
                else:
                    exc = ""
                    if os.acess(fpath, os.X_OK):
                        exc = "executable"
                    st += f'{mimetypes.guess_type(fpath[0])} {os.path.getsize(fpath):2} {exc}'
            print(st, f'{(pwd.getpwuid(os.stat(fpath).st_uid).pw_name):2} {(time.ctime(os.path.getmtime(fpath))):2}')
        else:
            sys.stderr.write(f'{argv[0]} No such file or directory\n')
            
    def delete(self, argv):
        if os.path.exists(argv[0]):
            for file in os.listdir(os.getcwd()):
                file = os.path.join(os.getcwd(), file)
                if os.path.islink(file) and os.readlink(file) == argv[0]:
                    try:
                        os.remove(file)
                    except OSError as e:
                        sys.stderr.write(str(e)+'\n')
            try:
                os.remove(argv[0])
            except OSError as e:
                sys.stderr.write(str(e)+'\n')
                
    def copy(self, argv):
        if os.path.exists(argv[0]):
            cpdir, cpfile = os.path.split(argv[1])
            if os.path.isdir(cpdir):
                if not os.path.exists(cpfile):
                    shutil.copy(os.path.realpath(argv[0]), argv[1])
            else:
                os.mkdir(cpdir)
                if not os.path.exists(cpfile):
                    shutil.copy(os.path.realpath(argv[0]), argv[1])
        else:
            sys.stderr.write('Error occurred while copying the file\n');
    
    def where(self):
        print(os.getcwd())
    
    def down(self, argv):
        if os.path.exists(argv[0]):
            cdir = os.path.realpath(argv[0])
            cwd = os.getcwd()
            if cwd in cdir:
                os.chdir(cdir)
        else:
            sys.stderr.write(f'{argv[0]} No such directory\n')
            
    def up(self):
        if os.getcwd() == "/":
            print(f'Already at {os.getcwd()} directory')
        else:
            os.chdir("..")
            
    def finish(self):
        sys.exit()
    
    def username(self):
        print(pwd.getpwuid(os.getuid()).pw_name)
    
    def hostname(self):
        print(os.uname()[1])
    
    def dirname(self):
        print(os.path.split(os.getcwd())[1])
    
    def err(self, argv, n):
        if len(argv) > n:
            sys.stderr.write("Unexpected argument(s)", *argv[1:], '\n')
        else:
            sys.stderr.write("Missing argument for command\n")
    
    def check_args(self, argv, n):
        if len(argv) == n:
            return True
        return False
    
    def completer(self, text, state):
        # auto completion on internal commands and directory contents
        options = [k+" " for k in [*self.cmds,*os.listdir(".")] if k.startswith(text)]
        if 0 <= state < len(options):
            return options[state]
    
    def read_input(self):
        return input((f'[{Colour.LIGHTMAGENTA}{pwd.getpwuid(os.getuid()).pw_name}'
                      f'{Colour.WHITE}@{Colour.LIGHTMAGENTA}{os.uname()[1]}{Colour.WHITE}:'
                      f'{Colour.LIGHTCYAN}{os.path.split(os.getcwd())[1]}{Colour.WHITE}]$ '))
    
    def main(self):
        print(f'{Colour.YELLOW}pysh:{Colour.WHITE} {Colour.BLUE}><(((\'> a bashwards compatible shell{Colour.WHITE}\nType \'help\' for a list of available commands')
        readline.parse_and_bind('tab: complete')  
        readline.set_completer(self.completer)
        readline.set_completer_delims(' \t\n;')
        signal.signal(signal.SIGINT, self.sigint_handler)
        while 1:
            line = self.read_input()
            args = line.split()
            if not args:
                continue
            elif args[0] in self.cmds:
                cmd = args[0]
                argc = self.cmds.get(args[0])
                argv = args[1:]
                if self.check_args(argv, argc):
                    cmd = "self."+cmd
                    if argc == 0:
                        eval(f'{cmd}()')
                    else:
                        eval(f'{cmd}(argv)')
                else:
                    self.err(argv, argc)
            else:
                self.run(args)
    
    def help(self):
        help = ("pysh, version 0.0.1-release (linux-gnu), a bashwards compatible shell"
		"\nType 'help' to see the list of internally available commands."
		"\nfiles"
		"\ninfo [FILE]"
		"\ndelete [FILE]"
		"\ncopy [FILE] [FILE]"
		"\nwhere"
		"\ndown [dir]"
		"\nup"
		"\nfinish"
		"\nsource")
        print(help)

if __name__ == '__main__':
    pysh = PySh()
    pysh.main()
