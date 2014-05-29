import numpy as np
import pyPyrUtils as ppu
#from myModule import *
from pyPyrCcode import *
import math
import matplotlib.cm as cm
from pylab import *
from operator import mul
import os
import scipy.misc as spm
import cmath

class pyramid:  # pyramid
    # properties
    pyr = []
    pyrSize = []
    pyrType = ''
    image = ''

    # constructor
    def __init__(self):
        print "please specify type of pyramid to create (Gpry, Lpyr, etc.)"
        return

    # methods
    def nbands(self):
        return len(self.pyr)

    def band(self, bandNum):
        return np.array(self.pyr[bandNum])

    def showPyr(self, *args):
        if self.pyrType == 'Gaussian':
            self.showLpyr(args)
        elif self.pyrType == 'Laplacian':
            self.showLpyr(args)
        elif self.pyrType == 'wavelet':
            self.showLpyr(args)
        else:
            print "pyramid type %s not currently supported" % (args[0])
            return

class Spyr(pyramid):
    filt = ''
    edges = ''
    
    #constructor
    def __init__(self, *args):    # (image height, filter file, edges)
        self.pyrType = 'steerable'
        if len(args) > 0:
            self.image = np.array(args[0])
        else:
            print "First argument (image) is required."
            return

        #------------------------------------------------
        # defaults:

        if len(args) > 2:
            if args[2] == 'sp0Filters':
                filters = ppu.sp0Filters()
            elif args[2] == 'sp1Filters':
                filters = ppu.sp1Filters()
            elif args[2] == 'sp3Filters':
                filters = ppu.sp3Filters()
            elif args[2] == 'sp5Filters':
                filters = ppu.sp5Filters()
            elif os.path.isfile(args[2]):
                print "Filter files not supported yet"
                return
            else:
                print "filter parameters value %s not supported" % (args[2])
                return
        else:
            filters = ppu.sp1Filters()

        harmonics = filters['harmonics']
        lo0filt = filters['lo0filt']
        hi0filt = filters['hi0filt']
        lofilt = filters['lofilt']
        bfilts = filters['bfilts']
        steermtx = filters['mtx']
            
        max_ht = ppu.maxPyrHt(self.image.shape, lofilt.shape)  # just lofilt[1]?
        if len(args) > 1:
            if args[1] == 'auto':
                ht = max_ht
            elif args[1] > max_ht:
                print "Error: cannot build pyramid higher than %d levels." % (
                    max_ht)
                return
            else:
                ht = args[1]
        else:
            ht = max_ht
        print 'ht = %d  max_ht = %d' % (ht, max_ht)

        if len(args) > 3:
            edges = args[3]
        else:
            edges = 'reflect1'

        #------------------------------------------------------

        self.pyr = []
        self.pyrSize = []
        im = self.image
        im_sz = im.shape
        pyrCtr = 0

        hi0 = corrDn(im_sz[1], im_sz[0], im, hi0filt.shape[0], hi0filt.shape[1],
                     hi0filt, edges);
        hi0 = np.array(hi0).reshape(im_sz[0], im_sz[1])

        #self.pyr[pyrCtr] = hi0.copy()
        #self.pyrSize[pyrCtr] = hi0.shape
        self.pyr.append(hi0.copy())
        self.pyrSize.append(hi0.shape)
        pyrCtr += 1

        lo = corrDn(im_sz[1], im_sz[0], im, lo0filt.shape[0], lo0filt.shape[1],
                    lo0filt, edges);
        lo = np.array(lo).reshape(im_sz[0], im_sz[1])

        for i in range(ht):
            lo_sz = lo.shape
            # assume square filters  -- start of buildSpyrLevs
            bfiltsz = math.floor(math.sqrt(bfilts.shape[0]))

            for b in range(bfilts.shape[1]-1,-1,-1):
                filt = bfilts[:,b].reshape(bfiltsz,bfiltsz)
                #band = np.negative( corrDn(lo_sz[1], lo_sz[0], lo, bfiltsz, 
                #                           bfiltsz, filt, edges) )
                band = np.negative( corrDn(lo_sz[1], lo_sz[0], lo, 
                                           filt.shape[0], filt.shape[1], filt, 
                                           edges) )
                #self.pyr[pyrCtr] = np.array(band.copy()).reshape(lo_sz[0], 
                #                                                 lo_sz[1])
                #self.pyrSize[pyrCtr] = lo_sz
                self.pyr.append( np.array(band.copy()).reshape(lo_sz[0], 
                                                               lo_sz[1]) )
                self.pyrSize.append(lo_sz)
                pyrCtr += 1

            lo = corrDn(lo_sz[1], lo_sz[0], lo, lofilt.shape[0], 
                        lofilt.shape[1], lofilt, edges, 2, 2)
            lo = np.array(lo).reshape(math.ceil(lo_sz[0]/2.0), 
                                      math.ceil(lo_sz[1]/2.0))

        #self.pyr[pyrCtr] = np.array(lo).copy()
        #self.pyrSize[pyrCtr] = lo.shape
        self.pyr.append(np.array(lo).copy())
        self.pyrSize.append(lo.shape)

    # methods
    def spyrLev(self, lev):
        if lev < 0 or lev > self.spyrHt()-1:
            print 'Error: level parameter must be between 0 and %d!' % (self.spyrHt()-1)
            return
        
        levArray = []
        for n in range(self.numBands()):
            levArray.append(self.spyrBand(lev, n))
        levArray = np.array(levArray)

        return levArray

    def spyrBand(self, lev, band):
        if lev < 0 or lev > self.spyrHt()-1:
            print 'Error: level parameter must be between 0 and %d!' % (self.spyrHt()-1)
            return
        if band < 0 or band > self.numBands()-1:
            print 'Error: band parameter must be between 0 and %d!' % (self.numBands()-1)

        return self.band( ((lev*self.numBands())+band)+1 )


    def spyrHt(self):
        if len(self.pyrSize) > 2:
            spHt = (len(self.pyrSize)-2)/self.numBands()
        else:
            spHt = 0
        return spHt

    def numBands(self):
        if len(self.pyrSize) == 2:
            return 0
        else:
            b = 2
            while ( b <= len(self.pyrSize) and 
                    self.pyrSize[b] == self.pyrSize[1] ):
                b += 1
            return b-1

    def pyrLow(self):
        return np.array(self.band(len(self.pyrSize)-1))

    def pyrHigh(self):
        return np.array(self.band(0))

    def reconSpyr(self, *args):
        print 'starting reconSpyr'
        # defaults
        if len(args) > 0:
            if args[0] == 'sp0Filters':
                filters = ppu.sp0Filters()
            elif args[0] == 'sp1Filters':
                filters = ppu.sp1Filters()
            elif args[0] == 'sp3Filters':
                filters = ppu.sp3Filters()
            elif args[0] == 'sp5Filters':
                filters = ppu.sp5Filters()
            elif os.path.isfile(args[0]):
                print "Filter files not supported yet"
                return
            else:
                print "supported filter parameters are 'sp0Filters' and 'sp1Filters'"
                return
        else:
            filters = ppu.sp1Filters()

        #harmonics = filters['harmonics']
        lo0filt = filters['lo0filt']
        hi0filt = filters['hi0filt']
        lofilt = filters['lofilt']
        bfilts = filters['bfilts']
        steermtx = filters['mtx']
        #print harmonics.shape
        # assume square filters  -- start of buildSpyrLevs
        bfiltsz = int(math.floor(math.sqrt(bfilts.shape[0])))

        if len(args) > 1:
            edges = args[1]
        else:
            edges = 'reflect1'
            
        if len(args) > 2:
            levs = args[2]
        else:
            levs = 'all'

        if len(args) > 3:
            bands = args[3]
        else:
            bands = 'all'

        #---------------------------------------------------------
        
        maxLev = 2 + self.spyrHt()
        if levs == 'all':
            levs = np.array(range(maxLev))
        else:
            levs = np.array(levs)
            if (levs < 0).any() or (levs >= maxLev-1).any():
                print "Error: level numbers must be in the range [0, %d]." % (maxLev-1)
            else:
                levs = np.array(levs)
                if len(levs) > 1 and levs[0] < levs[1]:
                    levs = levs[::-1]  # we want smallest first
        if bands == 'all':
            bands = np.array(range(self.numBands()))
        else:
            if (bands < 1).any() or (bands > self.numBands).any():
                print "Error: band numbers must be in the range [0, %d]." % (self.numBands())
            else:
                bands = np.array(bands)

        # make a list of all pyramid layers to be used in reconstruction
        # FIX: if not supplied by user
        Nlevs = self.spyrHt()+2
        Nbands = self.numBands()
        print 'Nbands = %d' % (Nbands)
        reconList = []  # pyr indices used in reconstruction
        for lev in levs:
            if lev == 0 or lev == Nlevs-1 :
                reconList.append( ppu.LB2idx(lev, -1, Nlevs, Nbands) )
            else:
                for band in bands:
                    reconList.append( ppu.LB2idx(lev, band, Nlevs, Nbands) )
                    
        # reconstruct
        # FIX: shouldn't have to enter step, start and stop in upConv!
        band = -1
        for lev in range(Nlevs-1,-1,-1):
            print 'lev = %d' % (lev)
            if lev == Nlevs-1 and ppu.LB2idx(lev,-1,Nlevs,Nbands) in reconList:
                print 'flag 1'
                idx = ppu.LB2idx(lev, band, Nlevs, Nbands)
                recon = np.array(self.pyr[len(self.pyrSize)-1].copy())
            elif lev == Nlevs-1:
                print 'flag 2'
                idx = ppu.LB2idx(lev, band, Nlevs, Nbands)
                recon = np.zeros(self.pyr[len(self.pyrSize)-1].shape)
            elif lev == 0 and 0 in reconList:
                print 'flag 3'
                idx = ppu.LB2idx(lev, band, Nlevs, Nbands)
                sz = recon.shape
                #recon = upConv(sz[0], sz[1], recon, hi0filt.shape[0], 
                #               hi0filt.shape[1], lo0filt, edges, 1, 1, 0, 0, 
                #               sz[1], sz[0])
                recon = upConv(sz[0], sz[1], recon, lo0filt.shape[0], 
                               lo0filt.shape[1], lo0filt, edges, 1, 1, 0, 0, 
                               sz[1], sz[0])
                #recon = np.array(recon).reshape(sz[0], sz[1])
                recon = upConv(self.pyrSize[idx][0], self.pyrSize[idx][1], 
                               self.pyr[idx], hi0filt.shape[0], 
                               hi0filt.shape[1], hi0filt, edges, 
                               1, 1, 0, 0, 
                               self.pyrSize[idx][1], self.pyrSize[idx][0], 
                               recon)
                #recon = np.array(recon).reshape(self.pyrSize[idx][0], self.pyrSize[idx][1], order='C')
            elif lev == 0:
                print 'flag 4'
                sz = recon.shape
                recon = upConv(sz[0], sz[1], recon, lo0filt.shape[0], 
                               lo0filt.shape[1], lo0filt, edges, 1, 1, 0, 0, 
                               sz[0], sz[1])
                #recon = np.array(recon).reshape(sz[0], sz[1])
            else:
                print 'flag 5'                
                for band in range(Nbands-1,-1,-1):
                    idx = ppu.LB2idx(lev, band, Nlevs, Nbands)
                    print 'lev=%d band=%d Nlevs=%d Nbands=%d idx=%d' % (lev, band, Nlevs, Nbands, idx)
                    if idx in reconList:
                        print 'band = %d' % (band)
                        #print bfilts.shape
                        #print bfilts[:,band]
                        #print bfiltsz
                        filt = np.negative(bfilts[:,band].reshape(bfiltsz, 
                                                                  bfiltsz,
                                                                  order='C'))
                        print self.pyrSize[idx]
                        print self.pyr[idx].shape
                        recon = upConv(self.pyrSize[idx][0], 
                                       self.pyrSize[idx][1], 
                                       self.pyr[idx],
                                       bfiltsz, bfiltsz, filt, edges, 1, 1, 0, 
                                       0, self.pyrSize[idx][1], 
                                       self.pyrSize[idx][0], recon)
                        #recon = np.array(recon).reshape(self.pyrSize[idx][0], 
                        #                                self.pyrSize[idx][1],
                        #                                order='C')
                print 'flag 5 end'

            # upsample
            #newSz = ppu.nextSz(recon.shape, self.pyrSize.values())
            newSz = ppu.nextSz(recon.shape, self.pyrSize)
            mult = newSz[0] / recon.shape[0]
            if newSz[0] % recon.shape[0] > 0:
                mult += 1
            if mult > 1:
                print 'flag 6'
                recon = upConv(recon.shape[1], recon.shape[0], 
                               recon.T,
                               lofilt.shape[0], lofilt.shape[1], lofilt, edges, 
                               mult, mult, 0, 0, newSz[0], newSz[1]).T
                print 'flag 6 end'
                #recon = np.array(recon).reshape(newSz[0], newSz[1], order='F')
        return recon

    def showPyr(self, *args):
        if len(args) > 0:
            prange = args[0]
        else:
            prange = 'auto2'

        if len(args) > 1:
            gap = args[1]
        else:
            gap = 1

        if len(args) > 2:
            scale = args[2]
        else:
            scale = 2

        ht = self.spyrHt()
        nind = len(self.pyr)
        nbands = self.numBands()

        ## Auto range calculations:
        if prange == 'auto1':
            prange = np.ones((nind,1))
            band = self.pyrHigh()
            mn = np.amin(band)
            mx = np.amax(band)
            for lnum in range(1,ht+1):
                for bnum in range(nbands):
                    idx = ppu.LB2idx(lnum, bnum, ht+2, nbands)
                    band = self.band(idx)/(np.power(scale,lnum))
                    prange[(lnum-1)*nbands+bnum+1] = np.power(scale,lnum-1)
                    bmn = np.amin(band)
                    bmx = np.amax(band)
                    mn = min([mn, bmn])
                    mx = max([mx, bmx])
            prange = np.outer(prange, np.array([mn, mx]))
            band = self.pyrLow()
            mn = np.amin(band)
            mx = np.amax(band)
            prange[nind-1,:] = np.array([mn, mx])
        elif prange == 'indep1':
            prange = np.zeros((nind,2))
            for bnum in range(nind):
                band = self.band(bnum)
                mn = band.min()
                mx = band.max()
                prange[bnum,:] = np.array([mn, mx])
        elif prange == 'auto2':
            prange = np.ones(nind)
            band = self.pyrHigh()
            sqsum = np.sum( np.power(band, 2) )
            numpixels = band.shape[0] * band.shape[1]
            for lnum in range(1,ht+1):
                for bnum in range(nbands):
                    band = self.band(ppu.LB2idx(lnum, bnum, ht+2, nbands))
                    band = band / np.power(scale,lnum-1)
                    sqsum += np.sum( np.power(band, 2) )
                    numpixels += band.shape[0] * band.shape[1]
                    prange[(lnum-1)*nbands+bnum+1] = np.power(scale, lnum-1)
            stdev = np.sqrt( sqsum / (numpixels-1) )
            prange = np.outer(prange, np.array([-3*stdev, 3*stdev]))
            band = self.pyrLow()
            av = np.mean(band)
            stdev = np.sqrt( np.var(band) )
            prange[nind-1,:] = np.array([av-2*stdev, av+2*stdev])
        elif prange == 'indep2':
            prange = np.zeros((nind,2))
            for bnum in range(nind-1):
                band = self.band(bnum)
                stdev = np.sqrt( np.var(band) )
                prange[bnum,:] = np.array([-3*stdev, 3*stdev])
            band = self.pyrLow()
            av = np.mean(band)
            stdev = np.sqrt( np.var(band) )
            prange[nind-1,:] = np.array([av-2*stdev, av+2*stdev])
        elif isinstance(prange, basestring):
            print "Error:Bad RANGE argument: %s'" % (prange)
        elif prange.shape[0] == 1 and prange.shape[1] == 2:
            scales = np.power(scale, range(ht))
            scales = np.outer( np.ones((nbands,1)), scales )
            scales = np.array([1, scales, np.power(scale, ht)])
            prange = np.outer(scales, prange)
            band = self.pyrLow()
            prange[nind,:] += np.mean(band) - np.mean(prange[nind,:])

        colormap = cm.Greys_r

        # compute positions of subbands
        llpos = np.ones((nind,2));

        if nbands == 2:
            ncols = 1
            nrows = 2
        else:
            ncols = int(np.ceil((nbands+1)/2))
            nrows = int(np.ceil(nbands/2))

        #relpos = np.array([np.concatenate([ range(1-nrows,1), 
        #                                    np.zeros(ncols-1)]), 
        #                   np.concatenate([ np.zeros(nrows), 
        #                                    range(-1, 1-ncols, -1) ])]).T
        a = np.array(range(1-nrows, 1))
        b = np.zeros((1,ncols))[0]
        ab = np.concatenate((a,b))
        c = np.zeros((1,nrows))[0]
        d = range(-1, -ncols-1, -1)
        cd = np.concatenate((c,d))
        relpos = np.vstack((ab,cd)).T
        
        if nbands > 1:
            mvpos = np.array([-1, -1]).reshape(1,2)
        else:
            mvpos = np.array([0, -1]).reshape(1,2)
        basepos = np.array([0, 0]).reshape(1,2)

        for lnum in range(1,ht+1):
            #ind1 = (lnum-1)*nbands + 2
            ind1 = (lnum-1)*nbands + 1
            sz = np.array(self.pyrSize[ind1]) + gap
            basepos = basepos + mvpos * sz
            if nbands < 5:         # to align edges
                sz += gap * (ht-lnum)
            llpos[ind1:ind1+nbands, :] = np.dot(relpos, np.diag(sz)) + ( np.ones((nbands,1)) * basepos )
    
        # lowpass band
        sz = np.array(self.pyrSize[nind-1]) + gap
        basepos += mvpos * sz
        llpos[nind-1,:] = basepos

        # make position list positive, and allocate appropriate image:
        llpos = llpos - ((np.ones((nind,2)) * np.amin(llpos, axis=0)) + 1) + 1
        llpos[0,:] = np.array([1, 1])
        #urpos = llpos + self.pyrSize.values()
        urpos = llpos + self.pyrSize
        d_im = np.zeros((np.amax(urpos), np.amax(urpos)))
        
        # paste bands into image, (im-r1)*(nshades-1)/(r2-r1) + 1.5
        nshades = 64;

        for bnum in range(1,nind):
            mult = (nshades-1) / (prange[bnum,1]-prange[bnum,0])
            d_im[llpos[bnum,0]:urpos[bnum,0], 
                 llpos[bnum,1]:urpos[bnum,1]] = mult * self.band(bnum) + (1.5-mult*prange[bnum,0])
            
        ppu.showIm(d_im)
 

