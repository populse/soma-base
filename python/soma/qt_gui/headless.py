# -*- coding: utf-8 -*-

''' soma.qt_gui.headless module implements a headless (off-screen) version of
Qt with OpenGL enabled, and some helper functions. The normal way to use it is via the :mod:`soma.qt_gui.qt_backend` module::

    from soma.qt_gui import qt_backend
    qt_backend.set_headless()
    # then use Qt:
    from soma.qt_gui.qt_backend import QtWidgets
    import sys

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

Otherwise, at lower_level, you may use::

    from soma.qt_gui import headless
    headless.setup_headless()

Note that this headless mode has to be activated prior to any OpenGL libraries being loaded in the current process and the display initialized, otherwise it will not be possible to set it up.

For OpenGL settings, it is more complex than that: the program must specify whether it will use OpenGL or not later, because the way we setup the headless mode depends on it. If we will not use OpenGL, then a "lighter" solution may work (using Qt "offscreen platform") in a wider range of situations. If Qt offscreen cannot be used, then we have to switch to a virtual X server (Xfvb), which starts a server in a separate process, and has to be shut down.

'''

# There is a pile of problems in this headless setup:
#
# - Qt "offscreen platform" mode sometimes works, but not always: we have to
#   test it in a separate test process.
# - if OpenGL has to be used, Qt "offscreen" mode only works if a X display is
#   actually available.
# - Xvfb with a GLX server may use VirtualGL for hardware rendering,
# - but it doesn't always work: we have to test it in a separate test process.
# - sometimes GLW won't work using the default current OpenGL implementation.
#   Then we have to switch to a software Mesa OpenGL library, if it is
#   available and found. Our casa-distro containers and pixi environments do
#   provide one.
# - But changing OpenGL library implies that it is not already loaded. So it
#   must be initialized before QtWidgets is imported.
# - some Qt modules (QtWebEngine) need to be imported before a QApplication is
#   built
# - Some QApplication static flags have to be set before QApplication is built
#
# so we have to control the order of import and initialization of everything...

from soma import subprocess
import os
from soma.subprocess import Popen, check_output
import time
import ctypes
import sys
import shutil
import atexit

virtual_display = 'xvfb'
virtual_display_proc = None
original_display = None
display = None
force_virtualgl = True
headless_initialized = None


def terminate_virtual_display():
    global virtual_display
    global virtual_display_proc
    global original_display
    global display

    if virtual_display_proc is None:
        return

    virtual_display_proc.terminate()
    virtual_display_proc.wait()
    virtual_display_proc = None

    if original_display:
        os.environ['DISPLAY'] = original_display
    else:
        del os.environ['DISPLAY']

    if virtual_display == 'xpra':
        subprocess.call(['xpra', 'stop', str(display)])


# this is not needed any longer for Xvfb, since on_parent_exit() is passed
# to Popen, but xpra needs to stop the corresponding server
#
# anyway we need to set it up at startup, begore Qt is initialized
# to have the correct call order for atexit functions.
# see https://github.com/The-Compiler/pytest-xvfb/issues/11
if virtual_display_proc is not None:
    atexit.register(terminate_virtual_display)


def setup_virtualGL():
    ''' Load VirtualGL libraries and LD_PRELOAD env variable to run the current
    process via VirtualGL.

    .. warning::
        If the current process has already used some libraries (libX11? libGL
        certainly), setting VirtualGL libs afterwards may cause segfaults and
        program crashes. So it is not safe to use it unless you are sure to do
        it straight at the beginning of the program, prior to importing many
        modules.

        Unfortunately, I don't know how to test it.
    '''
    if os.environ.get('VGL_ISACTIVE') == '1':
        return True
    try:
        if 'VGL_DISPLAY' not in os.environ and original_display is not None:
            # set VGL_DISPLAY to be the initial (3D accelerated) display
            os.environ['VGL_DISPLAY'] = original_display
            print('VGL_DISPLAY:', original_display)
        # needed if libGL is not directly linked against the executable
        os.environ['VGL_GLLIB'] = 'libGL.so.1'
        preload = ['libdlfaker']
        # vglrun may use either librrfaker or libvglfaker depending on its
        # version.
        try:
            vglfaker = ctypes.CDLL('librrfaker.so', ctypes.RTLD_GLOBAL)
            preload.append('librrfaker.so')
        except:
            vglfaker = ctypes.CDLL('libvglfaker.so', ctypes.RTLD_GLOBAL)
            preload.append('libvglfaker.so')
        #dlfaker = ctypes.CDLL('libdlfaker.so', ctypes.RTLD_GLOBAL)
        os.environ['LD_PRELOAD'] = ':'.join(preload)
        os.environ['VGL_ISACTIVE'] = '1'
    except Exception:
        return False
    return True


