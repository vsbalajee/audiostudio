#!/usr/bin/env python3
"""Audio Studio — transparent, local FFmpeg audio production engine.
No third-party Python packages. Requires ffmpeg and ffprobe on PATH.
"""
from __future__ import annotations
import argparse
import array
import datetime as dt
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import wave

VERSION="1.2.0"
RATE=48000
SUPPORTED={'.mp3','.wav','.m4a','.aac','.flac','.ogg','.oga','.opus','.mp4','.mov','.mkv','.webm','.wma'}
DEFAULTS={
 'project_name':'My Audio Project', 'voice_files':[], 'music_file':'', 'output_dir':'',
 'after_intro_seconds':5.0, 'between_seconds':3.0, 'outro_seconds':5.0,
 'music_under_intro':False, 'mute_music_during_final_voice':True,
 'music_voice_db':-25.0, 'music_gap_db':-17.0,
 'normalize_voice':True, 'gentle_cleanup':True, 'denoise_voice':False,
 'trim_edge_silence':False, 'export_stems':False,
 'additional_instructions':'',
}

class AudioStudioError(Exception): pass

def cmd_run(args, desc='FFmpeg operation'):
    p=subprocess.run([str(a) for a in args],stdout=subprocess.PIPE,stderr=subprocess.PIPE, text=True, errors='replace')
    if p.returncode:
        details=(p.stderr or p.stdout)[-3500:]
        raise AudioStudioError(f'{desc} failed (exit {p.returncode}):\n{details}')
    return p

def tool_check():
    for tool in ('ffmpeg','ffprobe'):
        if not shutil.which(tool): raise AudioStudioError(f'{tool} was not found. Install FFmpeg and add its bin folder to PATH.')

def ffprobe(path):
    p=cmd_run(['ffprobe','-v','error','-show_entries','format=duration:stream=index,codec_type,sample_rate,channels,codec_name','-of','json',path],'Inspect audio')
    j=json.loads(p.stdout)
    if not any(s.get('codec_type')=='audio' for s in j.get('streams',[])):
        raise AudioStudioError(f'No audio stream in {path}')
    try: duration=float(j['format']['duration'])
    except (ValueError,KeyError,TypeError): raise AudioStudioError(f'Could not measure duration of {path}')
    if not (math.isfinite(duration) and duration>0): raise AudioStudioError(f'Invalid duration: {path}')
    return duration,j

def natural_key(p):
    return [int(x) if x.isdigit() else x.casefold() for x in re.split(r'(\d+)', Path(p).stem)]

def gather_voice_files(folder):
    p=Path(folder)
    if not p.is_dir(): raise AudioStudioError(f'Voice folder does not exist: {p}')
    # Only direct children: don't accidentally mix music in a nested background-music folder into the voice sequence.
    return [str(f.resolve()) for f in sorted(p.iterdir(),key=natural_key) if f.is_file() and f.suffix.lower() in SUPPORTED]

def sanitize_name(name):
    return (re.sub(r'[^A-Za-z0-9 _-]+','',name).strip().replace(' ','_') or 'Audio_Studio_Project')[:65]

