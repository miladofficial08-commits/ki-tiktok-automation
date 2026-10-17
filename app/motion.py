"""Animated 18-beat demonstrator. Concept UI, never misrepresented as an actual AI-built app."""
from pathlib import Path
import math,os,subprocess,json
from PIL import Image,ImageDraw,ImageFont
SCENES=[
("EINE IDEE → EINE APP","Was, wenn deine Idee plötzlich auf deinem Handy funktioniert?","phone"),
("IM ALLTAG","Du planst drei Gewohnheiten und vergisst sie doch ständig.","problem"),
("DIE IDEE","Ein Habit-Tracker für Lesen, Sport und Lernen.","prompt"),
("EIN KLARER PLAN","Nicht zehn Funktionen. Nur abhaken und Fortschritt sehen.","plan"),
("DIE DATEIEN","Oberfläche, Design und Logik greifen ineinander.","terminal"),
("EIN EIGENER LOOK","Klares dunkles Design statt komplizierter Menüs.","palette"),
("DEIN DASHBOARD","Jetzt sehen wir drei Ziele auf einem Bildschirm.","phone"),
("ERSTER KLICK","Lesen erledigt. Das Häkchen erscheint sofort.","tap1"),
("ZWEITER KLICK","Auch Sport ist geschafft. Zwei von drei!","tap2"),
("FORTSCHRITT","Der Balken wächst. Das Ergebnis wird sichtbar.","progress"),
("LOKAL SPEICHERN","Die Auswahl bleibt direkt im Browser gespeichert.","storage"),
("NOCHMAL ÖFFNEN","Nach dem Neuladen sind die Häkchen noch da.","reload"),
("FUNKTIONSTEST","Wir prüfen echte Klicks statt nur hübscher Bilder.","terminal"),
("FEHLER KORRIGIEREN","Wenn etwas nicht klappt, muss die Logik verbessert werden.","debug"),
("VORHER / NACHHER","Eine Idee wird zu einer bedienbaren Mini-App.","compare"),
("DIE GRENZEN","Noch kein Login, keine Cloud und keine App-Store-Version.","limits"),
("FÜR WEN?","Für Schule, Sport oder deinen Alltag?","choices"),
("DEINE IDEE?","Was würdest du als Nächstes bauen?","outro")]
def f(s,b=False):
    p="/usr/share/fonts/truetype/dejavu/DejaVuSans"+("-Bold" if b else "")+".ttf"
    return ImageFont.truetype(p,s)
def box(d,c,fill="#17273e",r=16,outline="#38516b"):
    d.rounded_rectangle(c,radius=r,fill=fill,outline=outline,width=2)
def txt(d,x,y,s,sz=22,color="#f5f9ff",maxw=460,b=False):
    font=f(sz,b);w=""
    for word in s.split():
        n=(w+" "+word).strip()
        if d.textbbox((0,0),n,font=font)[2]>maxw and w:
            d.text((x,y),w,font=font,fill=color);y+=sz+9;w=word
        else:w=n
    if w:d.text((x,y),w,font=font,fill=color)
def phone(d,t,checked):
    y=285-10*math.sin(t*math.pi);x=98
    box(d,(x,y,x+344,y+410),"#080e1a",35,"#7188a4")
    box(d,(x+14,y+15,x+330,y+395),"#14243a",25,"#2d4563")
    txt(d,x+37,y+45,"MEIN TAG",17,"#63e4cf",b=True)
    txt(d,x+37,y+89,"Heute zählt.",27,b=True)
    for i,name in enumerate(["30 Min. lesen","20 Min. Sport","10 Min. lernen"]):
        a=y+151+i*62;box(d,(x+30,a,x+312,a+53),"#273951",10,"#314e67")
        txt(d,x+43,a+16,name,17)
        box(d,(x+259,a+11,x+296,a+43),"#62e4d0" if i<checked else "#273951",9,"#619c9c")
        if i<checked:txt(d,x+268,a+14,"✓",20,"#102d31",b=True)
    txt(d,x+38,y+348,str(checked)+" / 3 geschafft",17,"#62e4d0")
    box(d,(x+38,y+374,x+299,y+382),"#344860",5,"#344860")
    if checked:box(d,(x+38,y+374,x+38+261*checked/3,y+382),"#62e4d0",4,"#62e4d0")
