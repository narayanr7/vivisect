"""
Linux Platform Module
"""
# Copyright (C) 2007 Invisigoth - See LICENSE file for details
import os
import signal
import struct
import logging
import binascii
import platform
import traceback

import envi.cli as e_cli
import envi.bits as e_bits
import envi.memory as e_mem

import vtrace
import vtrace.exc as v_exc

import vtrace.archs.arm as v_arm
import vtrace.archs.i386 as v_i386
import vtrace.archs.amd64 as v_amd64

import vtrace.platforms.base as v_base
import vtrace.platforms.posix as v_posix

from ctypes import *
import ctypes.util as cutil

logger = logging.getLogger(__name__)

if os.getenv('ANDROID_ROOT'):
    libc = CDLL('/system/lib/libc.so')
else:
    libc = CDLL(cutil.find_library("c"), use_errno=True)

libc.lseek64.restype = c_ulonglong
libc.lseek64.argtypes = [c_uint, c_ulonglong, c_uint]
libc.read.restype = c_long
libc.read.argtypes = [c_uint, c_void_p, c_long]
libc.write.restype = c_long
libc.write.argtypes = [c_uint, c_void_p, c_long]

O_RDWR = 2
O_LARGEFILE = 0x8000

MAP_ANONYMOUS = 0x20
MAP_PRIVATE = 0x02

# Linux specific ptrace extensions
PT_GETREGS = 12
PT_SETREGS = 13
PT_GETFPREGS = 14
PT_SETFPREGS = 15
PT_ATTACH = 16
PT_DETACH = 17
PT_GETFPXREGS = 18
PT_SETFPXREGS = 19
PT_SYSCALL = 24
PT_SETOPTIONS = 0x4200
PT_GETEVENTMSG = 0x4201
PT_GETSIGINFO = 0x4202
PT_SETSIGINFO = 0x4203
PT_GETREGSET = 0x4204
PT_SETREGSET = 0x4205
PT_SEIZE = 0x4206
PT_INTERRUPT = 0x4207
# PT set options stuff.  ONLY TRACESYSGOOD may be used in 2.4...
PT_O_TRACESYSGOOD   = 0x00000001 # add 0x80 to TRAP when generated by syscall
# For each of the options below, the stop signal is (TRAP | PT_EVENT_FOO << 8)
PT_O_TRACEFORK      = 0x00000002 # Cause a trap at fork
PT_O_TRACEVFORK     = 0x00000004 # Cause a trap at vfork
PT_O_TRACECLONE     = 0x00000008 # Cause a trap at clone
PT_O_TRACEEXEC      = 0x00000010 # Cause a trap at exec
PT_O_TRACEVFORKDONE = 0x00000020 # Cause a trap when vfork done
PT_O_TRACEEXIT      = 0x00000040 # Cause a trap on exit
PT_O_MASK           = 0x0000007f
# Ptrace event types (TRAP | PT_EVENT_FOO << 8) means that type
# when using GETEVENTMSG for most of these, the new pid is the data
PT_EVENT_FORK       = 1
PT_EVENT_VFORK      = 2
PT_EVENT_CLONE      = 3
PT_EVENT_EXEC       = 4
PT_EVENT_VFORK_DONE = 5
PT_EVENT_EXIT       = 6


# Reg sets for use in ptrace PT_GETREGSET
# typlically defined in /usr/include/elf.h
# for now, we only need the one, but we can add more on demand
NT_X86_XSTATE = 0x202  # x86 extended state using xsave

# Used to tell some of the additional events apart
SIG_LINUX_SYSCALL = signal.SIGTRAP | 0x80
SIG_LINUX_CLONE = signal.SIGTRAP | (PT_EVENT_CLONE << 8)
SIG_LINUX_EXIT = signal.SIGTRAP | (PT_EVENT_EXIT << 8)

#following from Pandaboard ES (OMAP4460) Armv7a (cortex-a9)
class user_regs_arm(Structure):
    _fields_ = (
            ("r0", c_ulong),
            ("r1", c_ulong),
            ("r2", c_ulong),
            ("r3", c_ulong),
            ("r4", c_ulong),
            ("r5", c_ulong),
            ("r6", c_ulong),
            ("r7", c_ulong),
            ("r8", c_ulong),
            ("r9", c_ulong),
            ("r10", c_ulong), #aka 'sl' ?
            ("r11", c_ulong),
            ("r12", c_ulong),
            ("sp", c_ulong),
            ("lr", c_ulong),
            ("pc", c_ulong),
            ("cpsr", c_ulong),
            ("orig_r0", c_ulong),
    )

