# Class to process Emily files
import matplotlib
matplotlib.interactive(1)
import matplotlib.pyplot as plt
from operator import itemgetter

class Path:
    def __init__(self, path):
        self.pos = []         # access axes positional data as self.pos[axis]. axis=0 is time.
        self.vel = []
        self.acc = []
        self.jerk = []
        self.pathname = path
        self.TIME = 0
        self.AXES = [1, 2, 3, 4, 5, 6]

        if isinstance(path, str):
            self.load_file(path)
        if isinstance(path, list):
            self.load_array(path)

        self.tick = self.pos[0][1] - self.pos[0][0]
        self.generate_derivatives()
        # self.remap_time()   # Don't need this anymore because Mimic doesn't mess up time stamps!


    def load_file(self, path):
        res = []
        with open(path, 'r+') as fin:
            for line in fin:
                if line.strip().startswith("[RECORDS]"):
                    break
            for line in fin:
                if line.strip().startswith("[END]"):
                    break
                else:
                    res.append([float(n) for n in line.split()])
        self.pos = transpose(res)


    def load_array(self, array):
        self.pos = array


    def generate_derivatives(self):
        " Must call to re-generate all derivitive values (vel, acc, jerk).\
         NOTE: Maybe this should be automatic or include a flag? "
        self.vel = self.derivative(self.pos)
        self.acc = self.derivative(self.vel)
        self.jerk = self.derivative(self.acc)
        self.tick = self.pos[0][1] - self.pos[0][0]


    def derivative(self, p):
        res = []
        r = len(p)
        c = len(p[0])
        res.append(p[0])
        for j in range(1, r):
            sub_res = [0]
            for i in range(1,c):
                sub_res.append((p[j][i] - p[j][i-1]) / (p[0][i] - p[0][i-1]))
            res.append(sub_res)
        return res


    def moving_average(self, window_size, force_same_length=True):
        # if force_same_length==False, will make the path longer by (window_size-1) data points
        assert window_size > 2 , \
            "window_size must be greater than 2"
        assert window_size < 166, \
            "window_size must be less than 166 (1 sec of padding added standard)"
        assert window_size % 2 == 1, \
            "window_size must be odd integer"

        self.pad_start(window_size-1)
        self.pad_end(window_size-1)

        for a in self.AXES:
            cumulative_sum = [0]
            moving_avgs = []

            for i, x in enumerate(self.pos[a], 1):
                cumulative_sum.append(cumulative_sum[i - 1] + x)
                if i >= window_size:
                    moving_avg = (cumulative_sum[i] - cumulative_sum[i - window_size]) / window_size
                    moving_avgs.append(moving_avg)
            self.pos[a] = list(moving_avgs)

        if force_same_length:
            self.trim_end(int((window_size-1)/2))
            self.trim_start(int((window_size-1)/2))

        self.remap_time()


    def plot_param(self, param, axes=[1, 2, 3, 4, 5, 6], separate_plots=True, suppress_new_graph=False, **kwargs):
        if separate_plots == True:
            for i, axis in enumerate(axes):
                if not suppress_new_graph:
                    plt.figure()
                self.plot_single_axis_and_param(axis, param, **kwargs)                
        else:
            if not suppress_new_graph:
                plt.figure()
            for i, axis in enumerate(axes):
                self.plot_single_axis_and_param(axis, param, **kwargs)
                plt.title('{} A{} - A{}'.format(self.pathname, min(axes), max(axes), param.capitalize()))


    def plot_axis(self, axis, params=['pos', 'vel', 'acc', 'jerk'], separate_plots=True, suppress_new_graph=False, **kwargs):
        if separate_plots == True:
            for i, param in enumerate(params):
                if not suppress_new_graph:
                    plt.figure()
                self.plot_single_axis_and_param(axis, param, **kwargs)                
        else:
            if not suppress_new_graph:
                plt.figure()
            for i, param in enumerate(params):
                self.plot_single_axis_and_param(axis, param, skip_ylabel=True, **kwargs)                
                plt.title('{} A{} Params'.format(self.pathname, axis))


    def plot_single_axis_and_param(self, axis, param, start_time=0, end_time=-1, skip_ylabel=False, label_pathname=False):
        assert axis in [1, 2, 3, 4, 5, 6], \
            'Acceptable axis values are: 1, 2, 3, 4, 5, 6. Passed axis value: {}'.format(str(axis))

        assert param in ['pos', 'vel', 'acc', 'jerk'], \
            'Acceptable parameters are: \'pos\', \'vel\', \'acc\', \'jerk\'. Passed parameter: \'{}\''.format(str(param))

        start_time = int(start_time/self.tick)
        if end_time is not -1:
            end_time = int(end_time/self.tick)
        plt.title('{} A{} {}'.format(self.pathname, axis, param.capitalize()))
        plt.xlabel("Seconds")
        if not skip_ylabel:
            plt.ylabel(param.capitalize())

        if label_pathname:
            label_str ='{}: A{} {}'.format(self.pathname, axis, param.capitalize())
        else: 
            label_str ='A{} {}'.format(axis, param.capitalize())
            
        plt.plot(getattr(self, param.lower())[self.TIME][start_time:end_time], getattr(self, param.lower())[axis][start_time:end_time], label=label_str)
        plt.legend()


    def pad_start(self, pad_length):
        pos_trans = transpose(self.pos)
        res = []
        for i in range(pad_length):
            res.append(pos_trans[0])
        self.pos = transpose(res + pos_trans)
        self.remap_time()


    def pad_end(self, pad_length):
        res = transpose(self.pos)
        for i in range(pad_length):
            res.append(res[-1])
        self.pos = transpose(res)
        self.remap_time()


    def trim_start(self, trim_length):
        pos_trans = transpose(self.pos)
        for i in range(trim_length):
            pos_trans.pop(0)
        self.pos = transpose(pos_trans)
        self.remap_time()


    def trim_end(self, trim_length):
        pos_trans = transpose(self.pos)
        for i in range(trim_length):
            pos_trans.pop()
        self.pos = transpose(pos_trans)
        self.remap_time()


    def remap_time(self, tick=None):
        # Mostly used to repair time data (self.pos[0])
        # Can also be used to create faster/slower moves with the tick attribute
        if not tick:
            tick = self.tick
        self.pos[self.TIME] = []
        for i, x in enumerate(self.pos[1]):
            self.pos[self.TIME].append(tick * i)


    def write_path(self, fout):
        header = ["[HEADER]\n",
                  "\tGEAR_NOMINAL_VEL = 1.0\n",
                  "\tNUM_ROB_JOINTS = 6\n",
                  "[RECORDS]"]
        footer = "\n[END]"
        res = []

        for j, x in enumerate(self.pos[self.TIME]):
            line = ''
            for i, y in enumerate(self.pos):
                line += '\t{:f}'.format(y[j])
            res += '\n'
            res.append(line)

        with open(fout, 'w') as fout:
            fout.writelines(header)
            fout.writelines(res)
            fout.write(footer)