class SFpyr(Spyr):
    filt = ''
    edges = ''
    
    #constructor
    def __init__(self, *args):    # (image, height, order, twidth)
        self.pyrType = 'steerableFrequency'

        if len(args) > 0:
            self.image = args[0]
        else:
            print "First argument (image) is required."
            return

        #------------------------------------------------
        # defaults:

        max_ht = np.floor( np.log2( min(self.image.shape) ) ) - 2
        if len(args) > 1:
            if(args[1] > max_ht):
                print "Error: cannot build pyramid higher than %d levels." % (max_ht)
            ht = args[1]
        else:
            ht = max_ht
        ht = int(ht)
            
        if len(args) > 2:
            if args[2] > 15 or args[2] < 0:
                print "Warning: order must be an integer in the range [0,15]. Truncating."
                order = min( max(args[2],0), 15 )
            else:
                order = args[2]
        else:
            order = 3

        nbands = order+1

        if len(args) > 3:
            if args[3] <= 0:
                print "Warning: twidth must be positive. Setting to 1."
                twidth = 1
            else:
                twidth = args[3]
        else:
            twidth = 1

        #------------------------------------------------------
        # steering stuff:

        if nbands % 2 == 0:
            harmonics = np.array(range(nbands/2)) * 2 + 1
        else:
            harmonics = np.array(range((nbands-1)/2)) * 2

        steermtx = ppu.steer2HarmMtx(harmonics, 
                                     np.pi*np.array(range(nbands))/nbands,
                                     'even')
        #------------------------------------------------------
        
        dims = np.array(self.image.shape)
        ctr = np.ceil((np.array(dims)+0.5)/2)
        
        (xramp, yramp) = np.meshgrid((np.array(range(1,dims[1]+1))-ctr[1])/
                                     (dims[1]/2), 
                                     (np.array(range(1,dims[0]+1))-ctr[0])/
                                     (dims[0]/2))
        angle = np.arctan2(yramp, xramp)
        log_rad = np.sqrt(xramp**2 + yramp**2)
        log_rad[ctr[0]-1, ctr[1]-1] = log_rad[ctr[0]-1, ctr[1]-2]
        log_rad = np.log2(log_rad);

        ## Radial transition function (a raised cosine in log-frequency):
        (Xrcos, Yrcos) = ppu.rcosFn(twidth, (-twidth/2.0), np.array([0,1]))
        Yrcos = np.sqrt(Yrcos)

        YIrcos = np.sqrt(1.0 - Yrcos**2)
        lo0mask = np.array(pointOp(log_rad.shape[0], log_rad.shape[1], log_rad,
                                   YIrcos.shape[0], YIrcos, Xrcos[0], 
                                   Xrcos[1]-Xrcos[0], 0))

        imdft = np.fft.fftshift(np.fft.fft2(self.image))

        self.pyr = []
        self.pyrSize = []

        hi0mask = np.array(pointOp(log_rad.shape[0], log_rad.shape[1], log_rad,
                                   Yrcos.shape[0], Yrcos, Xrcos[0], 
                                   Xrcos[1]-Xrcos[0], 0))
        hi0dft = imdft * hi0mask.reshape(imdft.shape[0], imdft.shape[1])
        hi0 = np.fft.ifft2(np.fft.ifftshift(hi0dft))

        self.pyr.append(np.real(hi0.copy()))
        self.pyrSize.append(hi0.shape)

        lo0mask = lo0mask.reshape(imdft.shape[0], imdft.shape[1])
        lodft = imdft * lo0mask

        for i in range(ht):
            bands = np.zeros((lodft.shape[0]*lodft.shape[1], nbands))
            bind = np.zeros((nbands, 2))
        
            Xrcos -= np.log2(2)

            lutsize = 1024
            Xcosn = np.pi * np.array(range(-(2*lutsize+1), (lutsize+2))) / lutsize

            order = nbands -1
            const = (2**(2*order))*(spm.factorial(order, exact=True)**2)/float(nbands*spm.factorial(2*order, exact=True))
            Ycosn = np.sqrt(const) * (np.cos(Xcosn))**order
            himask = np.array(pointOp(log_rad.shape[0], log_rad.shape[1], 
                                      log_rad, Yrcos.shape[0], Yrcos, Xrcos[0],
                                      Xrcos[1]-Xrcos[0], 0))
            himask = himask.reshape(lodft.shape[0], lodft.shape[1])

            for b in range(nbands):
                anglemask = np.array(pointOp(angle.shape[0], angle.shape[1], 
                                             angle, Ycosn.shape[0], Ycosn, 
                                             Xcosn[0]+np.pi*b/nbands, 
                                             Xcosn[1]-Xcosn[0], 0))
                anglemask = anglemask.reshape(lodft.shape[0], lodft.shape[1])
                banddft = ((-np.power(-1+0j,0.5))**order) * lodft * anglemask * himask
                band = np.fft.ifft2(np.fft.ifftshift(banddft))
                self.pyr.append(np.real(band.copy()))
                self.pyrSize.append(band.shape)

            dims = np.array(lodft.shape)
            ctr = np.ceil((dims+0.5)/2)
            lodims = np.ceil((dims-0.5)/2)
            loctr = ceil((lodims+0.5)/2)
            lostart = ctr - loctr
            loend = lostart + lodims

            log_rad = log_rad[lostart[0]:loend[0], lostart[1]:loend[1]]
            angle = angle[lostart[0]:loend[0], lostart[1]:loend[1]]
            lodft = lodft[lostart[0]:loend[0], lostart[1]:loend[1]]
            YIrcos = np.abs(np.sqrt(1.0 - Yrcos**2))
            lomask = np.array(pointOp(log_rad.shape[0], log_rad.shape[1], 
                                      log_rad, YIrcos.shape[0], YIrcos, 
                                      Xrcos[0], Xrcos[1]-Xrcos[0],
                                      0))
            lodft = lodft * lomask.reshape(lodft.shape[0], lodft.shape[1])

        lodft = np.fft.ifft2(np.fft.ifftshift(lodft))
        self.pyr.append(np.real(np.array(lodft).copy()))
        self.pyrSize.append(lodft.shape)

    # methods
    def numBands(self):      # why isn't this inherited
        if len(self.pyrSize) == 2:
            return 0
        else:
            b = 2
            while ( b <= len(self.pyrSize) and 
                    self.pyrSize[b] == self.pyrSize[1] ):
                b += 1
            return b-1

    def spyrHt(self):
        if len(self.pyrSize) > 2:
            spHt = (len(self.pyrSize)-2)/self.numBands()
        else:
            spHt = 0
        return spHt

    def reconSFpyr(self, *args):
        if len(args) > 0:
            levs = args[0]
        else:
            levs = 'all'

        if len(args) > 1:
            bands = args[1]
        else:
            bands = 'all'

        if len(args) > 2:
            if args[2] <= 0:
                print "Warning: twidth must be positive. Setting to 1."
                twidth = 1
            else:
                twidth = args[2]
        else:
            twidth = 1

        #-----------------------------------------------------------------

        nbands = self.numBands()
        
        maxLev = 1 + self.spyrHt()
        if isinstance(levs, basestring) and levs == 'all':
            levs = np.array(range(maxLev+1))
        elif isinstance(levs, basestring):
            print "Error: %s not valid for levs parameter." % (levs)
            print "levs must be either a 1D numpy array or the string 'all'."
            return
        else:
            levs = np.array(levs)

        if isinstance(bands, basestring) and bands == 'all':
            bands = np.array(range(nbands))
        elif isinstance(bands, basestring):
            print "Error: %s not valid for bands parameter." % (bands)
            print "bands must be either a 1D numpy array or the string 'all'."
            return
        else:
            bands = np.array(bands)

        #-------------------------------------------------------------------
        # make list of dims and bounds
        boundList = []
        dimList = []
        for dimIdx in range(len(self.pyrSize)-1,-1,-1):
            dims = np.array(self.pyrSize[dimIdx])
            if (dims[0], dims[1]) not in dimList:
                dimList.append( (dims[0], dims[1]) )
            ctr = np.ceil((dims+0.5)/2)
            lodims = np.ceil((dims-0.5)/2)
            loctr = ceil((lodims+0.5)/2)
            lostart = ctr - loctr
            loend = lostart + lodims
            bounds = (lostart[0], lostart[1], loend[0], loend[1])
            if bounds not in boundList:
                boundList.append( bounds )
        boundList.append((0.0, 0.0, dimList[len(dimList)-1][0], 
                          dimList[len(dimList)-1][1]))
        dimList.append((dimList[len(dimList)-1][0], dimList[len(dimList)-1][1]))
        
        # matlab code starts here
        dims = np.array(self.pyrSize[0])
        ctr = np.ceil((dims+0.5)/2.0)

        (xramp, yramp) = np.meshgrid((np.array(range(1,dims[1]+1))-ctr[1])/
                                     (dims[1]/2), 
                                     (np.array(range(1,dims[0]+1))-ctr[0])/
                                     (dims[0]/2))
        angle = np.arctan2(yramp, xramp)
        log_rad = np.sqrt(xramp**2 + yramp**2)
        log_rad[ctr[0]-1, ctr[1]-1] = log_rad[ctr[0]-1, ctr[1]-2]
        log_rad = np.log2(log_rad);

        ## Radial transition function (a raised cosine in log-frequency):
        (Xrcos, Yrcos) = ppu.rcosFn(twidth, (-twidth/2.0), np.array([0,1]))
        Yrcos = np.sqrt(Yrcos)
        YIrcos = np.sqrt(1.0 - Yrcos**2)

        # from reconSFpyrLevs
        lutsize = 1024
        Xcosn = np.pi * np.array(range(-(2*lutsize+1), (lutsize+2))) / lutsize
        
        order = nbands -1
        const = (2**(2*order))*(spm.factorial(order, exact=True)**2)/float(nbands*spm.factorial(2*order, exact=True))
        Ycosn = np.sqrt(const) * (np.cos(Xcosn))**order

        # lowest band
        nres = self.pyr[len(self.pyr)-1]
        if self.spyrHt()+1 in levs:
            nresdft = np.fft.fftshift(np.fft.fft2(nres))
        else:
            nresdft = np.zeros(nres.shape)
        resdft = np.zeros(dimList[1]) + 0j

        bounds = (0, 0, 0, 0)
        for idx in range(len(boundList)-2, 0, -1):
            diff = (boundList[idx][2]-boundList[idx][0], 
                    boundList[idx][3]-boundList[idx][1])
            bounds = (bounds[0]+boundList[idx][0], bounds[1]+boundList[idx][1], 
                      bounds[0]+boundList[idx][0] + diff[0], 
                      bounds[1]+boundList[idx][1] + diff[1])
            Xrcos -= np.log2(2.0)
        nlog_rad = log_rad[bounds[0]:bounds[2], bounds[1]:bounds[3]]

        lomask = np.array(pointOp(nlog_rad.shape[0], nlog_rad.shape[1], 
                                  nlog_rad,
                                  YIrcos.shape[0], YIrcos, Xrcos[0], 
                                  Xrcos[1]-Xrcos[0], 0))
        lomask = lomask.reshape(nres.shape[0], nres.shape[1])
        lomask = lomask + 0j
        resdft[boundList[1][0]:boundList[1][2], 
               boundList[1][1]:boundList[1][3]] = nresdft * lomask

        # middle bands
        bandIdx = (len(self.pyr)-1) + nbands
        for idx in range(1, len(boundList)-1):
            bounds1 = (0, 0, 0, 0)
            bounds2 = (0, 0, 0, 0)
            for boundIdx in range(len(boundList)-1,idx-1,-1):
                diff = (boundList[boundIdx][2]-boundList[boundIdx][0], 
                        boundList[boundIdx][3]-boundList[boundIdx][1])
                bound2tmp = bounds2
                bounds2 = (bounds2[0]+boundList[boundIdx][0], 
                           bounds2[1]+boundList[boundIdx][1],
                           bounds2[0]+boundList[boundIdx][0] + diff[0], 
                           bounds2[1]+boundList[boundIdx][1] + diff[1])
                bounds1 = bound2tmp
            nlog_rad1=log_rad[bounds1[0]:bounds1[2], bounds1[1]:bounds1[3]]
            nlog_rad2=log_rad[bounds2[0]:bounds2[2],bounds2[1]:bounds2[3]]
            dims = dimList[idx]
            nangle = angle[bounds1[0]:bounds1[2], bounds1[1]:bounds1[3]]
            YIrcos = np.abs(np.sqrt(1.0 - Yrcos**2))
            if idx > 1:
                Xrcos += np.log2(2.0)
                lomask = np.array(pointOp(nlog_rad2.shape[0], 
                                          nlog_rad2.shape[1], 
                                          nlog_rad2, YIrcos.shape[0], YIrcos, 
                                          Xrcos[0], Xrcos[1]-Xrcos[0],
                                          0))
                lomask = lomask.reshape(bounds2[2]-bounds2[0],
                                        bounds2[3]-bounds2[1])
                lomask = lomask + 0j
                nresdft = np.zeros(dimList[idx]) + 0j
                nresdft[boundList[idx][0]:boundList[idx][2], 
                        boundList[idx][1]:boundList[idx][3]] = resdft * lomask
                resdft = nresdft.copy()

            bandIdx -= 2 * nbands

            # reconSFpyrLevs
            if idx != 0 and idx != len(boundList)-1:
                for b in range(nbands):
                    if (bands == b).any():
                        himask = np.array(pointOp(nlog_rad1.shape[0], 
                                                  nlog_rad1.shape[1], 
                                                  nlog_rad1, Yrcos.shape[0], 
                                                  Yrcos, 
                                                  Xrcos[0], Xrcos[1]-Xrcos[0], 
                                                  0))
                        himask = himask.reshape(nlog_rad1.shape)
                        anglemask = np.array(pointOp(nangle.shape[0], 
                                                     nangle.shape[1], 
                                                     nangle, Ycosn.shape[0], 
                                                     Ycosn, 
                                                     Xcosn[0]+np.pi*b/nbands, 
                                                     Xcosn[1]-Xcosn[0], 0))
                        anglemask = anglemask.reshape(nangle.shape)
                        band = self.pyr[bandIdx]
                        curLev = self.spyrHt() - (idx-1)
                        if curLev in levs and b in bands:
                            banddft = np.fft.fftshift(np.fft.fft2(band))
                        else:
                            banddft = np.zeros(band.shape)
                        resdft += ( (np.power(-1+0j,0.5))**(nbands-1) * 
                                    banddft * anglemask * himask )
                    bandIdx += 1

        # apply lo0mask
        Xrcos += np.log2(2.0)
        lo0mask = np.array(pointOp(log_rad.shape[0], log_rad.shape[1], 
                                   log_rad, YIrcos.shape[0], YIrcos, Xrcos[0], 
                                   Xrcos[1]-Xrcos[0], 0))
        lo0mask = lo0mask.reshape(dims[0], dims[1])
        resdft = resdft * lo0mask
        
        # residual highpass subband
        hi0mask = pointOp(log_rad.shape[0], log_rad.shape[1], log_rad, 
                          Yrcos.shape[0], Yrcos, Xrcos[0], Xrcos[1]-Xrcos[0], 0)
        hi0mask = np.array(hi0mask)
        hi0mask = hi0mask.reshape(resdft.shape[0], resdft.shape[1])
        if 0 in levs:
            hidft = np.fft.fftshift(np.fft.fft2(self.pyr[0]))
        else:
            hidft = np.zeros(self.pyr[0].shape)
        resdft += hidft * hi0mask

        outresdft = np.real(np.fft.ifft2(np.fft.ifftshift(resdft)))

        return outresdft