def test_glx(glxinfo_cmd=None, xdpyinfo_cmd=None, timeout=5.):
    ''' Test the presence of the GLX module in the X server, by running
    glxinfo or xdpyinfo command

    Parameters
    ----------
    glxinfo_cmd: str or list
        glxinfo command: may be a string ('glxinfo') or a list, which allows
        running it through a wrapper, ex: ['vglrun', 'glxinfo']
    xdpyinfo_cmd: str or list
        xdpyinfo command: may be a string ('xdpyinfo') or a list, which allows
        running it through a wrapper, ex: ['vglrun', 'xdpyinfo']. xdpyinfo is
        only used if glxinfo is not present, and can produce an inaccurate
        result (some xvfb servers advertise a GLX extension which does not
        work in fact).
    timeout: float (optional)
        try several times to connect the X server while waiting for it to
        startup. If 0, try only once and return.

    Returns
    -------
    2 if GLX is recognized through glxinfo (trustable), 1 if GLX is recognized
    through xdpyinfo (not always trustable), 0 otherwise.
    '''
    if glxinfo_cmd is None:
        glxinfo_cmd = shutil.which('glxinfo')
        if glxinfo_cmd is not None:
            glxinfo_cmd = [glxinfo_cmd]
    if glxinfo_cmd not in (None, []):
        glxinfo = ''
        t0 = time.time()
        t1 = 0
        while glxinfo == '' and t1 <= timeout:
            # universal_newlines = open stdout/stderr in text mode (Unicode)
            process = Popen(glxinfo_cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            universal_newlines=True)
            try:
                glxinfo, glxerr = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                glxinfo, glxerr = process.communicate()
                raise subprocess.TimeoutExpired(process.args, 5,
                                                output=glxinfo)
            retcode = process.poll()

            if retcode != 0:
                if u'unable to open display' not in glxerr:
                    # failed for another reason: probably GLX is not working
                    break
                time.sleep(0.01)
                t1 = time.time() - t0
        if glxinfo != u'' or t1 > timeout:
            if u' GLX Visuals' not in glxinfo:
                return 0
            else:
                return 2

    # here glxinfo has not been used or is not working
    if xdpyinfo_cmd is None:
        xdpyinfo_cmd = shutil.which('xdpyinfo')
    dpyinfo = u''
    t0 = time.time()
    t1 = 0
    while dpyinfo == u'' and t1 <= timeout:
        try:
            # universal_newlines = open stdout/stderr in text mode (Unicode)
            dpyinfo = check_output(xdpyinfo_cmd,
                                   universal_newlines=True)
        except Exception as e:
            time.sleep(0.01)
            t1 = time.time() - t0
    if u'GLX' not in dpyinfo:
        return 0
    else:
        return 1


def test_opengl(pid=None, verbose=False):
    ''' Test the presence of OpenGL libraries (and which ones) in the specified
    Unix process. Works only on Linux (or maybe ELF Unixes).

    Parameters
    ----------
    pid: int (optional)
        process id to look OpenbGL libs in. Default: current process
    verbose: bool (optional)
        if True, print found libs

    Returns
    -------
    set of loaded libGL libraries
    '''
    if pid is None:
        pid = os.getpid()
    gl_libs = set()
    with open('/proc/%d/maps' % pid) as f:
        for line in f.readlines():
            lib = line.split()[-1]
            if lib not in gl_libs and lib.find('libGL.so.') != -1:
                gl_libs.add(lib)
                if verbose:
                    print(lib)
    return gl_libs


