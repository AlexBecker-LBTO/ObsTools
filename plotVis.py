#!/usr/bin/python3
import sys, os
import argparse

import matplotlib.pyplot as plt
import astropy.units as u
from astropy.coordinates import EarthLocation, SkyCoord, AltAz
from pytz import timezone
from astropy.time import Time
import numpy as np
from astroplan import Observer
from astroplan import FixedTarget
from astroplan.plots import plot_airmass, plot_sky, plot_finder_image, plot_parallactic, plot_altitude
from astropy.io import ascii
from datetime import datetime
from math import ceil

def main():
	
    parser = argparse.ArgumentParser(description='Creates visibility plots, sky plots and other plots from ASCII tables and LBT OT and OB files.', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-m', '--mode', type=str, help='Take coordinates from file or single coordinate from command line?' , choices=['list', 'single'])
    parser.add_argument('-f', '--filename', type=str, help='Filename of object list. Accepts simple ASCII table, MODS acquistion script, LUCI XML, LBC XML, and OT XML files.')
    parser.add_argument('-c', '--coordinate', type=str, help='RA and DEC of object. Use "m" instead of "-" for negative declinations.', nargs=2, metavar=('ra', 'dec'))
    parser.add_argument('-o', '--output', type=str, help='Filename for output.')
    parser.add_argument('-p', '--plot', type=str, help='What kind of plot.', choices=['Alt', 'Sky', 'FC', 'par' , 'all', 'None'])
    parser.add_argument('-t', '--time', type=str, help='Observing time UT (YYYY-MM-TT HH:MM:SS). Also accepts "now" for date and time and "previous", "next", and "nearest" as time for midnight. The combination of a specific date and a midnight option will use the current time.', nargs=2, metavar=('date', 'time'))
    parser.add_argument('-s', '--survey', type=str, help='Survey for FC.', choices = ['DSS', 'SDSSr', 'SDSSdr7r', 'SDSSg', 'SDSSdr7g', '2MASS-J', '2MASS-H', '2MASS-K', 'UKIDSS-J', 'UKIDSS-H', 'UKIDSS-K'], default='DSS')
    parser.add_argument('-n', '--number', type=int, help='Maximum number of object per plot.', default=1)
    args = parser.parse_args()


    if args.plot == 'all' or args.plot=='FC':
        print('Warning! FC does not take PA into account.')
    if args.mode == 'list':
	    args.coordinate = ['','']
    if args.time[0] == 'now':
        datenow = Time(datetime.utcnow(), scale='utc')
        datenow = str(datenow).split()
        args.time[0] = datenow[0]
    if args.time[1] == 'now':
        datenow = Time(datetime.utcnow(), scale='utc')
        datenow = str(datenow).split()
        args.time[1] = datenow[1]   
    observer = Observer.at_site('lbt')
    if args.time[1] == 'next' or args.time[1] == 'nearest' or args.time == 'previous':
        timenow = Time(datetime.utcnow(), scale='utc')
        timenow = str(timenow).split()
        stime = Time(f'{args.time[0]} {timenow[1]}', scale='utc')
        midn = str(observer.midnight(stime, args.time[1]).iso).split(' ')
        args.time[0] = midn[0]
        args.time[1] = midn[1]

    if args.coordinate[1].startswith('m'): args.coordinate[1] = args.coordinate[1].replace('m', '-')
    preparePlotting(args)
			
		



def preparePlotting(args):
    if args.filename is not None:
        if "." in args.filename and ".acq." not in args.filename:
            filetype = args.filename.split('.')[-1].lower()
        elif ".acq." in filename:
            filetype = 'acq'
        else:
            filetype = 'unknown'	
    if args.mode == 'single':
        createPlot(args,1, 0)
    if args.mode == 'list' and filetype != 'xml' and filetype != 'acq':
        with open(args.filename) as filelist:
            lines = filelist.readlines()
            numberoftargets = len(lines)
            numberofplots = ceil(numberoftargets/args.number)
            for id,line in enumerate(lines):
                if (id+1)%args.number == 0:
                    saveflag = 1
                else:
                    saveflag = 0
                if (id+1) == numberoftargets:
                    saveflag = 1
                try:
                    args.output = line.split()[0]
                    args.coordinate[0] = line.split()[1]
                    args.coordinate[1] = line.split()[2]
                    createPlot(args, saveflag, id)
                except:
                    pass
    if args.mode == 'list' and filetype == 'xml':
        lines = parseXML(args)
        numberoftargets = len(lines)
        numberofplots = ceil(numberoftargets/args.number)
        for id,line in enumerate(lines):
            if (id+1)%args.number == 0:
                saveflag = 1
            else:
                saveflag = 0
            if (id+1) == numberoftargets:
                saveflag = 1
            try:
                args.output = line.split()[0]
                args.coordinate[0] = line.split()[1]
                args.coordinate[1] = line.split()[2]
                createPlot(args, saveflag, id)
            except:
                pass
    if args.mode == 'list' and '.acq' in filetype:
        args = parseMODsAcq(args)
        createPlot(args, 1, 0)


def parseMODsAcq(args):
    with open(args.filename) as acqfile:
        lines = acqfile.readlines()
        for line in lines:
            if 'OBJCOORDS' in line:
                line = line.strip().split(' ')
                args.coordinate[0] = line[1]
                args.coordinate[1] = line[2]
            if 'OBJNAME' in line and args.output is None:
                line = line.split('OBJNAME ')[1]
                line.replace(' ', '_')
                args.output = line
    return args

def crawlOTXML(lines):
    objlist = []
    for id,line in enumerate(lines):
        if '<paramset name="Targets" kind="dataObj">' in line:
            objlist.append(lines[id+3].strip().split('value="')[1].split('"/>')[0].replace(' ', '_') + ' ' + lines[id+7].strip().split('value="')[1].split('"/>')[0] + ' ' + lines[id+8].strip().split('value="')[1].split('"/>')[0])
    objlist = list(dict.fromkeys(objlist))
    print(f'\nCreating object list from OT XML file.\n{len(objlist)} unique sources found: \n')
    for obj in objlist:
        print(obj)
    return objlist

def crawlLUCIXML(lines):
    objlist = []
    for id,line in enumerate(lines):
        if line.strip().startswith('<mount objectName='):
            objlist.append(line.strip().split('"')[1] + ' ' + line.strip().split('"')[3] +  ' ' + line.strip().split('"')[5])
    print('Extracting object from LUCI XML file.')
    for obj in objlist:
        print(obj)
    return objlist

def crawlLBCXML(lines):
    objlist = []
    for id,line in enumerate(lines):
        if '<LBC_Target>' in line:
            print('Target found')
            objlist.append(lines[id+2].strip().split('</')[0].split(">")[1].replace(' ','_') + ' ' + lines[id+4].strip().split('</')[0].split(">")[1].replace(' ','_') + ' ' + lines[id+5].strip().split('</')[0].split(">")[1].replace(' ','_'))
    print('Extracting object from LBC XML file.')
    for obj in objlist:
        print(obj)
    return objlist


def parseXML(args):
    with open(args.filename) as xmlfile:
        lines = xmlfile.readlines()
        objlist = []
        if lines[3].strip() == '<document>': 
            objlist = crawlOTXML(lines)
        if lines[1].startswith('<observationProgram'):
            objlist = crawlLUCIXML(lines)
        if lines[0].strip().endswith('<ObservingBlock>'):
            objlist = crawlLBCXML(lines)
    return objlist

def createPlot(args,saveflag, id):
    observer = Observer.at_site('lbt')
    try:
        args.coordinate[0] = float(args.coordinate[0])
        args.coordinate[1] = float(args.coordinate[1])
        coordinates = SkyCoord(args.coordinate[0], args.coordinate[1], unit=(u.deg, u.deg), frame='icrs')
    except:
        coordinates = SkyCoord(args.coordinate[0], args.coordinate[1], unit=(u.hourangle, u.deg), frame='icrs')

    observe_time = Time(f'{args.time[0]} {args.time[1]}', scale='utc')
    target = FixedTarget(name=args.output, coord=coordinates)
    if args.mode == 'single':
        obs_time = Time(f'{args.time[0]} {args.time[1]}')
        lbtcoord = EarthLocation(lat=32.7016*u.deg, lon=-109.8719*u.deg, height=3221.0*u.m)
        altazcoord = coordinates.transform_to(AltAz(obstime=obs_time, location=lbtcoord))
        if args.output is None: args.output = 'Unknown'
        print(f'\n{args.output}:')
        print("Altitude = {0.alt:.4}".format(altazcoord))    
    if args.plot == 'Alt' or args.plot == 'all':
        if id == 0:
            plt.figure(figsize=(10,6))
        if args.mode == "list":
            plt.title(args.filename + '\n' + args.time[0])
        else:
            plt.title(args.output + '\n' + args.time[0])
        plot_altitude(target, observer, observe_time, brightness_shading=True)

        if saveflag == 1:
            if args.mode == 'list':
                filename = args.filename + '_' + str(ceil(id/args.number))
            else:
                filename = args.output
            #plt.tight_layout()
            plt.axhline(y=30, ls='--', color='k')
            plt.legend()
            plt.savefig(f'{filename}_Alt.png')
            plt.clf()
    if args.plot == 'Sky' or args.plot == 'all':
        observe_time2 = observe_time + np.linspace(-6, 6, 13)*u.hour
        if id == 0:
            plt.figure(figsize=(8,6))
        if args.mode == "list":
            plt.title(f'{args.filename}\n{args.time[0]} - {args.time[1]} UT', pad=13)
        else:
            plt.title(f'{args.time[0]} - {args.time[1]} UT', pad=13) 
        plot_sky(target, observer, observe_time, style_kwargs={'marker': '+', 'c': 'k', 's': 160})
        plot_sky(target, observer, observe_time2)  
        if saveflag == 1:
            if args.mode == 'list':
                filename = args.filename + '_' + str(ceil(id/args.number))
            else:
                filename = args.output
            handles, labels = plt.gca().get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            plt.legend(by_label.values(), by_label.keys(), loc='center left', bbox_to_anchor=(1.25, 0.5))
            plt.tight_layout()
            plt.savefig(f'{filename}_Sky.png')
            plt.clf()
    if args.plot == 'FC' or args.plot == 'all':
        plt.figure(figsize=(8,8))
        ax, hdu = plot_finder_image(target, survey=args.survey, fov_radius=5*u.arcmin, grid=True, reticle=True)
        if saveflag == 1:
            plt.savefig(f'{args.output}_FC.png')
            plt.clf()
    if args.plot == 'par' or args.plot == 'all':
        if id == 0:
            plt.figure(figsize=(10,6))
        plot_parallactic(target, observer, observe_time)
        if args.mode == "list":
            plt.title(args.filename + '\n' + args.time[0])

        if saveflag == 1:
            if args.mode == 'list':
                filename = args.filename + '_' + str(ceil(id/args.number))
            else:
                filename = args.output
            plt.legend()
            plt.tight_layout()
            plt.savefig(f'{filename}_par.png')
            plt.clf()
    if args.plot != 'None':
        del observe_time
        del observer
        del coordinates
        del target
        del observe_time2
if __name__ == '__main__':
    main()
