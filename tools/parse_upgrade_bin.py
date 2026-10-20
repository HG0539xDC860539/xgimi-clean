#!/usr/bin/env python3
"""
parse_upgrade_bin.py —— 解析极米 USB 强刷包 (XGIMI_IRONMAN_*.bin)

功能:
  1. 解析包头部 U-Boot 升级脚本, 列出全部分区及其在包内的偏移/大小
  2. 提取指定分区 (boot/recovery/mboot/dtb/...) 到文件
  3. 将分段 sparse(system/vendor) 合并还原为完整 ext4 镜像

用法:
  python parse_upgrade_bin.py list    <bin文件>
  python parse_upgrade_bin.py extract <bin文件> <分区名> <输出文件>
  python parse_upgrade_bin.py merge   <bin文件> <system|vendor> <输出img>

注意: sparse 分段每段的 total_blks 都是完整分区大小, 由 DON'T CARE 块跳过,
      必须按块偏移合并 (merge), 直接拼接会得到 N 倍大小的错误镜像。
"""
import re
import os
import struct
import sys

SPARSE_MAGIC = 0xED26FF3A
CHUNK_RAW, CHUNK_FILL, CHUNK_DONT_CARE, CHUNK_CRC32 = 0xCAC1, 0xCAC2, 0xCAC3, 0xCAC4


def read_script_head(path, limit=0x2000):
    with open(path, "rb") as f:
        head = f.read(limit)
    text = head.decode("ascii", errors="ignore")
    end = text.find("% <- this is end of script symbol")
    return text[:end] if end > 0 else text


def parse_items(text):
    sections = re.split(r"#\s*File Partition:\s*(\S+)", text)
    items = []
    for i in range(1, len(sections), 2):
        name, body = sections[i], sections[i + 1]
        for m in re.finditer(
            r"filepartload\s+\S+\s+\$\(UpgradeImage\)\s+(0x[0-9A-Fa-f]+)\s+(0x[0-9A-Fa-f]+)",
            body,
        ):
            items.append((name, int(m.group(1), 16), int(m.group(2), 16)))
    return items


def list_partitions(path):
    total = os.path.getsize(path)
    items = parse_items(read_script_head(path))
    print(f"固件: {path}  ({total:,} bytes)")
    for name, off, size in items:
        status = "OK" if off + size <= total else "缺失/不完整(文件被截断?)"
        print(f"{name:16s} off=0x{off:08X} size=0x{size:08X} ({size:>12,})  {status}")


def extract(path, part, out):
    items = parse_items(read_script_head(path))
    with open(path, "rb") as f, open(out, "wb") as o:
        for name, off, size in items:
            if name == part:
                f.seek(off)
                o.write(f.read(size))
                print(f"提取 {part} @0x{off:X} {size:,} -> {out}")
                return
    sys.exit(f"未找到分区 {part}; 可用分区见 list 子命令")


def merge_sparse(path, part, out):
    items = [(n, o, s) for n, o, s in parse_items(read_script_head(path)) if n == part]
    if not items:
        sys.exit(f"未找到分区 {part} 的 sparse 分段")
    with open(path, "rb") as f:
        first = items[0]
        f.seek(first[1])
        magic, _, _, fhdr, chdr, blk, total_blks, _, _ = struct.unpack("<IHHHHIIII", f.read(28))
        if magic != SPARSE_MAGIC:
            sys.exit("不是 sparse 镜像")
        size = total_blks * blk
        with open(out, "wb") as o:
            o.write(b"\x00" * size)
        print(f"{part}: 分区 {size:,} bytes, {len(items)} 个分段, 合并中 ...")
        for idx, (_, off, fsize) in enumerate(items):
            f.seek(off)
            data = f.read(fsize)
            _, _, _, _, _, blk2, tblks, tch, _ = struct.unpack("<IHHHHIIII", data[:28])
            assert blk2 == blk and tblks == total_blks
            coff, cursor, hits = fhdr, 0, 0
            for _ in range(tch):
                ctype, _res, sz_blks = struct.unpack("<HHI", data[coff:coff + 8])
                coff += chdr
                nbytes = sz_blks * blk
                if ctype == CHUNK_RAW:
                    with open(out, "r+b") as o:
                        o.seek(cursor * blk)
                        o.write(data[coff:coff + nbytes])
                    hits += sz_blks
                    coff += nbytes
                elif ctype == CHUNK_FILL:
                    fill = data[coff:coff + 4] * (nbytes // 4)
                    coff += 4
                    with open(out, "r+b") as o:
                        o.seek(cursor * blk)
                        o.write(fill)
                    hits += sz_blks
                elif ctype == CHUNK_DONT_CARE:
                    pass
                cursor += sz_blks
            print(f"  段{idx + 1}: {tch} chunks, 数据块 {hits:,}/{total_blks:,}")
    print(f"完成 -> {out}  (ext4 魔数应为 53ef, 可用 debugfs 浏览)")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return
    cmd, path = sys.argv[1], sys.argv[2]
    if cmd == "list":
        list_partitions(path)
    elif cmd == "extract" and len(sys.argv) == 5:
        extract(path, sys.argv[3], sys.argv[4])
    elif cmd == "merge" and len(sys.argv) == 5:
        merge_sparse(path, sys.argv[3], sys.argv[4])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