class fp_reg_arm(Structure):
    _fields_ = (
            ("sign1", c_long, 1),
            ("unused", c_long, 15),
            ("sign2", c_long, 1),
            ("exponent", c_long, 14),
            ("j", c_long, 1),
            ("mantissa1", c_long, 31),
            ("mantissa0", c_long, 32),
    )

class user_fpregs_arm(Structure):
    _fields_ = (
            ("fpregs", fp_reg_arm*8),
            ("fpsr", c_ulong, 32),
            ("fpcr", c_ulong, 32),
            ("ftype", c_ubyte*8),
            ("init_flag", c_ulong),
    )

class USER_arm(Structure):
    _fields_ = (
        ("regs",       user_regs_arm),
        ("u_fpvalid",  c_long),
        ("u_tsize",    c_ulong),
        ("u_dsize",    c_ulong),
        ("u_ssize",    c_ulong),
        ("start_code", c_ulong),
        ("start_stack",c_ulong),
        ("signal",     c_long),
        ("reserved",   c_long),
        ("u_ar0",      c_void_p),
        ("magic",      c_ulong),
        ("u_comm",     c_char*32),
        ("u_debugreg", c_long*8),
        ("fpregs",     user_fpregs_arm),
        ("u_fp0",      c_void_p)
    )

class user_regs_i386(Structure):
    _fields_ = (
        ("ebx",  c_ulong),
        ("ecx",  c_ulong),
        ("edx",  c_ulong),
        ("esi",  c_ulong),
        ("edi",  c_ulong),
        ("ebp",  c_ulong),
        ("eax",  c_ulong),
        ("ds",   c_ushort),
        ("__ds", c_ushort),
        ("es",   c_ushort),
        ("__es", c_ushort),
        ("fs",   c_ushort),
        ("__fs", c_ushort),
        ("gs",   c_ushort),
        ("__gs", c_ushort),
        ("orig_eax", c_ulong),
        ("eip",  c_ulong),
        ("cs",   c_ushort),
        ("__cs", c_ushort),
        ("eflags", c_ulong),
        ("esp",  c_ulong),
        ("ss",   c_ushort),
        ("__ss", c_ushort),
    )

class iovec(Structure):
    _fields_ = [
        ('iov_base', c_void_p),
        ('iov_len', c_size_t),
    ]

class user_fpregs_i386(Structure):
    _fields_ = [
        ('cwd', c_long),
        ('swd', c_long),
        ('twd', c_long),
        ('fip', c_long),
        ('fcs', c_long),
        ('foo', c_long),
        ('fos', c_long),
        ('st_space', c_long * 20),
    ]


class user_fpxregs_i386(Structure):
    _fields_ = [
        ('cwd', c_ushort),
        ('swd', c_ushort),
        ('twd', c_ushort),
        ('fop', c_ushort),
        ('fip', c_long),
        ('fcs', c_long),
        ('foo', c_long),
        ('fos', c_long),
        ('mxcsr', c_long),
        ('reserved', c_long),
        ('st_space', c_long * 32),
        ('xmm_space', c_long * 32),
        ('padding', c_long * 56),
    ]


class USER_i386(Structure):
    _fields_ = (
        # NOTE: Expand out the user regs struct so
        #       we can make one call to _rctx_Import
        ("regs",       user_regs_i386),
        ("u_fpvalid",  c_ulong),
        ("u_tsize",    c_ulong),
        ("u_dsize",    c_ulong),
        ("u_ssize",    c_ulong),
        ("start_code", c_ulong),
        ("start_stack",c_ulong),
        ("signal",     c_ulong),
        ("reserved",   c_ulong),
        ("u_ar0",      c_void_p),
        ("u_fpstate",  c_void_p),
        ("magic",      c_ulong),
        ("u_comm",     c_char*32),
        ("debug0",     c_ulong),
        ("debug1",     c_ulong),
        ("debug2",     c_ulong),
        ("debug3",     c_ulong),
        ("debug4",     c_ulong),
        ("debug5",     c_ulong),
        ("debug6",     c_ulong),
        ("debug7",     c_ulong),
    )

