"""Original 3D cutaway explainer: How an AI agent handles an email request.

Perspective-projected physical 3D geometry, continuous camera tracking, animated
data signals, explodable layers, and synchronized green two-word captions.
CONCEPT VISUALIZATION: does not access any real email account or send email.
"""
from __future__ import annotations
import bisect
import json
import math
import os
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from .voice import available, make_voice_aligned
from .captions import words_from_alignment, draw_karaoke

W, H, FPS = 540, 960, 10
PAPER = (242, 245, 239)
MINT = (110, 237, 173)
SCENES = [
    ("DAS INNENLEBEN", "Wie arbeitet ein KI-Agent wirklich?", "overview"),
    ("DIE AUFGABE", "Stell dir vor, du willst Kundenanfragen aus deinen E-Mails schneller bearbeiten.", "user"),
    ("DER AUFTRAG", "Du schreibst: Finde wichtige Anfragen und bereite einen passenden Antwortentwurf vor.", "input"),
    ("SCHRITT EINS", "Der Auftrag landet im Sprachmodell. Daraus entsteht zunächst ein Arbeitsplan.", "plan"),
    ("NICHT MAGISCH", "Aber das Modell kann dein Postfach nicht einfach so öffnen.", "lock"),
    ("FREIGEGEBENE TOOLS", "Erst eine von dir erlaubte Schnittstelle verbindet es mit deinen Daten.", "tool"),
    ("DATEN ZURÜCK", "Das E-Mail-Werkzeug liefert Informationen an den Agenten zurück.", "data"),
    ("AUSWERTUNG", "Jetzt entscheidet das Modell, welche Anfrage wichtig wirkt.", "brain"),
    ("REGELN GELTEN", "Ist etwas unklar, kann der Agent nachfragen oder die Aktion stoppen.", "guard"),
    ("ANTWORTENTWURF", "Für die wichtige Nachricht erstellt er einen Entwurf. Noch wird nichts versendet.", "draft"),
    ("DU ENTSCHEIDEST", "Du prüfst den Text und gibst ihn ausdrücklich frei.", "approve"),
    ("ERST JETZT", "Mit dieser Freigabe darf das angebundene Werkzeug die E-Mail verschicken.", "send"),
    ("RÜCKMELDUNG", "Der Agent erhält ein Ergebnis und kann dir den Status anzeigen.", "return"),
    ("WENN ES SCHEITERT", "Falls ein Werkzeug einen Fehler meldet, braucht der Ablauf eine sichere Reaktion.", "error"),
    ("DER UNTERSCHIED", "Anders als ein starrer Ablauf kann der Agent einzelne Schritte dynamisch wählen.", "compare"),
    ("DEINE AUTOMATION", "Welchen Job würdest du gern automatisieren? Schreib deine Idee in die Kommentare.", "outro"),
]
ACCENTS = {
    "overview":0, "user":0,"input":0,"plan":1,"lock":1,"tool":2,"data":2,
    "brain":1,"guard":1,"draft":3,"approve":3,"send":2,"return":3,"error":1,
    "compare":0,"outro":3,
}
def rgb(h):
    h=h.lstrip("#")
    return tuple(int(h[i:i+2],16) for i in (0,2,4))
def mix(a,b,f):
    return tuple(max(0,min(255,int(a[k]*(1-f)+b[k]*f))) for k in range(3))
