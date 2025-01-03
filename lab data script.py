import numpy as np
import pandas as pd
import matplotlib.pyplot as plot
import seaborn as sns
from collections import defaultdict
import os

file_paths_list = []
parent = None
if 'lunar_analog_spectra' not in os.listdir(os.getcwd()):
    print(f'lunar_analog_spectra folder not found')
else:
    parent = os.path.join(os.getcwd(), 'lunar_analog_spectra')
    for folder_name in os.listdir(parent):
        if folder_name[-9:] == ".DS_Store": continue
        folder_path = os.path.join(parent, folder_name)
        for file in os.listdir(folder_path):
            if file[-4:] == '.csv':
                file_path = os.path.join(folder_path, file)
                file_paths_list.append(file_path)

print(f"# of file paths: {len(file_paths_list)}" + f"\n" + f"first: {file_paths_list[0]}" + f" \n" + f"last:  {file_paths_list[-1]}")

# assumed step size between m3 points
STEPSIZE = 0.04

# boundaries for wavelengths, outside of which to ignore/truncate data
WL_MIN = 0.46
WL_MAX = 2.94

m3 = pd.read_csv('m3 original data.csv')
x_m3 = (m3['Wavelength (µm)']).tolist()
x_m3 = [f"{wl:.5f}" for wl in x_m3]
# print(f"# of m^3 wavelengths: {len(x_m3)}, first and last: {x_m3[0], x_m3[-1]}")

for file_path in file_paths_list:
    ### read, clean, establish raw lab data
    lab = pd.read_csv(file_path)
    lab['Wavelength (µm)'] = lab['Wavelength (nm)']/1000
    lab = lab.set_index('Wavelength (µm)')

    y_column_label = lab.columns[1]
    x_raw = list(lab.index)
    y_raw = list(lab[y_column_label])

    # print(f"first and last raw x,y pairs\n{(x_raw[0], y_raw[0])}\n{(x_raw[-1], y_raw[-1])}")

    ### create bins stored as dictionary of lists with numerical string keys
    binned_raw = defaultdict(list)
    for x in x_m3:
        binned_raw[x] = []
    len(binned_raw)

    ### populate bins
    # precondition: wavelengths are sorted in ascending order
    binCounter = 0
    for x,y in zip(x_raw, y_raw):
        if x < WL_MIN or x > WL_MAX: continue

        lbound = float(x_m3[binCounter]) - STEPSIZE/2
        rbound = float(x_m3[binCounter]) + STEPSIZE/2

        # while point doesn't fit into current bin
        # increment binCounter unless not found
        while x > rbound: 
            if binCounter + 1 < len(x_m3):
                binCounter += 1

                # update bin bounds
                lbound = float(x_m3[binCounter]) - STEPSIZE/2
                rbound = float(x_m3[binCounter]) + STEPSIZE/2
            else:
                print(f"Point {x, y} within WL MINMAX range {WL_MIN, WL_MAX} but no bin found, last {lbound, rbound}")
                break
        
        # add point to bin
        binned_raw[x_m3[binCounter]].append((x,y))
        
        # print(f"x {x}, band center {nextbin}, upper bound of bin {nextbin + STEPSIZE/2}")

    # print(f"last bin index: {binCounter}, input list size: {len(x_raw)}")

    ### average wavelengths and reflectance values per bin
    y_avg = []
    x_avg = []
    for count, bin in enumerate(binned_raw):
        if len(binned_raw[bin]) == 0:
            x_avg.append(bin)
            y_avg.append(-1)
            print(f"Empty bin at {bin}")
            continue

        # average over all raw reflectance values
        avgx = 0
        avgy = 0
        for x,y in binned_raw[bin]:
            avgx += x
            avgy += y
        avgx /= len(binned_raw[bin])
        avgy /= len(binned_raw[bin])

        y_avg.append(avgy)
        x_avg.append(avgx)

    # print(f"# of average reflectance values {len(y_avg)}, first and last averaged points {[(x_avg[0], y_avg[0]), (x_avg[-1], y_avg[-1])]}")

    ### cubic spline to same number of points as bins
    from scipy.interpolate import CubicSpline

    spline_points = len(x_avg)
    cs_avg = CubicSpline(x_avg, y_avg)

    x_spline_avg = list(np.linspace(min(x_avg), max(x_avg), spline_points))
    y_spline_avg = list(cs_avg(x_spline_avg))

    ### writing file
    def writeFile(path, mode): # x = new, w = overwrite
        output = open(path, mode)
        output.write(f"Wavelength raw,{y_column_label} raw,Wavelength bin avg,{y_column_label} bin avg,Wavelength cubic spline of bin avg,{y_column_label} cubic spline of bin avg\n")

        # ends when shortest zip input runs out
        for xr, yr, xavg, yavg, xspline, yspline in zip(x_raw, y_raw, x_avg, y_avg, x_spline_avg, y_spline_avg):
            output.write(f"{xr},{yr},{xavg},{yavg},{xspline},{yspline}\n")
        output.close()
    
    output_path = file_path.replace('/lunar_analog_spectra/', '/csv output/')

    try: 
        writeFile(output_path, 'x')
        print(output_path)
    except:
        writeFile(output_path,'w')
        # print(f'file present for {output_path}')
        pass

print("process finished")