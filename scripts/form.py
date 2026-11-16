#!/usr/bin/env python3
"""Audio Studio desktop form (Tkinter, standard-library only)."""
from __future__ import annotations
import json
from pathlib import Path
import queue
import re
import shutil
import sys
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import zipfile
from audio_studio import AudioStudioError, DEFAULTS, SUPPORTED, gather_voice_files, natural_key, run_project

BG='#0b1423';PANEL='#17253a';PANEL2='#213249';WHITE='#f6fafc';MUTED='#a6b7c9';ACCENT='#49dec1';ENTRY='#223449'
FONT=('Segoe UI',10);TITLE=('Segoe UI',25,'bold');SECTION=('Segoe UI',12,'bold')

class AudioStudioForm(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Audio Studio  |  Voice + Music Mixer')
        self.geometry('960x810');self.minsize(760,670);self.configure(bg=BG)
        self.voices=[];self.tempdirs=[];self.worker=None
        self.queue=queue.Queue()
        self.name=tk.StringVar(value='My Audio Project')
        self.music=tk.StringVar(value='')
        self.out=tk.StringVar(value=str(Path.home()/'Audio Studio'))
        self.intro_gap=tk.StringVar(value='5')
        self.between_gap=tk.StringVar(value='3')
        self.outro_gap=tk.StringVar(value='5')
        self.music_intro=tk.BooleanVar(value=False)
        self.mute_last=tk.BooleanVar(value=True)
        self.normalize=tk.BooleanVar(value=True)
        self.cleanup=tk.BooleanVar(value=True)
        self.denoise=tk.BooleanVar(value=False)
        self.trim=tk.BooleanVar(value=False)
        self.stems=tk.BooleanVar(value=False)
        self.music_mix=tk.StringVar(value='Quiet — voice first')
        self.last_result=None
        self.setup_styles()
        self.build()
        self.after(130,self.pump)
        self.protocol('WM_DELETE_WINDOW',self.close)

    def setup_styles(self):
        s=ttk.Style(self)
        s.theme_use('clam')
        s.configure('M.TCombobox',padding=8,fieldbackground=ENTRY,background=PANEL,foreground=WHITE,arrowcolor=ACCENT)
        s.map('M.TCombobox',fieldbackground=[('readonly',ENTRY)],foreground=[('readonly',WHITE)])
        s.configure('TProgressbar',troughcolor=PANEL,background=ACCENT,bordercolor=PANEL)

    def make_label(self,parent,txt,font=FONT,color=WHITE,**kw):
        return tk.Label(parent,text=txt,font=font,fg=color,bg=parent['bg'],**kw)

    def card(self,parent,title,desc=''):
        frame=tk.Frame(parent,bg=PANEL,highlightbackground='#2b4058',highlightthickness=1,padx=19,pady=16)
        frame.pack(fill='x',pady=8)
        self.make_label(frame,title,SECTION).pack(anchor='w',pady=(0,4))
        if desc:self.make_label(frame,desc,font=('Segoe UI',9),color=MUTED,wraplength=790,justify='left').pack(anchor='w',pady=(0,10))
        return frame

    def entry(self,parent,var,width=20):
        e=tk.Entry(parent,textvariable=var,font=FONT,fg=WHITE,bg=ENTRY,insertbackground=WHITE,relief='flat',width=width,highlightthickness=1,highlightbackground='#3b526a',highlightcolor=ACCENT)
        return e

    def button(self,parent,text,callback,accent=False):
        b=tk.Button(parent,text=text,command=callback,fg=BG if accent else WHITE,bg=ACCENT if accent else PANEL2,
                 activebackground='#86f0df' if accent else '#36516c',activeforeground=BG if accent else WHITE,
                 borderwidth=0,highlightthickness=0,cursor='hand2',padx=12,pady=9,font=('Segoe UI',9,'bold'))
        return b

    def checkbox(self,parent,label,var):
        b=tk.Checkbutton(parent,text=label,variable=var,fg=WHITE,bg=PANEL,selectcolor=ENTRY,activebackground=PANEL,activeforeground=WHITE,font=FONT)
        return b

    def inline_setting(self,parent,label,var,width=7):
        cell=tk.Frame(parent,bg=PANEL)
        self.make_label(cell,label,font=('Segoe UI',9),color=MUTED).pack(anchor='w')
        self.entry(cell,var,width).pack(anchor='w',pady=(5,0),ipady=7)
        cell.pack(side='left',padx=(0,25),pady=4)

    def build(self):
        hdr=tk.Frame(self,bg=BG,padx=30,pady=15);hdr.pack(fill='x')
        tk.Label(hdr,text='Audio  Studio',font=TITLE,bg=BG,fg=WHITE).pack(anchor='w')
        self.make_label(hdr,'Easy audio production — clear voice, gentle music, your creative control.',font=('Segoe UI',10),color=MUTED).pack(anchor='w')
        self.make_label(hdr,'100% local editing  •  Free FFmpeg engine  •  No AI listening claims',font=('Segoe UI',9),color=ACCENT).pack(anchor='w',pady=(7,0))
        content=tk.Frame(self,bg=BG);content.pack(fill='both',expand=True,padx=18)
        self.canvas=tk.Canvas(content,bg=BG,highlightthickness=0)
        scroll=tk.Scrollbar(content,orient='vertical',command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right',fill='y');self.canvas.pack(side='left',fill='both',expand=True)
        body=tk.Frame(self.canvas,bg=BG,padx=12,pady=4)
        self.window_id=self.canvas.create_window((0,0),window=body,anchor='nw')
        body.bind('<Configure>',lambda e:self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>',lambda e:self.canvas.itemconfigure(self.window_id,width=e.width))
        self.canvas.bind_all('<MouseWheel>',lambda e:self.canvas.yview_scroll(int(-e.delta/120),'units'))
        self.canvas.bind_all('<Button-4>',lambda e:self.canvas.yview_scroll(-1,'units'))
        self.canvas.bind_all('<Button-5>',lambda e:self.canvas.yview_scroll(1,'units'))

        p=self.card(body,'1. Your project','Give the finished recording a memorable name.')
        self.entry(p,self.name,width=57).pack(fill='x',ipady=7,pady=2)

        p=self.card(body,'2. Voice recordings','Add individual files, a folder, or a ZIP. Files can be MP3, WAV, M4A, MP4 and other common formats.')
        tools=tk.Frame(p,bg=PANEL);tools.pack(fill='x',pady=(0,10))
        for title,fn in [('Add files',self.add_files),('Add folder',self.add_folder),('Add ZIP',self.add_zip),('Sort 0 → 7',self.sort_voices)]:
            self.button(tools,title,fn).pack(side='left',padx=(0,8))
        main=tk.Frame(p,bg=PANEL);main.pack(fill='x')
        self.listbox=tk.Listbox(main,height=6,selectmode=tk.SINGLE,fg=WHITE,bg=ENTRY,selectforeground=BG,selectbackground=ACCENT,
                                font=('Segoe UI',10),borderwidth=0,highlightthickness=1,highlightbackground='#3b526a')
        self.listbox.pack(side='left',fill='both',expand=True)
        controls=tk.Frame(main,bg=PANEL);controls.pack(side='left',padx=(10,0))
        for name,cb in [('↑ Move up',lambda:self.move(-1)),('↓ Move down',lambda:self.move(1)),('Remove',self.remove_selected),('Clear',self.clear_voices)]:
            self.button(controls,name,cb).pack(fill='x',pady=(0,6))
        self.files_label=self.make_label(p,'No recordings added',font=('Segoe UI',9),color=MUTED)
        self.files_label.pack(anchor='w',pady=(8,0))

        p=self.card(body,'3. Background music','Choose one instrumental track. Music stays on a separate timeline during processing.')
        r=tk.Frame(p,bg=PANEL);r.pack(fill='x')
        self.entry(r,self.music,60).pack(side='left',fill='x',expand=True,ipady=7,padx=(0,8))
        self.button(r,'Choose music',self.choose_music).pack(side='right')
        levels=tk.Frame(p,bg=PANEL);levels.pack(fill='x',pady=(13,5))
        self.make_label(levels,'Music level',color=MUTED).pack(side='left',padx=(0,18))
        combo=ttk.Combobox(levels,state='readonly',style='M.TCombobox',textvariable=self.music_mix,
                 values=['Very quiet','Quiet — voice first','Balanced','More prominent'],width=23)
        combo.pack(side='left')
        self.checkbox(p,'Include music under the introduction',self.music_intro).pack(anchor='w',pady=2)
        self.checkbox(p,'NO MUSIC during the final voice recording',self.mute_last).pack(anchor='w',pady=2)

        p=self.card(body,'4. Timing & gentle cleanup','Set gaps in seconds. The original pauses inside your recordings are preserved by default.')
        rr=tk.Frame(p,bg=PANEL);rr.pack(fill='x')
        self.inline_setting(rr,'After Voice 0',self.intro_gap)
        self.inline_setting(rr,'Between other clips',self.between_gap)
        self.inline_setting(rr,'Music outro',self.outro_gap)
        r=tk.Frame(p,bg=PANEL);r.pack(fill='x',pady=(10,0))
        left=tk.Frame(r,bg=PANEL);left.pack(side='left',fill='x',expand=True)
        right=tk.Frame(r,bg=PANEL);right.pack(side='left',fill='x',expand=True)
        self.checkbox(left,'Balance voice volumes',self.normalize).pack(anchor='w')
        self.checkbox(left,'Remove low-frequency rumble',self.cleanup).pack(anchor='w')
        self.checkbox(right,'Optional gentle noise reduction',self.denoise).pack(anchor='w')
        self.checkbox(right,'Trim long edge silences',self.trim).pack(anchor='w')

        p=self.card(body,'5. Finish & export','MP3 is the default. Select stems if you also want voice and music WAV files for editing.')
        self.checkbox(p,'Also export separate editable WAV tracks',self.stems).pack(anchor='w',pady=(0,9))
        r=tk.Frame(p,bg=PANEL);r.pack(fill='x',pady=(0,8))
        self.entry(r,self.out,60).pack(side='left',fill='x',expand=True,ipady=7,padx=(0,8))
        self.button(r,'Output folder',self.choose_out).pack(side='right')
        self.make_label(p,'Additional instructions (saved in report; must be reviewed before they can be applied)',font=('Segoe UI',9),color=MUTED).pack(anchor='w',pady=(5,4))
        self.instructions=tk.Text(p,height=3,fg=WHITE,bg=ENTRY,insertbackground=WHITE,relief='flat',wrap='word',font=FONT)
        self.instructions.pack(fill='x')

        footer=tk.Frame(self,bg=BG,padx=30,pady=12);footer.pack(fill='x')
        self.status=self.make_label(footer,'Ready — add voice recordings to begin.',color=MUTED)
        self.status.pack(anchor='w',pady=(0,7))
        self.bar=ttk.Progressbar(footer,mode='indeterminate');self.bar.pack(fill='x',pady=(0,10))
        buttons=tk.Frame(footer,bg=BG);buttons.pack(fill='x')
        self.button(buttons,'Check project',self.preview).pack(side='left')
        self.go=self.button(buttons,'GENERATE MP3',self.generate,accent=True);self.go.pack(side='right',ipadx=15)
        self.open_button=self.button(buttons,'Open result folder',self.open_result);self.open_button.pack(side='right',padx=8)

    def refresh(self):
        self.listbox.delete(0,'end')
        for i,v in enumerate(self.voices):self.listbox.insert('end',f'{i:02}   {Path(v).name}')
        self.files_label.configure(text=f'{len(self.voices)} voice recording(s) selected' if self.voices else 'No recordings added')

    def add_new(self,files):
        count=0
        for f in files:
            if str(Path(f).suffix).lower() in SUPPORTED and str(Path(f).resolve()) not in self.voices:
                self.voices.append(str(Path(f).resolve()));count+=1
        self.refresh()
        if not count:messagebox.showinfo('Audio Studio','No new supported audio/video files were found.')

    def add_files(self):
        files=filedialog.askopenfilenames(title='Select voice recordings',filetypes=[('Audio/video files','*.mp3 *.wav *.m4a *.aac *.flac *.ogg *.opus *.mp4 *.mov *.mkv *.webm *.wma'),('All files','*.*')])
        self.add_new(files)

    def add_folder(self):
        folder=filedialog.askdirectory(title='Select voice recordings folder')
        if folder:self.add_new(gather_voice_files(folder))

    def add_zip(self):
        filename=filedialog.askopenfilename(title='Select ZIP of voice recordings',filetypes=[('ZIP archive','*.zip')])
        if not filename:return
        temp=tempfile.TemporaryDirectory(prefix='audio_studio_zip_')
        dest=Path(temp.name)
        try:
            with zipfile.ZipFile(filename) as z:
                items=sorted((i for i in z.infolist() if not i.is_dir() and Path(i.filename).suffix.lower() in SUPPORTED),key=lambda i:natural_key(Path(i.filename).name))
                if len(items)>200:raise AudioStudioError('ZIP has more than 200 audio files.')
                if sum(i.file_size for i in items)>2*1024**3:raise AudioStudioError('ZIP audio contents exceed 2 GB.')
                if any(i.file_size>1024**3 for i in items):raise AudioStudioError('A ZIP recording exceeds the 1 GB individual-file safety limit.')
                files=[]
                for index,item in enumerate(items):
                    ext=Path(item.filename).suffix.lower()
                    out=dest/f'{index:03}_{Path(item.filename).name}'
                    with z.open(item) as source, out.open('wb') as target:shutil.copyfileobj(source,target)
                    files.append(out)
            self.tempdirs.append(temp)
            self.add_new(sorted(files,key=lambda p:natural_key(p)))
        except (zipfile.BadZipFile,AudioStudioError,OSError) as exc:
            temp.cleanup();messagebox.showerror('ZIP import failed',str(exc))

    def sort_voices(self):self.voices.sort(key=natural_key);self.refresh()
    def move(self,d):
        sel=self.listbox.curselection()
        if not sel:return
        i=sel[0];j=i+d
        if 0<=j<len(self.voices):
            self.voices[i],self.voices[j]=self.voices[j],self.voices[i]
            self.refresh();self.listbox.selection_set(j)
    def remove_selected(self):
        sel=self.listbox.curselection()
        if sel:self.voices.pop(sel[0]);self.refresh()
    def clear_voices(self):self.voices.clear();self.refresh()
    def choose_music(self):
        f=filedialog.askopenfilename(title='Choose background instrumental',filetypes=[('Music files','*.mp3 *.wav *.m4a *.aac *.flac *.ogg *.opus'),('All files','*.*')])
        if f:self.music.set(f)
    def choose_out(self):
        f=filedialog.askdirectory(title='Choose output folder')
        if f:self.out.set(f)

    def config(self):
        levels={'Very quiet':(-29,-20),'Quiet — voice first':(-25,-17),'Balanced':(-22,-15),'More prominent':(-19,-12)}
        voice_db,gap_db=levels[self.music_mix.get()]
        return {'project_name':self.name.get(),'voice_files':list(self.voices),'music_file':self.music.get(),
                'output_dir':self.out.get(),'after_intro_seconds':float(self.intro_gap.get()),
                'between_seconds':float(self.between_gap.get()),'outro_seconds':float(self.outro_gap.get()),
                'music_under_intro':self.music_intro.get(),'mute_music_during_final_voice':self.mute_last.get(),
                'music_voice_db':voice_db,'music_gap_db':gap_db,'normalize_voice':self.normalize.get(),
                'gentle_cleanup':self.cleanup.get(),'denoise_voice':self.denoise.get(),
                'trim_edge_silence':self.trim.get(),'export_stems':self.stems.get(),
                'additional_instructions':self.instructions.get('1.0','end').strip()}

    def preview(self):
        try:
            p=run_project(self.config(),dry_run=True,progress=lambda _:None)
            rows='\n'.join(f'  {name}: {dur:.1f} seconds' for name,dur in p['files'])
            msg=f"PROJECT: {p['name']}\n\nVOICE FILES:\n{rows}\n\nESTIMATED LENGTH: {p['approx_total_seconds']:.1f} sec\n\nMusic: {Path(self.music.get()).name if self.music.get() else 'None'}\n\nAdditional instructions are saved, not automatically applied."
            messagebox.showinfo('Project Check',msg)
        except (AudioStudioError,ValueError,OSError) as e:messagebox.showerror('Check failed',str(e))

    def generate(self):
        if self.worker and self.worker.is_alive():return
        try: cfg=self.config()
        except (ValueError,OSError) as e:
            messagebox.showerror('Invalid settings',str(e));return
        if cfg['additional_instructions'] and not messagebox.askyesno('Important: extra instructions',
            'Your extra instructions will be SAVED in the report, not automatically executed.\n\nProceed using the selected controls only?'):
            return
        self.go.configure(state='disabled');self.bar.start(15)
        def run():
            try:self.queue.put(('done',run_project(cfg,progress=lambda msg:self.queue.put(('status',msg)))))
            except Exception as e:self.queue.put(('error',str(e)))
        self.worker=threading.Thread(target=run,daemon=True);self.worker.start()

    def pump(self):
        try:
            while True:
                typ,value=self.queue.get_nowait()
                if typ=='status':self.status.configure(text=value)
                elif typ=='done':
                    self.bar.stop();self.go.configure(state='normal');self.last_result=value
                    self.status.configure(text=f"Created {Path(value['mp3']).name} ({value['duration_seconds']:.1f}s)")
                    messagebox.showinfo('Success',f"Your MP3 is ready!\n\n{value['mp3']}\n\nTechnical report:\n{value['report']}\n\nPlease listen and approve the final artistic quality.")
                elif typ=='error':
                    self.bar.stop();self.go.configure(state='normal');self.status.configure(text='Failed — see details')
                    messagebox.showerror('Audio processing failed',value)
        except queue.Empty:pass
        self.after(130,self.pump)

    def open_result(self):
        folder=Path(self.last_result['mp3']).parent if self.last_result else Path(self.out.get()).expanduser()
        if not folder.exists():messagebox.showinfo('Output folder','Generate a file first.');return
        import subprocess
        if sys.platform.startswith('win'):import os;os.startfile(str(folder))
        elif sys.platform=='darwin':subprocess.Popen(['open',str(folder)])
        else:subprocess.Popen(['xdg-open',str(folder)])

    def close(self):
        if self.worker and self.worker.is_alive():
            messagebox.showwarning('Still processing','Please wait until the current render finishes before closing. This protects the temporary source files.')
            return
        for t in self.tempdirs:
            try:t.cleanup()
            except OSError:pass
        self.destroy()

if __name__=='__main__':
    try:AudioStudioForm().mainloop()
    except tk.TclError as exc:print(f'Could not open the form (graphical desktop required): {exc}',file=sys.stderr);sys.exit(2)