class user_regs_amd64(Structure):
    _fields_ = [
        ('r15',      c_uint64),
        ('r14',      c_uint64),
        ('r13',      c_uint64),
        ('r12',      c_uint64),
        ('rbp',      c_uint64),
        ('rbx',      c_uint64),
        ('r11',      c_uint64),
        ('r10',      c_uint64),
        ('r9',       c_uint64),
        ('r8',       c_uint64),
        ('rax',      c_uint64),
        ('rcx',      c_uint64),
        ('rdx',      c_uint64),
        ('rsi',      c_uint64),
        ('rdi',      c_uint64),
        ('orig_rax', c_uint64),
        ('rip',      c_uint64),
        ('cs',       c_uint64),
        ('eflags',   c_uint64),
        ('rsp',      c_uint64),
        ('ss',       c_uint64),
        ('fs_base',  c_uint64),
        ('gs_base',  c_uint64),
        ('ds',       c_uint64),
        ('es',       c_uint64),
        ('fs',       c_uint64),
        ('gs',       c_uint64),
    ]


intel_dbgregs = (0,1,2,3,6,7)


class LinuxMixin(v_posix.PtraceMixin, v_posix.PosixMixin):
    """
    The mixin to take care of linux specific platform traits.
    (mostly proc)
    """

    def __init__(self):
        # Wrap reads from proc in our worker thread
        v_posix.PtraceMixin.__init__(self)
        v_posix.PosixMixin.__init__(self)
        self.memfd = None
        self._stopped_cache = {}
        self._stopped_hack = False

        self.fireTracerThread()
        self.setMeta('BadMaps', ['[vvar]', '[vsyscall]'])

        self.initMode("Syscall", False, "Break On Syscalls")

    def setupMemFile(self, offset):
        """
        A utility to open (if necessary) and seek the memfile
        """
        if self.memfd is None:
            self.memfd = libc.open(b"/proc/%d/mem" % self.pid, O_RDWR | O_LARGEFILE, 0o755)
            if self.memfd < 0:
                logger.warning('Failed to get proper file descriptor (errno: %d)', get_errno())

        retn = libc.lseek64(self.memfd, offset, 0)
        if retn < 0:
            logger.warning('lseek64 hit issue with error: %d' % get_errno())

    @v_base.threadwrap
    def platformReadMemory(self, address, size):
        """
        A *much* faster way of reading memory that the 4 bytes
        per syscall allowed by ptrace
        """
        self.setupMemFile(address)
        # Use ctypes cause python implementation is teh ghey
        buf = create_string_buffer(size)
        x = libc.read(self.memfd, addressof(buf), size)
        if x != size:
            # libc.perror('libc.read %d (size: %d)' % (x,size))
            raise Exception("reading from invalid memory %s (%d returned) (errno: %d) (fd: %d)" % (hex(address), x, get_errno(), self.memfd))
        # We have to slice cause ctypes "helps" us by adding a null byte...
        return buf.raw

    @v_base.threadwrap
    def whynot_platformWriteMemory(self, address, data):
        """
        A *much* faster way of writting memory that the 4 bytes
        per syscall allowed by ptrace
        """
        self.setupMemFile(address)
        buf = create_string_buffer(data)
        size = len(data)
        x = libc.write(self.memfd, addressof(buf), size)
        if x != size:
            libc.perror('write mem failed: 0x%.8x (%d)' % (address, size))
            raise Exception("write memory failed: %d" % x)
        return x

    def _findExe(self, pid):
        exe = os.readlink("/proc/%d/exe" % pid)
        if "(deleted)" in exe:
            if "#prelink#" in exe:
                exe = exe.split(".#prelink#")[0]
            elif ";" in exe:
                exe = exe.split(";")[0]
            else:
                exe = exe.split("(deleted)")[0].strip()
        return exe

    @v_base.threadwrap
    def platformExec(self, cmdline):
        # Very similar to posix, but not
        # quite close enough...
        self.execing = True
        cmdlist = e_cli.splitargs(cmdline)
        os.stat(cmdlist[0])
        pid = os.fork()

        if pid == 0:
            try:
                # Don't use PT_TRACEME -- on some linux (tested on ubuntu)
                # it will cause immediate asignment of ptrace slot to parent
                # without parent having PT_ATTACH'D.... MAKES SYNCHRONIZATION HARD
                # SIGSTOP ourself until parent continues us
                os.kill(os.getpid(), signal.SIGSTOP)
                os.execv(cmdlist[0], cmdlist)
            except Exception as e:
                logger.error(e)
            sys.exit(-1)

        # Attach to child. should cause SIGSTOP
        if 0 != v_posix.ptrace(PT_ATTACH, pid, 0, 0):
            raise Exception("PT_ATTACH failed! linux platformExec")

        # Eat all SIGSTOP (or other signal) and break from loop on SIGTRAP.
        # SIGTRAP triggered by execv while PTRACE_ATTACH'd
        while True:
            wpid, status = os.waitpid(pid, os.WUNTRACED)
            if wpid != pid:  # should never happen
                continue
            if os.WIFSTOPPED(status):
                cause = os.WSTOPSIG(status)
                if cause == signal.SIGTRAP:
                    break
                if v_posix.ptrace(v_posix.PT_CONTINUE, pid, 0, 0) != 0:
                    raise Exception("PT_CONTINUE failed! linux platformExec")

        # Do a single step, which will allow a new stop event for the
        # rest of vtrace to eat up.
        if v_posix.ptrace(v_posix.PT_STEP, pid, 0, 0) != 0:
            raise Exception("PT_CONTINUE failed! linux platformExec")

        self.pthreads = [pid]
        self.setMeta("ExeName", self._findExe(pid))
        return pid

    @v_base.threadwrap
    def platformAttach(self, pid):
        self.pthreads = [pid]
        self.setMeta("ThreadId", pid)
        if v_posix.ptrace(PT_ATTACH, pid, 0, 0) != 0:
            raise Exception("PT_ATTACH failed!")
        self.setMeta("ExeName", self._findExe(pid))

    def platformPs(self):
        pslist = []
        for dname in self.platformListDir('/proc'):
            try:
                if not dname.isdigit():
                    continue
                cmdline = self.platformReadFile('/proc/%s/cmdline' % dname)
                cmdline = cmdline.replace(b"\x00", b" ")
                if len(cmdline) > 0:
                    pslist.append((int(dname), cmdline.decode('utf-8')))
            except Exception as e:
                pass  # Permissions...  quick process... whatev.
        return pslist

    def _simpleCreateThreads(self):
        for tid in self.threadsForPid( self.pid ):
            if tid == self.pid:
                continue
            self.attachThread( tid )

    def attachThread(self, tid, attached=False):
        self.doAttachThread(tid, attached=attached)
        self.setMeta("ThreadId", tid)
        self.fireNotifiers(vtrace.NOTIFY_CREATE_THREAD)

    @v_base.threadwrap
    def detachThread(self, tid, ecode):

        self.setMeta('ThreadId', tid)
        self._fireExitThread(tid, ecode)

        if v_posix.ptrace(PT_DETACH, tid, 0, 0) != 0:
            raise Exception("ERROR ptrace detach failed for thread %d" % tid)

        self.pthreads.remove(tid)

    @v_base.threadwrap
    def platformWait(self):
        # Blocking wait once...
        pid, status = os.waitpid(-1, 0x40000002)
        self.setMeta("ThreadId", pid)
        # Stop the rest of the threads...
        # why is linux debugging so Ghetto?!?!
        if not self.stepping:  # If we're stepping, only do the one
            for tid in self.pthreads:
                if tid == pid:
                    continue
                try:
                    # We use SIGSTOP here because they can't mask it.
                    os.kill(tid, signal.SIGSTOP)
                    os.waitpid(tid, 0x40000002)
                except Exception as e:
                    logger.warning("WARNING TID is invalid %d %s", tid, e)
        return pid, status

    @v_base.threadwrap
    def platformContinue(self):
        cmd = v_posix.PT_CONTINUE
        if self.getMode("Syscall", False):
            cmd = PT_SYSCALL
        pid = self.getPid()
        sig = self.getCurrentSignal()
        if sig is None:
            sig = 0
        # Only deliver signals to the main thread
        if v_posix.ptrace(cmd, pid, 0, sig) != 0:
            libc.perror('ptrace PT_CONTINUE failed for pid %d' % pid)
            raise Exception("ERROR ptrace failed for pid %d" % pid)

        for tid in self.pthreads:
            if tid == pid:
                continue
            if v_posix.ptrace(cmd, tid, 0, 0) != 0:
                pass

    @v_base.threadwrap
    def platformStepi(self):
        self.stepping = True
        tid = self.getMeta("ThreadId", 0)
        if v_posix.ptrace(v_posix.PT_STEP, tid, 0, 0) != 0:
            raise Exception("ERROR ptrace failed!")

    @v_base.threadwrap
    def platformDetach(self):
        libc.close(self.memfd)
        for tid in self.pthreads:
            v_posix.ptrace(PT_DETACH, tid, 0, 0)

    @v_base.threadwrap
    def doAttachThread(self, tid, attached=False):
        """
        Do the work for attaching a thread.  This must be *under*
        attachThread() so callers in notifiers may call it (because
        it's also gotta be thread wrapped).
        """
        if not attached:
            if v_posix.ptrace(PT_ATTACH, tid, 0, 0) != 0:
                raise Exception("ERROR ptrace attach failed for thread %d" % tid)

        # We may have already revcieved the stop signal
        if not self._stopped_cache.pop(tid, None):
            os.waitpid(tid, 0x40000002)

        self.setupPtraceOptions(tid)
        self.pthreads.append(tid)

    @v_base.threadwrap
    def setupPtraceOptions(self, tid):
        """
        Called per pid/tid to setup proper options
        for ptrace.
        """
        opts = PT_O_TRACESYSGOOD
        ver = tuple(platform.release()[:3].split('.'))
        if (int(ver[0]), int(ver[1])) >= (2, 6):
            opts |= PT_O_TRACECLONE | PT_O_TRACEEXIT
        x = v_posix.ptrace(PT_SETOPTIONS, tid, 0, opts)
        if x != 0:
            libc.perror('ptrace PT_SETOPTION failed for thread %d' % tid)

    def threadsForPid(self, pid):
        ret = []
        tpath = "/proc/%s/task" % pid
        if os.path.exists(tpath):
            for pidstr in os.listdir(tpath):
                ret.append(int(pidstr))
        return ret

    def platformProcessEvent(self, event):
        # Skim some linux specific events before passing to posix
        tid, status = event
        if os.WIFSTOPPED(status):
            sig = status >> 8 # Cant use os.WSTOPSIG() here...
            # print('STOPPED: %d %d %.8x %d' % (self.pid, tid, status, sig))

            # Ok... this is a crazy little state engine that tries
            # to account for the discrepancies in how linux posts
            # signals to the debugger...

            # Thread Creation:
            # In each case below, the kernel may deliver
            # any of the 3 signals in any order...  ALSO
            # (and more importantly) *if* the kernel sends
            # SIGSTOP to the thread first, the debugger
            # will get a SIGSTOP *instead* of SIG_LINUX_CLONE
            # ( this will go back and forth on *ONE BOX* with
            #   the same kernel version... Finally squished it
            #   because it presents more frequently ( 1 in 10 )
            #   on my new ARM linux dev board. WTF?!1?!one?!? )
            #
            # Case 1 (SIG_LINUX_CLONE):
            #     debugger gets SIG_LINUX CLONE as expected
            #     and can then use ptrace(PT_GETEVENTMSG)
            #     to get new TID and attach as normal
            # Case 2 (SIGSTOP delivered to thread)
            #     Thread is already stoped and attached but
            #     parent debugger doesn't know yet.  We add
            #     the tid to the stopped_cache so when the
            #     kernel gets around to telling the debugger
            #     we don't wait on him again.
            # Case 3 (SIGSTOP delivered to debugger)
            #     In both case 2 and case 3, this will cause
            #     the SIG_LINUX_CLONE to be skipped.  Either
            #     way, we should head down into thread attach.
            #     ( The thread may be already stopped )
            if sig == SIG_LINUX_SYSCALL:
                self.fireNotifiers(vtrace.NOTIFY_SYSCALL)

            elif sig == SIG_LINUX_EXIT:

                ecode = self.getPtraceEvent() >> 8

                if tid == self.getPid():
                    self._fireExit( ecode )
                    self.platformDetach()

                else:
                    self.detachThread(tid, ecode)

            elif sig == SIG_LINUX_CLONE:
                # Handle a new thread here!
                newtid = self.getPtraceEvent()
                # print('CLONE (new tid: %d)' % newtid)
                self.attachThread(newtid, attached=True)

            elif sig == signal.SIGSTOP and tid != self.pid:
                #print('OMG IM THE NEW THREAD! %d' % tid)
                # We're not even a real event right now...
                self.runAgain()
                self._stopped_cache[tid] = True

            elif sig == signal.SIGSTOP:
                # If we are still 'exec()'ing, we havent hit the SIGTRAP
                # yet ( so our process info is still python, lets skip it )
                if self.execing:
                    self._stopped_hack = True
                    self.setupPtraceOptions(tid)
                    self.runAgain()

                elif self._stopped_hack:
                    newtid = self.getPtraceEvent(tid)
                    #print("WHY DID WE GET *ANOTHER* STOP?: %d" % tid)
                    #print('PTRACE EVENT: %d' % newtid)
                    self.attachThread(newtid, attached=True)

                else: # on first attach...
                    self._stopped_hack = True
                    self.setupPtraceOptions(tid)
                    self.handlePosixSignal(sig)

            #FIXME eventually implement child catching!
            else:
                self.handlePosixSignal(sig)

            return

        v_posix.PosixMixin.platformProcessEvent(self, event)

    @v_base.threadwrap
    def getPtraceEvent(self, tid=None):
        """
        This *thread wrapped* function will get any pending GETEVENTMSG
        msgs.
        """
        p = c_ulong(0)
        if tid is None:
            tid = self.getMeta("ThreadId", -1)
        if v_posix.ptrace(PT_GETEVENTMSG, tid, 0, addressof(p)) != 0:
            raise Exception('ptrace PT_GETEVENTMSG failed!')
        return p.value

    def platformGetThreads(self):
        ret = {}
        for tid in self.pthreads:
            ret[tid] = tid  # FIXME make this pthread struct or stackbase soon
        return ret

    def platformGetMaps(self):
        maps = []
        with open("/proc/%d/maps" % self.pid, 'r') as mapfile:
            for line in mapfile:

                perms = 0
                sline = line.split(" ")
                addrs = sline[0]
                permstr = sline[1]
                fname = sline[-1].strip()
                addrs = addrs.split("-")
                base = int(addrs[0],16)
                max = int(addrs[1],16)
                mlen = max-base

                if "r" in permstr:
                    perms |= e_mem.MM_READ
                if "w" in permstr:
                    perms |= e_mem.MM_WRITE
                if "x" in permstr:
                    perms |= e_mem.MM_EXEC
                #if "p" in permstr:
                    #pass

                maps.append((base,mlen,perms,fname))
        return maps

    def platformGetFds(self):
        fds = []
        for name in os.listdir("/proc/%d/fd/" % self.pid):
            try:
                fdnum = int(name)
                fdtype = vtrace.FD_UNKNOWN
                link = os.readlink("/proc/%d/fd/%s" % (self.pid, name))
                if "socket:" in link:
                    fdtype = vtrace.FD_SOCKET
                elif "pipe:" in link:
                    fdtype = vtrace.FD_PIPE
                elif "/" in link:
                    fdtype = vtrace.FD_FILE

                fds.append((fdnum, fdtype, link))
            except Exception:
                logger.error(traceback.format_exc())

        return fds