def frame(k,t):
    title,voice,kind=SCENES[k]
    im=Image.new("RGB",(540,960),"#0b1427");d=ImageDraw.Draw(im)
    for i in range(0,10):
        d.ellipse((240-i*30,260-i*30,340+i*30,360+i*30),outline="#162942",width=1)
    box(d,(23,28,516,106),"#153044",21,"#27596c")
    txt(d,47,56,"KI ZUM NACHMACHEN   ✦",21,"#68e3d1",b=True)
    txt(d,34,143,f"{k+1:02d} / {len(SCENES)}    •    PRODUKTDEMO",16,"#a2b9cf",b=True)
    txt(d,34,190,title,30,"#ffffff",450,True)
    if kind in ("phone","tap1","tap2","reload"):
        phone(d,t, 1 if kind=="tap1" else 2 if kind in ("tap2","reload") else 0)
        if kind.startswith("tap"):
            y=455 if kind=="tap1" else 515
            d.ellipse((393-t*23,y-t*23,414+t*23,y+21+t*23),outline="#65e8d6",width=4)
    elif kind in ("terminal","debug","storage"):
        box(d,(45,295,497,677),"#0c192d",20)
        rows=(["index.html","design.css","app.js","console.log('OK')"] if kind=="terminal" else
              ["✓ Lesen = true","✓ Sport = true","• Lernen = false"] if kind=="storage" else
              ["Klick: okay","Anzeige: okay","Speichern: reparieren","Test: wiederholen"])
        for j,line in enumerate(rows):
            if t*6>=j:txt(d,76,342+78*j,"> "+line,22,"#69e9d0" if kind!="debug" or j!=2 else "#ff9f7f")
    elif kind=="palette":
        for j,col in enumerate(["#2c426a","#62e5d1","#f5faff","#ffae78"]):
            x=41+j%2*241;y=323+j//2*166;box(d,(x,y,x+216,y+141),col,23)
    elif kind=="progress":
        txt(d,70,363,f"{int(33+66*t)} %",86,b=True)
        box(d,(71,517,480,553),"#2a415d",18)
        box(d,(71,517,71+409*(.33+.67*t),553),"#62e5d1",18)
        txt(d,72,598,"Sichtbar bei jedem Klick",20,"#a8c3d6")
    elif kind=="compare":
        box(d,(28,335,255,666),"#2d3651")
        box(d,(285,335,512,666),"#215654")
        txt(d,54,380,"VORHER",23,"#ffb9a1",170,True)
        txt(d,306,380,"NACHHER",23,"#73f4d0",190,True)
        txt(d,52,480,"Notizen auf Papier",21,maxw=165)
        txt(d,306,480,"Klickbare App",21,maxw=175)
    elif kind=="limits":
        box(d,(37,310,507,652),"#28344e")
        for j,line in enumerate(["✓ Lokal im Browser","× Noch kein Login","× Keine Cloud","× Nicht im App Store"]):
            txt(d,65,359+j*75,line,21,"#86e2d2" if j==0 else "#ffd3a6")
    elif kind in ("choices","outro"):
        for j,s in enumerate(["SCHULE","FITNESS","ARBEIT"]):
            y=324+98*j;box(d,(67,y,479,y+75),"#203652",15,"#3d938d")
            txt(d,101,y+22,s,24,b=True)
    else:
        box(d,(45,310,498,678),"#20314a",24)
        snippets=(["Weniger vergessen","Mehr durchziehen","Kleine Schritte zählen"] if kind=="problem" else
                  ["Baue einen Habit Tracker","3 einfache Gewohnheiten","mit sichtbarem Fortschritt"] if kind=="prompt" else
                  ["1  Aufgaben anzeigen","2  Häkchen schalten","3  Stand speichern"])
        for j,s in enumerate(snippets):
            y=347+j*98
            box(d,(71,y,470,y+74),"#2a4860" if j<t*4 else "#25384e")
            txt(d,90,y+23,s,21)
    box(d,(25,754,515,863),"#182f48",18)
    txt(d,45,775,voice,19,maxw=446)
    box(d,(28,898,512,904),"#28445a",4)
    box(d,(28,898,28+484*(k+t)/len(SCENES),904),"#68e3d1",4)
    txt(d,40,922,"KONZEPT-DEMO  •  KEINE LIVE-APP",12,"#8eabba")
    return im
def duration(path):
    c=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(path)],capture_output=True,text=True,check=True,timeout=12)
    return float(c.stdout.strip())
def render(folder,version=1):
    from .voice import available,make_voice
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    narration=" ".join(x[1] for x in SCENES)
    if available():
        audio=make_voice(narration,folder/"voice-motion.mp3")
        engine="elevenlabs-v2"
    else:
        raise RuntimeError("This production test requires a configured natural voice")
    total=max(65,min(89,duration(audio)+1))
    weights=[len(s[1].split())+5 for s in SCENES]
    ss=sum(weights);cuts=[0.]
    for w in weights:cuts.append(cuts[-1]+w/ss*total)
    output=folder/"preview.mp4"
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s","540x960","-r","9","-i","-","-i",str(audio),"-filter_complex","[0:v]scale=720:1280,format=yuv420p[v];[1:a]apad[a]","-map","[v]","-map","[a]","-t",str(total),"-c:v","libx264","-preset","ultrafast","-crf","29","-c:a","aac","-b:a","80k","-movflags","+faststart",str(output)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    try:
        import bisect
        for i in range(int(total*9)):
            moment=i/9;shot=min(17,bisect.bisect_right(cuts,moment)-1)
            prog=(moment-cuts[shot])/max(.1,cuts[shot+1]-cuts[shot])
            proc.stdin.write(frame(shot,max(0,min(1,prog))).tobytes())
        proc.stdin.close();err=proc.stderr.read().decode(errors="replace");ret=proc.wait(timeout=45)
        if ret:raise RuntimeError("ffmpeg error: "+err[:170])
    except Exception:
        proc.kill();proc.wait();raise
    return {"video_path":str(output),"duration":duration(output),"voice_engine":engine,"shots":18,"visual_style":"animated concept UI","production_quality":False}
