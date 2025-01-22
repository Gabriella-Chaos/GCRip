from datetime import timedelta
import json
import os
import MPLS


class MPLSTools():

    def __init__(self, mpls_dir):
        self.mpls_dir = mpls_dir

    def save_chapters(self, out_dir):

        chp_txt = self.all_chapter_str()
        chp_fdict = {}

        for fn in chp_txt:
            txt_path = os.path.join(out_dir, fn + ".txt")
            with open(txt_path, 'w') as f:
                f.write(chp_txt[fn])

            chp_fdict[fn] = txt_path
        return chp_fdict

    def all_chapter_str(self):

        chp = self.scan_chapters()
        chp_str = {}

        for fn in chp:
            chp_str[fn] = self.chapters2txt(chp[fn])

        return chp_str

    def chapters2txt(self, chapters):

        chp_txt = ""
        for chp in chapters:
            chp_txt = chp_txt + f"CHAPTER{chp['number']:02d}={chp['timespan']}\n"
            chp_txt = chp_txt + f"CHAPTER{chp['number']:02d}NAME=Chapter {chp['number']:02d}\n"
        return chp_txt

    def scan_chapters(self):
        mpls_dir = self.mpls_dir
        fnames = [fn for fn in os.listdir(mpls_dir) if fn.endswith(".mpls")]

        chp = {}

        for fn in fnames:
            mpls_path = os.path.join(mpls_dir, fn)

            for f, chapters in self.get_chapters(mpls_path):

                if (f not in chp) or (len(chp[f]) < len(chapters)):
                    if len(chapters) > 1:
                        chp[f] = chapters

        return chp

    def get_chapters(self, fpath):
        with open(fpath, "rb") as f:
            header, _ = MPLS.load_header(f)

            f.seek(header["PlayListStartAddress"], os.SEEK_SET)
            playlist, _ = MPLS.load_PlayList(f)

            f.seek(header["PlayListMarkStartAddress"], os.SEEK_SET)
            playlist_marks, _ = MPLS.load_PlayListMark(f)
            playlist_marks = playlist_marks["PlayListMarks"]

            for i, play_item in enumerate(playlist["PlayItems"]):
                filename = f"{play_item['ClipInformationFileName']}.{play_item['ClipCodecIdentifier'].lower()}"

                play_item_marks = [
                    x
                    for x in playlist_marks
                    if x["MarkType"] == 1 and x["RefToPlayItemID"] == i
                ]
                if not play_item_marks:
                    # no chapters for this play item?
                    # print("No chapters in Playlist for", filename)
                    continue

                offset = play_item_marks[0]["MarkTimeStamp"]
                if play_item["INTime"] < offset:
                    offset = play_item["INTime"]

                chapters = []
                for n, play_item_mark in enumerate(play_item_marks):
                    duration = ((play_item_mark["MarkTimeStamp"] - offset) / 45000) * 1000
                    timespan = str(timedelta(milliseconds=duration))
                    if timespan.startswith("0:"):
                        timespan = f"0{timespan}"
                    if "." not in timespan:
                        timespan = f"{timespan}.000000"
                    chapters.append({
                        "clip": filename,
                        "number": n + 1,
                        "duration": duration,
                        "timespan": timespan,
                    })
                yield play_item['ClipInformationFileName'], chapters


if __name__ == '__main__':
    import sys

    mpls_dir = sys.argv[1]
    mpls = MPLSTools(mpls_dir)
    chpf = mpls.save_chapters("./")

    print(chpf)
    