def test_qapp():
    ''' If QtGui is already loaded, switching to VirtualGL in the running
    process leads to segfaults, or even using GLX in PyQt6.
    Moreover if QApplication is instantiated, the display is already connected
    and cannot change in Qt afterwards.
    However if only a QCoreApplication exists, it is possible to instantiate a
    QApplication in addition (without deleting the QCoreApplication). But
    VirtualGL cannot be used.
    '''
    from soma.qt_gui.qt_backend import QtCore
    if QtCore.QCoreApplication.instance() is not None:
        if QtCore.QCoreApplication.instance().__class__.__name__ \
                != 'QCoreApplication':
            return 'QApp'
        from soma.qt_gui import qt_backend
        if qt_backend.qt_backend == 'PyQt6' and 'PyQt6.QtGui' in sys.modules:
            return 'QApp'  # QtGui is loaded: don't use headless
        return 'QtCore'
    return None



def find_mesa():
    ''' Try to find a software Mesa library in the libraries search path.
    Parses the LD_LIBRARY_PATH env variable and libs listed by the command
    "ldconfig -p", looks for a mesa/ subdir containing a libGL.so.1 file.

    Returns
    -------
    Mesa library file with full path, or None if not found
    '''
    paths = os.environ.get('LD_LIBRARY_PATH')
    ldconfig = check_output(['ldconfig', '-p'], text=True)
    paths2 = [os.path.dirname(p.split()[-1])
              for p in ldconfig.split('\n')[1:-1]]
    if paths:
        paths = paths.split(':')
    else:
        paths = []
    spaths = set(paths)
    for p in paths2:
        if p not in spaths:
            paths.append(p)
            spaths.add(p)
    if os.path.exists('/proc/self/maps'):
        # add lib paths not configured but found via rpaths
        with open('/proc/self/maps') as f:
            for line in f.readlines():
                lib = line.strip().split()[-1]
                p = os.path.abspath(os.path.dirname(lib))
                if p not in spaths:
                    paths.append(p)
                    spaths.add(p)
    for path in paths:
        for p in ['mesa', 'mesalib/lib', '../mesalib/lib']:
            test_gl = os.path.abspath(os.path.join(path, p, 'libGL.so.1'))
            if os.path.exists(test_gl):
                return test_gl
    return None


def start_xvfb(displaynum=None):
    if shutil.which('Xvfb') is None:
        return None
    if displaynum is None:
        for tdisplay in range(100):
            if not os.path.exists('/tmp/.X11-unix/X%d' % tdisplay) \
                    and not os.path.exists('/tmp/.X%d-lock' % tdisplay):
                break
        else:
            raise RuntimeError('Too many X servers')
    else:
        tdisplay = int(displaynum)
    xvfb = Popen(['Xvfb', '-screen', '0', '1280x1024x24',
                  '+extension', 'GLX', ':%d' % tdisplay],
                 preexec_fn=on_parent_exit('SIGINT'))
    if xvfb:
        global display
        display = tdisplay

    return xvfb


def start_xpra(displaynum=None):
    if shutil.which('xpra') is None:
        return None
    if displaynum is None:
        for tdisplay in range(100):
            if not os.path.exists('/tmp/.X11-unix/X%d' % tdisplay) \
                    and not os.path.exists('/tmp/.X%d-lock' % tdisplay):
                break
        else:
            raise RuntimeError('Too many X servers')
    else:
        tdisplay = str(displaynum)
    xpra = Popen(['xpra', 'start', ':%d' % tdisplay,],
                 preexec_fn=on_parent_exit('SIGINT'))
    if xpra:
        global display
        display = tdisplay

    return xpra


def start_virtual_display(display=None):
    global virtual_display
    global virtual_display_proc

    if virtual_display == 'xvfb':
        virtual_display_proc = start_xvfb(display)
        if virtual_display_proc is not None:
            return virtual_display_proc
        else:
            virtual_display = 'xpra'
    if virtual_display == 'xpra':
        virtual_display_proc = start_xpra(display)
    return virtual_display_proc


class PrCtlError(Exception):
    pass


def on_parent_exit(signame):
    """
    Return a function to be run in a child process which will trigger SIGNAME
    to be sent when the parent process dies

    found on https://gist.github.com/evansd/2346614
    """
    import signal
    from ctypes import cdll

    # Constant taken from https://linux.die.net/man/2/prctl
    PR_SET_PDEATHSIG = 1

    signum = getattr(signal, signame)

    def set_parent_exit_signal():
        # https://linux.die.net/man/2/prctl
        result = cdll['libc.so.6'].prctl(PR_SET_PDEATHSIG, signum)
        if result != 0:
            raise PrCtlError('prctl failed with error code %s' % result)
    return set_parent_exit_signal