def validated_config(raw):
    if not isinstance(raw,dict): raise AudioStudioError("Project configuration must be a JSON object.")
    unknown=sorted(set(raw)-set(DEFAULTS)-{"voice_folder"})
    if unknown: raise AudioStudioError("Unsupported configuration field(s): "+", ".join(unknown))
    c=DEFAULTS | raw
    voices=c.get('voice_files') or []
    if c.get('voice_folder') and not voices: voices=gather_voice_files(c['voice_folder'])
    if not isinstance(voices,list) or not voices: raise AudioStudioError('Add at least one voice recording.')
    if len(voices)>200: raise AudioStudioError('This version supports up to 200 voice recordings.')
    c['voice_files']=[str(Path(f).expanduser().resolve()) for f in voices]
    for fn in c['voice_files']:
        if not Path(fn).is_file(): raise AudioStudioError(f'Missing voice file: {fn}')
        if Path(fn).suffix.lower() not in SUPPORTED: raise AudioStudioError(f'Unsupported voice format: {fn}')
    if len(set(c['voice_files']))!=len(c['voice_files']): raise AudioStudioError('Duplicate voice file detected in sequence.')
    music=c.get('music_file') or ''
    if music:
        music=str(Path(music).expanduser().resolve())
        if not Path(music).is_file(): raise AudioStudioError(f'Music file missing: {music}')
        if Path(music).suffix.lower() not in SUPPORTED: raise AudioStudioError(f'Unsupported music format: {music}')
    c['music_file']=music
    for k,maxvalue in [('after_intro_seconds',300),('between_seconds',300),('outro_seconds',300)]:
        try: v=float(c[k])
        except (TypeError,ValueError): raise AudioStudioError(f'{k} must be a number')
        if not (math.isfinite(v) and 0<=v<=maxvalue): raise AudioStudioError(f'{k} must be between 0 and {maxvalue} seconds.')
        c[k]=v
    for k in ('music_voice_db','music_gap_db'):
        try: v=float(c[k])
        except (TypeError,ValueError): raise AudioStudioError(f'{k} must be a dB number.')
        if not (-60<=v<=0): raise AudioStudioError(f'{k} must be between -60 and 0 dB.')
        c[k]=v
    for k in ('music_under_intro','mute_music_during_final_voice','normalize_voice','gentle_cleanup','denoise_voice','trim_edge_silence','export_stems'):
        if not isinstance(c[k],bool): raise AudioStudioError(f'{k} must be true or false.')
    c['output_dir']=str(Path(c['output_dir'] or (Path.home()/'Audio Studio')).expanduser().resolve())
    c['project_name']=str(c['project_name'] or 'Audio Studio Project')
    c['additional_instructions']=str(c.get('additional_instructions') or '')
    return c

def measure_voice_gain(p):
    # Gentle, clip-wide gain only: never use aggressive automatic word-level amplification.
    info=cmd_run(['ffmpeg','-nostdin','-hide_banner','-i',p,'-map','0:a:0','-vn','-af','volumedetect','-f','null','-'],'Measure voice level').stderr
    mean=re.search(r'mean_volume:\s*(-?[\d.]+) dB',info)
    peak=re.search(r'max_volume:\s*(-?[\d.]+) dB',info)
    if not mean or not peak: return 0.0
    mean_db=float(mean.group(1)); peak_db=float(peak.group(1))
    return round(max(-7.0,min(7.0, -24.0-mean_db, -2.5-peak_db)),2)

def detect_edge_trim(wav_path):
    """Conservative only: trim edge silence >=0.75 sec and keep 0.25 sec padding."""
    with wave.open(str(wav_path),'rb') as f:
        if f.getnchannels()!=1 or f.getsampwidth()!=2: return 0.0,0.0
        n=f.getnframes(); framesize=int(.05*RATE)
        if n==0: return 0.0,0.0
        # Avoid reading huge entire recordings in memory.
        blocks=[]
        while f.tell()<n:
            b=f.readframes(framesize)
            if not b:break
            a=array.array('h'); a.frombytes(b)
            if sys.byteorder=='big':a.byteswap()
            rms=math.sqrt(sum(float(v)*v for v in a)/max(1,len(a)))/32768.0
            blocks.append(rms)
    first=next((i for i,v in enumerate(blocks) if v>.008),0)
    last=next((i for i in range(len(blocks)-1,-1,-1) if blocks[i]>.008),len(blocks)-1)
    leading=max(0,first*.05-.25)
    trailing=max(0, n/RATE - (last+1)*.05-.25)
    if leading<.75:leading=0
    if trailing<.75:trailing=0
    if leading+trailing>n/RATE-1.0:return 0.0,0.0
    return round(leading,3),round(trailing,3)

