import sys
from os import listdir
from .decode import adpcm2wav
from .audiopack import extract, rebuild
from .encode import encoderaw, encodewav


def usage() -> None:
    print("usage: python -m audiotools extract      <header> <data>")
    print("                            extract      <header+data>")
    print("                            ex-decode    <header+data>")
    print("                            rebuild      <folder>")
    print("                            decode       <inputfile <outputfile>")
    print("                            encode       <inputfile <outputfile>")
    exit()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        usage()
    match sys.argv[1]:
        case "extract":
            extract(*sys.argv[2:])
            print(f'Extracting to "{sys.argv[2].split(".")[0]}"')
        case "rebuild":
            rebuild(sys.argv[2])
            print(f'Creating "{sys.argv[2]}.head" and "{sys.argv[2]}.snd"')
        case "decode":
            if len(sys.argv) < 4:
                usage()
            adpcm2wav(sys.argv[2], sys.argv[3])
        case "ex-decode":
            tracks = extract(*sys.argv[2:])
            dir: str = f'{sys.argv[2].split(".")[0]}_snd'
            for i, info in enumerate(tracks):
                adpcm2wav(
                    f'{dir}/SND{i:0>2}.RAW',
                    f'{dir}/SND{i:0>2}.WAV',
                    channels=info.channels+1,
                    freq=info.frequency,
                    sample=16
                )
            print(f'Extracting to "{dir}"')
        case "encode":
            if len(sys.argv) < 4:
                usage()
            if sys.argv[2].endswith(".wav"):
                encodewav(sys.argv[2], sys.argv[3])
            else:
                encoderaw(sys.argv[2], sys.argv[3])
        case _:
            usage()
