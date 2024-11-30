from os import mkdir
from os.path import exists
from struct import unpack, pack
import sys


class Track:
    def __init__(self, data: bytes, channels: int, freq: int, interleave: int, addr: int) -> None:
        self.data: bytes = data
        self.frequency: int = freq
        self.channels: int = channels
        self.interleave: int = interleave
        self.offset: int = addr
    
    @property
    def duration(self) -> int:
        return len(self.data)/(self.frequency * 2 * self.channels+1)
    
    def __str__(self):
        return f'ADPCM Track - {self.duration:.3f}s {self.frequency}Hz {self.channels+1}ch'


def parseVagi(header: bytes, offset: int) -> list[tuple[int, int, int]]:
    tracks: list[tuple[int, int, int]] = []
    offset += 0x8
    cnt: int = unpack("I", header[offset:offset+4])[0]
    offset += 0x8
    for x in range(cnt+1):
        tracks.append(unpack("<5I", header[offset:offset+0x14]))
        offset += 0x14
    
    return tracks


def read(header: str, snd_data: str | None = None) -> tuple[list[Track], bytes]:
    HEADER: bytes
    SOUNDS: bytes
    if snd_data is not None:
        with open(header, "rb") as hdr, open(snd_data, "rb") as snd:
            HEADER = hdr.read()
            SOUNDS = snd.read()
    else:
        with open(header, "rb") as vag:
            vag.seek(0xC)
            hdr_size = unpack("<I", vag.read(4))[0]
            vag.seek(0)
            HEADER = vag.read(hdr_size)
            SOUNDS = vag.read()
    
    vagi: int = unpack("I", HEADER[0x1C:0x20])[0]
    
    tracks: Track = []
    for track in parseVagi(HEADER, vagi):
        tracks.append(
            Track(SOUNDS[track[0]:track[0]+track[1]], track[2], track[3], track[4], track[0])
        )
    
    return tracks, HEADER


def saveFiles(tracks: list[Track], path) -> None:
    dir: str = path.split(".")[0]+"_snd"
    index: int = 0
    if not exists(dir):
        mkdir(dir)
    for track in tracks:
        with open(f'{dir}/SND{index:0>2}.RAW', "wb") as file:
            file.write(track.data)
        index += 1
    
    return dir


def extract(header: str, snd_data: str | None = None) -> list[Track]:
    tracks, head = read(header=header, snd_data=snd_data)
    dir: str = saveFiles(tracks, header)
    with open(f'{dir}/HEAD.BIN', "wb") as file:
        file.write(head)
    with open(f'{dir}/TRACKS.TXT', "w", encoding="utf-8") as file:
        file.writelines([str(track)+"\n" for track in tracks])
    
    return tracks


def rebuild(path: str) -> None:
    if not exists(f'{path}/HEAD.BIN') or not exists(f'{path}/TRACKS.TXT'):
        print("Specified folder doesn't contain the necessary files for rebuilding")
        exit()
    with open(f'{path}/HEAD.BIN', "rb") as head:
        HEADER = head.read()
    with open(f'{path}/TRACKS.TXT', "r", encoding="utf-8") as file:
        tracks = [(int(line.split(" ")[-2].replace("Hz", "")), int(line.split(" ")[-1].split("ch")[0])) for line in file.readlines()]
    
    vagi: int = unpack("I", HEADER[0x1C:0x20])[0]
    
    TRACK_INFO = []
    DATA: bytes = b''

    for track, info in enumerate(tracks):
        with open(f'{path}/SND{track:0>2}.RAW', "rb") as file:
            snd = file.read()
            TRACK_INFO.append((len(DATA), len(snd), info[1]-1, info[0]))
            DATA += snd
    
    with open(f'{path}.head', "wb+") as header:
        header.write(HEADER)
        header.seek(vagi)
        header.write(b'Vagi')
        header.write(pack("<3i", len(TRACK_INFO) * 0x14 + 0x18, len(TRACK_INFO)-1, -1))

        for track in TRACK_INFO:
            header.write(pack("<4I4x", *track))

        header.write(b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF')

    with open(f'{path}.snd', "wb") as snd:
        snd.write(DATA)


def usage() -> None:
    print("usage: python audiopack.py extract <header> <data>")
    print("                           extract <header+data>")
    print("                           rebuild <folder>")
    exit()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        usage()
    match sys.argv[1]:
        case "extract":
            extract(*sys.argv[2:])
            print(f'Extracting to "{sys.argv[2].split(".")[0]}_snd"')
        case "rebuild":
            rebuild(sys.argv[2])
            print(f'Creating "{sys.argv[2]}.head" and "{sys.argv[2]}.snd"')
        case _:
            usage()
