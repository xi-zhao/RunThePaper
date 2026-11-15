"""Fetch and verify only selected ordinary ZIP members using public HTTP ranges."""
from collections import Counter
import concurrent.futures
import hashlib
import json
from pathlib import Path
import pickletools
import struct
from urllib.request import Request, urlopen
import zlib

URL="https://zenodo.org/api/records/14037434/files/Archive.zip/content"
TOTAL=723603260
ROOT=Path("source/features")
NAMES={"fidelities_dic.pkl","gate_feature_dic.pkl","t1_fidelity_dic.pkl","mm_fidelity_dic.pkl",
       "zz_fidelity_dic.pkl","circuit_types_dic.pkl","Hellinger_fidelity_dic.pkl","success_fraction_dic.pkl"}


def get_member(row):
    batch,file=row["name"].split("/")
    dest=ROOT/batch/file
    if not dest.is_file():
        start=row["header_offset"]
        end=start+row["compressed"]+1023
        req=Request(URL,headers={"Range":f"bytes={start}-{end}","User-Agent":"curl/8.7.1"})
        with urlopen(req,timeout=18) as stream:
            assert stream.status==206 and stream.headers["Content-Range"]==f"bytes {start}-{end}/{TOTAL}"
            data=stream.read(end-start+2)
        assert len(data)==end-start+1
        header=struct.unpack_from("<4s5H3I2H",data)
        assert header[0]==b"PK\x03\x04" and header[3]==8 and header[2]&1==0
        offset=30+sum(header[-2:])
        assert data[30:30+header[-2]].decode()==row["name"]
        decompressor=zlib.decompressobj(-15)
        data=decompressor.decompress(data[offset:offset+row["compressed"]],row["uncompressed"]+1)
        assert decompressor.eof and len(data)==row["uncompressed"] and zlib.crc32(data)==row["crc"]
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(data)
    data=dest.read_bytes()
    assert len(data)==row["uncompressed"] and zlib.crc32(data)==row["crc"]
    ops=Counter(o.name for o,arg,pos in pickletools.genops(data))
    unsafe={k:n for k,n in ops.items() if k in {"GLOBAL","STACK_GLOBAL","REDUCE","BUILD","NEWOBJ","NEWOBJ_EX","PERSID","BINPERSID","EXT1","EXT2","EXT4","INST","OBJ"}}
    return dict(member=row["name"],bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),crc32=row["crc"],object_opcodes=unsafe)


def rows():
    return [r for r in json.loads(Path("checks/zip-index.json").read_text())
            if r["name"].startswith("ibmq_") and r["name"].split("/")[-1] in NAMES]


if __name__=="__main__":
    import sys
    select=rows()
    if len(sys.argv)>1:
        select=[x for x in select if x["name"].startswith(sys.argv[1])]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        logs=list(pool.map(get_member,select))
    Path("checks/feature-members.json").write_text(json.dumps(logs,indent=2)+"\n")
    print(len(logs),"members",sum(r["bytes"] for r in logs),"bytes")
    for r in logs[:12]:print(r["member"],r["object_opcodes"])