############################################################################
#
# NOTE: Both of these use class locals set by the i386/amd64 variants
#
    @v_base.threadwrap
    def platformGetRegCtx(self, tid):
        ctx = self.archGetRegCtx()
        u = self.user_reg_struct()
        if v_posix.ptrace(PT_GETREGS, tid, 0, addressof(u)) == -1:
            raise v_exc.PtraceException("PT_GETREGS")

        ctx._rctx_Import(u)
        return ctx

    @v_base.threadwrap
    def platformSetRegCtx(self, tid, ctx):
        u = self.user_reg_struct()
        # Populate the reg struct with the current values (to allow for
        # any regs in that struct that we don't track... *fs_base*ahem*
        if v_posix.ptrace(PT_GETREGS, tid, 0, addressof(u)) == -1:
            raise v_exc.PtraceException("PT_GETREGS")

        ctx._rctx_Export(u)
        if v_posix.ptrace(PT_SETREGS, tid, 0, addressof(u)) == -1:
            raise v_exc.PtraceException("PT_SETREGS")

class Linuxi386Trace(
        vtrace.Trace,
        LinuxMixin,
        v_i386.i386Mixin,
        v_posix.ElfMixin,
        v_base.TracerBase):

    user_reg_struct = user_regs_i386
    user_dbg_offset = 252
    reg_val_mask = 0xffffffff

    def __init__(self):
        vtrace.Trace.__init__(self)
        v_base.TracerBase.__init__(self)
        v_posix.ElfMixin.__init__(self)
        v_i386.i386Mixin.__init__(self)
        LinuxMixin.__init__(self)

        # Pre-calc the index of the debug regs
        self.dbgidx = self.archGetRegCtx().getRegisterIndex("debug0")

    @v_base.threadwrap
    def platformGetRegCtx(self, tid):
        ctx = LinuxMixin.platformGetRegCtx( self, tid )
        for i in intel_dbgregs:
            offset = self.user_dbg_offset + (self.psize * i)
            r = v_posix.ptrace(v_posix.PT_READ_U, tid, offset, 0)
            ctx.setRegister(self.dbgidx+i, r & self.reg_val_mask)
        return ctx

    @v_base.threadwrap
    def platformSetRegCtx(self, tid, ctx):
        LinuxMixin.platformSetRegCtx( self, tid, ctx )
        for i in intel_dbgregs:
            val = ctx.getRegister(self.dbgidx + i)
            offset = self.user_dbg_offset + (self.psize * i)
            if v_posix.ptrace(v_posix.PT_WRITE_U, tid, offset, val) != 0:
                libc.perror('PT_WRITE_U failed for debug%d' % i)

    @v_base.threadwrap
    def platformAllocateMemory(self, size, perms=e_mem.MM_RWX, suggestaddr=0):
        sp = self.getStackCounter()
        pc = self.getProgramCounter()

        # Xlate perms (mmap is backward)
        realperm = 0
        if perms & e_mem.MM_READ:
            realperm |= 1
        if perms & e_mem.MM_WRITE:
            realperm |= 2
        if perms & e_mem.MM_EXEC:
            realperm |= 4

        #mma is struct of mmap args for linux syscall
        mma = struct.pack("<6L", suggestaddr, size, realperm, MAP_ANONYMOUS|MAP_PRIVATE, 0, 0)

        regsave = self.getRegisters()

        stacksave = self.readMemory(sp, len(mma))
        ipsave = self.readMemory(pc, 2)

        SYS_mmap = 90

        self.writeMemory(sp, mma)
        self.writeMemory(pc, b"\xcd\x80")
        self.setRegisterByName("eax", SYS_mmap)
        self.setRegisterByName("ebx", sp)
        self._syncRegs()

        try:
            # Step over our syscall instruction
            tid = self.getMeta("ThreadId", 0)
            self.platformStepi()
            os.waitpid(tid, 0)
            eax = self.getRegisterByName("eax")
            if eax & 0x80000000:
                raise Exception("Linux mmap syscall error: %d" % eax)
            return eax

        finally:
            # Clean up all our fux0ring
            self.writeMemory(sp, stacksave)
            self.writeMemory(pc, ipsave)
            self.setRegisters(regsave)


