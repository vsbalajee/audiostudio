"""Run with: python tests/test_audio.py. Tests create synthetic recordings, not user's files."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import wave
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from audio_studio import run_project, envelope_points, AudioStudioError

def make_tone(path,duration,freq=440):
    subprocess.run(['ffmpeg','-nostdin','-y','-loglevel','error','-f','lavfi','-i',f'sine=frequency={freq}:sample_rate=48000:duration={duration}','-c:a','pcm_s16le',str(path)],check=True)

def wav_rms_at(path, start, dur):
    with wave.open(str(path),'rb') as f:
        rate=f.getframerate(); channels=f.getnchannels();width=f.getsampwidth()
        assert width==2
        f.setpos(min(int(start*rate), f.getnframes()-1))
        b=f.readframes(int(dur*rate))
    import array,math
    a=array.array('h');a.frombytes(b)
    if not a:return 0
    if sys.byteorder=='big': a.byteswap()
    return math.sqrt(sum(float(v)**2 for v in a)/len(a))/32768

class AudioTests(unittest.TestCase):
    def test_end_to_end(self):
        with tempfile.TemporaryDirectory() as td:
            t=Path(td)
            files=[]
            for i in range(3):
                p=t/f'{i}.wav';make_tone(p,1.2,freq=250+i*100);files.append(str(p))
            m=t/'music.wav';make_tone(m,2.4,freq=140)
            c={'project_name':'Tamil Tribute Test','voice_files':files,'music_file':str(m),'output_dir':str(t/'out'),'after_intro_seconds':2,'between_seconds':1.5,'outro_seconds':3,'export_stems':True,'mute_music_during_final_voice':True,'normalize_voice':False}
            out=run_project(c,progress=lambda _:None)
            self.assertTrue(Path(out['mp3']).is_file())
            report=json.loads(Path(out['report']).read_text())
            tl=report['timeline']
            self.assertAlmostEqual(tl[1]['start']-tl[0]['end'],2.0,places=2)
            self.assertAlmostEqual(tl[2]['start']-tl[1]['end'],1.5,places=2)
            self.assertAlmostEqual(out['duration_seconds'],1.2*3+2+1.5+3,delta=.2)
            self.assertLess(wav_rms_at(out['music_stem'],tl[2]['start']+.1,.6),.0002,'Music must be absent during last voice')
            self.assertGreater(wav_rms_at(out['music_stem'],tl[2]['end']+.8,.6),.0003,'Outro music should play')
            self.assertLess(wav_rms_at(out['voice_stem'],tl[0]['end']+.5,.6),.00005,'Voice should be silent during intro gap')
            self.assertTrue(out['mp3'].endswith('.mp3'))
            self.assertEqual(len(report['voice_files']),3)
    def test_no_music(self):
        with tempfile.TemporaryDirectory() as td:
            t=Path(td);p=t/'single.wav';make_tone(p,1.2)
            c={'project_name':'Voice only','voice_files':[str(p)],'output_dir':str(t/'out')}
            out=run_project(c,progress=lambda _:None)
            self.assertAlmostEqual(out['duration_seconds'],1.2,delta=.1)
            self.assertIsNone(out['music_stem'])
    def test_validation(self):
        with self.assertRaises(AudioStudioError):run_project({'voice_files':[]},dry_run=True)
        with self.assertRaises(AudioStudioError):run_project({'voice_files':['missing.wav']},dry_run=True)

if __name__=='__main__':unittest.main(verbosity=2)