def process_voice(src,dst,c,tempdir,index):
    gain=measure_voice_gain(src) if c['normalize_voice'] else 0.0
    filters=[]
    if c['gentle_cleanup']:filters.append('highpass=f=70')
    if c['denoise_voice']:filters.append('afftdn=nf=-45:tn=1')
    if abs(gain)>.02:filters.append(f'volume={gain}dB')
    filters.append('aresample=48000')
    p=Path(tempdir)/f'pre_{index:03}.wav'
    args=['ffmpeg','-y','-nostdin','-v','error','-i',src,'-map','0:a:0','-vn','-ac','1','-ar',str(RATE)]
    if filters:args+=['-af',','.join(filters)]
    cmd_run(args+['-c:a','pcm_s16le',p],f'Process voice {index}')
    dur,_=ffprobe(p)
    lead,tail=detect_edge_trim(p) if c['trim_edge_silence'] else (0,0)
    trimmed=max(0.01,dur-lead-tail)
    fade=min(.025,trimmed/5)
    filters2=[]
    if lead or tail:filters2.append(f'atrim=start={lead:.3f}:end={dur-tail:.3f}')
    filters2.append('asetpts=PTS-STARTPTS')
    filters2 += [f'afade=t=in:st=0:d={fade:.4f}',f'afade=t=out:st={max(0,trimmed-fade):.4f}:d={fade:.4f}']
    cmd_run(['ffmpeg','-y','-nostdin','-v','error','-i',p,'-af',','.join(filters2),'-ac','1','-ar',str(RATE),'-c:a','pcm_s16le',dst],f'Finalize voice {index}')
    actual,_=ffprobe(dst)
    return {'index':index,'name':Path(src).name,'duration_original':round(dur,3),'duration_used':round(actual,3),'gain_db':gain,'trimmed_start_sec':lead,'trimmed_end_sec':tail}

def silence(dest,duration):
    cmd_run(['ffmpeg','-y','-nostdin','-v','error','-f','lavfi','-i',f'anullsrc=r={RATE}:cl=mono','-t',f'{duration:.6f}','-c:a','pcm_s16le',dest], 'Create silence')

def concat_voice(clips,c,tempdir,outstem):
    silence_a=Path(tempdir)/'intro_silence.wav'
    silence_b=Path(tempdir)/'between_silence.wav'
    silence_out=Path(tempdir)/'outro_silence.wav'
    if len(clips)>=2 and c['after_intro_seconds']>0: silence(silence_a,c['after_intro_seconds'])
    if len(clips)>=3 and c['between_seconds']>0: silence(silence_b,c['between_seconds'])
    if c['music_file'] and c['outro_seconds']>0: silence(silence_out,c['outro_seconds'])
    pieces=[];timeline=[];t=0.0
    for i, clip in enumerate(clips):
        if i:
            gap=c['after_intro_seconds'] if i==1 else c['between_seconds']
            if gap>0:
                pieces.append(silence_a if i==1 else silence_b)
                t+=gap
        st=t;t+=clip['duration_used']
        timeline.append({'index':i,'name':clip['name'],'start':round(st,5),'end':round(t,5)})
        pieces.append(Path(tempdir)/f'voice_{i:03}.wav')
    last_voice_end=t
    if c['music_file'] and c['outro_seconds']>0:
        pieces.append(silence_out);t+=c['outro_seconds']
    listfile=Path(tempdir)/'voice.ffconcat'
    # FFmpeg concat demuxer requires escaped single quotes, stable local paths.
    lines=['ffconcat version 1.0']
    for file in pieces:
        s=file.as_posix().replace("'", "'\\''")
        lines.append(f"file '{s}'")
    listfile.write_text('\n'.join(lines)+'\n',encoding='utf8')
    cmd_run(['ffmpeg','-y','-nostdin','-v','error','-safe','0','-f','concat','-i',listfile,'-c:a','pcm_s16le','-ar',str(RATE),'-ac','1',outstem],'Assemble voice timeline')
    total,_=ffprobe(outstem)
    if abs(total-t)>.12:raise AudioStudioError(f'Voice timeline mismatch: expected {t:.2f}, got {total:.2f}')
    return timeline,total,last_voice_end

