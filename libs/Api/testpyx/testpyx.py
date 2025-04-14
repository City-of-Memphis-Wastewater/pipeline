#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Niniejsze dane stanowią tajemnicę przedsiębiorstwa.
# The contents of this file is proprietary information.

import pyxeds2
import time
import sys

# -----------------------------------------------------------------------------
# pyxeds2.LiveEDS test
# -----------------------------------------------------------------------------

def test_live(rhost, rport):
    live = pyxeds2.createLive()
    live.setupLogger('debug=7 subsystems=ALL logger=console:7')

    err = live.init(pyxeds2.LiveMode.ReadWrite,
                    '0.0.0.0', 0,
                    rhost, rport, 0, 32768)

    if pyxeds2.liveErrCode(err) != pyxeds2.LiveErrCode.NoError:
        print 'init() returned:', pyxeds2.liveErrMessage(err)
        return

    lid_1 = live.findByIESS_NoCase('0_IesS')
    lid_2 = live.findByIESS_NoCase('110_IESS')
    lid_3 = live.findByIESS_NoCase('150_iEss')

    print 'lid_1 =', lid_1
    print 'lid_2 =', lid_2
    print 'lid_3 =', lid_3

    live.setInput(lid_3)
    live.setInput(lid_2)
    live.setOutput(lid_1)

    field_id = live.fieldIdFromName('UN')

    for z in range(0, 6):
        errcode = pyxeds2.liveErrCode(live.synchronizeInput())
        if errcode != pyxeds2.LiveErrCode.NoError:
            print 'synchronizeInput() returned:',pyxeds2.liveErrMessage(errcode)
            if errcode == pyxeds2.LiveErrCode.ProtocolMismatch:
                return

        try:
            print 'lid=%d IESS=%s' % (lid_3,
                                      live.readStringField(lid_3, 'IESS'))
            print 'lid=%d value=%s' % (lid_3, live.readAnalog(lid_3))
            print 'lid=%d UN=%s' % (lid_3,
                                    live.readStringField(lid_3, field_id))
            print 'lid=%d T=%s' % (lid_3, live.readStringField(lid_3, 'T'))

            print 'lid=%d IESS=%s' % (lid_2,
                                      live.readStringField(lid_2, 'IESS'))
            print 'lid=%d value=%s' % (lid_2,live.readAnalog(lid_2))
            print 'lid=%d UN=%s' % (lid_2,
                                    live.readStringField(lid_2, field_id))
            print 'lid=%d T=%s' % (lid_2, live.readStringField(lid_2, 'T'))
        except:
            print sys.exc_info()[0]

        value = float(z)
        quality = 'G'

        errcode = pyxeds2.liveErrCode(live.writeAnalog(lid_1, value, quality))
        if errcode != pyxeds2.LiveErrCode.NoError:
            print pyxeds2.liveErrMessage(errcode)
        errcode = pyxeds2.liveErrCode(live.writeXSTn(lid_1, 1, z))
        if errcode != pyxeds2.LiveErrCode.NoError:
            print pyxeds2.liveErrMessage(errcode)

        errcode = pyxeds2.liveErrCode(live.synchronizeOutput())
        if errcode != pyxeds2.LiveErrCode.NoError:
            print 'synchronizeOutput() returned:',
            pyxeds2.liveErrMessage(errcode)
            if errcode == pyxeds2.LiveErrCode.ProtocolMismatch:
                return

        time.sleep(1)

    live.shut()

# -----------------------------------------------------------------------------
# pyxeds2.ArchEDS test
# -----------------------------------------------------------------------------

def test_hist(host, rport, aport):
    live = pyxeds2.createLive()
    arch = pyxeds2.createArch()

    live.setupLogger('debug=7 subsystems=ALL logger=console:7')
    arch.setupLogger('debug=7 subsystems=ALL logger=console:7')

    err = live.init(pyxeds2.LiveMode.Read, '0.0.0.0', 0,
                    host, rport, 0, 32768)

    if err:
        print 'live.init failed:', pyxeds2.liveErrMessage(err)
        return

    err = arch.init('0.0.0.0', 0,
                    host, aport, 0, 32768)

    if err:
        print 'arch.init failed:', pyxeds2.archErrMessage(err)
        return

    lid_1 = live.findByIESS('A1')
    lid_2 = live.findByIESS('A2')

    print 'lid_1 =', lid_1
    print 'lid_2 =', lid_2

    sid_1 = live.getSID(lid_1)
    sid_2 = live.getSID(lid_2)

    print 'sid_1 =', sid_1
    print 'sid_2 =', sid_2

    min_1 = arch.getFunction('MIN_VALUE')
    avg_1 = arch.getFunction('AVG')

    t = int(time.time())

    min_1.pushPointParam(sid_1, 0xff, pyxeds2.ArchShadeMode.PreferArch)
    min_1.pushTimestampParam(t - 24 * 3600)
    min_1.pushTimestampParam(t)

    avg_1.pushPointParam(sid_2, 0xff, pyxeds2.ArchShadeMode.PreferShade)
    avg_1.pushTimestampParam(t - 24 * 3600)
    avg_1.pushTimestampParam(t)

    min_id = arch.addQuery(min_1)
    avg_id = arch.addQuery(avg_1)

    print 'min_id =', min_id
    print 'avg_id =', avg_id

    arch.executeQueries()

    try:
        result = arch.getResponse(min_id)
        print 'MIN_VALUE: %f%c' % result
    except:
        print 'arch.getResponse for min_id failed'
        return

    try:
        result = arch.getResponse(avg_id)
        print 'AVG: %f%c' % result
    except:
        print 'arch.getResponse for avg_id failed'
        return

    arch.addShadeValue(sid_1, t - 5 * 3600, t, 10.0, 'G')
    arch.addShadeValue(sid_2, t - 5 * 3600, t, 20.0, 'G')
    arch.addShadeValue(sid_2, t - 2 * 3600, t + 5 * 3600, 40.0, 'G')

    err = arch.writeShades()
    if err:
        print 'arch.writeShades fialed:', pyxeds2.archErrMessage(err)
        return

    print 'Shades written'

    tab_1 = arch.getTabTrend(sid_1, 'VALUE')
    tab_2 = arch.getTabTrend(sid_2, 'AVG')

    arch.addTabTrend(tab_1, pyxeds2.ArchShadeMode.PreferShade)
    arch.addTabTrend(tab_2, pyxeds2.ArchShadeMode.PreferArch)

    arch.executeTabTrends(t - 5 * 3600, 5 * 3600, 600, True)
    print 'VALUE:\tAVG:'
    row = arch.fetchTabTrendRow()
    while len(row):
        for i in range(0, len(row)):
            print '%f%c' % (row[i].val, row[i].qual),
        print '\n',
        row = arch.fetchTabTrendRow()

    print 'Shutting'
    live.shut()
    arch.shut()


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

if len(sys.argv) != 5:
    print 'Args:',sys.argv
    print 'Required arguments: type=(live/hist), host, rport, aport'
    print 'For example: type=live localhost 43000 43001'
    sys.exit()

if 'type=live' in sys.argv:
    test_live(sys.argv[2], int(sys.argv[3]))
elif 'type=hist' in sys.argv:
    test_hist(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
else:
    print 'Unknown test type'