class LinuxAmd64Trace(
        vtrace.Trace,
        LinuxMixin,
        v_amd64.Amd64Mixin,
        v_posix.ElfMixin,
        v_base.TracerBase):

    user_reg_struct = user_regs_amd64
    user_dbg_offset = 848
    reg_val_mask = 0xffffffffffffffff

    def __init__(self):
        vtrace.Trace.__init__(self)
        v_base.TracerBase.__init__(self)
        v_posix.ElfMixin.__init__(self)
        v_amd64.Amd64Mixin.__init__(self)
        LinuxMixin.__init__(self)
        self.dbgidx = self.archGetRegCtx().getRegisterIndex("debug0")

    @v_base.threadwrap
    def platformGetRegCtx(self, tid):
        ctx = LinuxMixin.platformGetRegCtx( self, tid )
        for i in intel_dbgregs:
            offset = self.user_dbg_offset + (self.psize * i)
            r = v_posix.ptrace(v_posix.PT_READ_U, tid, offset, 0)
            ctx.setRegister(self.dbgidx+i, r & self.reg_val_mask)

        self.platformGetExtendedRegs(tid, ctx)
        return ctx

    @v_base.threadwrap
    def platformSetRegCtx(self, tid, ctx):
        LinuxMixin.platformSetRegCtx( self, tid, ctx )
        for i in intel_dbgregs:
            val = ctx.getRegister(self.dbgidx + i)
            offset = self.user_dbg_offset + (self.psize * i)
            if v_posix.ptrace(v_posix.PT_WRITE_U, tid, offset, val) != 0:
                libc.perror('PT_WRITE_U failed for debug%d' % i)

    def parseXSave(self, ctx, iovec):
        '''
        PT_GETREGSET basically just dumps the xsave memory region, so we need to parse that out
        '''
        # There are other registers that are saved in here, but for now, fuck 'em
        simd_regs = [0 for i in range(16)]
        fpu_off = 32
        fpu_len = 8
        # yes you could get this by various other PTRACE calls, but since we already have to call into NT_X86_XSTATE, 
        # might as well grab these while we're here
        regidx = self.archGetRegCtx().getRegisterIndex("st0")
        mask = 0xFFFFFFFFFFFFFFFFFFFF  # 80 bit mask for floating points regs
        for i in range(fpu_len):
            offset = fpu_off + i * 16
            # the upper 48 bits of the st/mm registers are marked as reserved
            valu = e_bits.parsebytes(bytes(iovec[offset:offset+10]), 0, 10)
            ctx.setRegister(regidx+i, valu)

        xmm_off = 160

        # these are just the lower bits of the simd registers (just the xmm portion)
        for i in range(len(simd_regs)):
            offset = xmm_off + i * 16
            simd_regs[i] = e_bits.parsebytes(bytes(iovec[offset:offset+16]), 0, 16)

        xstate_bv = e_bits.parsebytes(bytes(iovec[512:520]), 0, 8)
        has_avx = xstate_bv & 0x4
        # XXX: Sooooo....we're gonna cheat a bit here. Technically what we're supposed to do
        # is check CPUID.(EAX=0x0D, ECX=i) for every feature and se how many bytes it takes up, but 
        # right now the goal is just to get the upper YMM registers, and we know exactly how
        # many bytes those take up, and they're literally the first state component in the extended
        # xsave region (standard or compacted), so let's parse us some bytes if the has_avx bit is set.
        # (we're also doing it this way because I don't feel like figuring out how to directly call
        # the cpuid asm instruction from python)
        if has_avx:
            ymm_offset = 576
            for i in range(len(simd_regs)):
                offset = ymm_offset + i*16
                valu = e_bits.parsebytes(bytes(iovec[offset:offset+16]), 0, 16)
                simd_regs[i] |= valu << 128

        regidx = self.archGetRegCtx().getRegisterIndex("ymm0")
        for i, valu in enumerate(simd_regs):
            ctx.setRegister(regidx+i, valu)

    def platformGetExtendedRegs(self, tid, ctx):
        '''
        for now, the only real way to get access to things like YMM and ZMM registers
        '''
        buflen = 2048  # Guess. Actual length will be set by kernel
        buffer = (c_uint8 * buflen)()
        vec = iovec(cast(buffer, c_void_p), buflen)

        if v_posix.ptrace(PT_GETREGSET, tid, NT_X86_XSTATE, addressof(vec)) != 0:
            raise v_exc.PtraceException("PT_GETREGSET(NT_X86_XSTATE)")

        self.parseXSave(ctx, buffer)