class SCFpyr(SFpyr):
    filt = ''
    edges = ''
    
    #constructor
    def __init__(self, *args):    # (image, height, order, twidth)
        self.pyrType = 'steerableFrequency'

        if len(args) > 0:
            self.image = args[0]
        else:
            print "First argument (image) is required."
            return

        #------------------------------------------------
        # defaults:

        max_ht = np.floor( np.log2( min(self.image.shape) ) ) - 2
        if len(args) > 1:
            if(args[1] > max_ht):
                print "Error: cannot build pyramid higher than %d levels." % (max_ht)
            ht = args[1]
        else:
            ht = max_ht
        ht = int(ht)
            
        if len(args) > 2:
            if args[2] > 15 or args[2] < 0:
                print "Warning: order must be an integer in the range [0,15]. Truncating."
                order = min( max(args[2],0), 15 )
            else:
                order = args[2]
        else:
            order = 3

        nbands = order+1

        if len(args) > 3:
            if args[3] <= 0:
                print "Warning: twidth must be positive. Setting to 1."
                twidth = 1
            else:
                twidth = args[3]
        else:
            twidth = 1

        #------------------------------------------------------
        # steering stuff:

        if nbands % 2 == 0:
            harmonics = np.array(range(nbands/2)) * 2 + 1
        else:
            harmonics = np.array(range((nbands-1)/2)) * 2

        steermtx = ppu.steer2HarmMtx(harmonics, 
                                     np.pi*np.array(range(nbands))/nbands,
                                     'even')
        #------------------------------------------------------
        
        dims = np.array(self.image.shape)
        ctr = np.ceil((np.array(dims)+0.5)/2)
        
        (xramp, yramp) = np.meshgrid((np.array(range(1,dims[1]+1))-ctr[1])/
                                     (dims[1]/2), 
                                     (np.array(range(1,dims[0]+1))-ctr[0])/
                                     (dims[0]/2))
        angle = np.arctan2(yramp, xramp)
        log_rad = np.sqrt(xramp**2 + yramp**2)
        log_rad[ctr[0]-1, ctr[1]-1] = log_rad[ctr[0]-1, ctr[1]-2]
        log_rad = np.log2(log_rad);

        ## Radial transition function (a raised cosine in log-frequency):
        (Xrcos, Yrcos) = ppu.rcosFn(twidth, (-twidth/2.0), np.array([0,1]))
        Yrcos = np.sqrt(Yrcos)

        YIrcos = np.sqrt(1.0 - Yrcos**2)
        lo0mask = np.array(pointOp(log_rad.shape[0], log_rad.shape[1], log_rad,
                                   YIrcos.shape[0], YIrcos, Xrcos[0], 
                                   Xrcos[1]-Xrcos[0], 0))

        imdft = np.fft.fftshift(np.fft.fft2(self.image))

        self.pyr = []
        self.pyrSize = []

        hi0mask = np.array(pointOp(log_rad.shape[0], log_rad.shape[1], log_rad,
                                   Yrcos.shape[0], Yrcos, Xrcos[0], 
                                   Xrcos[1]-Xrcos[0], 0))
        hi0dft = imdft * hi0mask.reshape(imdft.shape[0], imdft.shape[1])
        hi0 = np.fft.ifft2(np.fft.ifftshift(hi0dft))

        self.pyr.append(np.real(hi0.copy()))
        self.pyrSize.append(hi0.shape)

        lo0mask = lo0mask.reshape(imdft.shape[0], imdft.shape[1])
        lodft = imdft * lo0mask

        for i in range(ht):
            bands = np.zeros((lodft.shape[0]*lodft.shape[1], nbands))
            bind = np.zeros((nbands, 2))
        
            Xrcos -= np.log2(2)

            lutsize = 1024
            Xcosn = np.pi * np.array(range(-(2*lutsize+1), (lutsize+2))) / lutsize

            order = nbands -1
            const = (2**(2*order))*(spm.factorial(order, exact=True)**2)/float(nbands*spm.factorial(2*order, exact=True))

            alfa = ( (np.pi+Xcosn) % (2.0*np.pi) ) - np.pi
            Ycosn = ( 2.0*np.sqrt(const) * (np.cos(Xcosn)**order) * 
                      (np.abs(alfa)<np.pi/2.0).astype(int) )
            himask = np.array(pointOp(log_rad.shape[0], log_rad.shape[1], 
                                      log_rad, Yrcos.shape[0], Yrcos, Xrcos[0],
                                      Xrcos[1]-Xrcos[0], 0))
            himask = himask.reshape(lodft.shape[0], lodft.shape[1])

            for b in range(nbands):
                anglemask = np.array(pointOp(angle.shape[0], angle.shape[1], 
                                             angle, Ycosn.shape[0], Ycosn, 
                                             Xcosn[0]+np.pi*b/nbands, 
                                             Xcosn[1]-Xcosn[0], 0))
                anglemask = anglemask.reshape(lodft.shape[0], lodft.shape[1])
                banddft = (cmath.sqrt(-1)**order) * lodft * anglemask * himask
                band = np.negative(np.fft.ifft2(np.fft.ifftshift(banddft)))
                self.pyr.append(band.copy())
                self.pyrSize.append(band.shape)

            dims = np.array(lodft.shape)
            ctr = np.ceil((dims+0.5)/2)
            lodims = np.ceil((dims-0.5)/2)
            loctr = ceil((lodims+0.5)/2)
            lostart = ctr - loctr
            loend = lostart + lodims

            log_rad = log_rad[lostart[0]:loend[0], lostart[1]:loend[1]]
            angle = angle[lostart[0]:loend[0], lostart[1]:loend[1]]
            lodft = lodft[lostart[0]:loend[0], lostart[1]:loend[1]]
            YIrcos = np.abs(np.sqrt(1.0 - Yrcos**2))
            lomask = np.array(pointOp(log_rad.shape[0], log_rad.shape[1], 
                                      log_rad, YIrcos.shape[0], YIrcos, 
                                      Xrcos[0], Xrcos[1]-Xrcos[0],
                                      0))
            lodft = lodft * lomask.reshape(lodft.shape[0], lodft.shape[1])

        lodft = np.fft.ifft2(np.fft.ifftshift(lodft))
        self.pyr.append(np.real(np.array(lodft).copy()))
        self.pyrSize.append(lodft.shape)

    # methods
    def reconSCFpyr(self, *args):
        if len(args) > 0:
            levs = args[0]
        else:
            levs = 'all'

        if len(args) > 1:
            bands = args[1]
        else:
            bands = 'all'

        if len(args) > 2:
            if args[2] <= 0:
                print "Warning: twidth must be positive. Setting to 1."
                twidth = 1
            else:
                twidth = args[2]
        else:
            twidth = 1

        #-----------------------------------------------------------------

        pind = self.pyrSize
        Nsc = np.log2(pind[0][0] / pind[-1][0])
        Nor = (len(pind)-2) / Nsc

        pyrIdx = 1
        for nsc in range(Nsc):
            firstBnum = nsc * Nor+2
            dims = pind[firstBnum.astype(int)][:]
            ctr = (np.ceil((dims[0]+0.5)/2.0), np.ceil((dims[1]+0.5)/2.0)) #-1?
            ang = ppu.mkAngle(dims, 0, ctr)
            ang[ctr[0]-1, ctr[1]-1] = -np.pi/2.0
            for nor in range(Nor):
                nband = nsc * Nor + nor + 1
                ch = self.pyr[nband.astype(int)]
                ang0 = np.pi * nor / Nor
                xang = ((ang-ang0+np.pi) % (2.0*np.pi)) - np.pi
                amask = 2 * (np.abs(xang) < (np.pi/2.0)).astype(int) + (np.abs(xang) == (np.pi/2.0)).astype(int)
                amask[ctr[0]-1, ctr[1]-1] = 1
                amask[:,0] = 1
                amask[0,:] = 1
                amask = np.fft.fftshift(amask)
                ch = np.fft.ifft2(amask * np.fft.fft2(ch))  # 'Analytic' version
                # f = 1.000008  # With this factor the reconstruction SNR
                                # goes up around 6 dB!
                f = 1
                ch = f*0.5*np.real(ch)   # real part
                self.pyr[pyrIdx] = ch
                pyrIdx += 1

        res = self.reconSFpyr(levs, bands, twidth);

        return res


