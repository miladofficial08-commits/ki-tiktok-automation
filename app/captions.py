"""Two-word karaoke captions aligned to ElevenLabs spoken-character timestamps."""
from __future__ import annotations
import bisect
from PIL import ImageDraw, ImageFont

FONT_PATHS = [
    "/app/fonts/Sora-SemiBold.ttf",
    "/usr/share/fonts/truetype/lato/Lato-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

def font(size):
    for path in FONT_PATHS:
        try: return ImageFont.truetype(path, size)
        except OSError: pass
    return ImageFont.load_default()

def words_from_alignment(al):
    chars=al.get("characters") or []
    starts=al.get("character_start_times_seconds") or []
    ends=al.get("character_end_times_seconds") or []
    if not (len(chars)==len(starts)==len(ends)):
        raise ValueError("Invalid ElevenLabs alignment")
    result=[];letters=[];s=None;e=0
    for char,begin,end in zip(chars,starts,ends):
        if str(char).isspace():
            if letters:
                result.append({"word":"".join(letters),"start":float(s),"end":float(e)})
                letters=[];s=None
        else:
            if s is None:s=float(begin)
            letters.append(str(char));e=end
    if letters:result.append({"word":"".join(letters),"start":float(s),"end":float(e)})
    return result

def scene_boundaries(al,scenes):
    times=al.get("character_start_times_seconds") or []
    if not times:raise ValueError("Missing speech alignment")
    idx=0;result=[]
    for _,text,_ in scenes:
        result.append(float(times[min(idx,len(times)-1)]))
        idx+=len(text)+1
    return result

def draw_karaoke(image,words,time_s):
    if not words:return image
    starts=[w["start"] for w in words]
    i=bisect.bisect_right(starts,time_s)-1
    if i<0 or i>=len(words):return image
    if time_s>=words[i]["end"] and i+1<len(words) and time_s<words[i+1]["start"]:return image
    pairindex=(i//2)*2
    pair=words[pairindex:pairindex+2]
    active=i-pairindex
    draw=ImageDraw.Draw(image,"RGBA")
    W,H=image.size;sz=34;gap=14
    label=[w["word"] for w in pair]
    while True:
        face=font(sz)
        widths=[draw.textbbox((0,0),w,font=face)[2] for w in label]
        width=sum(widths)+gap*(len(widths)-1)
        if width<=W-85 or sz<=23:break
        sz-=2
    x=(W-width)/2;y=int(H*.815);pad=23
    draw.rounded_rectangle((x-pad,y-15,x+width+pad,y+sz+22),radius=19,fill=(13,23,24,237),outline=(90,152,116,120),width=1)
    for j,(word,w) in enumerate(zip(label,widths)):
        draw.text((round(x),y),word,font=face,fill=(104,238,158,255) if j==active else (246,246,241,255))
        x+=w+gap
    return image
