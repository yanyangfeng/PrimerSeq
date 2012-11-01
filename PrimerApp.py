#!/usr/bin/env python
# -*- coding: utf-8 -*-
# generated by wxGlade 0.6.5 on Mon Oct 29 22:23:14 2012

# these imports are to prevent import errors when I distribute the code
import anydbm
import dbhash

# useful imports
import wx
import os
import re
import sys
from pygr.seqdb import SequenceFileDB
import sam
import primer
import traceback
import logging
import datetime

# begin wxGlade: extracode
# end wxGlade


class PrimerFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: PrimerFrame.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        # Menu Bar
        self.primer_frame_menubar = wx.MenuBar()
        wxglade_tmp_menu = wx.Menu()
        wxglade_tmp_menu.Append(wx.NewId(), "Quit", "", wx.ITEM_NORMAL)
        self.primer_frame_menubar.Append(wxglade_tmp_menu, "File")
        self.SetMenuBar(self.primer_frame_menubar)
        # Menu Bar end
        self.primer_frame_statusbar = self.CreateStatusBar(1, 0)
        self.primer_notebook = wx.Notebook(self, -1, style=0)
        self.primer_notebook_pane_1 = wx.Panel(self.primer_notebook, -1)
        self.fasta_label = wx.StaticText(self.primer_notebook_pane_1, -1, "FASTA:")
        self.choose_fasta_button = wx.Button(self.primer_notebook_pane_1, -1, "Choose . . .")
        self.panel_1 = wx.ScrolledWindow(self.primer_notebook_pane_1, -1, style=wx.TAB_TRAVERSAL)
        self.fasta_choice_label = wx.StaticText(self.panel_1, -1, "None")
        self.gtf_label = wx.StaticText(self.primer_notebook_pane_1, -1, "GTF:")
        self.choose_gtf_button = wx.Button(self.primer_notebook_pane_1, -1, "Choose . . .")
        self.panel_2 = wx.ScrolledWindow(self.primer_notebook_pane_1, -1, style=wx.TAB_TRAVERSAL)
        self.gtf_choice_label = wx.StaticText(self.panel_2, -1, "None")
        self.bam_label = wx.StaticText(self.primer_notebook_pane_1, -1, "SAM/BAM(s):")
        self.choose_bam_button = wx.Button(self.primer_notebook_pane_1, -1, "Choose . . .")
        self.panel_3 = wx.Panel(self.primer_notebook_pane_1, -1)
        self.bam_choice_label = wx.StaticText(self.panel_3, -1, "None")
        self.sizer_4_staticbox = wx.StaticBox(self.primer_notebook_pane_1, -1, "Load Files")
        self.coordinates_label = wx.StaticText(self.primer_notebook_pane_1, -1, "Coordinates:")
        self.coordinates_text_field = wx.TextCtrl(self.primer_notebook_pane_1, -1, "", style=wx.TE_MULTILINE)
        self.output_label = wx.StaticText(self.primer_notebook_pane_1, -1, "Output:")
        self.choose_output_button = wx.Button(self.primer_notebook_pane_1, -1, "Choose . . .")
        self.panel_4 = wx.Panel(self.primer_notebook_pane_1, -1)
        self.output_choice_label = wx.StaticText(self.panel_4, -1, "None")
        self.run_button = wx.Button(self.primer_notebook_pane_1, -1, "Run PrimerSeq")
        self.primer_notebook_pane_2 = wx.Panel(self.primer_notebook, -1)
        self.psi_label = wx.StaticText(self.primer_notebook_pane_2, -1, "PSI:")
        self.psi_text_field = wx.TextCtrl(self.primer_notebook_pane_2, -1, ".95")
        self.psi_help_info = wx.StaticText(self.primer_notebook_pane_2, -1, "0 < PSI <= 1")
        self.type_label = wx.StaticText(self.primer_notebook_pane_2, -1, "Type:")
        self.type_combo_box = wx.ComboBox(self.primer_notebook_pane_2, -1, choices=["Annotation", "RNA-Seq + Annotation"], style=wx.CB_DROPDOWN | wx.CB_DROPDOWN)
        self.type_help_info = wx.StaticText(self.primer_notebook_pane_2, -1, "Novel Jcts?")
        self.gene_id_label = wx.StaticText(self.primer_notebook_pane_2, -1, "Gene ID:")
        self.gene_id_combo_box = wx.ComboBox(self.primer_notebook_pane_2, -1, choices=["Valid", "Not Valid"], style=wx.CB_DROPDOWN | wx.CB_DROPDOWN)
        self.gene_id_help_info = wx.StaticText(self.primer_notebook_pane_2, -1, "In GTF?")
        self.temp_label = wx.StaticText(self.primer_notebook_pane_2, -1, "Keep Temporary:")
        self.temp_combo_box = wx.ComboBox(self.primer_notebook_pane_2, -1, choices=["No", "Yes"], style=wx.CB_DROPDOWN | wx.CB_DROPDOWN)
        self.read_threshold_label = wx.StaticText(self.primer_notebook_pane_2, -1, "Read Threshold:")
        self.read_threshold_text_field = wx.TextCtrl(self.primer_notebook_pane_2, -1, "5")
        self.anchor_length_label = wx.StaticText(self.primer_notebook_pane_2, -1, "Anchor Length:")
        self.anchor_length_text_field = wx.TextCtrl(self.primer_notebook_pane_2, -1, "8")
        self.min_jct_count_label = wx.StaticText(self.primer_notebook_pane_2, -1, "Min. Jct Count:")
        self.min_jct_count_text_field = wx.TextCtrl(self.primer_notebook_pane_2, -1, "1")
        self.sizer_11_staticbox = wx.StaticBox(self.primer_notebook_pane_2, -1, "Advanced")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_MENU, self.quit_event, id=-1)
        self.Bind(wx.EVT_BUTTON, self.choose_fasta_button_event, self.choose_fasta_button)
        self.Bind(wx.EVT_BUTTON, self.choose_gtf_button_event, self.choose_gtf_button)
        self.Bind(wx.EVT_BUTTON, self.choose_bam_button_event, self.choose_bam_button)
        self.Bind(wx.EVT_BUTTON, self.choose_output_button_event, self.choose_output_button)
        self.Bind(wx.EVT_BUTTON, self.run_button_event, self.run_button)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: PrimerFrame.__set_properties
        self.SetTitle("PrimerSeq")
        self.primer_frame_statusbar.SetStatusWidths([-1])
        # statusbar fields
        primer_frame_statusbar_fields = ["primer_frame_statusbar"]
        for i in range(len(primer_frame_statusbar_fields)):
            self.primer_frame_statusbar.SetStatusText(primer_frame_statusbar_fields[i], i)
        self.fasta_label.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Sans"))
        self.fasta_choice_label.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Sans"))
        self.panel_1.SetScrollRate(10, 10)
        self.gtf_label.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Sans"))
        self.gtf_choice_label.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Sans"))
        self.panel_2.SetScrollRate(10, 10)
        self.bam_label.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Sans"))
        self.bam_choice_label.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Sans"))
        self.coordinates_label.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Sans"))
        self.coordinates_text_field.SetMinSize((396, 60))
        self.output_label.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Sans"))
        self.output_choice_label.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Sans"))
        self.psi_label.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Sans"))
        self.psi_text_field.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Sans"))
        self.psi_help_info.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Sans"))
        self.type_label.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Sans"))
        self.type_combo_box.SetMinSize((85, 27))
        self.type_combo_box.SetSelection(0)
        self.type_help_info.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Sans"))
        self.gene_id_label.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Sans"))
        self.gene_id_combo_box.SetMinSize((85, 27))
        self.gene_id_combo_box.SetSelection(0)
        self.gene_id_help_info.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Sans"))
        self.temp_label.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Sans"))
        self.temp_combo_box.SetMinSize((100, 27))
        self.temp_combo_box.SetSelection(-1)
        self.read_threshold_label.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Sans"))
        self.anchor_length_label.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Sans"))
        self.min_jct_count_label.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "Sans"))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: PrimerFrame.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_10 = wx.BoxSizer(wx.VERTICAL)
        self.sizer_11_staticbox.Lower()
        sizer_11 = wx.StaticBoxSizer(self.sizer_11_staticbox, wx.HORIZONTAL)
        grid_sizer_4 = wx.GridSizer(4, 2, 0, 0)
        grid_sizer_3 = wx.GridSizer(3, 3, 0, 0)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.VERTICAL)
        sizer_8 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_2 = wx.GridSizer(1, 3, 0, 0)
        sizer_9 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_4_staticbox.Lower()
        sizer_4 = wx.StaticBoxSizer(self.sizer_4_staticbox, wx.VERTICAL)
        grid_sizer_1 = wx.GridSizer(3, 3, 0, 0)
        sizer_7 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_5 = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer_1.Add(self.fasta_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_1.Add(self.choose_fasta_button, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_5.Add(self.fasta_choice_label, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        self.panel_1.SetSizer(sizer_5)
        grid_sizer_1.Add(self.panel_1, 1, wx.EXPAND, 0)
        grid_sizer_1.Add(self.gtf_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_1.Add(self.choose_gtf_button, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_6.Add(self.gtf_choice_label, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        self.panel_2.SetSizer(sizer_6)
        grid_sizer_1.Add(self.panel_2, 1, wx.EXPAND, 0)
        grid_sizer_1.Add(self.bam_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_1.Add(self.choose_bam_button, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_7.Add(self.bam_choice_label, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        self.panel_3.SetSizer(sizer_7)
        grid_sizer_1.Add(self.panel_3, 1, wx.EXPAND, 0)
        sizer_4.Add(grid_sizer_1, 1, wx.EXPAND, 0)
        sizer_3.Add(sizer_4, 1, wx.EXPAND, 0)
        sizer_8.Add(self.coordinates_label, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_8.Add(self.coordinates_text_field, 0, wx.EXPAND, 0)
        grid_sizer_2.Add(self.output_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_2.Add(self.choose_output_button, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_9.Add(self.output_choice_label, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        self.panel_4.SetSizer(sizer_9)
        grid_sizer_2.Add(self.panel_4, 1, wx.EXPAND, 0)
        sizer_8.Add(grid_sizer_2, 1, wx.EXPAND, 0)
        sizer_3.Add(sizer_8, 1, wx.EXPAND, 0)
        sizer_2.Add(sizer_3, 1, wx.EXPAND, 0)
        sizer_2.Add(self.run_button, 0, wx.EXPAND, 0)
        self.primer_notebook_pane_1.SetSizer(sizer_2)
        grid_sizer_3.Add(self.psi_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_3.Add(self.psi_text_field, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_3.Add(self.psi_help_info, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_3.Add(self.type_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_3.Add(self.type_combo_box, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 1)
        grid_sizer_3.Add(self.type_help_info, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_3.Add(self.gene_id_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_3.Add(self.gene_id_combo_box, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_3.Add(self.gene_id_help_info, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_10.Add(grid_sizer_3, 1, wx.EXPAND, 0)
        grid_sizer_4.Add(self.temp_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_4.Add(self.temp_combo_box, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_4.Add(self.read_threshold_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_4.Add(self.read_threshold_text_field, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_4.Add(self.anchor_length_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_4.Add(self.anchor_length_text_field, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 2)
        grid_sizer_4.Add(self.min_jct_count_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_4.Add(self.min_jct_count_text_field, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_11.Add(grid_sizer_4, 1, wx.EXPAND, 0)
        sizer_10.Add(sizer_11, 1, wx.EXPAND, 0)
        self.primer_notebook_pane_2.SetSizer(sizer_10)
        self.primer_notebook.AddPage(self.primer_notebook_pane_1, "Required")
        self.primer_notebook.AddPage(self.primer_notebook_pane_2, "Optional")
        sizer_1.Add(self.primer_notebook, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()
        # end wxGlade


    def quit_event(self, event):  # wxGlade: PrimerFrame.<event_handler>
        print "Event handler `quit_event' not implemented!"
        event.Skip()

    def choose_output_button_event(self, event):  # wxGlade: PrimerFrame.<event_handler>
        dlg = wx.FileDialog(self, message='Choose your output file', defaultDir=os.getcwd(),
                            wildcard='Text file (*.txt)|*.txt')  # open file dialog

        if dlg.ShowModal() == wx.ID_OK:
            self.output = dlg.GetPath()  # get the new filenames from the dialog
            dlg.Destroy()  # best to do this sooner
            self.output_choice_label.SetLabel(self.output.split('/')[-1])
        event.Skip()

    def choose_fasta_button_event(self, event):  # wxGlade: PrimerFrame.<event_handler>
        dlg = wx.FileDialog(self, message='Choose your FASTA file', defaultDir=os.getcwd(),
                            wildcard='FASTA file (*.fa)|*.fa|FASTA file(*.fasta)|*.fasta')  # open file dialog
        # if they press ok
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()  # get the new filenames from the dialog
            dlg.Destroy()  # best to do this sooner

            try:
                # set the fasta attribute
                load_progress = wx.ProgressDialog('FASTA', 'Loading FASTA . . . this may take ~1 min.',
                                                  maximum=100, parent=self, style=wx.PD_CAN_ABORT
                                                  | wx.PD_APP_MODAL
                                                  | wx.PD_ELAPSED_TIME)  # add progress dialog so user knows what happens
                self.fasta = SequenceFileDB(filename.encode('ascii', 'replace'))
                self.fasta_choice_label.SetLabel(filename.split('/')[-1])  # set label to just the filename and not the whole path
                load_progress.Update(100, 'Done.')
            except:
                load_progress.Destroy()
                t, v, trace = sys.exc_info()
                print('ERROR! For more information read the following lines')
                print('Type: ' + str(t))
                print('Value: ' + str(v))
                print('Traceback:\n' + traceback.format_exc())
        else:
            dlg.Destroy()  # make sure to destroy if they hit cancel
        event.Skip()

    def choose_gtf_button_event(self, event):  # wxGlade: PrimerFrame.<event_handler>
        dlg = wx.FileDialog(self, message='Choose your GTF file', defaultDir=os.getcwd(),
                            wildcard='GTF file (*.gtf)|*.gtf')  # open file dialog
        # if they press ok
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()  # get the new filenames from the dialog
            dlg.Destroy()  # best to do this sooner

            # set the gtf attribute
            print filename
            filename_without_path = dlg.GetFilename()  # only grab the actual filenames and none of the path information
            load_progress = wx.ProgressDialog('GTF', 'Loading GTF . . . will take ~1 min',
                                              maximum=100, parent=self, style=wx.PD_CAN_ABORT
                                              | wx.PD_APP_MODAL
                                              | wx.PD_ELAPSED_TIME)  # add progress dialog so user knows what happens
            load_progress.Update(0)
            self.gtf = primer.gene_annotation_reader(filename)
            load_progress.Update(100)
            self.gtf_choice_label.SetLabel(filename_without_path)
        else:
            dlg.Destroy()  # make sure to destroy if they hit cancel
        event.Skip()

    def choose_bam_button_event(self, event):  # wxGlade: PrimerFrame.<event_handler>
        dlg = wx.FileDialog(self, message='Choose your bam files', defaultDir=os.getcwd(),
                            wildcard='BAM files (*.bam)|*.bam|SAM files (*.sam)|*.sam', style=wx.FD_MULTIPLE)  # open file dialog
        # if they press ok
        if dlg.ShowModal() == wx.ID_OK:
            filenames = dlg.GetPaths()  # get the new filenames from the dialog
            filenames_without_path = dlg.GetFilenames()  # only grab the actual filenames and none of the path information
            dlg.Destroy()  # best to do this sooner
            self.bam = []  # clear bam attribute

            # set the bam attribute
            load_progress = wx.ProgressDialog('BAM', 'Setting up BAM file list',
                                              maximum=100, parent=self, style=wx.PD_CAN_ABORT
                                              | wx.PD_APP_MODAL
                                              | wx.PD_ELAPSED_TIME)  # add progress dialog so user knows what happens
            for i, filename in enumerate(filenames):
                load_progress.Update(int(float(i) / len(filenames) * 100), 'Reading %s . . .' % filenames_without_path[i])  # Display txt to user
                my_sam = sam.Sam(filename)
                self.bam.append(my_sam)  # [sam.Sam, sam.Sam, ...]
            load_progress.Update(100, 'Done.')
            self.bam_choice_label.SetLabel(', '.join(filenames_without_path))
        else:
            dlg.Destroy()  # make sure to destroy if they hit cancel
        event.Skip()

    def run_button_event(self, event):  # wxGlade: PrimerFrame.<event_handler>
        strandList, chrList, startList, endList = [], [], [], []  # stores all coordinate info

        # handle the coordinates in self.coordinates_text_input
        coordinates_string = self.coordinates_text_field.GetValue()  # a string
        coordinates = map(str, filter(lambda x: x != '', re.split('\s*,*\s*', coordinates_string)))  # ['(strand)(chr):(start)-(end)', ...]

        # define logging file before using logging.debug
        if not os.path.exists(primer.config_options['log']): os.mkdir(primer.config_options['log'])  # make directory to put log files
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(message)s',
                            filename=primer.config_options['log'] + '/log.primer.' + str(datetime.datetime.now()),
                            filemode='w')

        # options for primer.py
        options = {}
        options['target'] = zip(range(1, len(coordinates) + 1), coordinates)
        options['gtf'] = self.gtf
        options['fasta'] = self.fasta
        options['rnaseq'] = self.bam
        options['psi'] = float(self.psi_text_field.GetValue())
        options['rnaseq_flag'] = False
        options['annotation_flag'] = True if str(self.type_combo_box.GetValue()) == 'Annotation' else False
        options['both_flag'] = True if str(self.type_combo_box.GetValue()) == 'RNA-Seq + Annotation' else False
        options['output'] = self.output
        options['read_threshold'] = int(self.read_threshold_text_field.GetValue())
        options['keep_temp'] = False if str(self.temp_combo_box.GetValue()) == 'No' else True
        options['big_bed'] = None
        options['no_gene_id'] = False if str(self.gene_id_combo_box.GetValue()) == 'Valid' else True
        options['min_jct_count'] = int(self.min_jct_count_text_field.GetValue())
        options['job_id'] = 'jobs_id'

        load_progress = wx.ProgressDialog('Run', 'Designing primers . . .',
                                          maximum=100, parent=self, style=wx.PD_CAN_ABORT
                                          | wx.PD_APP_MODAL
                                          | wx.PD_ELAPSED_TIME)  # add progress dialog so user knows what happens
        load_progress.Update(0, 'Designing primers . . .')

        # design primers by calling the primer.main function
        primer.main(options)

        load_progress.Update(100, 'Done.')
        event.Skip()


# end of class PrimerFrame
class PrimerApp(wx.App):
    def OnInit(self):
        wx.InitAllImageHandlers()
        primer_frame = PrimerFrame(None, -1, "")
        self.SetTopWindow(primer_frame)
        primer_frame.Show()
        return 1

# end of class PrimerApp

if __name__ == "__main__":
    PrimerApp = PrimerApp(0)
    PrimerApp.MainLoop()
