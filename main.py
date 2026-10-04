import os,asyncio,requests,time,difflib,subprocess,re,glob,mimetypes
from telethon import TelegramClient,events
from telethon.sessions import StringSession
from telethon.tl import types
from PIL import Image

API_ID=int(os.getenv("API_ID") or 0)
API_HASH=os.getenv("API_HASH") or ""
SESS=os.getenv("SESSION_STRING") or ""
TO=os.getenv("TO_CHANNEL") or "Palestineforours"
FROM=os.getenv("FROM_CHANNELS") or "QudsN,livequds,palnws24,tjrebe1111,alersalps"
FB_ID=os.getenv("FB_PAGE_ID") or "172704622752280"
FB_TOK=os.getenv("FB_PAGE_ACCESS_TOKEN") or ""
LINK="https://t.me/Palestineforours"
LOGO="logo.png"
LAST=0
SEEN=[]
ALBUMS={}

def cleanup():
    for f in glob.glob("*_wm.mp4"):
        try: os.remove(f)
        except: pass

def remove_links(t):
    if not t: return ""
    t=re.sub(r'https?://\S+','',t)
    t=re.sub(r'www\.\S+','',t)
    t=re.sub(r't\.me/\S+','',t,flags=re.IGNORECASE)
    t=re.sub(r'@\w+','',t)
    return t
def clean(t): return remove_links(t) if t else ""
def dup(txt):
    global SEEN
    now=time.time()
    SEEN=[(a,b) for a,b in SEEN if now-b<3600]
    n="".join(clean(txt).lower().split())[:300]
    if len(n)<20: return False
    for o,_ in SEEN:
        if n==o or difflib.SequenceMatcher(None,n,o).ratio()>0.85: return True
    SEEN.append((n,now))
    return False

def wm_image(p):
    try:
        if not os.path.exists(LOGO): return p
        b=Image.open(p).convert("RGBA")
        l=Image.open(LOGO).convert("RGBA")
        w=int(b.width*0.18)
        l=l.resize((w,int(w*l.height/l.width)), Image.LANCZOS)
        b.paste(l,(b.width-l.width-15,15),l)
        b.convert("RGB").save(p,"JPEG",quality=95)
        print("IMG WM OK")
        return p
    except Exception as e:
        print(f"IMG ERR {e}")
        return p

def wm_video(p):
    try:
        if not os.path.exists(LOGO): return p
        from imageio_ffmpeg import get_ffmpeg_exe
        ff=get_ffmpeg_exe()
        out=os.path.splitext(p)[0]+"_wm.mp4"
        if os.path.exists(out):
            try: os.remove(out)
            except: pass
        print(f"WM START {os.path.basename(p)}")
        # لوجو فوق يمين - القديم
        filt="[1:v]scale=200:-1[wm];[0:v][wm]overlay=W-w-15:15:shortest=1,format=yuv420p"
        cmd=[ff,"-y","-i",p,"-i",LOGO,"-filter_complex",filt,"-map","0:v:0","-map","0:a?","-c:v","libx264","-preset","veryfast","-crf","23","-c:a","aac",out]
        subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=180)
        if os.path.exists(out) and os.path.getsize(out)>5000:
            os.remove(p)
            print("VIDEO WM OK")
            return out
        else:
            print("WM FAIL - SEND ORIGINAL")
            return p
    except Exception as e:
        print(f"WM EXC {e}")
        return p

def is_video(p):
    if not p or not os.path.exists(p): return False
    mime,_=mimetypes.guess_type(p)
    if mime and mime.startswith("video"): return True
    return os.path.getsize(p)>300000

def fb_video(txt,fp):
    if not FB_TOK or not fp or not os.path.exists(fp): return
    if os.path.getsize(fp)>90000000: return
    try:
        safe=clean(txt)[:1500]+"\n\n#فلسطين_لنا\n"+LINK
        url=f"https://graph.facebook.com/v20.0/{FB_ID}/videos"
        with open(fp,'rb') as f:
            r=requests.post(url,data={"description":safe,"access_token":FB_TOK},files={"source":f},timeout=300)
        print(f"FB REEL {r.status_code}")
    except Exception as e: print(f"FB ERR {e}")