arm_break_be = binascii.unhexlify('e7f001f0')
arm_break_le = binascii.unhexlify('f001f0e7')

class LinuxArmTrace(
        vtrace.Trace,
        LinuxMixin,
        v_arm.ArmMixin,
        v_posix.ElfMixin,
        v_base.TracerBase):

    user_reg_struct = user_regs_arm
    reg_val_mask = 0xffffffff

    def __init__(self):
        vtrace.Trace.__init__(self)
        v_base.TracerBase.__init__(self)
        v_posix.ElfMixin.__init__(self)
        v_arm.ArmMixin.__init__(self)
        LinuxMixin.__init__(self)

        self._break_after_bp = False
        self._step_cleanup = []

    def _fireStep(self):
        # See notes below about insanity...
        if self._step_cleanup is not None:
            [ self.writeMemory( bva, bytes ) for (bva,bytes) in self._step_cleanup ]
            self._step_cleanup = None
        return v_base.TracerBase._fireStep( self )

    def archGetBreakInstr(self):
        return arm_break_le

    @v_base.threadwrap
    def platformStepi(self):
        # This is a total rediculous hack to account
        # for the fact that the arm platform couldn't
        # be bothered to implement single stepping in
        # the stupid hardware...

        self.stepping = True

        pc = self.getProgramCounter()
        op = self.parseOpcode( pc )

        branches = op.getBranches( self )
        if not branches:
            raise Exception('''
                    The branches for the instruction %r were not decoded correctly.  This means that
                    we cant properly predict the possible next instruction executions in a way that allows us
                    to account for the STUPID INSANE FACT THAT THERE IS NO HARDWARE SINGLE STEP CAPABILITY ON
                    ARM (non-realtime or JTAG anyway).  We *would* have written invalid instructions to each
                    of those locations and cleaned them up before you ever knew anything was amiss... which is
                    how we pretend arm can single step... even though IT CANT. (please tell visi...)
            ''' % op)

        # Save the memory at the branches for later
        # restoration in the _fireStep callback.

        self._step_cleanup = []
        for bva,bflags in op.getBranches( self ):
            self._step_cleanup.append( (bva, self.readMemory( bva, 4 )) )
            self.writeMemory( bva, arm_break_le )

        tid = self.getMeta('ThreadId')

        if v_posix.ptrace(v_posix.PT_CONTINUE, tid, 0, 0) != 0:
            raise Exception("ERROR ptrace failed for tid %d" % tid)

