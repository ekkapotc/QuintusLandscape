from matplotlib.tri.triangulation import Triangulation
import numpy as np
import pandas as pd
import matplotlib
from matplotlib import tri as tri
from matplotlib import pyplot as plt
from scipy.interpolate import griddata
from scipy.stats import gaussian_kde

def scatter():

    #read in data from the csv file
    data = pd.read_csv('data/raw_data.csv')

    H = data['H']
    V = data['V']
    I = data['Intensity']

    #find min and max intensity
    minI = I.min()
    maxI = I.max()
    
    print('Min Intensity : ',minI)
    print('Max Intensity : ',maxI)

    #create a scatter plot with the 'Spectial_r' color map where red means large and blue means small
    #plt.scatter(H, V, c=I, cmap='Spectral_r', marker='x', s=15)

    #create a scatter plot with a dicrete color map with 4 colors
    plt.scatter(H, V, c=I, cmap=plt.cm.get_cmap('Spectral_r',4), marker='x', s=15)

    #set up a color bar
    cbar = plt.colorbar(orientation='vertical',extend='both')
    cbar.set_label('Light Intensity')

    #set up the title and the x- and y-axis
    plt.title('Vertical Scanning')
    plt.xlabel('Horizontal Degrees')
    plt.ylabel('Vertical Degrees')
    
    #set color limits
    plt.clim(minI,maxI)

    #display the plot
    plt.show()

def grid(x, y, z, resX=100, resY=100):

    xi = np.linspace(min(x), max(x), resX)
    yi = np.linspace(min(y), max(y), resY)
    X, Y = np.meshgrid(xi, yi)
    Z =  griddata((x, y) , z ,  (xi[None,:], yi[:,None]) ,method='cubic'   )
    
    return X, Y, Z

def contour():
    #read in data from the csv file
    data = pd.read_csv('data/raw_data.csv')

    H = data['H']
    V = data['V']
    I = data['Intensity']

    #find min and max intensity
    minI = I.min()
    maxI = I.max()

    H,V,I = grid(H,V,I)

    fig, ax = plt.subplots(nrows=2, ncols=2,sharex=True, sharey=True)
    plt.subplots_adjust(hspace=0.3)

    for i in range(2):
        for j in range(2):
            
            levels = 15;

            #sc = ax[i,j].scatter(H, V, c=I, cmap='Spectral_r', marker='x', s=15)
            cs = ax[i,j].contour(H,V,I, levels=levels, linewidths=0.4, linestyles='dashed', colors='k')
            #plt.clabel(cs, inline=1, fontsize=5)
            csf = ax[i,j].contourf(H,V,I,levels=levels, cmap='Spectral_r',vmin=minI,vmax=maxI)
            ax[i,j].set_title('Light ID: {0}'.format(i*2+j),fontsize=10)
            fig.colorbar(csf,ax=ax[i,j],shrink=0.60)
        
    #set up the common color bar
    #fig.colorbar(csf, ax=ax,shrink=0.70,label='Light Intensity')

    #set up the title and the x- and y-axis
    fig.supxlabel('Horizontal Degrees')
    fig.supylabel('Vertical Degrees')
    fig.suptitle('Vertical Scanning')

    #display the plot
    plt.show()

def tricontour():

    #read in data from the csv file
    data = pd.read_csv('data/raw_data.csv')

    H = data['H'].values
    V = data['V'].values
    I = data['Intensity'].values

    #find min and max intensity
    minI = I.min()
    maxI = I.max()

    fig, ax = plt.subplots(nrows=2, ncols=2,sharex=True, sharey=True)
    plt.subplots_adjust(hspace=0.3)

    for i in range(2):
        for j in range(2):

            triang = Triangulation(H,V)
            triang.set_mask(np.hypot(H[triang.triangles].mean(axis=1),
                         V[triang.triangles].mean(axis=1))< 0.10)
    
            refiner = tri.UniformTriRefiner(triang)
            triang_refi, I_refi = refiner.refine_field(I, subdiv=3)

            tricon = ax[i,j].tricontour(triang_refi, I_refi,levels=15, linewidths=0.5, colors='k')
            triconf =ax[i,j].tricontourf(triang_refi,I_refi,levels=15, cmap='Spectral_r',vmin=0 , vmax=maxI)

            ax[i,j].set_title('Light ID: {0}'.format(i*2+j),fontsize=10)
        
    #set up the common color bar
    fig.colorbar(triconf, ax=ax,shrink=0.70,label='Light Intensity')
             
    #set up the title and the x- and y-axis
    fig.supxlabel('Horizontal Degrees')
    fig.supylabel('Vertical Degrees')
    fig.suptitle('Vertical Scanning')

    #display the plot
    plt.show()
    

contour()