def loop_music(music,duration,dst,notes):
    music_duration,_=ffprobe(music)
    cross=min(1.25, music_duration*.12)
    if music_duration < .8:raise AudioStudioError('Background music must be at least 0.8 seconds long.')
    count=max(1,math.ceil((duration-cross)/(music_duration-cross)))
    if count<=10:
        args=['ffmpeg','-y','-nostdin','-v','error']
        for _ in range(count):args+=['-i',music]
        chunks=[f'[{i}:a:0]aresample={RATE},aformat=sample_fmts=fltp:channel_layouts=stereo,asetpts=PTS-STARTPTS[a{i}]' for i in range(count)]
        last='a0'
        for i in range(1,count):
            out=f'x{i}'
            chunks.append(f'[{last}][a{i}]acrossfade=d={cross:.3f}:c1=tri:c2=tri[{out}]')
            last=out
        chunks.append(f'[{last}]atrim=duration={duration:.6f},asetpts=PTS-STARTPTS[z]')
        cmd_run(args+['-filter_complex',';'.join(chunks),'-map','[z]','-ar',str(RATE),'-ac','2','-c:a','pcm_s16le',dst],'Seamless music loop')
        notes.append(f'Music source repeated {count} time(s) with {cross:.2f}s crossfades between repeats.')
    else:
        cmd_run(['ffmpeg','-y','-nostdin','-v','error','-stream_loop','-1','-i',music,'-t',f'{duration:.6f}','-ar',str(RATE),'-ac','2','-c:a','pcm_s16le',dst],'Repeat music')
        notes.append('Very short music source: simple repeated looping used; loop boundary may be audible.')

def envelope_points(timeline,total,c):
    db=lambda x:10**(x/20.0)
    quiet=db(c['music_voice_db']); gaplevel=db(c['music_gap_db'])
    # Build volume automation as piecewise-linear curves; no content-based emotional detection.
    vals=[]
    def add(t,v):
        t=max(0,min(total,float(t)))
        if vals and abs(vals[-1][0]-t)<.0001: vals[-1]=(t,float(v))
        elif vals and vals[-1][0]>t+.0001: raise AudioStudioError('Non-monotonic music envelope points')
        else: vals.append((t,float(v)))
    n=len(timeline)
    first_level=quiet if c['music_under_intro'] and not (n==1 and c['mute_music_during_final_voice']) else 0.0
    add(0,0)
    if first_level and timeline[0]['end']>.5:add(min(.4,timeline[0]['end']/4),first_level)
    add(timeline[0]['end'],first_level)
    for i in range(1,n):
        prev=timeline[i-1]
        current=timeline[i]
        gs=prev['end'];ge=current['start'];gapdur=max(0,ge-gs)
        current_level=0.0 if (i==n-1 and c['mute_music_during_final_voice']) else quiet
        prev_level=vals[-1][1]
        if gapdur>.03:
            rise=min(.55,gapdur/3)
            fall=min(.55,gapdur/3)
            add(gs+rise,gaplevel)
            add(ge-fall,gaplevel)
            add(ge,current_level)
        else: add(ge,current_level)
        add(current['end'],current_level)
    last_end=timeline[-1]['end'];outro=max(0,total-last_end)
    if outro>.03:
        last_level=vals[-1][1]
        rise=min(.55,outro*.2)
        fall=min(2.5,outro*.5)
        add(last_end+rise,gaplevel)
        if outro>rise+fall: add(total-fall,gaplevel)
        add(total,0)
    elif vals[-1][0]<total:add(total,vals[-1][1])
    return vals

def volume_expr(points):
    if len(points)==1:return f'{points[0][1]:.9f}'
    expr=f'{points[-1][1]:.9f}'
    for (ta,va),(tb,vb) in reversed(list(zip(points[:-1],points[1:]))):
        if tb-ta<.00001: continue
        interp=f'({va:.9f}+({vb-va:.9f})*(t-{ta:.5f})/{tb-ta:.5f})'
        expr=f'if(lt(t,{tb:.5f}),{interp},{expr})'
    return expr