class Lpyr(pyramid):
    filt = ''
    edges = ''
    height = ''

    # constructor
    def __init__(self, *args):    # (image, height, filter1, filter2, edges)
        self.pyrType = 'Laplacian'
        if len(args) > 0:
            self.image = args[0]
        else:
            print "pyr = Lpyr(image, height, filter1, filter2, edges)"
            print "First argument (image) is required"
            return

        if len(args) > 2:
            filt1 = args[2]
            if isinstance(filt1, basestring):
                filt1 = ppu.namedFilter(filt1)
            elif len(filt1.shape) != 1 and ( filt1.shape[0] != 1 and
                                             filt1.shape[1] != 1 ):
                print "Error: filter1 should be a 1D filter (i.e., a vector)"
                return
        else:
            filt1 = ppu.namedFilter('binom5')
        #if len(filt1.shape) == 1 or self.image.shape[0] == 1
        #    filt1 = filt1.reshape(1,len(filt1))
        if len(filt1.shape) == 1:
            filt1 = filt1.reshape(1,len(filt1))
        elif self.image.shape[0] == 1:
            filt1 = filt1.reshape(filt1.shape[1], filt1.shape[0])

        if len(args) > 3:
            filt2 = args[3]
            if isinstance(filt2, basestring):
                filt2 = ppu.namedFilter(filt2)
            elif len(filt2.shape) != 1 and ( filt2.shape[0] != 1 and
                                            filt2.shape[1] != 1 ):
                print "Error: filter2 should be a 1D filter (i.e., a vector)"
                return
        else:
            filt2 = filt1

        maxHeight = 1 + ppu.maxPyrHt(self.image.shape, filt1.shape)

        if len(args) > 1:
            if args[1] is "auto":
                self.height = maxHeight
            else:
                self.height = args[1]
                if self.height > maxHeight:
                    print ( "Error: cannot build pyramid higher than %d levels"
                            % (maxHeight) )
                    return
        else:
            self.height = maxHeight

        if len(args) > 4:
            edges = args[4]
        else:
            edges = "reflect1"

        # make pyramid
        self.pyr = []
        self.pyrSize = []
        pyrCtr = 0
        im = np.array(self.image).astype(float)
        if len(im.shape) == 1:
            im = im.reshape(im.shape[0], 1)
        los = {}
        los[self.height] = im
        # compute low bands
        for ht in range(self.height-1,0,-1):
            im_sz = im.shape
            filt1_sz = filt1.shape
            if im_sz[0] == 1:
                lo2 = np.array( corrDn(1, im_sz[1], im, filt1_sz[0], 
                                       filt1_sz[1], filt1, edges, 
                                       1, 2, 0, 0, 
                                       int(math.ceil(im_sz[1]/2.0)), 1) ).T
            elif len(im_sz) == 1 or im_sz[1] == 1:
                lo2 = np.array( corrDn(im_sz[0], 1, im, filt1_sz[0], 
                                       filt1_sz[1], filt1, edges, 2, 1, 0, 0, 
                                       int(math.ceil(im_sz[0]/2.0)), 1) ).T
            else:
                lo = np.array( corrDn(im_sz[1], im_sz[0], im, filt1_sz[0], 
                                      filt1_sz[1], filt1, edges, 2, 1, 0, 0, 
                                      im_sz[0], im_sz[1]) )
                #lo = np.array(lo).reshape(math.ceil(im_sz[0]/1.0), 
                #                          math.ceil(im_sz[1]/2.0), 
                #                          order='C')
                lo2 = np.array( corrDn(int(math.ceil(im_sz[0]/1.0)), 
                                       int(math.ceil(im_sz[1]/2.0)), lo.T, 
                                       filt1_sz[0], filt1_sz[1], filt1, edges, 
                                       2, 1, 0, 0, im_sz[0], im_sz[1]) ).T
                #lo2 = np.array(lo2).reshape(math.ceil(im_sz[0]/2.0), 
                #                            math.ceil(im_sz[1]/2.0), 
                #                            order='F')
            los[ht] = lo2
                
            im = lo2

        #self.pyr[self.height-1] = lo2
        #self.pyrSize[self.height-1] = lo2.shape
        # adjust shape if 1D if needed
        self.pyr.append(lo2.copy())
        self.pyrSize.append(lo2.shape)

        # compute hi bands
        im = self.image
        for ht in range(self.height, 1, -1):
            im = los[ht-1]
            im_sz = los[ht-1].shape
            filt2_sz = filt2.shape
            if len(im_sz) == 1 or im_sz[1] == 1:
                hi2 = upConv(im_sz[0], im_sz[1], im, filt2_sz[0], filt2_sz[1], 
                            filt2, edges, 2, 1, 0, 0, los[ht].shape[0], 
                             los[ht].shape[1]).T
            elif im_sz[0] == 1:
                hi2 = upConv(im_sz[0], im_sz[1], im, filt2_sz[1], filt2_sz[0], 
                            filt2, edges, 1, 2, 0, 0, los[ht].shape[0], 
                             los[ht].shape[1]).T
            else:
                hi = upConv(im_sz[0], im_sz[1], im.T, filt2_sz[0], filt2_sz[1], 
                            filt2, edges, 2, 1, 0, 0, los[ht].shape[0], 
                            im_sz[1]).T
                #hi = np.array(hi).reshape(los[ht].shape[0], im_sz[1], order='F')
                int_sz = hi.shape
                hi2 = upConv(los[ht].shape[0], im_sz[1], hi.T, filt2_sz[1], 
                             filt2_sz[0], filt2, edges, 1, 2, 0, 0, 
                             los[ht].shape[0], los[ht].shape[1]).T
                #hi2 = np.array(hi2).reshape(los[ht].shape[0], los[ht].shape[1],
                #                            order='F')

            hi2 = los[ht] - hi2
            #self.pyr[pyrCtr] = hi2
            #self.pyrSize[pyrCtr] = hi2.shape
            self.pyr.insert(pyrCtr, hi2.copy())
            self.pyrSize.insert(pyrCtr, hi2.shape)
            pyrCtr += 1

    # methods
    # return concatenation of all levels of 1d pyramid
    def catBands(self, *args):
        outarray = np.array([]).reshape((1,0))
        for i in range(self.height):
            tmp = self.band(i).T
            outarray = np.concatenate((outarray, tmp), axis=1)
        return outarray

    # set a pyramid value
    def set(self, *args):
        if len(args) != 3:
            print 'Error: three input parameters required:'
            print '  set(band, element, value)'
        self.pyr[args[0]][args[1]] = args[2] 

    def reconLpyr(self, *args):
        if len(args) > 0:
            levs = np.array(args[0])
        else:
            levs = 'all'

        if len(args) > 1:
            filt2 = args[1]
        else:
            filt2 = 'binom5'

        if len(args) > 2:
            edges = args[2]
        else:
            edges = 'reflect1';

        maxLev = self.height

        if levs == 'all':
            levs = range(0,maxLev)
        else:
            if (levs > maxLev-1).any():
                print ( "Error: level numbers must be in the range [0, %d]." % 
                        (maxLev-1) )
                return

        if isinstance(filt2, basestring):
            filt2 = ppu.namedFilter(filt2)
        else:
            if len(filt2.shape) == 1:
                filt2 = filt2.reshape(1, len(filt2))

        res = []
        lastLev = -1
        for lev in range(maxLev-1, -1, -1):
            if lev in levs and len(res) == 0:
                res = self.band(lev)
            elif len(res) != 0:
                res_sz = res.shape
                new_sz = self.band(lev).shape
                filt2_sz = filt2.shape
                if res_sz[0] == 1:
                    hi2 = upConv(new_sz[0], res_sz[1], res.T, filt2_sz[1], 
                                 filt2_sz[0], filt2, edges, 1, 2, 0, 0, 
                                 new_sz[0], new_sz[1]).T
                elif res_sz[1] == 1:
                    hi2 = upConv(new_sz[0], res_sz[1], res.T, filt2_sz[0], 
                                 filt2_sz[1], filt2, edges, 2, 1, 0, 0, 
                                 new_sz[0], new_sz[1]).T
                else:
                    hi = upConv(res_sz[0], res_sz[1], res.T, filt2_sz[0], 
                                filt2_sz[1], filt2, edges, 2, 1, 0, 0, 
                                new_sz[0], res_sz[1]).T
                    hi2 = upConv(new_sz[0], res_sz[1], hi.T, filt2_sz[1], 
                                 filt2_sz[0], filt2, edges, 1, 2, 0, 0, 
                                 new_sz[0], new_sz[1]).T
                if lev in levs:
                    bandIm = self.band(lev)
                    bandIm_sz = bandIm.shape
                    res = hi2 + bandIm
                else:
                    res = hi2
        return res                           
                
    def pyrLow(self):
        return np.array(self.band(self.height-1))

    def showPyr(self, *args):
        if ( len(self.band(0).shape) == 1 or self.band(0).shape[0] == 1 or
             self.band(0).shape[1] == 1 ):
            oned = 1
        else:
            oned = 0

        if len(args) <= 1:
            if oned == 1:
                pRange = 'auto1'
            else:
                pRange = 'auto2'
        
        if len(args) <= 2:
            gap = 1

        if len(args) <= 3:
            if oned == 1:
                scale = math.sqrt(2)
            else:
                scale = 2

        #nind = self.height - 1
        nind = self.height
            
        # auto range calculations
        if pRange == 'auto1':
            pRange = np.zeros((nind,1))
            mn = 0.0
            mx = 0.0
            for bnum in range(nind):
                band = self.band(bnum)
                band /= np.power(scale, bnum-1)
                pRange[bnum] = np.power(scale, bnum-1)
                bmn = np.amin(band)
                bmx = np.amax(band)
                mn = np.amin([mn, bmn])
                mx = np.amax([mx, bmx])
            if oned == 1:
                pad = (mx-mn)/12       # magic number
                mn -= pad
                mx += pad
            pRange = np.outer(pRange, np.array([mn, mx]))
            band = self.pyrLow()
            mn = np.amin(band)
            mx = np.amax(band)
            if oned == 1:
                pad = (mx-mn)/12
                mn -= pad
                mx += pad
            pRange[nind-1,:] = [mn, mx];
        elif pRange == 'indep1':
            pRange = np.zeros((nind,1))
            for bnum in range(nind):
                band = self.band(bnum)
                mn = np.amin(band)
                mx = np.amax(band)
                if oned == 1:
                    pad = (mx-mn)/12;
                    mn -= pad
                    mx += pad
                pRange[bnum,:] = np.array([mn, mx])
        elif pRange == 'auto2':
            pRange = np.zeros((nind,1))
            sqsum = 0
            numpixels = 0
            for bnum in range(0, nind-1):
                band = self.band(bnum)
                band /= np.power(scale, bnum)
                sqsum += np.sum( np.power(band, 2) )
                numpixels += np.prod(band.shape)
                pRange[bnum,:] = np.power(scale, bnum)
            stdev = math.sqrt( sqsum / (numpixels-1) )
            pRange = np.outer( pRange, np.array([-3*stdev, 3*stdev]) )
            band = self.pyrLow()
            av = np.mean(band)
            stdev = np.std(band)
            pRange[nind-1,:] = np.array([av-2*stdev, av+2*stdev]);#by ref? safe?
        elif pRange == 'indep2':
            pRange = np.zeros(nind,2)
            for bnum in range(0,nind-1):
                band = self.band(bnum)
                stdev = np.std(band)
                pRange[bnum,:] = np.array([-3*stdev, 3*stdev])
            band = self.pyrLow()
            av = np.mean(band)
            stdev = np.std(band)
            pRange[nind,:] = np.array([av-2*stdev, av+2*stdev])
        elif isinstance(pRange, basestring):
            print "Error: band range argument: %s" % (pRange)
            return
        elif pRange.shape[0] == 1 and pRange.shape[1] == 2:
            scales = np.power( np.array( range(0,nind) ), scale)
            pRange = np.outer( scales, pRange )
            band = self.pyrLow()
            pRange[nind,:] = ( pRange[nind,:] + np.mean(band) - 
                               np.mean(pRange[nind,:]) )

        # draw
        if oned == 1:
            fig = plt.figure()
            ax0 = fig.add_subplot(nind, 1, 0)
            ax0.set_frame_on(False)
            ax0.get_xaxis().tick_bottom()
            ax0.get_xaxis().tick_top()
            ax0.get_yaxis().tick_right()
            ax0.get_yaxis().tick_left()
            ax0.get_yaxis().set_visible(False)
            for bnum in range(0,nind):
                subplot(nind, 1, bnum+1)
                plot(np.array(range(np.amax(self.band(bnum).shape))).T, 
                     self.band(bnum).T)
                ylim(pRange[bnum,:])
                xlim((0,self.band(bnum).shape[1]-1))
            plt.show()
        else:
            colormap = cm.Greys_r
            # skipping background calculation. needed?

            # compute positions of subbands:
            llpos = np.ones((nind, 2)).astype(float)
            dirr = np.array([-1.0, -1.0])
            ctr = np.array([self.band(0).shape[0]+1+gap, 1]).astype(float)
            sz = np.array([0.0, 0.0])
            for bnum in range(nind):
                prevsz = sz
                sz = self.band(bnum).shape
                
                # determine center position of new band:
                ctr = ( ctr + gap*dirr/2.0 + dirr * 
                        np.floor( (prevsz+(dirr<0).astype(int))/2.0 ) )
                dirr = np.dot(dirr,np.array([ [0, -1], [1, 0] ])) # ccw rotation
                ctr = ( ctr + gap*dirr/2 + dirr * 
                        np.floor( (sz+(dirr<0).astype(int)) / 2.0) )
                llpos[bnum,:] = ctr - np.floor(np.array(sz))/2.0 
            # make position list positive, and allocate appropriate image
            llpos = llpos - np.ones((nind,1))*np.min(llpos)
            pind = range(self.height)
            for i in pind:
                pind[i] = self.band(i).shape
            urpos = llpos + pind
            d_im = np.zeros((np.max(urpos), np.max(urpos)))  # need bg here?
            
            # paste bands into image, (im-r1)*(nshades-1)/(r2-r1) + 1.5
            nshades = 256
            for bnum in range(nind):
                mult = (nshades-1) / (pRange[bnum,1]-pRange[bnum,0])
                d_im[llpos[bnum,0]:urpos[bnum,0], llpos[bnum,1]:urpos[bnum,1]]=(
                    mult*self.band(bnum) + (1.5-mult*pRange[bnum,0]) )
                # layout works
                #d_im[llpos[bnum,0]:urpos[bnum,0],llpos[bnum,1]:urpos[bnum,1]]=(
                    #(bnum+1)*10 )
            
            ppu.showIm(d_im)

class Gpyr(Lpyr):
    filt = ''
    edges = ''
    height = ''

    # constructor
    def __init__(self, *args):    # (image, height, filter, edges)
        self.pyrType = 'Gaussian'
        if len(args) < 1:
            print "pyr = Gpyr(image, height, filter, edges)"
            print "First argument (image) is required"
            return
        else:
            self.image = args[0]

        if len(args) > 2:
            filt = args[2]
            if not (filt.shape == 1).any():
                print "Error: filt should be a 1D filter (i.e., a vector)"
                return
        else:
            print "no filter set, so filter is binom5"
            filt = ppu.namedFilter('binom5')
            if self.image.shape[0] == 1:
                filt = filt.reshape(1,5)
            else:
                filt = filt.reshape(5,1)

        maxHeight = 1 + ppu.maxPyrHt(self.image.shape, filt.shape)

        if len(args) > 1:
            if args[1] is "auto":
                self.height = maxHeight
            else:
                self.height = args[1]
                if self.height > maxHeight:
                    print ( "Error: cannot build pyramid higher than %d levels"
                            % (maxHeight) )
                    return
        else:
            self.height = maxHeight

        if len(args) > 3:
            edges = args[3]
        else:
            edges = "reflect1"

        # make pyramid
        self.pyr = []
        self.pyrSize = []
        pyrCtr = 0
        im = np.array(self.image).astype(float)

        if len(im.shape) == 1:
            im = im.reshape(im.shape[0], 1)

        #self.pyr[pyrCtr] = im
        #self.pyrSize[pyrCtr] = im.shape
        self.pyr.append(im.copy())
        self.pyrSize.append(im.shape)
        pyrCtr += 1

        for ht in range(self.height-1,0,-1):
            im_sz = im.shape
            filt_sz = filt.shape
            if len(im_sz) == 1:
                lo2 = np.array( corrDn(im_sz[0], 1, im, filt_sz[0], filt_sz[1],
                                       filt, edges, 2, 1, 0, 0, im_sz[0], 1) )
                #lo2 = np.array(lo2).reshape(im_sz[0]/2, 1, order='C')
                print lo2
            elif im_sz[0] == 1:
                #lo2 = np.array( corrDn(1, im_sz[1], im, filt_sz[0], filt_sz[1],
                #                       filt, edges, 1, 2, 0, 0, 1, im_sz[1]) )
                print im
                print im.shape
                print filt
                print filt.shape
                filt = filt[0,:]
                print filt.shape
                lo2 = np.array( corrDn(im_sz[0], 1, im, filt_sz[0], filt_sz[1],
                                       filt, edges, 2, 1, 0, 0, im_sz[0], 1) )
                print lo2
                #lo2 = np.array(lo2).reshape(1, im_sz[1]/2, order='C')
            elif im_sz[1] == 1:
                #lo2 = np.array( corrDn(im_sz[0], 1, im, filt_sz[0], filt_sz[1],
                #                       filt, edges, 2, 1, 0, 0, im_sz[0], 1) )
                lo2 = np.array( corrDn(1, im_sz[1], im, filt_sz[0], filt_sz[1],
                                       filt, edges, 1, 2, 0, 0, 1, im_sz[1]) )
                print lo2
                #lo2 = np.array(lo2).reshape(im_sz[0]/2, 1, order='C')
            else:
                lo = np.array( corrDn(im_sz[1], im_sz[0], im, filt_sz[0], 
                                      filt_sz[1], filt, edges, 2, 1, 0, 0, 
                                      im_sz[0], im_sz[1]) )
                print lo
                #lo = np.array(lo).reshape(math.ceil(im_sz[0]/1.0), 
                #                          math.ceil(im_sz[1]/2.0), 
                #                          order='C')
                lo2 = np.array( corrDn(math.ceil(im_sz[0]/1.0), 
                                       math.ceil(im_sz[1]/2.0), 
                                       lo.T, filt_sz[0], filt_sz[1], filt, 
                                       edges, 2, 1, 0, 0, im_sz[0], im_sz[1]) ).T
                print lo2
                #lo2 = np.array(lo2).reshape(math.ceil(im_sz[0]/2.0), 
                #                            math.ceil(im_sz[1]/2.0), 
                #                            order='F')

            #self.pyr[pyrCtr] = lo2
            #self.pyrSize[pyrCtr] = lo2.shape
            self.pyr.append(lo2.copy())
            self.pyrSize.append(lo2.shape)
            pyrCtr += 1

            im = lo2
        
    # methods