def fb_normal(txt,fp=None):
    global LAST
    if time.time()-LAST<300: return
    if not FB_TOK: return
    try:
        safe=clean(txt)[:1800]+"\n\n#فلسطين_لنا\n"+LINK
        u1=f"https://graph.facebook.com/v20.0/{FB_ID}/photos"
        u2=f"https://graph.facebook.com/v20.0/{FB_ID}/feed"
        if fp and os.path.exists(fp) and os.path.getsize(fp)<8000000 and fp.lower().endswith((".jpg",".jpeg",".png")):
            with open(fp,'rb') as f: r=requests.post(u1,data={"message":safe,"access_token":FB_TOK},files={"source":f},timeout=90)
        else:
            if fp and is_video(fp): return
            r=requests.post(u2,data={"message":safe,"access_token":FB_TOK},timeout=30)
        if r and r.status_code==200: LAST=time.time()
    except: pass

SRC=[x.strip() for x in FROM.split(",") if x.strip()]
cli=TelegramClient(StringSession(SESS),API_ID,API_HASH)

async def send_album(gid):
    await asyncio.sleep(4)
    data=ALBUMS.pop(gid,None)
    if not data: return
    files=data.get("files",[]); txt=data.get("txt","")
    if not files or dup(txt):
        for f in files:
            try: os.remove(f)
            except: pass
        return
    fin="فلسطين لنا/ \n\n"+(txt or "")+"\n\n#فلسطين_لنا\n\n"+LINK
    try:
        await cli.send_message(TO,fin,file=files,link_preview=False)
        print(f"ALBUM {len(files)} SENT")
        if files and is_video(files[0]): fb_video(txt,files[0])
        elif files: fb_normal(txt,files[0])
    except Exception as e: print(f"ALBUM ERR {e}")
    finally:
        for f in files:
            try: os.remove(f)
            except: pass

@cli.on(events.NewMessage(chats=SRC))
async def h(ev):
    fp=None
    try:
        msg=ev.message
        txt=remove_links(msg.message or ""); txt=re.sub(r'\n{3,}','\n\n',txt).strip()
        gid=msg.grouped_id
        if gid:
            if gid not in ALBUMS:
                ALBUMS[gid]={"files":[],"txt":txt}
                asyncio.create_task(send_album(gid))
            if msg.media and not isinstance(msg.media,types.MessageMediaWebPage):
                p=await cli.download_media(msg.media)
                if p:
                    try:
                        Image.open(p); p=wm_image(p)
                    except:
                        p=wm_video(p)
                    ALBUMS[gid]["files"].append(p)
                    if txt: ALBUMS[gid]["txt"]=txt
            return
        if msg.media and not isinstance(msg.media,types.MessageMediaWebPage):
            fp=await cli.download_media(msg.media)
            if fp:
                try:
                    Image.open(fp); fp=wm_image(fp)
                except:
                    fp=wm_video(fp)
        if not txt and not fp: return
        if dup(txt): return
        fin="فلسطين لنا/ \n\n"+(txt or "")+"\n\n#فلسطين_لنا\n\n"+LINK
        await cli.send_message(TO,fin,file=fp,link_preview=False)
        print("TG SENT OK")
        if fp and is_video(fp): fb_video(txt,fp)
        else: fb_normal(txt,fp)
    except Exception as e: print(f"ERR {e}")
    finally:
        if fp and os.path.exists(fp):
            try: os.remove(fp)
            except: pass

async def main():
    cleanup()
    print(f"LOGO={os.path.exists(LOGO)}")
    await cli.start()
    print("READY OLD - TOP RIGHT")
    await cli.run_until_disconnected()

if __name__=='__main__': asyncio.run(main())
