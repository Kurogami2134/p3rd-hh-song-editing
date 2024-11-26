from struct import pack, unpack


def encode(file, data_size: int, path: str) -> None:
    sample_buf: int
    samples: tuple[int]
    lines: int = 0

    with open(path, "wb") as new:
        while lines < data_size//56:
            buf = file.read(min(56, data_size-lines*56))
            if len(buf):
                buf += bytes(56-len(buf))
            
            samples = unpack("28h", buf)
            new.write(b'\x00\x00')
            
            for i, sample in enumerate(samples):
                sample = (sample >> 12) & 0xF
                sample = (sample & 7) - (sample & 8)

                if i % 2:
                    sample_buf |= sample << 4
                    new.write(pack("b", sample_buf))
                else:
                    sample_buf = sample & 0xF
            
            lines += 1


def encodewav(path: str, out_path: str) -> None:
    with open(path, "rb") as wav:
        wav.seek(0x10)
        fmt_size, fmt_tag = unpack("IH", wav.read(6))
        if fmt_tag != 1:
            print("This wav file is not in PCM format")
        
        wav.seek(0x14+fmt_size+4)
        data_size = unpack("<I", wav.read(4))[0]
        
        encode(wav, data_size, out_path)


def encoderaw(path: str, out_path: str) -> None:
    with open(path, "rb") as file:
        size = len(file.read())
        file.seek(0)
        encode(file, size, out_path)