# Misc Functions

def transpose(p):
    res = list(map(list, zip(*p)))
    return res


def compare_paths(paths, axes=[1, 2, 3, 4, 5, 6], params=['pos', 'vel', 'acc', 'jerk'], **kwargs):
    for param in params:
        for axis in axes:   
            plt.figure()
            for path in paths:
                path.plot_single_axis_and_param(axis, param, label_pathname=True, **kwargs)
            plt.title('A{} {}'.format(axis, param.capitalize()))


# NOTE: Requires matplotlib for graphing (which requires numpy)
# Also, there is a bug where graphs can occasionally get titled incorrectly,
# but the axes and legend labels should still be correct. I never got around to fixing this...


# Example usage...

# Create path object
# path = Path('test.emily')

# Graph jerk for all axes
# path.plot_param('jerk')

# Graph jerk for axes 1, 2 only
# path.plot_param('jerk', [1,2])

# Graph pos/vel/acc/jerk for axis 4
# path.plot_axis(4)

# Graph only vel/jerk for axis 4
# path.plot_axis(4, ['vel', 'jerk'])

# Create another path object
# path2 = Path('test.emily')

# Smooth path2 instance:
# path2.moving_average(11)
# path2.moving_average(5)
# path2.moving_average(3)
# path2.generate_derivatives()

# Some notes about moving_average():
# This is just a simple moving average. We tried a handful of different smoothing techniques, and this is what worked the best. 
# moving_average() must be called with an odd 'window_size'. window_size is the number of values moving_average() looks at when computing an average.
# moving_average() will affect a time span of: window_size * emily time step (typically .012) 
# Paths that get smoothed with this technique need padding (time where the robot sits without moving) at the head and tail of the emily file.
# Padding at each end should be minimum: window_size * time_step (typically .012) / 2
# If you need to add padding to a path, you can use the pad_start(), pad_end() methods. trim_start(), trim_end() do the opposite.
# If the time step is larger than expected, you're going to apply a lot more smoothing than you expect because this function is pretty naive.. 
# We've found that you can achieve a good balance between smoothing a path and maintaining positional accuracy by applying moving_average() 
# three times and cutting the window_size in (approximately) half each time.
# moving_average() only operates on the robot positional data, so if you want to graph the data afterward you have to explicitly call generate_derivatives()

# Change the name of path2 so it displays in the legend when we graph path1 and path2 together 
# path2.pathname = 'test.emily (smooth)'

# Graph pos/vel of axes 4,6 (always the problem axes) and compare the original vs the smoothed path 
# compare_paths([path, path2], axes=[4, 6], params=['pos', 'jerk'])

# Can also pass start_time and end_time params (in seconds) to any graphing function and only that timeframe will get graphed
# You should run this... it's pretty interesting to see how tiny positional changes lead to large changes in jerk
# compare_paths([path, path2], axes=[4, 6], params=['pos', 'jerk'], start_time=4, end_time=5)

# Save a path:
# path2.write_path('test_smooth.emily')

