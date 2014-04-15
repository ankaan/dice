import numpy as np

def manual_boxplot(self, x, vert=1, positions=None, widths=None):
    if not self._hold: self.cla()
    holdStatus = self._hold
    whiskers, caps, boxes, medians = [], [], [], []

    col = len(x)

    # get some plot info
    if positions is None:
        positions = range(1, col + 1)
    if widths is None:
        distance = max(positions) - min(positions)
        widths = min(0.15*max(distance,1.0), 0.5)
    if isinstance(widths, float) or isinstance(widths, int):
        widths = np.ones((col,), float) * widths

    # loop through columns, adding each to plot
    self.hold(True)
    for i,pos in enumerate(positions):
        (wisk_lo, q1, med, q3, wisk_hi) = x[i]

        # get x locations for whisker, whisker cap and box sides
        box_x_min = pos - widths[i] * 0.5
        box_x_max = pos + widths[i] * 0.5

        wisk_x = np.ones(2) * pos

        cap_x_min = pos - widths[i] * 0.25
        cap_x_max = pos + widths[i] * 0.25
        cap_x = [cap_x_min, cap_x_max]

        # get y location for median
        med_y = [med, med]

        # make our box vectors
        box_x = [box_x_min, box_x_max, box_x_max, box_x_min, box_x_min ]
        box_y = [q1, q1, q3, q3, q1 ]
        # make our median line vectors
        med_x = [box_x_min, box_x_max]

        # vertical or horizontal plot?
        if vert:
            def doplot(*args):
                return self.plot(*args)
        else:
            def doplot(*args):
                shuffled = []
                for i in xrange(0, len(args), 3):
                    shuffled.extend([args[i+1], args[i], args[i+2]])
                return self.plot(*shuffled)

        whiskers.extend(doplot(wisk_x, [q1, wisk_lo], 'b--',
                               wisk_x, [q3, wisk_hi], 'b--'))
        caps.extend(doplot(cap_x, [wisk_hi, wisk_hi], 'k-',
                           cap_x, [wisk_lo, wisk_lo], 'k-'))
        boxes.extend(doplot(box_x, box_y, 'b-'))
        medians.extend(doplot(med_x, med_y, 'r-'))

    # fix our axes/ticks up a little
    if 1 == vert:
        setticks, setlim = self.set_xticks, self.set_xlim
    else:
        setticks, setlim = self.set_yticks, self.set_ylim

    newlimits = min(positions)-0.5, max(positions)+0.5
    setlim(newlimits)
    setticks(positions)

    # reset hold status
    self.hold(holdStatus)

    return dict(whiskers=whiskers, caps=caps, boxes=boxes,
                medians=medians)