class Wpyr_new(Lpyr):
    filt = ''
    edges = ''
    height = ''
    
    #constructor
    def __init__(self, *args):    # (image, height, order, twidth)
        self.pyr = []
        self.pyrSize = []
        self.pyrType = 'wavelet'

        if len(args) > 0:
            im = args[0]
        else:
            print "First argument (image) is required."
            return

        #------------------------------------------------
        # defaults:

        if len(args) > 2:
            filt = args[1]
        else:
            filt = "qmf9"
        if isinstance(filt, basestring):
            filt = ppu.namedFilter(filt)

        if len(filt.shape) != 1 and filt.shape[0] != 1 and filt.shape[1] != 1:
            print "Error: filter should be 1D (i.e., a vector)";
            return
        hfilt = ppu.modulateFlip(filt).T

        if len(args) > 3:
            edges = args[2]
        else:
            edges = "reflect1"

        # Stagger sampling if filter is odd-length:
        if filt.shape[0] % 2 == 0:
            stag = 2
        else:
            stag = 1
        #print 'stag = %d' % (stag)

        im_sz = im.shape
        if len(im.shape) == 1 or im.shape[1] == 1:
            im = im.reshape(1, im.shape[0])

        if len(filt.shape) == 1 or filt.shape[1] == 1:
            filt = filt.reshape(1, filt.shape[0])
        filt_sz = filt.shape

        max_ht = ppu.maxPyrHt(im_sz, filt_sz)

        if len(args) > 1:
            ht = args[1]
            if ht == 'auto':
                ht = max_ht
            elif(ht > max_ht):
                print "Error: cannot build pyramid higher than %d levels." % (max_ht)
        else:
            ht = max_ht
        ht = int(ht)
        self.height = ht + 1  # used with showPyr() method

        for lev in range(ht):
            #print "lev = %d" % (lev)
            im_sz = im.shape
            #if len(im.shape) == 1:
            #    im_sz = (1, im.shape[0])
            #elif im.shape[1] == 1:
            #    im_sz = (im.shape[1], im.shape[0])
            #print "im_sz"
            #print im_sz
            if len(im_sz) == 1 or im_sz[1] == 1:
                lolo = np.array( corrDn(im_sz[0], im_sz[1], im.T, filt_sz[0],
                                        filt_sz[1], filt, edges, 2, 1, stag-1, 
                                        0) )
                hihi = np.array( corrDn(im_sz[0], im_sz[1], im.T, filt_sz[0], 
                                        filt_sz[1], hfilt, edges, 2, 1, 1, 0) )
            elif im_sz[0] == 1:
                #lolo = np.array( corrDn(im_sz[0], im_sz[1], im, filt_sz[0], 
                #                        filt_sz[1], filt, edges, 1, 2, 0, 
                #                        stag-1) )
                lolo = np.array( corrDn(im_sz[0], im_sz[1], im, filt_sz[0], 
                                        filt_sz[1], filt, edges, 1, 2, 0, 1) ).T
                hihi = np.array( corrDn(im_sz[0], im_sz[1], im, filt_sz[0], 
                                        filt_sz[1], hfilt, edges, 1, 2, 0, 1) ).T
            else:
                lo = np.array( corrDn(im.shape[0], im.shape[1], im.T, 
                                      filt.shape[0], 1, filt, edges, 2, 1, 
                                      stag-1, 0) ).T
                #lo = lo.reshape(math.ceil(im.shape[0]/2.0), 
                #                math.ceil(im.shape[1]/stag), order='F')
                hi = np.array( corrDn(im.shape[0], im.shape[1], im.T, 
                                      hfilt.shape[0], 1, hfilt, edges, 2, 1, 1,
                                      0) ).T
                #hi = hi.reshape(math.floor(im.shape[0]/2.0), im.shape[1], 
                #                order='F')
                lolo = np.array( corrDn(lo.shape[0], lo.shape[1], lo.T, 1, 
                                        filt.shape[0], filt, edges, 1, 2, 0, 
                                        stag-1) ).T 
                #lolo = lolo.reshape(math.ceil(lo.shape[0]/float(stag)), 
                #                    math.ceil(lo.shape[1]/2.0), order='F')
                lohi = np.array( corrDn(hi.shape[0], hi.shape[1], hi.T, 1, 
                                        filt.shape[0], filt, edges, 1, 2, 0, 
                                        stag-1) ).T
                #lohi = lohi.reshape(hi.shape[0], math.ceil(hi.shape[1]/2.0), 
                #                    order='F')
                hilo = np.array( corrDn(lo.shape[0], lo.shape[1], lo.T, 1,
                                        hfilt.shape[0], hfilt, edges, 1, 2, 0, 
                                        1) ).T
                #hilo = hilo.reshape(lo.shape[0], math.floor(lo.shape[1]/2.0), 
                #                    order='F')
                hihi = np.array( corrDn(hi.shape[0], hi.shape[1], hi.T, 1, 
                                        hfilt.shape[0], hfilt, edges, 1, 2, 0, 
                                        1) ).T
                #hihi = hihi.reshape(hi.shape[0], math.floor(hi.shape[1]/2.0), 
                #                    order='F')
            if im_sz[0] == 1 or im_sz[1] == 1:
                self.pyr.append(hihi)
                self.pyrSize.append(hihi.shape)
            else:
                self.pyr.append(lohi)
                self.pyrSize.append(lohi.shape)
                self.pyr.append(hilo)
                self.pyrSize.append(hilo.shape)
                self.pyr.append(hihi)
                self.pyrSize.append(hihi.shape)
            im = lolo
        self.pyr.append(lolo)
        self.pyrSize.append(lolo.shape)

    # methods

    def wpyrHt(self):
        if ( len(self.pyrSize[0]) == 1 or self.pyrSize[0][0] == 1 or 
             self.pyrSize[0][1] == 1 ): 
            nbands = 1
        else:
            nbands = 3

        ht = (len(self.pyrSize)-1)/float(nbands)

        return int(ht)


    def reconWpyr(self, *args):
        # Optional args
        if len(args) > 0:
            filt = args[0]
        else:
            filt = 'qmf9'
            
        if len(args) > 1:
            edges = args[1]
        else:
            edges = 'reflect1'

        if len(args) > 2:
            levs = args[2]
        else:
            levs = 'all'

        if len(args) > 3:
            bands = args[3]
        else:
            bands = 'all'

        #------------------------------------------------------

        print self.pyrSize
        maxLev = self.wpyrHt() + 1
        print "maxLev = %d" % maxLev
        if levs == 'all':
            levs = np.array(range(maxLev))
        else:
            tmpLevs = []
            for l in levs:
                tmpLevs.append((maxLev-1)-l)
            levs = np.array(tmpLevs)
            if (levs > maxLev).any():
                print "Error: level numbers must be in the range [0, %d]" % (maxLev)
        allLevs = np.array(range(maxLev))

        print "levs:"
        print levs
        
        if bands == "all":
            bands = np.array(range(3))
        else:
            bands = np.array(bands)
            if (bands < 0).any() or (bands > 2).any():
                print "Error: band numbers must be in the range [0,2]."
        
        if isinstance(filt, basestring):
            filt = ppu.namedFilter(filt)

        print "filt"
        print filt
        hfilt = ppu.modulateFlip(filt)
        print "hfilt"
        print hfilt

        # for odd-length filters, stagger the sampling lattices:
        if len(filt) % 2 == 0:
            stag = 2
        else:
            stag = 1
        print "stag = %d" % (stag)

        #if 0 in levs:
        #    res = self.pyr[len(self.pyr)-1]
        #else:
        #    res = np.zeros(self.pyr[len(self.pyr)-1].shape)
        #print res

        print "pyrSize[0]:"
        print self.pyrSize[0]
        print "pyrSize[3]:"
        print self.pyrSize[3]

        print 'len pyrSize = %d' % (len(self.pyr))

        idx = len(self.pyrSize)-1

        print "levs:"
        print levs
        print "bands:"
        print bands

        #for lev in levs:
        for lev in allLevs:
            print "starting levs loop lev = %d" % lev

            if lev == 0:
                if 0 in levs:
                    res = self.pyr[len(self.pyr)-1]
                else:
                    res = np.zeros(self.pyr[len(self.pyr)-1].shape)
                print res
            elif lev > 0:
                # compute size of result image: assumes critical sampling
                resIdx = len(self.pyrSize)-(3*(lev-1))-3
                print "resIdx = %d" % resIdx
                res_sz = self.pyrSize[resIdx]
                print 'res_sz'
                print res_sz
                print 'self.pyrSize'
                print self.pyrSize
                if res_sz[0] == 1:
                    res_sz = (1, sum([i[1] for i in self.pyrSize]))
                elif res_sz[1] == 1:
                    res_sz = (sum([i[0] for i in self.pyrSize]), 1)
                else:
                #horizontal + vertical bands
                    res_sz = (self.pyrSize[resIdx][0]+self.pyrSize[resIdx-1][0],
                              self.pyrSize[resIdx][1]+self.pyrSize[resIdx-1][1])
                    lres_sz = np.array([self.pyrSize[resIdx][0], res_sz[1]])
                    hres_sz = np.array([self.pyrSize[resIdx-1][0], res_sz[1]])

                imageIn = res
                #fp = open('tmp.txt', 'a')
                #fp.write('%d ires\n' % lev)
                #fp.close()
                if res_sz[0] == 1:
                    #res = upConv(nres, filt', edges, [1 2], [1 stag], res_sz);
                    res = upConv(res.shape[0], res.shape[1], res, filt.shape[1],
                                 filt.shape[0], filt, edges, 1, 2, 0, stag-1, 
                                 res_sz[0], res_sz[1])
                elif res_sz[1] == 1:
                    #res = upConv(nres, filt, edges, [2 1], [stag 1], res_sz);
                    res = upConv(res.shape[0], res.shape[1], res, filt.shape[0],
                                 filt.shape[1], filt, edges, 2, 1, stag-1, 0, 
                                 res_sz[0], res_sz[1])
                else:
                    print "filt shape = %d %d\n" % (filt.shape[0], 
                                                    filt.shape[1])
                    ires = upConv(imageIn.shape[1], 
                                  imageIn.shape[0],
                                  imageIn.T, filt.shape[1], filt.shape[0], 
                                  filt, edges, 1, 2, 0, stag-1, lres_sz[0], 
                                  lres_sz[1])
                    ires = np.array(ires).T
                    print "%d ires" % (lev)
                    print ires
                    print ires.shape
                    print "hfilt"
                    print hfilt
                    #fp = open('tmp.txt', 'a')
                    #fp.write("%d res\n" % (lev))
                    #fp.close()
                    res = upConv(ires.shape[1], ires.shape[0], ires.T, 
                                 filt.shape[0],
                                 filt.shape[1], filt, edges, 2, 1, stag-1, 0, 
                                 res_sz[0], res_sz[1]).T
                    res = np.array(res)
                    print "%d res" % (lev)
                    print res

                idx = resIdx - 1
                print 'starting bands idx = %d' % (idx)
                #if res_sz[0] == 1:
                #    #upConv(pyrBand(pyr,ind,1), hfilt', edges, [1 2], [1 2], 
                #    #  res_sz, res);
                #    res = upConv(self.band(0).shape[0], self.band(0).shape[1], 
                #                 self.band(0), hfilt.shape[0], hfilt.shape[1], 
                #                 hfilt, edges, 1, 2, 0, 1, res_sz[0], 
                #                 res_sz[1], res)
                #elif res_sz[1] == 1:
                #    #upConv(pyrBand(pyr,ind,1), hfilt, edges, [2 1], [2 1], 
                #    #  res_sz, res);
                #    res = upConv(self.band(0).shape[0], self.band(0).shape[1],
                #                 self.band(0), hfilt.shape[1], hfilt.shape[0], 
                #                 hfilt, edges, 2, 2, 1, 0, res_sz[0], 
                #                 res_sz[1], res)
                #else:
                    #if 0 in bands:
                if 0 in bands and lev in levs:
                    print "0 band"
                    print "idx = %d" % idx
                    print "resIdx = %d" % resIdx
                    print "input band"
                    print self.band(idx)
                        #fp = open('tmp.txt', 'a')
                        #fp.write("ires 0 band\n")
                        #fp.close()
                        # broken for even filters
                        #ires = upConv(self.band(idx).shape[0], 
                        #              self.band(idx).shape[1],
                        #              self.band(idx).T, 
                        #              filt.shape[1], filt.shape[0], filt, 
                        #              edges, 1, 2, stag-1, 0, hres_sz[0], 
                        #              hres_sz[1])
                        # works with even filter
                    ires = upConv(self.band(idx).shape[0], 
                                  self.band(idx).shape[1],
                                  self.band(idx).T, 
                                  filt.shape[1], filt.shape[0], filt, 
                                  edges, 1, 2, 0, stag-1, hres_sz[0], 
                                  hres_sz[1])
                    ires = np.array(ires).T
                        #ires = ires.reshape(hres_sz[1], hres_sz[0]).T
                    print "ires"
                    print ires
                    print ires.shape

                    print "pre upconv res"
                    print res
                        #fp = open('tmp.txt', 'a')
                        #fp.write("res 0 band\n")
                        #fp.close()
                    print "pre res size"
                    print res.shape
                    res = upConv(ires.shape[0], ires.shape[1], ires.T, 
                                 hfilt.shape[1], hfilt.shape[0], hfilt, 
                                 edges, 2, 1, 1, 0, 
                                 res_sz[0], res_sz[1], res.T)
                    res = np.array(res).T
                    print "res size %d %d" % (res_sz[1], res_sz[0])
                    print "post res size"
                    print res.shape
                    print "post upconv res"
                    print res
                idx += 1
                    #if 1 in bands:
                if 1 in bands and lev in levs:
                    print "1 band"
                    print "idx = %d" % idx
                    print "lres_sz"
                    print lres_sz
                    print lres_sz[0]
                    print lres_sz[1]
                    print "self.band(idx)"
                    print self.band(idx)
                    print self.band(idx).shape
                    print hfilt
                        #fp = open('tmp.txt', 'a')
                        #fp.write("ires 1 band\n")
                        #fp.close()
                    ires = upConv(self.band(idx).shape[0], 
                                  self.band(idx).shape[1], 
                                  self.band(idx).T, 
                                  hfilt.shape[0], hfilt.shape[1], hfilt, 
                                  edges, 1, 2, 0, 1, lres_sz[0], lres_sz[1])
                    ires = np.array(ires).T
                    print "ires"
                    print ires
                    print ires.shape
                    print filt.shape
                    print "pre res"
                    print res
                    print filt
                    print edges
                    print "stag = %d" % stag
                        #fp = open('tmp.txt', 'a')
                        #fp.write("res 1 band\n")
                        #fp.close()
                    res = upConv(ires.shape[0], ires.shape[1], ires.T, 
                                 filt.shape[0], filt.shape[1], filt, 
                                 edges, 2, 1, stag-1, 0, 
                                 res_sz[0], res_sz[1], res.T)
                    res = np.array(res).T
                        #res = res.reshape(res_sz[1], res_sz[0]).T
                    print "res"
                    print res
                idx += 1
                    #if 2 in bands:
                if 2 in bands and lev in levs:
                    print "2 band"
                    print "idx = %d" % idx
                    print "input image"
                    print self.band(idx)
                        #fp = open('tmp.txt', 'a')
                        #fp.write("ires 2 band\n")
                        #fp.close()
                    ires = upConv(self.band(idx).shape[0],
                                  self.band(idx).shape[1],
                                  self.band(idx).T,
                                  hfilt.shape[0], hfilt.shape[1], hfilt, 
                                  edges, 1, 2, 0, 1, hres_sz[0], hres_sz[1])
                    ires = np.array(ires).T
                        #ires = ires.reshape(hres_sz[1], hres_sz[0]).T
                    print "ires"
                    print ires
                    print "pre res"
                    print res
                        #fp = open('tmp.txt', 'a')
                        #fp.write("res 2 band\n")
                        #fp.close()
                    res = upConv(ires.shape[1], ires.shape[0], ires.T, 
                                 hfilt.shape[1], hfilt.shape[0], hfilt,
                                 edges, 2, 1, 1, 0, res_sz[0], res_sz[1], 
                                 res.T)
                    res = np.array(res).T
                    print "res"
                    print res
                idx += 1
                    # need to jump back n bands in the idx each loop
                idx -= 2*len(bands)
        return res

