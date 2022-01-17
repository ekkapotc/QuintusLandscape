import os
import math
import configparser
import datetime

import numpy as np
from numpy import average

import pandas as pd

from jinja2 import Environment, FileSystemLoader

from matplotlib import pyplot as plt
from scipy.interpolate import griddata

import PyPDF2
from scipy.interpolate.interpnd import CloughTocher2DInterpolator
from weasyprint import HTML,CSS
from weasyprint.fonts import FontConfiguration

import QtUtils
import QtConfigure

def get_num_rows( num_entries, num_cols ):
    return int(np.ceil(num_entries/num_cols))


def grid(x, y, z, resX=100, resY=100):

    xi = np.linspace(min(x), max(x), resX)
    yi = np.linspace(min(y), max(y), resY)
    X, Y = np.meshgrid(xi, yi)
    Z =  griddata((x, y) , z ,  (xi[None,:], yi[:,None]) ,method='cubic'   )
    
    return X, Y, Z

class QtReport:

    def __init__(self , df , * , report_file_name , agent_name , airport_name , way_name ):
        
        #Configure the DLL searc path the weasyprint module depends on 
        QtUtils.setDLLSearchPath()

        #Configure the underlying settings
        QtConfigure.QtConfig()

        self.config = configparser.ConfigParser();
        self.config.read("QtConfig.ini")
        
        self.reportFileName = report_file_name
        self.agentName = agent_name
        self.airportName = airport_name
        self.wayName = way_name
        
        #Initialze a list for keeping track of the individual pdf files generated 
        self.pdfNames = []
        #Store dataframe
        self.df = df
        #Transform dataframe
        self.__transformDF()

        self.gminI = self.df['I'].min()
        self.gmaxI = self.df['I'].max()

        return

    def __transformDF(self):
        #Extract all the light sources and sort them in increasing order of their ids
        id_list = np.sort(self.df['Light ID'].unique())
    
        imax_list = []
        iavg_list = []
        hmax_list = []
        vmax_list = []
        icao_list = []
        color_list = []
        outcome_list = []

        #Extract necessary information from the initial dataframe
        for id in id_list:

            imax = self.df.loc[self.df['Light ID'] == id]['I'].max()
            maxIDF = self.df.loc[self.df['I'] == imax]
            hmax = maxIDF.iloc[0]['H']
            vmax = maxIDF.iloc[0]['V']
            iavg = self.df.loc[self.df['Light ID'] == id]['I'].mean()

            icao = maxIDF.iloc[0]['%ICAO']
            color = maxIDF.iloc[0]['C']
            outcome = maxIDF.iloc[0]['S']

            imax_list.append(imax)
            iavg_list.append(iavg)
            hmax_list.append(hmax)
            vmax_list.append(vmax)
            icao_list.append(icao)
            color_list.append(color)
            outcome_list.append(outcome)

        data = {
                'Light ID': id_list,
                '%ICAO': icao_list,
                'Iavg': iavg_list,
                'Imax' : imax_list,
                'Hmax' : hmax_list,
                'Vmax' : vmax_list,
                'C' : color_list,
                'S' : outcome_list
            }
        
        columns =('Light ID','%ICAO', 'Iavg','Imax','Hmax','Vmax','C','S')

        #construct a dataframe 
        self.mtab_df = pd.DataFrame(data,columns=columns)
        
        #set 'LightID' as index
        self.mtab_df.set_index(['Light ID'],inplace=True)

        return

    def __plot( self , page_no , start_row , end_row ):

        H = []
        V = []
        I = []
        
        #Prepare the specified number of sets of data to be plotted (default=6)
        for cur_id in range(start_row+1 , end_row+2):

            cur_df = self.df.loc[self.df['Light ID'] == cur_id]

            cur_idx = (cur_id-1)%self.num_rows_per_page

            H.append(cur_df['H'])
            V.append(cur_df['V'])
            I.append(cur_df['I'])

            H[cur_idx],V[cur_idx],I[cur_idx] = grid(H[cur_idx],V[cur_idx],I[cur_idx])

        #Set up M x N subplots
        ncols = self.num_subplot_cols
        nrows = get_num_rows(self.num_rows_per_page,ncols)
        
        fig, ax = plt.subplots(nrows=nrows, ncols=ncols,sharex=True, sharey=True)
        plt.subplots_adjust(hspace=0.3)

        #Choose the number of contour levels
        nlevels = int(self.config['ContourFormat']['nlevels'])
        levels = np.linspace(0,self.gmaxI,nlevels+1)
        cticks = np.arange(0,self.gmaxI,2000)

        #Compute the number of subplots
        nSubplots = len(H)

        #Determine whether to disable the axis for each (row,col)
        for row in range(0,nrows):
            for col in range(0,ncols):
                if ncols*row+col < nSubplots:
                    ax[row,col].axis('on')
                else:
                    ax[row,col].axis('off')

        #plot the contour for each entry
        for row in range(0,nrows):
            for col in range(0,ncols):
                if ncols*row+col<nSubplots:   
                    cs = ax[row,col].contour(H[ncols*row+col],V[ncols*row+col],I[ncols*row+col], levels=levels, linewidths=0.4, linestyles='dashed', colors='k') 
                    
                    csf = ax[row,col].contourf(H[ncols*row+col],V[ncols*row+col],I[ncols*row+col],levels=levels, cmap='Spectral_r',extend='both')
                    
                    ax[row,col].set_title('Light ID: {0}'.format(start_row+1+ncols*row+col),fontsize=10)
                    
                    fig.colorbar(csf,ax=ax[row,col],ticks=cticks) 
        
        #set up the title and the x- and y-axis
        fig.supxlabel('Horizontal Degrees')
        fig.supylabel('Vertical Degrees')
        fig.suptitle('Vertical Scanning')

        #save the plot as an image file
        save_as = os.path.join( self.config['Locations']['templocation'] , '{0}-{1}.png'.format(self.reportFileName,page_no))

        #save the plot
        plt.savefig( save_as , dpi=400  )
        plt.close()
        
        return

    def __onePDF( self , * , html_page , page_no ):

        save_as = os.path.join( self.config['Locations']['templocation'] , '{0}-{1}.pdf'.format(self.reportFileName,page_no) )

        #Set base url to img folder
        HTML( string=html_page , base_url='img' ).write_pdf(save_as) 

        QtUtils.displayInfo('{0} was made...'.format(save_as))

        return
    
    def __generateOnePDF( self , page_no , start_row , end_row ):

         #Draw contours
        self.__plot(page_no, start_row, end_row)

        #Get the entries for the current page
        cur_df = self.mtab_df.iloc[start_row:end_row+1] #end_row exclusive

        #Convert the dataframe into an HTML table, excluding the index column
        m_table = cur_df.to_html(index=True) 

        datetime_of_report = datetime.datetime.today()

         #Render each page 
        html_page =  self.template.render(
                                    m_table=m_table,
                                    page_no=page_no, 
                                    report_file_name=self.reportFileName,  
                                    air_port_name=self.airportName,
                                    way_name=self.wayName,
                                    agent_name=self.agentName,  
                                    date_of_report=QtUtils.getDate(datetime_of_report),
                                    time_of_report=QtUtils.getTime(datetime_of_report),
                                    plot_path='{0}-{1}.png'.format(self.reportFileName,page_no)   
                                )

        self.pdfNames.append('{0}-{1}.pdf'.format(self.reportFileName,page_no))

        #Compute the name of the current HTML
        save_as = os.path.join( self.config['Locations']['templocation'] , '{0}-{1}.html'.format(self.reportFileName,page_no) ) 
        
        with open( save_as , 'w' , encoding='utf-8') as html_file: 
            html_file.write(html_page)

        QtUtils.displayInfo('{0} was made...'.format(save_as))

        #Export as a pdf file
        self.__onePDF( html_page=html_page , page_no=page_no )

        return

    def __mergePDFs(self):

        input_dir = self.config['Locations']['templocation']
        output_dir = self.config['Locations']['reportlocation']

        merge_list = []

        for f in os.listdir(input_dir):
            if f in self.pdfNames:
                merge_list.append(os.path.join(input_dir,f))

        sorted(merge_list)

        merger = PyPDF2.PdfFileMerger()

        for f in merge_list:
            merger.append(f)

        save_as = os.path.join(output_dir,'{0}.pdf'.format(self.reportFileName))
        merger.write(save_as) 
        merger.close()

        return
    
    def generate( self ):

        file_loader = FileSystemLoader(self.config['Locations']['templatelocation']) 
        env = Environment(loader=file_loader,trim_blocks=True)
        self.template = env.get_template('template.html') 

        #Get the total number of entries
        num_of_rows  = self.mtab_df.shape[0]
    
        #Get the number of rows per page
        self.num_rows_per_page = int(self.config['ReportFormat']['numberofrowsperpage'])
        self.num_subplot_cols = int(self.config['ReportFormat']['numberofcolumns'])
        
        #Calculate the number of pages based on the config where the number of entries per page is set
        num_of_pages = math.ceil(num_of_rows / self.num_rows_per_page)

        row = 0
        for page_no in range( 1 , num_of_pages+1 ):
            start_row = row
            end_row = start_row + self.num_rows_per_page -1

            if end_row > num_of_rows-1:
                end_row = num_of_rows-1

            #Export the current page 
            self.__generateOnePDF( page_no , start_row , end_row )

            row = end_row+1

        #Merge PDFs
        self.__mergePDFs()

        #Delete temp files
        dir = self.config['Locations']['templocation']
        for f in os.listdir(dir):
           os.remove(os.path.join(dir,f))

        return
