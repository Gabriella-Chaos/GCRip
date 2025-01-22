import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from mpls import MPLSTools


def Ripper():

    def __init__(self, args):
        args = self.args

    def stream_info(m2ts_path):
        command = [
            "ffprobe",
            "-i", m2ts_path,
            "-show_streams",
            "-print_format", "json",
            "-loglevel", "quiet"
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        streams_info = json.loads(result.stdout)
        return streams_info.get("streams", [])

    def process_video(self, fpath, work_dir, streams):
        script_path = self.args.script_path
        outpath = os.path.join(work_dir, "out.hevc")

        script_dir, fname = os.path.split(script_path)
        os.chdir(script_path)

        module = os.path.splitext(fname)[0]

        script = import_module(module)

        clip = script.main(fpath)

        x265 = shutil.which('x265')
        x265_cmd = [x265, '--frames', f'{len(clip)}',
                     '--y4m', '--asm', 'avx2',
                     '--input-depth', f'{clip.format.bits_per_sample}',
                     '--output-depth', f'{clip.format.bits_per_sample}',
                     '--input-res', f'{clip.width}x{clip.height}',
                     '--fps', f'{clip.fps_num}/{clip.fps_den}',
                     '--no-open-gop', '--preset', 'placebo','--deblock', '-1:-1', 
                     '--b-intra', '--no-rect', '--no-amp', '--weightb', '--ref', '7',
                     '--rd', '6', '--no-sao', '--crf', '13.3', '--aq-mode', '1', 
                     '--aq-strength', '0.8', '--psy-rd', '3.3', '--psy-rdoq', '1.3',
                     '--pbratio', '1.2', '--cbqpoffs', '-1', '--crqpoffs', '-1', 
                     '--no-strong-intra-smoothing', '--rc-lookahead', '66',
                     '--output', outpath,
                     '-'] 

                    # '--ctu', '32', '--qg-size', '8', '--me', '3', '--subme', '4', '--merange', '38',
                    # '--rc-lookahead', '66', '--rd', '5', '--no-sao', '--crf', '13.3', '--aq-mode', '1',

        process = subprocess.Popen(x265_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        clip.output(process.stdin, y4m=True)
        process.communicate()

    def forge_mkv(self, item, m2ts_path, vpath, out_path):
        command = ["mkvmerge", "-o", output_path, vpath, "--no-video", m2ts_path]
        if item in self.chapter_files:
            command.extend(["--chapters", self.chapter_files[item]])

        subprocess.run(command, check=True)

    def rip(self, item, work_dir, out_path):

        work_dir = work_dir / (item + "_build")
        work_dir.mkdir(parents=True, exist_ok=True)

        vpath = self.process_video(m2ts_path, work_dir, streams)
        self.forge_mkv(item, m2ts_path, vpath, out_path)

    def rip_all(self):
        args = self.args

        work_dir = Path(args.build_dir) / Path(datetime.now().strftime("%y_%m_%d_%H_%M_%S"))
        work_dir.mkdir(parents=True, exist_ok=True)

        mpls = MPLSTools(args.mpls_dir)
        self.chapter_files = mpls.save_chapters(work_dir)

        fnames = [n[:-5] for n in os.listdir(args.m2ts_dir) if n[-5:] == ".m2ts"]

        for i, item in enumerate(fnames):
            outpath = os.path.join(args.out_dir, f"clip_{i}.mkv")
            rip(item, args, work_dir, out_path)


def main():
    parser = argparse.ArgumentParser(description='Automated BDRip Workflow')
    parser.add_argument(dest='script_path', type=str, help='Absolute or relative path to the encoding script', required=True)
    parser.add_argument(dest='m2ts_dir', type=str, help='Absolute or relative path to the m2ts directory', required=True)
    parser.add_argument(dest='mpls_dir', type=str, help='Absolute or relative path to the mpls directory', required=True)
    parser.add_argument('--build', '-b', dest='build_dir', type=str, default='./', help='Absolute or relative path to the build directory')
    parser.add_argument('--output', '-o', dest='out_dir', type=str, default='./', help='Absolute or relative path to the output directory')

    args = parser.parse_args()

    starttime = time.time()
    Ripper(args).rip_all()
    print(f'done in {time.time() - starttime:.2f}s')
