from struct import pack
import sys



def decode(base, new) -> None:
    prev_sample = 0
    pre_prev_sample = 0

    while len(line := base.read(0x10)) == 0x10:
        shift = line[0] & 0xF
        shift = 9 if shift > 12 else shift
        filter = (line[0] >> 4) & 0x07
        for i in range(28):
            sample = line[2+(i//2)]
            
            if i % 2 == 0:
                sample &= 0xF
            else:
                sample = sample >> 4
            
            sample = ((sample & 7) - (sample & 8)) << (12 - shift)

            match filter:
                case 0:  # no filter
                    pass
                case 1:  # use previous
                    sample += (60 * prev_sample / 64)
                case 2:  # use 2 previous
                    sample += ((115 * prev_sample) + (-52 * pre_prev_sample)) / 64
                case 3:
                    sample += ((98 * prev_sample) + (-55 * pre_prev_sample)) / 64
                case 4:
                    sample += ((122 * prev_sample) + (-60 * pre_prev_sample)) / 64
            
            sample = max(-0x8000, min(0x7FFF, int(sample)))

            new.write(pack("<h", sample))

            pre_prev_sample = prev_sample
            prev_sample = sample


def header(channel, rate, sample_size, sectors) -> bytes:
    hdr = b'WAVEfmt '
    hdr += pack("<I2H2I2H", 16, 1, channel, rate, rate*channel*(sample_size//8), (channel*sample_size)//8, sample_size)
    hdr += b'data' + pack("I", sectors*56)
    hdr = b'RIFF' + pack("<I", len(hdr) + 8 + sectors*56) + hdr

    return hdr


def adpcm2wav(adpcm_path: str, wav_path: str, channels: int = 1, freq: int = 16000, sample: int = 16) -> None:
    with open(adpcm_path, "rb") as adpcm, open(wav_path, "wb") as wav:
        sectors = len(adpcm.read())//16
        wav.write(header(channels, freq, sample, sectors))
        adpcm.seek(0)
        decode(adpcm, wav)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: python decode.py <inputfile> <outputfile> <frequency> <channels>")
        exit()
    
    adpcm2wav(sys.argv[1], sys.argv[2], sys.argv[4], sys.argv[3])