def fnt(sz, bold=True):
    paths=(["/usr/share/fonts/truetype/inter/InterDisplay-SemiBold.ttf",
            "/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf",
            "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"] if bold else
           ["/usr/share/fonts/opentype/inter/Inter-Regular.otf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
    for p in paths:
        try:return ImageFont.truetype(p,sz)
        except OSError:pass
    return ImageFont.load_default()
def norm(v):
    d=math.sqrt(sum(x*x for x in v)) or 1.
    return tuple(x/d for x in v)
def sub(a,b):return tuple(a[i]-b[i] for i in range(3))
def dot(a,b):return sum(a[i]*b[i] for i in range(3))
def cross(a,b):
    return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def ease(t):
    t=max(0.,min(1.,t))
    return t*t*(3-2*t)
class Camera:
    def __init__(self,theta,phi,target=(0,0,0),dist=13.8):
        self.pos=(target[0]+dist*math.sin(theta)*math.cos(phi),
                  target[1]+dist*math.sin(phi),
                  target[2]+dist*math.cos(theta)*math.cos(phi))
        self.forward=norm(sub(target,self.pos))
        self.right=norm(cross(self.forward,(0,1,0)))
        self.up=cross(self.right,self.forward)
    def pr(self,p):
        v=sub(p,self.pos)
        depth=dot(v,self.forward)
        scale=720/max(1,depth)
        return (W/2+dot(v,self.right)*scale,
                H*.495-dot(v,self.up)*scale,depth)
def cubefaces(cx,cy,cz,dx,dy,dz,col,cam,outlined=True):
    x0,x1=cx-dx/2,cx+dx/2
    y0,y1=cy-dy/2,cy+dy/2
    z0,z1=cz-dz/2,cz+dz/2
    verts=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
           (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    faces=[([0,1,2,3],.62),([4,5,6,7],.76),([0,3,7,4],.57),
           ([1,2,6,5],.69),([3,2,6,7],1.20),([0,1,5,4],.40)]
    projected=[cam.pr(v) for v in verts]
    out=[]
    for face,light in faces:
        depth=sum(projected[k][2] for k in face)/4
        pts=[(projected[k][0],projected[k][1]) for k in face]
        tone=tuple(min(255,int(c*light)) for c in col)
        out.append((depth,pts,tone,(23,36,44) if outlined else tone))
    return out
class Scene:
    def __init__(self,i,progress,clock):
        self.i,self.p,self.clock=i,progress,clock
        self.kind=SCENES[i][2]
        a=ACCENTS[self.kind]
        tracking=[0.,-2.7,-3.1,-1.1,-1.1,2.65,2.25,0.3,.4,4.,4.0,2.7,0.6,1.7,0.,0.]
        x=tracking[i]*(.7+.3*ease(min(1,progress*2)))
        theta=.36+math.sin(i*.65)*.25+(.30 if self.kind in ("overview","compare") else .13)*progress
        phi=.31+.05*math.sin(clock*.3)
        self.cam=Camera(theta,phi,target=(x,0.15,0.0),dist=14 if i in (0,14,15) else 12.5)
        self.faces=[]
        self.markers=[]
    def cube(self,x,y,z,sx,sy,sz,color,outline=True):
        self.faces.extend(cubefaces(x,y,z,sx,sy,sz,rgb(color) if isinstance(color,str) else color,self.cam,outline))
    def orb(self,p,r,color,glow=False):
        px,py,d=self.cam.pr(p)
        rad=max(2,r*720/max(d,1))
        self.markers.append((d,(px,py,rad),color,glow))
    def floor(self,d):
        for a in range(-7,8):
            pa,pb=self.cam.pr((a,-1.6,-5)),self.cam.pr((a,-1.6,5))
            d.line((pa[0],pa[1],pb[0],pb[1]),fill=(35,54,60),width=1)
        for z in range(-5,6):
            pa,pb=self.cam.pr((-7,-1.6,z)),self.cam.pr((7,-1.6,z))
            d.line((pa[0],pa[1],pb[0],pb[1]),fill=(35,54,60),width=1)
    def assemble(self):
        a=ACCENTS[self.kind]
        pulse=.5+.5*math.sin(self.clock*6)
        bases=[(-3.55,-.55,0.,1.62,1.28,1.6,"#44626c"),
               (-1.18,-.49,0.,1.62,1.48,1.7,"#4c6774"),
               (1.13,-.28,0.,2.10,1.88,2.05,"#234c49"),
               (3.73,-.58,0.,1.72,1.35,1.55,"#445e68")]
        for idx,(x,y,z,dx,dy,dz,col) in enumerate(bases):
            self.cube(x,y,z,dx+.17,0.14,dz+.17,"#122b35")
            self.cube(x,y,z,dx,dy,dz,col)
            self.cube(x,y+dy/2+.07,z,dx,.11,dz,"#64d99f" if idx==a else "#849a9e")
            if idx==a:
                for j in range(4):
                    self.orb((x-.48+j*.32,y+dy/2+.19,z-.35),.062+j*.002,
                             (108,245,177),True)
        # Transparent roof explodes to reveal the internal mechanism.
        if self.kind in ("plan","brain","guard","compare","overview"):
            lift=.95+1.5*ease(self.p)
            self.cube(1.12,1.0+lift,0.,2.08,.16,2.02,"#88a6b0")
            for j in range(4):
                self.orb((.5+j*.4,-.18,.0),.13,(100,235,172),True)
        # signal ducts with luminous moving data packets
        for n,(x0,x1) in enumerate([(-2.73,-2.03),(-.35,.07),(2.22,2.83)]):
            self.cube((x0+x1)/2,-.55,0,x1-x0,.19,.18,"#51726c")
            speed=(self.clock*.34+n*.30)%1
            self.orb((x0+(x1-x0)*speed,-.35,.0),.13,MINT,True)
        # small mailbox drawer, document and approval gate
        if self.kind in ("user","input","tool","data"):
            for n in range(3):
                self.cube(-4.20+n*.42, .43+.15*math.sin(self.clock*3+n),-.92,.38,.52,.065,"#ded8c6")
        if self.kind in ("draft","approve","send","return"):
            for n in range(3):
                self.cube(3.0+n*.49,.47+(.45*ease(self.p) if n==1 else 0),-.98,.43,.63,.075,"#f0eee2")
            self.orb((3.72,1.21,-.4),.20,MINT,True)
        if self.kind=="lock":
            self.cube(1.14,.78,-1.17,.65,.68,.25,"#a5b0a9")
            self.cube(1.14,1.24,-1.17,.41,.4,.16,"#c8d8ce")
        if self.kind=="error":
            self.orb((1.15,1.65,0),.33,(241,145,122),True)
        if self.kind=="outro":
            self.orb((1.15,1.75,0),.43,MINT,True)
    def draw(self):
        im=Image.new("RGB",(W,H),(9,17,22))
        d=ImageDraw.Draw(im)
        # muted moving environment
        for j in range(21):
            xx=(j*83+32)%W
            yy=170+(j*113)%620
            d.ellipse((xx,yy,xx+1,yy+1),fill=(40,66,61))
        d.rounded_rectangle((18,24,W-18,93),radius=18,fill=(22,37,38),outline=(50,80,75),width=1)
        d.text((37,42),"K I   /   A U T O M A T I S I E R U N G",font=fnt(17),fill=(170,228,205))
        self.floor(d)
        self.assemble()
        for dep,pts,color,edge in sorted(self.faces,key=lambda x:-x[0]):
            d.polygon(pts,fill=color)
            d.line(pts+[pts[0]],fill=edge,width=1)
        for dep,(x,y,r),color,glow in sorted(self.markers,key=lambda x:-x[0]):
            if glow:
                for k,alpha in [(2.1,.14),(1.5,.26)]:
                    rr=r*k;d.ellipse((x-rr,y-rr,x+rr,y+rr),fill=mix((9,17,22),color,alpha))
            d.ellipse((x-r,y-r,x+r,y+r),fill=color)
        # HUD surfaces, labels: these are separate from karaoke captions.
        d.rounded_rectangle((29,105,511,186),radius=18,fill=(18,32,34),outline=(41,75,67),width=1)
        d.text((47,119),f"{self.i+1:02d} / 16   ·   3D-SCHNITTMODELL",font=fnt(16),fill=(159,205,186))
        d.text((46,146),SCENES[self.i][0],font=fnt(23),fill=(245,246,239))
        # distinctive module markers
        for x,lab in [(60,"ANFRAGE"),(195,"PLAN"),(331,"TOOLS"),(424,"ERGEBNIS")]:
            d.text((x,742),lab,font=fnt(13),fill=(159,190,175))
        d.rounded_rectangle((36,772,504,778),radius=3,fill=(46,69,64))
        d.rounded_rectangle((36,772,36+468*(self.i+self.p)/len(SCENES),778),radius=3,fill=MINT)
        d.text((37,920),"KONZEPT-VISUALISIERUNG  ·  KEIN LIVE-POSTFACH",font=fnt(12),fill=(129,163,148))
        return im

def probe_duration(audio):
    cmd=["ffprobe","-v","error","-show_entries","format=duration","-of",
         "default=noprint_wrappers=1:nokey=1",str(audio)]
    return float(subprocess.run(cmd,capture_output=True,text=True,timeout=15,check=True).stdout.strip())
def boundaries(al):
    starts=al.get("character_start_times_seconds") or []
    if not starts:raise ValueError("No ElevenLabs alignment")
    pos=0
    out=[]
    for _,text,_ in SCENES:
        out.append(float(starts[min(pos,len(starts)-1)]))
        pos+=len(text)+1
    return out
def render(folder):
    folder=Path(folder)
    folder.mkdir(parents=True,exist_ok=True)
    if not available():raise RuntimeError("ElevenLabs is required for V3")
    spoken=" ".join(s[1] for s in SCENES)
    audio,align=make_voice_aligned(spoken,folder/"v3-voice.mp3")
    words=words_from_alignment(align)
    total=probe_duration(audio)+1.0
    if total>100:raise RuntimeError("Narration too long for video")
    cuts=boundaries(align)
    frames=int(total*FPS)+1
    outfile=folder/"v3-preview.mp4"
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-f","rawvideo","-pix_fmt","rgb24",
         "-s",f"{W}x{H}","-r",str(FPS),"-i","-","-i",str(audio),
         "-filter_complex","[0:v]scale=720:1280:flags=bicubic,format=yuv420p[v];[1:a]apad[a]",
         "-map","[v]","-map","[a]","-t",str(total),"-c:v","libx264","-preset","ultrafast",
         "-crf","27","-c:a","aac","-b:a","112k","-movflags","+faststart",str(outfile)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    try:
        for n in range(frames):
            t=n/FPS
            s=min(len(SCENES)-1,max(0,bisect.bisect_right(cuts,t)-1))
            end=cuts[s+1] if s+1<len(cuts) else total
            pct=max(0,min(1,(t-cuts[s])/max(.1,end-cuts[s])))
            im=Scene(s,pct,t).draw()
            draw_karaoke(im,words,t)
            proc.stdin.write(im.tobytes())
        proc.stdin.close()
        err=proc.stderr.read().decode(errors="replace")
        result=proc.wait(timeout=90)
        if result!=0:raise RuntimeError("FFmpeg encoding failed "+err[:160])
    except Exception:
        proc.kill();proc.wait()
        raise
    return {"video_path":str(outfile),"duration":round(probe_duration(outfile),2),
            "shots":16,"voice_engine":"elevenlabs","captions":"two_word_exact_green",
            "visual_style":"original 3D projected cross-section explainer",
            "production_quality":False,"public_posting":False}