def test_qt_offscreen():
    # test OpenGL context creation in a separate process
    script = '''from soma.qt_gui.qt_backend import Qt
import os
import sys

if Qt.QT_VERSION >= 0x060000:
    # in Qt6 we get the message
    # "QOpenGLWidget is not supported on this platform."
    # then the application crashes when using AWindow3D.snapshot().
    sys.exit(1)

Qt.QCoreApplication.setAttribute(
    Qt.Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
app = Qt.QApplication([sys.argv[0], '-platform', 'offscreen'])
# sip.transferto(app, None)  # to prevent deletion just after now

# test OpenGL context creation
context = Qt.QOpenGLContext()
if not context.create():
    res = 1
else:
    res = 0
sys.exit(res)
'''
    cmd = [sys.executable, '-c', script]
    try:
        res = True
        subprocess.check_call(cmd)
        print('Qt offscreen works.')
    except Exception:
        print('Qt offscreen does not work.')
        res = False

    return res


def setup_headless_xvfb(need_opengl=True, allow_virtualgl=True,
                        force_virtualgl=force_virtualgl):
    ''' Sets up a headless virtual X server and tunes the current process
    libraries to use it appropriately.

    .. warning::
        calling this function may run a Xvfb or xpra process, and change the
        current process libraries to use VirtualGL or Mesa GL.

    If OpenGL library or Qt QtGui module is loaded, then VirtualGL will not be
    allowed to prevent crashes.

    If Qt QApplication is instantiated, headless mode is disabled because Qt
    is already connected to a display that cannot change afterwards.

    If no configuration proves to work, raise an exception.

    Parameters
    ----------
    need_opengl: bool (optional)
        if True, OpenGL is required, thus we will try to force GLX extension
        and perhaps VirtualGL in the X seerver.
    allow_virtualgl: bool (optional)
        If False, VirtualGL will not be attempted. Default is True.
        Use it if you experience crashes in your programs: it probably means
        that some incompatible libraries have alrealy been loaded.
    force_virtualgl: bool (optional)
        only meaningful if allow_virtualgl is True. If force_virtualgl True,
        virtualGL will be attempted even if the X server advertises a GLX
        extension. This is useful when GLX is present but does not work when
        OpenGL is used.
    '''

    global virtual_display_proc
    global virtual_display
    global original_display

    class Result(object):
        def __init__(self):
            self.virtual_display_proc = None
            self.original_display = None
            self.display = None
            self.glx = None
            self.virtualgl = None
            self.headless = None
            self.mesa = False
            self.qtapp = None
            self.qapp = None

    result = Result()
    result.virtual_display_proc = virtual_display_proc
    result.original_display = original_display

    if virtual_display_proc:
        # already setup
        return result
    if sys.platform in ('darwin', 'win32'):
        # not a X11 implementation
        result.headless = False
        return result

    qtapp = test_qapp()
    # print('qtapp:', qtapp)
    result.qtapp = qtapp

    if qtapp == 'QApp':
        import sip
        from soma.qt_gui.qt_backend import QtWidgets

        sip.delete(QtWidgets.QApplication.instance())
        # it seems that deleting the QApplication and recreating it actually
        # works (but virtualGL should not be used).

        ## QApplication has already opened the current display: we cannot change
        ## it afterwards.
        #print('QApplication already instantiated, headless Qt is not '
              #'possible.')
        #result.headless = False
        #return result

    use_xvfb = True
    glxinfo_cmd = shutil.which('glxinfo')
    xdpyinfo_cmd = shutil.which('xdpyinfo')
    # if not xdpyinfo_cmd:
    # not a X client, probably not Linux
    # use_xvfb = False
    xvfb_cmd = shutil.which('Xvfb')
    if not xvfb_cmd:
        use_xvfb = False

    if use_xvfb:
        virtual_display_proc = start_virtual_display()

    if virtual_display_proc is not None:
        global display

        original_display = os.environ.get('DISPLAY', None)
        print('using DISPLAY=:%s' % display)
        os.environ['DISPLAY'] = ':%s' % display

        result.original_display = original_display
        result.display = display
        result.virtual_display_proc = virtual_display_proc
        result.headless = True

        if need_opengl:
            glx = test_glx(glxinfo_cmd=glxinfo_cmd, xdpyinfo_cmd=xdpyinfo_cmd)
            result.glx = glx

            gl_libs = set()
            if not glx:
                gl_libs = test_opengl(verbose=True)
                if len(gl_libs) != 0:
                    print('OpenGL lib already loaded. Using Xvfb or xpra will '
                          'not be possible.')
                    result.virtual_display_proc = None

            # WARNING: the test was initially glx < 2, but then it would not
            # enable virtualGL if glx is detected through glxinfo. I don't
            # remember why this was done this way, we perhaps experienced some
            # crashes.

            if (glx < 2 or force_virtualgl) and not gl_libs \
                    and allow_virtualgl and qtapp is None:
                # try VirtualGL
                vgl = shutil.which('vglrun')
                if vgl:
                    print('VirtualGL found.')
                    vglglxinfo_cmd = None
                    vglxdpyinfo_cmd = None
                    disp = original_display
                    if disp is None:
                        disp = ""  # will fail but the command will run
                    if glxinfo_cmd:
                        vglglxinfo_cmd = [vgl, '-d', disp, glxinfo_cmd]
                    if xdpyinfo_cmd:
                        vglxdpyinfo_cmd = [vgl, '-d', disp, xdpyinfo_cmd]
                    if test_glx(glxinfo_cmd=vglglxinfo_cmd,
                                xdpyinfo_cmd=vglxdpyinfo_cmd, timeout=0):
                        print('VirtualGL should work.')

                        glx = setup_virtualGL()
                        result.virtualgl = glx

                        if glx:
                            print('Running through VirtualGL + %s: '
                                  'this is optimal.' % virtual_display)
                        else:
                            print('But VirtualGL could not be loaded...')

                        # test_opengl(verbose=True)
            else:
                print('Too dangerous to use VirtualGL: QCoreApplication is '
                      'instantiated, or GLX is not completely OK, or OpenGL '
                      'libs are loaded.')

            if not glx and not gl_libs:
                # try Mesa, if found
                mesa = find_mesa()
                if mesa:
                    print('MESA found:', mesa)
                    preload = mesa
                    try:
                        mesa_lib = ctypes.CDLL(mesa, ctypes.RTLD_GLOBAL)
                    except OSError:
                        glapi = os.path.join(os.path.dirname(mesa),
                                             'libglapi.so.0')
                        ctypes.CDLL(glapi, ctypes.RTLD_GLOBAL)
                        mesa_lib = ctypes.CDLL(mesa, ctypes.RTLD_GLOBAL)
                        preload = f'{glapi}:{mesa}'
                    os.environ['LD_PRELOAD'] = preload
                    os.environ['LD_LIBRARY_PATH'] \
                        = os.path.dirname(mesa) + ':' \
                        + os.getenv('LD_LIBRARY_PATH')
                    # re-run Xvfb using new path
                    virtual_display_proc.terminate()
                    virtual_display_proc.wait()
                    virtual_display_proc = start_virtual_display(
                        display=display)
                    result.virtual_display_proc = virtual_display_proc
                    #self.mesa_lib = mesa_lib
                    glx = test_glx(glxinfo_cmd, xdpyinfo_cmd)
                    result.glx = glx
                    result.mesa = True
                    if glx:
                        print('Running using Mesa software OpenGL: '
                              'performance '
                              'will be slow. To get faster results, and if X '
                              'server connection can be obtained, consider '
                              'installing VirtualGL (https://virtualgl.org) '
                              'and running again before loading QtGui.')
                else:
                    print('Mesa not found.')

            if not glx:
                print('The current virtual display does not have a GLX '
                      'extension. Aborting it.')
                virtual_display_proc.terminate()
                virtual_display_proc.wait()
                virtual_display_proc = None
                result.virtual_display_proc = None
                if original_display is not None:
                    os.environ['DISPLAY'] = original_display
                    result.display = original_display
                else:
                    del os.environ['DISPLAY']
                    result.display = None
                use_xvfb = False
                #raise RuntimeError('GLX extension missing')

        if not use_xvfb:
            if xdpyinfo_cmd:
                glx = test_glx(glxinfo_cmd, xdpyinfo_cmd, 0)
                result.glx = glx
                if not glx:
                    raise RuntimeError('GLX extension missing')
            print('Qt running in normal (non-headless) mode')
            result.headless = False

    # for an obscure unknown reason, we now need to use the offscreen mode of
    # Qt, even through xvfb, otherwise it cannot build an OpenGL context.
    from soma.qt_gui.qt_backend import Qt
    Qt.QCoreApplication.setAttribute(
        Qt.Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    # QtWebEngine has very strict and difficult requirements. We have to
    # load it now.
    from soma.qt_gui.qt_backend import sip
    if Qt.QCoreApplication.instance() is not None:
        sip.delete(Qt.QCoreApplication.instance())
    try:
        from soma.qt_gui.qt_backend import QtWebEngineWidgets
    except ImportError:
        pass  # maybe not installed

    app = Qt.QApplication([sys.argv[0], '-platform', 'offscreen'])
    sip.transferto(app, None)  # to prevent deletion just after now
    # we need to keep a reference to the qapp, otherwise it gets
    # replaced with a QCoreApplication instance for an unknown reason.
    result.qapp = app

    return result


def setup_headless(need_opengl=True, allow_virtualgl=True,
                   force_virtualgl=force_virtualgl):

    class Result(object):
        def __init__(self):
            self.virtual_display_proc = None
            self.original_display = None
            self.display = None
            self.glx = None
            self.virtualgl = None
            self.headless = None
            self.mesa = False
            self.qtapp = None
            self.qt_offscreen = None
            self.qapp = None

    global headless_initialized
    if headless_initialized is not None:
        return headless_initialized

    result = Result()
    result.virtual_display_proc = virtual_display_proc
    result.original_display = original_display
    headless_initialized = result
    # print('HEADLESS INIT:', headless_initialized, test_opengl())

    qtapp = test_qapp()
    # print('qtapp:', qtapp)
    result.qtapp = qtapp
    if need_opengl and not test_qt_offscreen():
        # a context cannot be created: happens if a X server connection cannot
        # be obtained. The offscreen mode of Qt doesn't show widgets,
        # but for OpenGL, it requires a X11 connection (on linux systems)
        print('Cannot allocate an OpenGL context. Using Xvfb if possible.')
        if qtapp != 'QApp':
            # only if no QtApp has been built, try the xvfb method
            headless_initialized = setup_headless_xvfb(
                need_opengl=need_opengl,
                allow_virtualgl=allow_virtualgl,
                force_virtualgl=force_virtualgl)
            return headless_initialized
        qtapp = 'QApp'

    if qtapp == 'QApp':
        # QApplication has already opened the current display: we cannot change
        # it afterwards.
        print('QApplication already instantiated, headless Qt is not '
              'possible.')
        result.qt_offscreen = False
        result.headless = False
        return result

    print('starting QApplication offscreen.')
    # import QtWidgets in non-headless mode (to avoid recursion)
    from soma.qt_gui import qt_backend
    qt_backend.headless = False
    from soma.qt_gui.qt_backend import QtWidgets, QtCore
    qt_backend.headless = True
    # print('former app:', QtCore.QCoreApplication.instance())
    QtCore.QCoreApplication.setAttribute(
        QtCore.Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    if hasattr(QtWidgets, 'QApplication'):
        # QtWebEngine has very strict and difficult requirements. We have to
        # load it now.
        from soma.qt_gui.qt_backend import sip
        if QtCore.QCoreApplication.instance() is not None:
            sip.delete(QtCore.QCoreApplication.instance())
        try:
            qt_backend.headless = False
            from soma.qt_gui.qt_backend import QtWebEngineWidgets
            qt_backend.headless = True
        except ImportError:
            pass  # maybe not installed

        app = QtWidgets.QApplication([sys.argv[0], '-platform', 'offscreen'])
        sip.transferto(app, None)  # to prevent deletion just after now
        # we need to keep a reference to the qapp, otherwise it gets
        # replaced with a QCoreApplication instance for an unknown reason.
        result.qapp = app
    # else we are inside qt_backend import of Qt: it will finish it on his side

    result.qt_offscreen = True
    result.headless = True
    if need_opengl:
        # here test_qt_offscreen() should be OK, mark it as working
        result.glx = 2

    return result