def music_stem(music,timeline,total,c,tempdir,dest,notes):
    loopfile=Path(tempdir)/'looped_music.wav'
    loop_music(music,total,loopfile,notes)
    points=envelope_points(timeline,total,c)
    expr=volume_expr(points)
    guard=''
    if c['mute_music_during_final_voice']:
        start=timeline[-1]['start'];end=timeline[-1]['end']
        # Start guard slightly before the final voice, protecting frame-based volume evaluation.
        guard=f'if(between(t,{max(0,start-.05):.5f},{end:.5f}),0,{expr})'
    else:guard=expr
    filt=f"volume='{guard}':eval=frame"
    cmd_run(['ffmpeg','-y','-nostdin','-v','error','-i',loopfile,'-af',filt,'-c:a','pcm_s16le','-ar',str(RATE),'-ac','2',dest],'Apply music automation')
    d,_=ffprobe(dest)
    if abs(d-total)>.12:raise AudioStudioError('Music track duration is not aligned to voice timeline.')
    return [{'time_sec':round(t,3),'music_gain_percent':round(v*100,3)} for t,v in points]

def final_mix(voice,music,out,has_music):
    if has_music:
        filt='[0:a]aformat=channel_layouts=stereo[v];[v][1:a]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0,alimiter=limit=0.89[out]'
        args=['ffmpeg','-y','-nostdin','-v','error','-i',voice,'-i',music,'-filter_complex',filt,'-map','[out]']
    else:
        args=['ffmpeg','-y','-nostdin','-v','error','-i',voice,'-af','alimiter=limit=0.89']
    cmd_run(args+['-ar',str(RATE),'-ac','2','-c:a','libmp3lame','-b:a','320k',out],'Export MP3')