class Wpyr_bak(pyramid):
    filt = ''
    edges = ''
    
    #constructor
    def __init__(self, *args):    # (image, height, order, twidth)
        self.pyr = []
        self.pyrSize = []
        self.pyrType = 'wavelet'

        if len(args) > 0:
            im = args[0]
        else:
            print "First argument (image) is required."
            return

        #------------------------------------------------
        # defaults:

        if len(args) > 2:
            filt = args[1]
        else:
            filt = "qmf9"
        if isinstance(filt, basestring):
            filt = ppu.namedFilter(filt)

        if len(filt.shape) != 1 and filt.shape[0] != 1 and filt.shape[1] != 1:
            print "Error: filter should be 1D (i.e., a vector)";
            return
        hfilt = ppu.modulateFlip(filt).T

        if len(args) > 3:
            edges = args[2]
        else:
            edges = "reflect1"

        # Stagger sampling if filter is odd-length:
        if filt.shape[0] % 2 == 0:
            stag = 2
        else:
            stag = 1

        im_sz = im.shape
        if len(im.shape) == 1:
            im_sz = (1, im.shape[0])
        elif im.shape[1] == 1:
            im_sz = (im.shape[1], im.shape[0])
        print "im_sz"
        print im_sz
        #if len(im.shape) == 1 or im.shape[1] == 1:
        #    im = im.reshape(1, im.shape[0])

        if len(filt.shape) == 1:
            filt_sz = (1, filt.shape[0])
        #elif filt.shape[1] == 1:  # FIX for 1D: breaks other tests
        #    filt_sz = (filt.shape[1], filt.shape[0])
        else:
            filt_sz = filt.shape
        print "filt_sz"
        print filt_sz
        max_ht = ppu.maxPyrHt(im_sz, filt_sz)
        print "max_ht = %d" % (max_ht)
        if len(args) > 1:
            ht = args[1]
            if ht == 'auto':
                ht = max_ht
            elif(ht > max_ht):
                print "Error: cannot build pyramid higher than %d levels." % (max_ht)
        else:
            ht = max_ht
        ht = int(ht)

        for lev in range(ht):
            print "lev = %d" % (lev)
            im_sz = im.shape
            if len(im.shape) == 1:
                im_sz = (1, im.shape[0])
            elif im.shape[1] == 1:
                im_sz = (im.shape[1], im.shape[0])
                print "im_sz"
                print im_sz
            if len(im_sz) == 1 or im_sz[1] == 1:
                lolo = np.array( corrDn(im_sz[0], im_sz[1], im.T, filt_sz[0],
                                        filt_sz[1], filt, edges, 2, 1, stag-1, 
                                        0) )
                hihi = np.array( corrDn(im_sz[0], im_sz[1], im.T, filt_sz[0], 
                                        filt_sz[1], hfilt, edges, 2, 1, 1, 0) )
            elif im_sz[0] == 1:
                lolo = np.array( corrDn(im_sz[0], im_sz[1], im, filt_sz[0], 
                                        filt_sz[1], filt, edges, 1, 2, 0, 
                                        stag-1) )
                hihi = np.array( corrDn(im_sz[0], im_sz[1], im, filt_sz[0], 
                                        filt_sz[1], hfilt, edges, 1, 2, 0, 1) )
            else:
                lo = np.array( corrDn(im.shape[0], im.shape[1], im.T, 
                                      filt.shape[0], 1, filt, edges, 2, 1, 
                                      stag-1, 0) ).T
                #lo = lo.reshape(math.ceil(im.shape[0]/2.0), 
                #                math.ceil(im.shape[1]/stag), order='F')
                hi = np.array( corrDn(im.shape[0], im.shape[1], im.T, 
                                      hfilt.shape[0], 1, hfilt, edges, 2, 1, 1,
                                      0) ).T
                #hi = hi.reshape(math.floor(im.shape[0]/2.0), im.shape[1], 
                #                order='F')
                lolo = np.array( corrDn(lo.shape[0], lo.shape[1], lo.T, 1, 
                                        filt.shape[0], filt, edges, 1, 2, 0, 
                                        stag-1) ).T 
                #lolo = lolo.reshape(math.ceil(lo.shape[0]/float(stag)), 
                #                    math.ceil(lo.shape[1]/2.0), order='F')
                lohi = np.array( corrDn(hi.shape[0], hi.shape[1], hi.T, 1, 
                                        filt.shape[0], filt, edges, 1, 2, 0, 
                                        stag-1) ).T
                #lohi = lohi.reshape(hi.shape[0], math.ceil(hi.shape[1]/2.0), 
                #                    order='F')
                hilo = np.array( corrDn(lo.shape[0], lo.shape[1], lo.T, 1,
                                        hfilt.shape[0], hfilt, edges, 1, 2, 0, 
                                        1) ).T
                #hilo = hilo.reshape(lo.shape[0], math.floor(lo.shape[1]/2.0), 
                #                    order='F')
                hihi = np.array( corrDn(hi.shape[0], hi.shape[1], hi.T, 1, 
                                        hfilt.shape[0], hfilt, edges, 1, 2, 0, 
                                        1) ).T
                #hihi = hihi.reshape(hi.shape[0], math.floor(hi.shape[1]/2.0), 
                #                    order='F')
            if im_sz[0] == 1 or im_sz[1] == 1:
                self.pyr.append(hihi)
                self.pyrSize.append(hihi.shape)
            else:
                self.pyr.append(lohi)
                self.pyrSize.append(lohi.shape)
                self.pyr.append(hilo)
                self.pyrSize.append(hilo.shape)
                self.pyr.append(hihi)
                self.pyrSize.append(hihi.shape)
            im = lolo
        self.pyr.append(lolo)
        self.pyrSize.append(lolo.shape)

    # methods

    def wpyrHt(self):
        if ( len(self.pyrSize[0]) == 1 or self.pyrSize[0][0] == 1 or 
             self.pyrSize[0][1] == 1 ): 
            nbands = 1
        else:
            nbands = 3

        ht = (len(self.pyrSize)-1)/float(nbands)

        return ht


    def reconWpyr(self, *args):
        # Optional args
        if len(args) > 0:
            filt = args[0]
        else:
            filt = 'qmf9'
            
        if len(args) > 1:
            edges = args[1]
        else:
            edges = 'reflect1'

        if len(args) > 2:
            levs = args[2]
        else:
            levs = 'all'

        if len(args) > 3:
            bands = args[3]
        else:
            bands = 'all'

        #------------------------------------------------------

        print self.pyrSize
        maxLev = self.wpyrHt() + 1
        print "maxLev = %d" % maxLev
        if levs == 'all':
            levs = np.array(range(maxLev))
        else:
            tmpLevs = []
            for l in levs:
                tmpLevs.append((maxLev-1)-l)
            levs = np.array(tmpLevs)
            if (levs > maxLev).any():
                print "Error: level numbers must be in the range [0, %d]" % (maxLev)
        allLevs = np.array(range(maxLev))

        print "levs:"
        print levs
        
        if bands == "all":
            bands = np.array(range(3))
        else:
            bands = np.array(bands)
            if (bands < 0).any() or (bands > 2).any():
                print "Error: band numbers must be in the range [0,2]."
        
        if isinstance(filt, basestring):
            filt = ppu.namedFilter(filt)

        print "filt"
        print filt
        hfilt = ppu.modulateFlip(filt)
        print "hfilt"
        print hfilt

        # for odd-length filters, stagger the sampling lattices:
        if len(filt) % 2 == 0:
            stag = 2
        else:
            stag = 1
        print "stag = %d" % (stag)

        #if 0 in levs:
        #    res = self.pyr[len(self.pyr)-1]
        #else:
        #    res = np.zeros(self.pyr[len(self.pyr)-1].shape)
        #print res

        print "pyrSize[0]:"
        print self.pyrSize[0]
        print "pyrSize[3]:"
        print self.pyrSize[3]

        print 'len pyrSize = %d' % (len(self.pyr))

        idx = len(self.pyrSize)-1

        print "levs:"
        print levs
        print "bands:"
        print bands

        #for lev in levs:
        for lev in allLevs:
            print "starting levs loop lev = %d" % lev

            if lev == 0:
                if 0 in levs:
                    res = self.pyr[len(self.pyr)-1]
                else:
                    res = np.zeros(self.pyr[len(self.pyr)-1].shape)
                print res
            elif lev > 0:
                # compute size of result image: assumes critical sampling
                resIdx = len(self.pyrSize)-(3*(lev-1))-3
                res_sz = self.pyrSize[resIdx]
                print "resIdx = %d" % resIdx
                if res_sz[0] == 1:
                    res_sz[1] = sum(self.pyrSize[:,1])
                elif res_sz[1] == 1:
                    res_sz[0] = sum(self.pyrSize[:,0])
                else:
                #horizontal + vertical bands
                    res_sz = (self.pyrSize[resIdx][0]+self.pyrSize[resIdx-1][0],
                              self.pyrSize[resIdx][1]+self.pyrSize[resIdx-1][1])
                    lres_sz = np.array([self.pyrSize[resIdx][0], res_sz[1]])
                    hres_sz = np.array([self.pyrSize[resIdx-1][0], res_sz[1]])

                print 'pyrSizes'
                print self.pyrSize[resIdx]
                print self.pyrSize[resIdx+1]
                print self.pyrSize[resIdx-1]
                print "res_sz"
                print res_sz
                print "hres_sz"
                print hres_sz
                print "lres_sz"
                print lres_sz

                # FIX: how is this changed with subsets of levs?
                #if lev <= 1:
                #    print "lev = %d" % lev
                #    print "levs"
                #    print levs
                #    if lev in levs:
                #        print "idx = %d" % (idx)
                #        print self.pyrSize
                #        imageIn = self.band(idx)
                #    else:
                #        imageIn = np.zeros(self.band(idx).shape)
                #    print "input image"
                #    print imageIn
                #else:
                #    imageIn = res
                imageIn = res
                #fp = open('tmp.txt', 'a')
                #fp.write('%d ires\n' % lev)
                #fp.close()
                print "filt shape = %d %d\n" % (filt.shape[0], filt.shape[1])
                ires = upConv(imageIn.shape[1], 
                              imageIn.shape[0],
                              imageIn.T, filt.shape[1], filt.shape[0], 
                              filt, edges, 1, 2, 0, stag-1, lres_sz[0], 
                              lres_sz[1])
                ires = np.array(ires).T
                #ires = ires.reshape(lres_sz[1], lres_sz[0]).T
                print "%d ires" % (lev)
                print ires
                print ires.shape
                print "hfilt"
                print hfilt
                #fp = open('tmp.txt', 'a')
                #fp.write("%d res\n" % (lev))
                #fp.close()
                res = upConv(ires.shape[1], ires.shape[0], ires.T, 
                             filt.shape[0],
                             filt.shape[1], filt, edges, 2, 1, stag-1, 0, 
                             res_sz[0], res_sz[1]).T
                res = np.array(res)
                #res = res.reshape(res_sz[1], res_sz[0]).T
                print "%d res" % (lev)
                print res

                idx = resIdx - 1

                ### FIX: do we need stag here?! Check with even size filter
                #if 0 in bands:
                if 0 in bands and lev in levs:
                    print "0 band"
                    print "idx = %d" % idx
                    print "resIdx = %d" % resIdx
                    print "input band"
                    print self.band(idx)
                    #fp = open('tmp.txt', 'a')
                    #fp.write("ires 0 band\n")
                    #fp.close()
                    # broken for even filters
                    #ires = upConv(self.band(idx).shape[0], 
                    #              self.band(idx).shape[1],
                    #              self.band(idx).T, 
                    #              filt.shape[1], filt.shape[0], filt, 
                    #              edges, 1, 2, stag-1, 0, hres_sz[0], 
                    #              hres_sz[1])
                    # works with even filter
                    ires = upConv(self.band(idx).shape[0], 
                                  self.band(idx).shape[1],
                                  self.band(idx).T, 
                                  filt.shape[1], filt.shape[0], filt, 
                                  edges, 1, 2, 0, stag-1, hres_sz[0], 
                                  hres_sz[1])
                    ires = np.array(ires).T
                    #ires = ires.reshape(hres_sz[1], hres_sz[0]).T
                    print "ires"
                    print ires
                    print ires.shape

                    print "pre upconv res"
                    print res
                    #fp = open('tmp.txt', 'a')
                    #fp.write("res 0 band\n")
                    #fp.close()
                    print "pre res size"
                    print res.shape
                    res = upConv(ires.shape[0], ires.shape[1], ires.T, 
                                 hfilt.shape[1], hfilt.shape[0], hfilt, 
                                 edges, 2, 1, 1, 0, 
                                 res_sz[0], res_sz[1], res.T)
                    res = np.array(res).T
                    print "res size %d %d" % (res_sz[1], res_sz[0])
                    print "post res size"
                    print res.shape
                    print "post upconv res"
                    print res
                idx += 1
                #if 1 in bands:
                if 1 in bands and lev in levs:
                    print "1 band"
                    print "idx = %d" % idx
                    print "lres_sz"
                    print lres_sz
                    print lres_sz[0]
                    print lres_sz[1]
                    print "self.band(idx)"
                    print self.band(idx)
                    print self.band(idx).shape
                    print hfilt
                    #fp = open('tmp.txt', 'a')
                    #fp.write("ires 1 band\n")
                    #fp.close()
                    ires = upConv(self.band(idx).shape[0], 
                                  self.band(idx).shape[1], 
                                  self.band(idx).T, 
                                  hfilt.shape[0], hfilt.shape[1], hfilt, edges,
                                  1, 2, 0, 1, lres_sz[0], lres_sz[1])
                    ires = np.array(ires).T
                    #ires = ires.reshape(lres_sz[1], lres_sz[0]).T
                    print "ires"
                    print ires
                    print ires.shape
                    print filt.shape
                    print "pre res"
                    print res
                    print filt
                    print edges
                    print "stag = %d" % stag
                    # FIX: stag is not correct here. does this need to flip
                    #      because python is 0 based?
                    #fp = open('tmp.txt', 'a')
                    #fp.write("res 1 band\n")
                    #fp.close()
                    # works with odd filters
                    #res = upConv(ires.shape[0], ires.shape[1], ires.T, 
                    #             filt.shape[0], filt.shape[1], filt, 
                    #             edges, 2, 1, 0, 0, 
                    #             res_sz[0], res_sz[1], res.T)
                    # works with even filters
                    #res = upConv(ires.shape[0], ires.shape[1], ires.T, 
                    #             filt.shape[0], filt.shape[1], filt, 
                    #             edges, 2, 1, 1, 0, 
                    #             res_sz[0], res_sz[1], res.T)
                    res = upConv(ires.shape[0], ires.shape[1], ires.T, 
                                 filt.shape[0], filt.shape[1], filt, 
                                 edges, 2, 1, stag-1, 0, 
                                 res_sz[0], res_sz[1], res.T)
                    res = np.array(res).T
                    #res = res.reshape(res_sz[1], res_sz[0]).T
                    print "res"
                    print res
                idx += 1
                #if 2 in bands:
                if 2 in bands and lev in levs:
                    print "2 band"
                    print "idx = %d" % idx
                    print "input image"
                    print self.band(idx)
                    #fp = open('tmp.txt', 'a')
                    #fp.write("ires 2 band\n")
                    #fp.close()
                    ires = upConv(self.band(idx).shape[0],
                                  self.band(idx).shape[1],
                                  self.band(idx).T,
                                  hfilt.shape[0], hfilt.shape[1], hfilt, 
                                  edges, 1, 2, 0, 1, hres_sz[0], hres_sz[1])
                    ires = np.array(ires).T
                    #ires = ires.reshape(hres_sz[1], hres_sz[0]).T
                    print "ires"
                    print ires
                    print "pre res"
                    print res
                    #fp = open('tmp.txt', 'a')
                    #fp.write("res 2 band\n")
                    #fp.close()
                    res = upConv(ires.shape[1], ires.shape[0], ires.T, 
                                 hfilt.shape[1], hfilt.shape[0], hfilt,
                                 edges, 2, 1, 1, 0, res_sz[0], res_sz[1], res.T)
                    res = np.array(res).T
                    print "res"
                    print res
                idx += 1
                # need to jump back n bands in the idx each loop
                idx -= 2*len(bands)
        return res

