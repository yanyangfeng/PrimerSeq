# Note to self, pubsub import must immediately follow wx
import wx
from wx.lib.pubsub import setuparg1
from wx.lib.pubsub import pub

import custom_thread as ct
import csv
import os
import utils
import primer
import logging
import json
import draw
import depth_plot
import subprocess
import gtf


class CustomDialog(wx.Dialog):
    def __init__(self, parent, id, title, text=''):
        wx.Dialog.__init__(self, parent, id, title, size=(300, 100))

        self.parent = parent
        self.text = wx.StaticText(self, -1, text)
        self.empty_text = wx.StaticText(self, -1, '')

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.empty_text, 0, wx.ALIGN_CENTER)
        sizer.Add(self.text, 0, wx.ALIGN_CENTER)
        sizer.Add(self.empty_text, 0, wx.ALIGN_CENTER)

        self.SetSizer(sizer)
        self.Show()

    def Update(self, val, update_text=''):
        if val == 100:
            self.Destroy()
        else:
            pass

    def check_dialog(self):
        pass


class PlotDialog(wx.Dialog):
    def __init__(self, parent, id, title, output_file, text=''):
        wx.Dialog.__init__(self, parent, id, title, size=(300, 100), style=wx.DEFAULT_DIALOG_STYLE)

        self.output_file = output_file

        self.parent = parent
        self.text = wx.StaticText(self, -1, text)

        self.bigwig_label = wx.StaticText(self, -1, "BigWig(s):")
        self.choose_bigwig_button = wx.Button(self, -1, "Choose . . .")
        self.bigwig = []
        self.panel_3 = wx.Panel(self, -1)
        self.bigwig_choice_label = wx.StaticText(self, -1, "None")
        bigwig_sizer = wx.GridSizer(1, 3, 0, 0)
        bigwig_sizer.Add(self.bigwig_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        bigwig_sizer.Add(self.choose_bigwig_button, 0, wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL, 0)
        bigwig_sizer.Add(self.bigwig_choice_label, 0, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL, 0)

        # read in valid primer output
        with open(self.output_file) as handle:
            self.results = filter(lambda x: len(x) > 1,  # if there is no tabs then it represents an error msg in the output
                                  csv.reader(handle, delimiter='\t'))[1:]
            select_results = [', '.join(r[:2]) for r in self.results]

        # target selection widgets
        target_sizer = wx.GridSizer(1, 2, 0, 0)
        self.target_label = wx.StaticText(self, -1, "Select Target:")
        self.target_combo_box = wx.ComboBox(self, -1, choices=select_results, style=wx.CB_DROPDOWN | wx.CB_DROPDOWN)
        self.target_combo_box.SetMinSize((145, 27))
        target_sizer.Add(self.target_label, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 0)
        target_sizer.Add(self.target_combo_box, 0, wx.ALIGN_LEFT, 0)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.plot_button = wx.Button(self, -1, 'Plot')
        self.cancel_button = wx.Button(self, -1, 'Cancel')
        button_sizer.Add(self.plot_button, 0, wx.ALIGN_RIGHT)
        button_sizer.Add(self.cancel_button, 0, wx.ALIGN_LEFT)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(bigwig_sizer, 0, wx.EXPAND, 10)
        sizer.Add(target_sizer, 0, wx.EXPAND)
        sizer.Add(button_sizer, 0, wx.ALIGN_CENTER)
        sizer.SetMinSize((300, 100))

        self.Bind(wx.EVT_BUTTON, self.choose_bigwig_event, self.choose_bigwig_button)
        self.Bind(wx.EVT_BUTTON, self.plot_button_event, self.plot_button)
        self.Bind(wx.EVT_BUTTON, self.cancel_button_event, self.cancel_button)
        self.SetSizer(sizer)
        self.Show()

        pub.subscribe(self.plot_update, "plot_update")

    def cancel_button_event(self, event):
        self.Destroy()
        event.Skip()

    def choose_bigwig_event(self, event):
        dlg = wx.FileDialog(self, message='Choose your BigWig files', defaultDir=os.getcwd(),
                            wildcard='BigWig files (*.bw)|*.bw|BigWig files (*.bigWig)|*.bigWig', style=wx.FD_MULTIPLE)  # open file dialog
        # if they press ok
        if dlg.ShowModal() == wx.ID_OK:
            filenames = dlg.GetPaths()  # get the new filenames from the dialog
            filenames_without_path = dlg.GetFilenames()  # only grab the actual filenames and none of the path information
            dlg.Destroy()  # best to do this sooner

            self.bigwig = filenames
            self.bigwig_choice_label.SetLabel(', '.join(filenames_without_path))
        else:
            dlg.Destroy()

    def plot_button_event(self, event):
        if not self.bigwig or not self.target_combo_box.GetValue():
            dlg = wx.MessageDialog(self, 'Please select a BigWig file and the target exon\nyou want to plot.', style=wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            return

        self.target_id = str(self.target_combo_box.GetValue().split(',')[0])
        self.target_of_interest = str(self.target_combo_box.GetValue().split(', ')[1])

        # get the line from the file that matches the user selection
        for row in self.results:
            if row[0] == self.target_id:
                row_of_interest = row

        # find where the plot should span
        tmp_upstream_start, tmp_upstream_end = utils.get_pos(row_of_interest[9])
        tmp_downstream_start, tmp_downstream_end = utils.get_pos(row_of_interest[11])
        start = min(tmp_upstream_start, tmp_downstream_start)
        end = max(tmp_upstream_end, tmp_downstream_end)
        chr = utils.get_chr(row_of_interest[9])
        plot_domain = utils.construct_coordinate(chr, start, end)

        self.plot_button.SetLabel('Ploting . . .')
        self.plot_button.Disable()

        # draw isoforms
        plot_thread = ct.PlotThread(target=self.generate_plots, args=(self.target_id, plot_domain, self.bigwig, self.output_file))

    def generate_plots(self, tgt_id, plt_domain, bigwig, out_file):
        # generate isoform drawing
        opts = {'json': primer.config_options['tmp'] + '/isoforms/' + tgt_id + '.json',
                'output': primer.config_options['tmp'] + '/' + 'draw/' + tgt_id + '.png',
                'scale': 1,
                'primer_file': out_file,
                'id': tgt_id}
        self.draw_isoforms(opts)

        # generate read depth plot
        opts = {'bigwig': ','.join(bigwig),
                'position': plt_domain,
                'gene': 'Not Used',
                'size': 2.,
                'step': 1,
                'output': primer.config_options['tmp'] + '/depth_plot/' + tgt_id + '.png'}
        self.depth_plot(opts)

    def draw_isoforms(self, opts):
        '''
        Draw isoforms by using draw.py
        '''
        logging.debug('Drawing isoforms %s . . .' % str(opts))
        # load json file that has information isoforms and their counts
        with open(opts['json']) as handle:
            my_json = json.load(handle)

        coord = draw.read_primer_file(self.output_file, opts['id'])
        draw.main(my_json['path'], my_json['counts'], coord, opts)
        logging.debug('Finished drawing isoforms.')

    def depth_plot(self, opts):
        '''
        Create a read depth plot by using depth_plot.py
        '''
        logging.debug('Creating read depth plot %s . . .' % str(opts))
        depth_plot.read_depth_plot(opts)
        logging.debug('Finished creating read depth plot.')

    def plot_update(self, msg):
        self.plot_button.SetLabel('Plot')
        self.plot_button.Enable()
        DisplayPlotDialog(self, -1, 'Primer Results for ' + self.target_of_interest,
                          ['tmp/depth_plot/' + self.target_id + '.png',
                           'tmp/draw/' + self.target_id + '.png'])


class SortGtfDialog(wx.Dialog):
    def __init__(self, parent, id, title):
        wx.Dialog.__init__(self, parent, id, title, size=(300, 100), style=wx.DEFAULT_DIALOG_STYLE)

        self.parent = parent

        self.gtf_label = wx.StaticText(self, -1, "GTF:")
        self.choose_gtf_button = wx.Button(self, -1, "Choose . . .")
        self.panel_3 = wx.Panel(self, -1)
        self.gtf_choice_label = wx.StaticText(self, -1, "None")
        gtf_sizer = wx.GridSizer(1, 3, 0, 0)
        gtf_sizer.Add(self.gtf_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        gtf_sizer.Add(self.choose_gtf_button, 0, wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL, 0)
        gtf_sizer.Add(self.gtf_choice_label, 0, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL, 0)
        self.output_gtf_label = wx.StaticText(self, -1, "Sorted GTF:")
        self.choose_output_gtf_button = wx.Button(self, -1, "Choose . . .")
        self.panel_3 = wx.Panel(self, -1)
        self.output_gtf_choice_label = wx.StaticText(self, -1, "None")
        output_gtf_sizer = wx.GridSizer(1, 3, 0, 0)
        output_gtf_sizer.Add(self.output_gtf_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        output_gtf_sizer.Add(self.choose_output_gtf_button, 0, wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL, 0)
        output_gtf_sizer.Add(self.output_gtf_choice_label, 0, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL, 0)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sort_button = wx.Button(self, -1, 'Sort')
        self.cancel_button = wx.Button(self, -1, 'Cancel')
        button_sizer.Add(self.sort_button, 0, wx.ALIGN_RIGHT)
        button_sizer.Add(self.cancel_button, 0, wx.ALIGN_LEFT)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(gtf_sizer, 0, wx.EXPAND, 10)
        sizer.Add(output_gtf_sizer, 0, wx.EXPAND)
        sizer.Add(button_sizer, 0, wx.ALIGN_CENTER)
        sizer.SetMinSize((300, 100))

        self.Bind(wx.EVT_BUTTON, self.choose_gtf_event, self.choose_gtf_button)
        self.Bind(wx.EVT_BUTTON, self.choose_output_gtf_event, self.choose_output_gtf_button)
        self.Bind(wx.EVT_BUTTON, self.sort_button_event, self.sort_button)
        self.Bind(wx.EVT_BUTTON, self.cancel_button_event, self.cancel_button)
        self.SetSizer(sizer)
        self.Show()

        pub.subscribe(self.sort_update, "sort_update")

    def cancel_button_event(self, event):
        self.Destroy()
        event.Skip()

    def choose_output_gtf_event(self, event):
        dlg = wx.FileDialog(self, message='Choose your GTF file to be sorted', defaultDir=os.getcwd(),
                            wildcard='GTF file (*.gtf)|*.gtf')  # open file dialog
        # if they press ok
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()  # get the new filenames from the dialog
            filename_without_path = dlg.GetFilename()  # only grab the actual filenames and none of the path information
            dlg.Destroy()  # best to do this sooner

            self.output_gtf = filename
            self.output_gtf_choice_label.SetLabel(filename_without_path)
        else:
            dlg.Destroy()

    def choose_gtf_event(self, event):
        dlg = wx.FileDialog(self, message='Choose your GTF file to be sorted', defaultDir=os.getcwd(),
                            wildcard='GTF file (*.gtf)|*.gtf')  # open file dialog
        # if they press ok
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()  # get the new filenames from the dialog
            filename_without_path = dlg.GetFilename()  # only grab the actual filenames and none of the path information
            dlg.Destroy()  # best to do this sooner

            self.gtf = filename
            self.gtf_choice_label.SetLabel(filename_without_path)
        else:
            dlg.Destroy()

    def sort_gtf(self, infile, outfile):
        try:
            gtf.sort_gtf(infile, outfile)
        except MemoryError:
            cmd = 'java -jar -Xmx2048m "bin/SortGtf.jar" "%s" "%s"' % (infile, outfile)
            subprocess.check_call(cmd, shell=True)

    def sort_button_event(self, event):
        self.sort_button.SetLabel('Sorting . . .')
        self.sort_button.Disable()

        # draw isoforms
        sort_thread = ct.UpdateThread(target=self.sort_gtf,
                                      args=(self.gtf, self.output_gtf),
                                      update='sort_update')

    def sort_update(self, msg):
        self.sort_button.SetLabel('Sort')
        self.sort_button.Enable()

class AddGeneIdsDialog(wx.Dialog):
    def __init__(self, parent, id, title):
        wx.Dialog.__init__(self, parent, id, title, size=(300, 100), style=wx.DEFAULT_DIALOG_STYLE)

        self.parent = parent

        self.gtf_label = wx.StaticText(self, -1, "GTF:")
        self.choose_gtf_button = wx.Button(self, -1, "Choose . . .")
        self.panel_3 = wx.Panel(self, -1)
        self.gtf_choice_label = wx.StaticText(self, -1, "None")
        gtf_sizer = wx.GridSizer(1, 3, 0, 0)
        gtf_sizer.Add(self.gtf_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        gtf_sizer.Add(self.choose_gtf_button, 0, wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL, 0)
        gtf_sizer.Add(self.gtf_choice_label, 0, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL, 0)
        self.kgxref_label = wx.StaticText(self, -1, "kgXref:")
        self.choose_kgxref_button = wx.Button(self, -1, "Choose . . .")
        self.panel_3 = wx.Panel(self, -1)
        self.kgxref_choice_label = wx.StaticText(self, -1, "None")
        kgxref_sizer = wx.GridSizer(1, 3, 0, 0)
        kgxref_sizer.Add(self.kgxref_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        kgxref_sizer.Add(self.choose_kgxref_button, 0, wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL, 0)
        kgxref_sizer.Add(self.kgxref_choice_label, 0, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL, 0)
        self.output_gtf_label = wx.StaticText(self, -1, "GTF W/ Genes:")
        self.choose_output_gtf_button = wx.Button(self, -1, "Choose . . .")
        self.panel_3 = wx.Panel(self, -1)
        self.output_gtf_choice_label = wx.StaticText(self, -1, "None")
        output_gtf_sizer = wx.GridSizer(1, 3, 0, 0)
        output_gtf_sizer.Add(self.output_gtf_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        output_gtf_sizer.Add(self.choose_output_gtf_button, 0, wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL, 0)
        output_gtf_sizer.Add(self.output_gtf_choice_label, 0, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL, 0)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.add_genes_button = wx.Button(self, -1, 'Change Gene IDs')
        self.cancel_button = wx.Button(self, -1, 'Cancel')
        button_sizer.Add(self.add_genes_button, 0, wx.ALIGN_RIGHT)
        button_sizer.Add(self.cancel_button, 0, wx.ALIGN_LEFT)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(gtf_sizer, 0, wx.EXPAND, 10)
        sizer.Add(kgxref_sizer, 0, wx.EXPAND, 10)
        sizer.Add(output_gtf_sizer, 0, wx.EXPAND)
        sizer.Add(button_sizer, 0, wx.ALIGN_CENTER)
        sizer.SetMinSize((300, 100))

        self.Bind(wx.EVT_BUTTON, self.choose_gtf_event, self.choose_gtf_button)
        self.Bind(wx.EVT_BUTTON, self.choose_kgxref_event, self.choose_kgxref_button)
        self.Bind(wx.EVT_BUTTON, self.choose_output_gtf_event, self.choose_output_gtf_button)
        self.Bind(wx.EVT_BUTTON, self.add_genes_button_event, self.add_genes_button)
        self.Bind(wx.EVT_BUTTON, self.cancel_button_event, self.cancel_button)
        self.SetSizerAndFit(sizer)
        # self.SetSizer(sizer)
        self.Show()

        pub.subscribe(self.add_gene_ids_update, "add_update")

    def cancel_button_event(self, event):
        self.Destroy()
        event.Skip()

    def choose_output_gtf_event(self, event):
        dlg = wx.FileDialog(self, message='Choose your GTF file to be sorted', defaultDir=os.getcwd(),
                            wildcard='GTF file (*.gtf)|*.gtf')  # open file dialog
        # if they press ok
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()  # get the new filenames from the dialog
            filename_without_path = dlg.GetFilename()  # only grab the actual filenames and none of the path information
            dlg.Destroy()  # best to do this sooner

            self.output_gtf = filename
            self.output_gtf_choice_label.SetLabel(filename_without_path)
        else:
            dlg.Destroy()

    def choose_gtf_event(self, event):
        dlg = wx.FileDialog(self, message='Choose your GTF file to be sorted', defaultDir=os.getcwd(),
                            wildcard='GTF file (*.gtf)|*.gtf')  # open file dialog
        # if they press ok
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()  # get the new filenames from the dialog
            filename_without_path = dlg.GetFilename()  # only grab the actual filenames and none of the path information
            dlg.Destroy()  # best to do this sooner

            self.gtf = filename
            self.gtf_choice_label.SetLabel(filename_without_path)
        else:
            dlg.Destroy()

    def choose_kgxref_event(self, event):
        dlg = wx.FileDialog(self, message='Choose kgxref txt file', defaultDir=os.getcwd(),
                            wildcard='txt file (*.txt)|*.txt')  # open file dialog
        # if they press ok
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()  # get the new filenames from the dialog
            filename_without_path = dlg.GetFilename()  # only grab the actual filenames and none of the path information
            dlg.Destroy()  # best to do this sooner

            self.kgxref = filename
            self.kgxref_choice_label.SetLabel(filename_without_path)
        else:
            dlg.Destroy()

    def add_genes_button_event(self, event):
        self.add_genes_button.SetLabel('Adding . . .')
        self.add_genes_button.Disable()

        opts = {'annotation': self.gtf,
                'kgxref': self.kgxref,
                'output': self.output_gtf}

        # draw isoforms
        gene_thread = ct.UpdateThread(target=gn.main,
                                      args=(opts,),
                                      update='add_update')

    def add_gene_ids_update(self, msg):
        self.add_genes_button.SetLabel('Change Gene IDs')
        self.add_genes_button.Enable()


class DisplayPlotDialog(wx.Dialog):
    def __init__(self, parent, id, title, img_files):
        # call super constructor
        wx.Dialog.__init__(self, parent, id, title, style=wx.DEFAULT_DIALOG_STYLE ^ wx.RESIZE_BORDER)

        # containers for imgs
        depth_png = wx.Image(img_files[0], wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        draw_png = wx.Image(img_files[1], wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        self.draw_bitmap = wx.StaticBitmap(self, -1, draw_png, (10, 5), (draw_png.GetWidth(), draw_png.GetHeight()))
        self.depth_bitmap = wx.StaticBitmap(self, -1, depth_png, (10, 5), (depth_png.GetWidth(), depth_png.GetHeight()))

        self.parent = parent

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.depth_bitmap, 0, wx.ALIGN_CENTER)
        sizer.Add(self.draw_bitmap, 0, wx.ALIGN_CENTER)

        self.SetSizerAndFit(sizer)
        self.Show()