def run_project(cfg,progress=lambda msg: print(msg,flush=True),dry_run=False):
    c=validated_config(cfg);tool_check()
    progress('Validating source files...')
    source_durations=[]
    for f in c['voice_files']:
        d,_=ffprobe(f);source_durations.append(d)
    musicdur=ffprobe(c['music_file'])[0] if c['music_file'] else None
    preview_duration=sum(source_durations)+(c['after_intro_seconds'] if len(source_durations)>1 else 0)+max(0,len(source_durations)-2)*c['between_seconds']+(c['outro_seconds'] if c['music_file'] else 0)
    if preview_duration>6*3600:raise AudioStudioError('This version limits projects to six hours.')
    preflight={'name':c['project_name'],'files':list(zip([Path(f).name for f in c['voice_files']],source_durations)),'music_duration_sec':musicdur,'approx_total_seconds':preview_duration}
    if dry_run:return preflight
    outdir=Path(c['output_dir']);outdir.mkdir(parents=True,exist_ok=True)
    project=sanitize_name(c['project_name']);output=outdir/(project+'_FINAL.mp3')
    # Never silently overwrite completed work.
    if output.exists():
        stamp=dt.datetime.now().strftime('%Y%m%d_%H%M%S')
        candidate=outdir/(project+'_'+stamp+'_FINAL.mp3')
        counter=2
        while candidate.exists():
            candidate=outdir/(project+'_'+stamp+f'_{counter}_FINAL.mp3')
            counter+=1
        output=candidate
    stem=output.stem.removesuffix('_FINAL')
    changes=[];warnings=[]
    with tempfile.TemporaryDirectory(prefix='audio_studio_') as tempdir:
        processed=[]
        for i,src in enumerate(c['voice_files']):
            progress(f'Processing voice {i+1}/{len(c["voice_files"])}: {Path(src).name}')
            dst=Path(tempdir)/f'voice_{i:03}.wav'
            processed.append(process_voice(src,dst,c,tempdir,i))
        progress('Arranging voice timeline...')
        voice_stem=Path(tempdir)/'voice_timeline.wav'
        timeline,total,last_voice_end=concat_voice(processed,c,tempdir,voice_stem)
        music_file=None;envelope=[]
        if c['music_file']:
            progress('Building background music with transitions...')
            music_file=Path(tempdir)/'music_timeline.wav'
            envelope=music_stem(c['music_file'],timeline,total,c,tempdir,music_file,changes)
            if c['mute_music_during_final_voice']:
                warnings.append('Music muted during final voice by deterministic timeline; this does not assess artistic appropriateness.')
        progress('Exporting 320 kbps MP3...')
        final_mix(voice_stem,music_file,output,bool(music_file))
        got,meta=ffprobe(output)
        if abs(got-total)>.25: raise AudioStudioError(f'Final duration mismatch. Expected {total:.2f}s, got {got:.2f}s.')
        voiceout=None;musicout=None
        if c['export_stems']:
            voiceout=outdir/(stem+'_VOICE_ONLY.wav')
            shutil.copy2(voice_stem,voiceout)
            if music_file:
                musicout=outdir/(stem+'_MUSIC_ONLY.wav')
                shutil.copy2(music_file,musicout)
    report={
        'skill':f'Audio Studio {VERSION}','generated_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'project':c['project_name'], 'voice_files':processed,'timeline':timeline,
        'total_duration_seconds':round(got,3),'final_voice_end_seconds':round(last_voice_end,3),
        'music_file':c['music_file'],'music_envelope':envelope,
        'applied':{'voice_clip_order':'As supplied in config','intro_gap_seconds':c['after_intro_seconds'],
          'between_gap_seconds':c['between_seconds'],'outro_seconds':c['outro_seconds'] if c['music_file'] else 0,
          'music_under_intro':c['music_under_intro'],'mute_music_during_final_voice':c['mute_music_during_final_voice'],
          'music_voice_gain_db':c['music_voice_db'],'music_gap_gain_db':c['music_gap_db'],
          'normalize_voice':c['normalize_voice'],'gentle_cleanup':c['gentle_cleanup'],
          'denoise_voice':c['denoise_voice'],'trim_edge_silence':c['trim_edge_silence'],
          'micro_fades':'25 ms maximum at each voice edge',
          'master_limiter':'0.89 linear max amplitude','mp3_bitrate':'320 kbps'},
        'processing_notes':changes,
        'additional_instructions_unexecuted':c['additional_instructions'],
        'warnings':warnings + (['Free-text instructions were saved for human/LLM review, not automatically interpreted or executed.'] if c['additional_instructions'].strip() else []),
        'verification':'FFprobe duration and codec checks only. No perceptual listening, emotion recognition, or pronunciation review.',
        'outputs':{'final_mp3':str(output),'voice_only_wav':str(voiceout) if voiceout else None,'music_only_wav':str(musicout) if musicout else None}
    }
    rp=outdir/(stem+'_REPORT.json')
    rp.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    progress('Finished successfully.')
    return {'mp3':str(output),'report':str(rp),'duration_seconds':round(got,3),'voice_stem':str(voiceout) if voiceout else None,'music_stem':str(musicout) if musicout else None}

def main():
    parser=argparse.ArgumentParser(description='Audio Studio offline audio mixer')
    parser.add_argument('--version',action='version',version=f'Audio Studio {VERSION}')
    parser.add_argument('command',choices=['render','validate'])
    parser.add_argument('--config',required=True,help='UTF-8 JSON project configuration')
    args=parser.parse_args()
    try:
        config=json.loads(Path(args.config).read_text(encoding='utf8'))
        result=run_project(config,dry_run=args.command=='validate')
        print(json.dumps(result,indent=2,ensure_ascii=False))
    except (AudioStudioError,OSError,ValueError,subprocess.SubprocessError) as e:
        print(f'ERROR: {e}',file=sys.stderr);return 2
    return 0
if __name__=='__main__':raise SystemExit(main())