class Wpyr(Lpyr):
    filt = ''
    edges = ''
    height = ''

    #constructor
    def __init__(self, *args):    # (image, height, order, twidth)
        self.pyr = []
        self.pyrSize = []
        self.pyrType = 'wavelet'

        if len(args) > 0:
            im = args[0]
        else:
            print "First argument (image) is required."
            return

        #------------------------------------------------
        # defaults:

        if len(args) > 2:
            filt = args[2]
        else:
            filt = "qmf9"
        if isinstance(filt, basestring):
            filt = ppu.namedFilter(filt)

        if len(filt.shape) != 1 and filt.shape[0] != 1 and filt.shape[1] != 1:
            print "Error: filter should be 1D (i.e., a vector)";
            return
        hfilt = ppu.modulateFlip(filt).T

        if len(args) > 3:
            edges = args[3]
        else:
            edges = "reflect1"

        # Stagger sampling if filter is odd-length:
        if filt.shape[0] % 2 == 0:
            stag = 2
        else:
            stag = 1

        #im_sz = im.shape
        #if len(im.shape) == 1:
        #    im_sz = (1, im.shape[0])
        #elif im.shape[1] == 1:
        #    im_sz = (im.shape[1], im.shape[0])
        #print "im_sz"
        #print im_sz
        if len(im.shape) == 1 or im.shape[1] == 1:
            im = im.reshape(1, im.shape[0])

        #if len(filt.shape) == 1:
        #    filt_sz = (1, filt.shape[0])
        #else:
        #    filt_sz = filt.shape
        #print "filt_sz"
        #print filt_sz
        # if 1D filter, match to image dimensions
        if len(filt.shape) == 1 or filt.shape[1] == 1:
            if im.shape[0] == 1:
                filt = filt.reshape(1, filt.shape[0])
            elif im.shape[1] == 1:
                filt = filt.reshape(filt.shape[0], 1)
        elif filt.shape[0] == 1:
            if im.shape[0] == 1:
                filt = filt.reshape(1, filt.shape[1])
            elif im.shape[1] == 1:
                filt = filt.reshape(filt.shape[1], 1)

        #max_ht = ppu.maxPyrHt(im_sz, filt_sz)
        max_ht = ppu.maxPyrHt(im.shape, filt.shape)
        #print "max_ht = %d" % (max_ht)
        if len(args) > 1:
            ht = args[1]
            if ht == 'auto':
                ht = max_ht
            elif(ht > max_ht):
                print "Error: cannot build pyramid higher than %d levels." % (max_ht)
        else:
            ht = max_ht
        ht = int(ht)
        self.height = ht + 1  # used with showPyr() method

        for lev in range(ht):
            #print "lev = %d" % (lev)
            #im_sz = im.shape
            #if len(im.shape) == 1:
            #    im_sz = (1, im.shape[0])
            #elif im.shape[1] == 1:
            #    im_sz = (im.shape[1], im.shape[0])
            #    print "im_sz"
            #    print im_sz
            if len(im.shape) == 1 or im.shape[1] == 1:
                im = im.reshape(1, im.shape[0])
            if len(im.shape) == 1 or im.shape[1] == 1:
                lolo = np.array( corrDn(im.shape[0], im.shape[1], im.T, 
                                        filt.shape[0], filt.shape[1], filt, 
                                        edges, 2, 1, stag-1, 0) ).T
                hihi = np.array( corrDn(im.shape[0], im.shape[1], im.T, 
                                        hfilt.shape[1], hfilt.shape[0], hfilt, 
                                        edges, 2, 1, 1, 0) ).T
            #elif im_sz[0] == 1:
            elif im.shape[0] == 1:
                lolo = np.array( corrDn(im.shape[0], im.shape[1], im, 
                                        filt.shape[0], filt.shape[1], filt, 
                                        edges, 1, 2, 0, stag-1) ).T
                hihi = np.array( corrDn(im.shape[0], im.shape[1], im, 
                                        hfilt.shape[1], hfilt.shape[0], hfilt, 
                                        edges, 1, 2, 0, 1) ).T
            else:
                lo = np.array( corrDn(im.shape[0], im.shape[1], im.T, 
                                      filt.shape[0], 1, filt, edges, 2, 1, 
                                      stag-1, 0) ).T
                #lo = lo.reshape(math.ceil(im.shape[0]/2.0), 
                #                math.ceil(im.shape[1]/stag), order='F')
                hi = np.array( corrDn(im.shape[0], im.shape[1], im.T, 
                                      hfilt.shape[0], 1, hfilt, edges, 2, 1, 1,
                                      0) ).T
                #hi = hi.reshape(math.floor(im.shape[0]/2.0), im.shape[1], 
                #                order='F')
                lolo = np.array( corrDn(lo.shape[0], lo.shape[1], lo.T, 1, 
                                        filt.shape[0], filt, edges, 1, 2, 0, 
                                        stag-1) ).T 
                #lolo = lolo.reshape(math.ceil(lo.shape[0]/float(stag)), 
                #                    math.ceil(lo.shape[1]/2.0), order='F')
                lohi = np.array( corrDn(hi.shape[0], hi.shape[1], hi.T, 1, 
                                        filt.shape[0], filt, edges, 1, 2, 0, 
                                        stag-1) ).T
                #lohi = lohi.reshape(hi.shape[0], math.ceil(hi.shape[1]/2.0), 
                #                    order='F')
                hilo = np.array( corrDn(lo.shape[0], lo.shape[1], lo.T, 1,
                                        hfilt.shape[0], hfilt, edges, 1, 2, 0, 
                                        1) ).T
                #hilo = hilo.reshape(lo.shape[0], math.floor(lo.shape[1]/2.0), 
                #                    order='F')
                hihi = np.array( corrDn(hi.shape[0], hi.shape[1], hi.T, 1, 
                                        hfilt.shape[0], hfilt, edges, 1, 2, 0, 
                                        1) ).T
                #hihi = hihi.reshape(hi.shape[0], math.floor(hi.shape[1]/2.0), 
                #                    order='F')
            #if im_sz[0] == 1 or im_sz[1] == 1:
            if im.shape[0] == 1 or im.shape[1] == 1:
                self.pyr.append(hihi)
                self.pyrSize.append(hihi.shape)
            else:
                self.pyr.append(lohi)
                self.pyrSize.append(lohi.shape)
                self.pyr.append(hilo)
                self.pyrSize.append(hilo.shape)
                self.pyr.append(hihi)
                self.pyrSize.append(hihi.shape)
            im = lolo
        self.pyr.append(lolo)
        self.pyrSize.append(lolo.shape)

    # methods

    def wpyrHt(self):
        if ( len(self.pyrSize[0]) == 1 or self.pyrSize[0][0] == 1 or 
             self.pyrSize[0][1] == 1 ): 
            nbands = 1
        else:
            nbands = 3

        ht = (len(self.pyrSize)-1)/float(nbands)

        return ht


    def reconWpyr_old(self, *args):
        # Optional args
        if len(args) > 0:
            filt = args[0]
        else:
            filt = 'qmf9'
            
        if len(args) > 1:
            edges = args[1]
        else:
            edges = 'reflect1'

        if len(args) > 2:
            levs = args[2]
        else:
            levs = 'all'

        if len(args) > 3:
            bands = args[3]
        else:
            bands = 'all'

        #------------------------------------------------------

        print self.pyrSize
        maxLev = int(self.wpyrHt() + 1)
        print "maxLev = %d" % maxLev
        if levs == 'all':
            levs = np.array(range(maxLev))
        else:
            tmpLevs = []
            for l in levs:
                tmpLevs.append((maxLev-1)-l)
            levs = np.array(tmpLevs)
            if (levs > maxLev).any():
                print "Error: level numbers must be in the range [0, %d]" % (maxLev)
        allLevs = np.array(range(maxLev))

        print "levs:"
        print levs
        
        if bands == "all":
            if ( len(self.band(0)) == 1 or self.band(0).shape[0] == 1 or 
                 self.band(0).shape[1] == 1 ):
                bands = np.array([0]);
            else:
                bands = np.array(range(3))
        else:
            bands = np.array(bands)
            if (bands < 0).any() or (bands > 2).any():
                print "Error: band numbers must be in the range [0,2]."
        
        if isinstance(filt, basestring):
            filt = ppu.namedFilter(filt)

        print "filt"
        print filt
        hfilt = ppu.modulateFlip(filt)
        print "hfilt"
        print hfilt

        # for odd-length filters, stagger the sampling lattices:
        if len(filt) % 2 == 0:
            stag = 2
        else:
            stag = 1
        print "stag = %d" % (stag)

        #if 0 in levs:
        #    res = self.pyr[len(self.pyr)-1]
        #else:
        #    res = np.zeros(self.pyr[len(self.pyr)-1].shape)
        #print res

        print "pyrSize[0]:"
        print self.pyrSize[0]
        print "pyrSize[3]:"
        print self.pyrSize[3]

        print 'len pyrSize = %d' % (len(self.pyr))

        idx = len(self.pyrSize)-1
        print 'idx = %d' % (idx)

        print "levs:"
        print levs
        print "bands:"
        print bands

        #for lev in levs:
        for lev in allLevs:
            print "starting levs loop lev = %d" % lev

            if lev == 0:
                if 0 in levs:
                    res = self.pyr[len(self.pyr)-1]
                else:
                    res = np.zeros(self.pyr[len(self.pyr)-1].shape)
                print res
            elif lev > 0:
                # compute size of result image: assumes critical sampling
                if ( len(self.pyrSize[0]) == 1 or self.pyrSize[0][0] == 1 or
                     self.pyrSize[0][1] == 1 ):
                    resIdx = len(self.pyrSize)-2
                else:
                    resIdx = len(self.pyrSize)-(3*(lev-1))-3
                print "resIdx = %d" % resIdx
                res_sz = self.pyrSize[resIdx]
                print 'pre res_sz'
                print res_sz
                if res_sz[0] == 1:
                    #res_sz[1] = sum(self.pyrSize[:,1])
                    res_sz = (res_sz[0], sum([x[1] for x in self.pyrSize]))
                elif res_sz[1] == 1:
                    #res_sz[0] = sum(self.pyrSize[:,0])
                    res_sz = (res_sz[0], sum([x[0] for x in self.pyrSize]))
                else:
                    #horizontal + vertical bands
                    res_sz = (self.pyrSize[resIdx][0]+self.pyrSize[resIdx-1][0],
                              self.pyrSize[resIdx][1]+self.pyrSize[resIdx-1][1])
                    lres_sz = np.array([self.pyrSize[resIdx][0], res_sz[1]])
                    hres_sz = np.array([self.pyrSize[resIdx-1][0], res_sz[1]])
                print 'post res_sz'
                print res_sz

                print 'pyrSizes'
                print self.pyrSize[resIdx]
                #print self.pyrSize[resIdx+1]
                #print self.pyrSize[resIdx-1]
                print "res_sz"
                print res_sz
                #print "hres_sz"
                #print hres_sz
                #print "lres_sz"
                #print lres_sz

                # FIX: how is this changed with subsets of levs?
                #if lev <= 1:
                #    print "lev = %d" % lev
                #    print "levs"
                #    print levs
                #    if lev in levs:
                #        print "idx = %d" % (idx)
                #        print self.pyrSize
                #        imageIn = self.band(idx)
                #    else:
                #        imageIn = np.zeros(self.band(idx).shape)
                #    print "input image"
                #    print imageIn
                #else:
                #    imageIn = res
                imageIn = res
                #fp = open('tmp.txt', 'a')
                #fp.write('%d ires\n' % lev)
                #fp.close()
                if res_sz[0] == 1:
                    #res = upConv(nres, filt', edges, [1 2], [1 stag], res_sz);
                    print 'flag 1'
                    res = upConv(imageIn.shape[0], imageIn.shape[1], imageIn, 
                                 filt.shape[1], filt.shape[0], filt, edges,
                                 1, 2, 0, stag-1, res_sz[0], res_sz[1])
                    res = np.array(res).T
                elif res_sz[1] == 1:
                    #res = upConv(nres, filt, edges, [2 1], [stag 1], res_sz);
                    print 'flag 2'
                    res = upConv(imageIn.shape[0], imageIn.shape[1], imageIn, 
                                 filt.shape[0], filt.shape[1], filt, edges,
                                 2, 1, stag-1, 1, res_sz[0], res_sz[1])
                    res = np.array(res).T
                else:
                    print "filt shape = %d %d\n" % (filt.shape[0], 
                                                    filt.shape[1])
                    ires = upConv(imageIn.shape[1], 
                                  imageIn.shape[0],
                                  imageIn.T, filt.shape[1], filt.shape[0], 
                                  filt, edges, 1, 2, 0, stag-1, lres_sz[0], 
                                  lres_sz[1])
                    ires = np.array(ires).T
                    #ires = ires.reshape(lres_sz[1], lres_sz[0]).T
                    print "%d ires" % (lev)
                    print ires
                    print ires.shape
                    print "hfilt"
                    print hfilt
                    #fp = open('tmp.txt', 'a')
                    #fp.write("%d res\n" % (lev))
                    #fp.close()
                    res = upConv(ires.shape[1], ires.shape[0], ires.T, 
                                 filt.shape[0],
                                 filt.shape[1], filt, edges, 2, 1, stag-1, 0, 
                                 res_sz[0], res_sz[1]).T
                    res = np.array(res)
                    #res = res.reshape(res_sz[1], res_sz[0]).T
                    print "%d res" % (lev)
                    print res

                print 'self.pyrSize'
                print self.pyrSize[0]
                if ( len(self.pyrSize[0]) == 1 or self.pyrSize[0][0] == 1 or
                     self.pyrSize[0][1] == 1 ):
                    print 'idx flag 1'
                    idx = idx
                else:
                    print 'idx flag 2'
                    idx = resIdx - 1
                print '1### idx = %d' % (idx)
                if res_sz[0] ==1 and lev in levs:
                    #upConv(pyrBand(pyr,ind,1), hfilt', edges, [1 2], [1 2], res_sz, res);
                    print '1d band'
                    print self.band(idx)
                    res = upConv(self.band(idx).shape[0], 
                                 self.band(idx).shape[1],
                                 self.band(idx), hfilt.shape[0], hfilt.shape[1],
                                 hfilt, edges, 1, 2, 0, 1, res_sz[0], res_sz[1],
                                 res)
                    res = np.array(res).T
                    idx -= 1
                    print '2### idx = %d' % (idx)
                elif res_sz[1] == 1:
                    #upConv(pyrBand(pyr,ind,1), hfilt, edges, [2 1], [2 1], res_sz, res);
                    print '1d band'
                    print self.band(idx)
                    res = upConv(self.band(idx).shape[0], 
                                 self.band(idx).shape[1],
                                 self.band(idx), hfilt.shape[1], hfilt.shape[0],
                                 hfilt, edges, 2, 1, 1, 0, res_sz[0], res_sz[1],
                                 res)
                    res = np.array(res).T
                    idx -= 1
                    print '3### idx = %d' % (idx)
                else:
                    #if 0 in bands:
                    if 0 in bands and lev in levs:
                        print "0 band"
                        print "idx = %d" % idx
                        print "resIdx = %d" % resIdx
                        print "input band"
                        print self.band(idx)
                        #fp = open('tmp.txt', 'a')
                        #fp.write("ires 0 band\n")
                        #fp.close()
                        ires = upConv(self.band(idx).shape[0], 
                                      self.band(idx).shape[1],
                                      self.band(idx).T, 
                                      filt.shape[1], filt.shape[0], filt, 
                                      edges, 1, 2, 0, stag-1, hres_sz[0], 
                                      hres_sz[1])
                        ires = np.array(ires).T
                        #ires = ires.reshape(hres_sz[1], hres_sz[0]).T
                        print "ires"
                        print ires
                        print ires.shape

                        print "pre upconv res"
                        print res
                        #fp = open('tmp.txt', 'a')
                        #fp.write("res 0 band\n")
                        #fp.close()
                        print "pre res size"
                        print res.shape
                        res = upConv(ires.shape[0], ires.shape[1], ires.T, 
                                     hfilt.shape[1], hfilt.shape[0], hfilt, 
                                     edges, 2, 1, 1, 0, 
                                     res_sz[0], res_sz[1], res.T)
                        res = np.array(res).T
                        print "res size %d %d" % (res_sz[1], res_sz[0])
                        print "post res size"
                        print res.shape
                        print "post upconv res"
                        print res
                    idx += 1
                    #if 1 in bands:
                    if 1 in bands and lev in levs:
                        print "1 band"
                        print "idx = %d" % idx
                        print "lres_sz"
                        print lres_sz
                        print lres_sz[0]
                        print lres_sz[1]
                        print "self.band(idx)"
                        print self.band(idx)
                        print self.band(idx).shape
                        print hfilt
                        #fp = open('tmp.txt', 'a')
                        #fp.write("ires 1 band\n")
                        #fp.close()
                        ires = upConv(self.band(idx).shape[0], 
                                      self.band(idx).shape[1], 
                                      self.band(idx).T, 
                                      hfilt.shape[0], hfilt.shape[1], hfilt, 
                                      edges, 1, 2, 0, 1, lres_sz[0], lres_sz[1])
                        ires = np.array(ires).T
                        #ires = ires.reshape(lres_sz[1], lres_sz[0]).T
                        print "ires"
                        print ires
                        print ires.shape
                        print filt.shape
                        print "pre res"
                        print res
                        print filt
                        print edges
                        print "stag = %d" % stag
                        #fp = open('tmp.txt', 'a')
                        #fp.write("res 1 band\n")
                        #fp.close()
                        res = upConv(ires.shape[0], ires.shape[1], ires.T, 
                                     filt.shape[0], filt.shape[1], filt, 
                                     edges, 2, 1, stag-1, 0, 
                                     res_sz[0], res_sz[1], res.T)
                        res = np.array(res).T
                        print "res"
                        print res
                    idx += 1
                    if 2 in bands and lev in levs:
                        print "2 band"
                        print "idx = %d" % idx
                        print "input image"
                        print self.band(idx)
                        #fp = open('tmp.txt', 'a')
                        #fp.write("ires 2 band\n")
                        #fp.close()
                        ires = upConv(self.band(idx).shape[0],
                                      self.band(idx).shape[1],
                                      self.band(idx).T,
                                      hfilt.shape[0], hfilt.shape[1], hfilt, 
                                      edges, 1, 2, 0, 1, hres_sz[0], hres_sz[1])
                        ires = np.array(ires).T
                        #ires = ires.reshape(hres_sz[1], hres_sz[0]).T
                        print "ires"
                        print ires
                        print "pre res"
                        print res
                        #fp = open('tmp.txt', 'a')
                        #fp.write("res 2 band\n")
                        #fp.close()
                        res = upConv(ires.shape[1], ires.shape[0], ires.T, 
                                     hfilt.shape[1], hfilt.shape[0], hfilt,
                                     edges, 2, 1, 1, 0, res_sz[0], res_sz[1], 
                                     res.T)
                        res = np.array(res).T
                        print "res"
                        print res
                    idx += 1
                # need to jump back n bands in the idx each loop
                print 'self.pyrSize[0]'
                print self.pyrSize[0]
                if ( len(self.pyrSize[0]) == 1 or self.pyrSize[0][0] == 1 or
                     self.pyrSize[0][1] == 1 ):
                    #idx -= 1
                    idx = idx
                else:
                    idx -= 2*len(bands)
                    print '4### idx = %d' % (idx)
        return res

    def reconWpyr(self, *args):
        # Optional args
        if len(args) > 0:
            filt = args[0]
        else:
            filt = 'qmf9'
            
        if len(args) > 1:
            edges = args[1]
        else:
            edges = 'reflect1'

        if len(args) > 2:
            levs = args[2]
        else:
            levs = 'all'

        if len(args) > 3:
            bands = args[3]
        else:
            bands = 'all'

        #------------------------------------------------------

        maxLev = int(self.wpyrHt() + 1)

        if levs == 'all':
            levs = np.array(range(maxLev))
        else:
            tmpLevs = []
            for l in levs:
                tmpLevs.append((maxLev-1)-l)
            levs = np.array(tmpLevs)
            if (levs > maxLev).any():
                print "Error: level numbers must be in the range [0, %d]" % (maxLev)
        allLevs = np.array(range(maxLev))

        if bands == "all":
            if ( len(self.band(0)) == 1 or self.band(0).shape[0] == 1 or 
                 self.band(0).shape[1] == 1 ):
                bands = np.array([0]);
            else:
                bands = np.array(range(3))
        else:
            bands = np.array(bands)
            if (bands < 0).any() or (bands > 2).any():
                print "Error: band numbers must be in the range [0,2]."
        
        if isinstance(filt, basestring):
            filt = ppu.namedFilter(filt)

        hfilt = ppu.modulateFlip(filt)

        # for odd-length filters, stagger the sampling lattices:
        if len(filt) % 2 == 0:
            stag = 2
        else:
            stag = 1

        idx = len(self.pyrSize)-1
        #print 'idx = %d' % (idx)

        #for lev in levs:
        for lev in allLevs:
            #print "starting levs loop lev = %d" % lev

            if lev == 0:
                if 0 in levs:
                    res = self.pyr[len(self.pyr)-1]
                else:
                    res = np.zeros(self.pyr[len(self.pyr)-1].shape)
                #print res
                #print 'lev 0 res'
                #print res
            elif lev > 0:
                # compute size of result image: assumes critical sampling
                #if ( len(self.pyrSize[0]) == 1 or self.pyrSize[0][0] == 1 or
                #     self.pyrSize[0][1] == 1 ):
                #    resIdx = len(self.pyrSize)-lev-2
                #else:
                #    resIdx = len(self.pyrSize)-(3*(lev-1))-3
                #    #res_sz = self.pyrSize[resIdx]
                #print "resIdx = %d" % resIdx
                #res_sz = self.pyrSize[resIdx]
                #print 'res_sz'
                #print res_sz
                #if res_sz[0] == 1:
                #    #res_sz = (res_sz[0], sum([x[1] for x in self.pyrSize]))
                #    if lev == 1:
                #        res_sz = res_sz
                #    else:
                #        res_sz = (1, res_sz[1]*2)
                #elif res_sz[1] == 1:
                #    #res_sz = (res_sz[0], sum([x[0] for x in self.pyrSize]))
                #    if lev == 1:
                #        res_sz = res_sz
                #    else:
                #        res_sz = (res_sz[1]*2, 1)
                #else:
                #    #horizontal + vertical bands
                #    res_sz = (self.pyrSize[resIdx][0]+self.pyrSize[resIdx-1][0],
                #self.pyrSize[resIdx][1]+self.pyrSize[resIdx-1][1])
                #    lres_sz = np.array([self.pyrSize[resIdx][0], res_sz[1]])
                #    hres_sz = np.array([self.pyrSize[resIdx-1][0], res_sz[1]])
                #print 'post res_sz'
                #print res_sz
                if ( len(self.pyrSize[0]) == 1 or self.pyrSize[0][0] == 1 or
                     self.pyrSize[0][1] == 1 ):
                    resIdx = len(self.pyrSize)-lev-2
                    #print "resIdx = %d" % resIdx
                    #res_sz = self.pyrSize[resIdx]
                    #print 'lev = %d' % (lev)
                    #print 'allLevs'
                    #print allLevs
                    if self.pyrSize[0][0] == 1:
                        #res_sz = (res_sz[0], sum([x[1] for x in self.pyrSize]))
                        if lev == allLevs[-1]:
                            #print 'lev flag 1'
                            res_sz = (1, res_sz[1]*2)
                        else:
                            #print 'lev flag 2'
                            res_sz = self.pyrSize[resIdx]
                    elif self.pyrSize[0][1] == 1:
                        #res_sz = (res_sz[0], sum([x[0] for x in self.pyrSize]))
                        if lev == allLevs[-1]:
                            #print 'lev flag 1'
                            res_sz = (res_sz[1]*2, 1)
                        else:
                            #print 'lev flag 2'
                            res_sz = self.pyrSize[resIdx]
                else:
                    resIdx = len(self.pyrSize)-(3*(lev-1))-3
                    #print "resIdx = %d" % resIdx
                    #horizontal + vertical bands
                    res_sz = (self.pyrSize[resIdx][0]+self.pyrSize[resIdx-1][0],
                              self.pyrSize[resIdx][1]+self.pyrSize[resIdx-1][1])
                    lres_sz = np.array([self.pyrSize[resIdx][0], res_sz[1]])
                    hres_sz = np.array([self.pyrSize[resIdx-1][0], res_sz[1]])
                #print 'post res_sz'
                #print res_sz



                imageIn = res
                if res_sz[0] == 1:
                    #print 'imagein'
                    #print imageIn
                    res = upConv(imageIn.shape[0], imageIn.shape[1], imageIn, 
                                 filt.shape[1], filt.shape[0], filt, edges,
                                 1, 2, 0, stag-1, res_sz[0], res_sz[1])
                    res = np.array(res).T
                    #print 'lev %d res' % (lev)
                    #print res
                elif res_sz[1] == 1:
                    #print 'imagein'
                    #print imageIn
                    res = upConv(imageIn.shape[0], imageIn.shape[1], imageIn, 
                                 filt.shape[0], filt.shape[1], filt, edges,
                                 2, 1, stag-1, 1, res_sz[0], res_sz[1])
                    res = np.array(res).T
                    #print 'lev %d res' % (lev)
                    #print res
                else:
                    ires = upConv(imageIn.shape[1], 
                                  imageIn.shape[0],
                                  imageIn.T, filt.shape[1], filt.shape[0], 
                                  filt, edges, 1, 2, 0, stag-1, lres_sz[0], 
                                  lres_sz[1])
                    ires = np.array(ires).T
                    res = upConv(ires.shape[1], ires.shape[0], ires.T, 
                                 filt.shape[0],
                                 filt.shape[1], filt, edges, 2, 1, stag-1, 0, 
                                 res_sz[0], res_sz[1]).T
                    res = np.array(res)

                if ( len(self.pyrSize[0]) == 1 or self.pyrSize[0][0] == 1 or
                     self.pyrSize[0][1] == 1 ):
                    idx = resIdx + 1
                else:
                    idx = resIdx - 1

                if res_sz[0] ==1 and lev in levs:
                    #print 'self.band(idx)'
                    #print self.band(idx)
                    res = upConv(self.band(idx).shape[0], 
                                 self.band(idx).shape[1],
                                 self.band(idx), hfilt.shape[0], hfilt.shape[1],
                                 hfilt, edges, 1, 2, 0, 1, res_sz[0], res_sz[1],
                                 res)
                    res = np.array(res)
                    idx -= 1
                    #print 'lev %d band res' % (lev)
                    #print res
                elif res_sz[1] == 1:
                    #print 'self.band(idx)'
                    #print self.band(idx)
                    res = upConv(self.band(idx).shape[0], 
                                 self.band(idx).shape[1],
                                 self.band(idx), hfilt.shape[1], hfilt.shape[0],
                                 hfilt, edges, 2, 1, 1, 0, res_sz[0], res_sz[1],
                                 res)
                    res = np.array(res)
                    idx -= 1
                    #print 'lev %d band res' % (lev)
                    #print res
                else:
                    if 0 in bands and lev in levs:
                        ires = upConv(self.band(idx).shape[0], 
                                      self.band(idx).shape[1],
                                      self.band(idx).T, 
                                      filt.shape[1], filt.shape[0], filt, 
                                      edges, 1, 2, 0, stag-1, hres_sz[0], 
                                      hres_sz[1])
                        ires = np.array(ires).T

                        res = upConv(ires.shape[0], ires.shape[1], ires.T, 
                                     hfilt.shape[1], hfilt.shape[0], hfilt, 
                                     edges, 2, 1, 1, 0, 
                                     res_sz[0], res_sz[1], res.T)
                        res = np.array(res).T
                    idx += 1
                    if 1 in bands and lev in levs:
                        ires = upConv(self.band(idx).shape[0], 
                                      self.band(idx).shape[1], 
                                      self.band(idx).T, 
                                      hfilt.shape[0], hfilt.shape[1], hfilt, 
                                      edges, 1, 2, 0, 1, lres_sz[0], lres_sz[1])
                        ires = np.array(ires).T

                        res = upConv(ires.shape[0], ires.shape[1], ires.T, 
                                     filt.shape[0], filt.shape[1], filt, 
                                     edges, 2, 1, stag-1, 0, 
                                     res_sz[0], res_sz[1], res.T)
                        res = np.array(res).T
                    idx += 1
                    if 2 in bands and lev in levs:
                        ires = upConv(self.band(idx).shape[0],
                                      self.band(idx).shape[1],
                                      self.band(idx).T,
                                      hfilt.shape[0], hfilt.shape[1], hfilt, 
                                      edges, 1, 2, 0, 1, hres_sz[0], hres_sz[1])
                        ires = np.array(ires).T

                        res = upConv(ires.shape[1], ires.shape[0], ires.T, 
                                     hfilt.shape[1], hfilt.shape[0], hfilt,
                                     edges, 2, 1, 1, 0, res_sz[0], res_sz[1], 
                                     res.T)
                        res = np.array(res).T
                    idx += 1
                # need to jump back n bands in the idx each loop
                if ( len(self.pyrSize[0]) == 1 or self.pyrSize[0][0] == 1 or
                     self.pyrSize[0][1] == 1 ):
                    idx = idx
                else:
                    idx -= 2*len(bands)
        return res

    def set_old(self, *args):
        if len(args) != 3:
            print 'Error: three input parameters required:'
            print '  set(band, location, value)'
            print '  where band and value are integer and location is a tuple'
        self.pyr[args[0]][args[1][0]][args[1][1]] = args[2] 

    def set(self, *args):
        if len(args) != 3:
            print 'Error: three input parameters required:'
            print '  set(band, location, value)'
            print '  where band and value are integer and location is a tuple'
        if isinstance(args[1], (int, long)):
            self.pyr[args[0]][0][args[1]] = args[2]
        elif isinstance(args[1], tuple):
            self.pyr[args[0]][args[1][0]][args[1][1]] = args[2] 
        else:
            print 'Error: location parameter must be int or tuple!'
            return
            

    def set1D(self, *args):
        if len(args) != 3:
            print 'Error: three input parameters required:'
            print '  set(band, location, value)'
            print '  where band and value are integer and location is a tuple'
        print '%d %d %d' % (args[0], args[1], args[2])
        print self.pyr[args[0]][0][1]
        #self.pyr[args[0]][args[1]] = args[2] 

    def pyrLow(self):
        return np.array(self.band(len(self.pyrSize)-1))

