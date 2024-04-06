import requests,os,mypkg,json
from search import encode
from dataprint import print
GOOGLEAPIS="translate.googleapis.com"
CLIENTS5="clients5.google.com"
GOOGLE="translate.google."
GOOGLECOM=GOOGLE+"com"
GOOGLECH=GOOGLE+"ch"

def b(service,path):
    if path.startswith("/"):path=path[1:]
    if path.endswith("/"):path=path[:1]
    base=os.path.join(service,path)
    if not base.startswith("http"):
        base="https://"+base
    return base

class GoogleTransApi:
    def __init__(self,service=GOOGLECH,client=["t","gtx","dict-chrome-ex"],path="translate_a/single",input_encoding="UTF-8",output_encoding="UTF-8",json_response=1):
        self.service=service
        self.client=[client] if isinstance(client,str) else client
        self.path=path
        self.input_encoding=input_encoding
        self.output_encoding=output_encoding
        self.dj=int(bool(json_response))
    def _request(self,**params):
        base=b(self.service,self.path)
        params["ie"]=self.input_encoding
        params["oe"]=self.output_encoding
        params["dj"]=self.dj
        p="&".join(map(lambda i:(str(i[0])+"="+encode(i[1])),params.items()))
        for c in self.client.copy():
            url=base+"?client="+c+"&"+p
            print(url)
            r=requests.get(url)
            try:
                r.raise_for_status()
            except Exception as err:
                error=err
                self.client.append(self.client.pop(0))
                continue
            j=json.loads(r.text.replace("\u200b",""))
            try:
                t=j[0]
            except:t=None
            if isinstance(t,str):return t
            return j
        raise error
    def translate(self,text,dest="en",src="auto",alternative=False):
        j=self._request(sl=src,tl=dest,dt=("at" if alternative else "t"),q=text)
        if isinstance(j,str):return j
        if alternative:
            tr=[]
            if self.dj:
                for e in j["alternative_translations"][0]["alternative"]:
                    tr.append(e["word_postproc"])
                return tr
            for e in j[5][0][2]:
                tr.append(e[0])
            return tr
        if self.dj:
            return j["sentences"][0]["trans"]
        return j[0][0][0]
    def transcription(self,word,src="auto"):
        j=self._request(sl=src,dt="rm",q=word)
        if self.dj:
            return j["sentences"][0]["src_translit"]
        return j[0][0][3]
    def dictionary(self,text,dest="en",src="auto"):
        j=self._request(sl=src,tl=dest,dt="bd",q=text)
        d={}
        if self.dj:
            for e in j["dict"][0]["entry"]:
                d[e["word"]]=e["reverse_translation"]
            return d
        for e in j[1][0][2]:
            print(e)
            d[e[0]]=e[1]
        return d
    def definitions(self,word,defs=True,syns=True,ex=True,seealso=True,src="auto"):
        global df,dr
        def add(id,**params):
            n="new" in params and params["new"]
            gc="gram_class" in params
            def rve(k,a,v):
                raise ValueError("in add("+repr(id)+") k="+repr(k)+" "+repr(a)+"!="+repr(v))
            try:
                d=df[id]
            except:
                d=df[id]=(len(dr)-(0 if n else 1),{})
                d=d[1]
                if n:
                    dd={"gram_class":None,"definitions":[d]}
                    if gc:
                        dd["gram_class"]=params["gram_class"]
                    else:
                        del dd["gram_class"]
                    dr.append(dd)
                elif dr:
                    dr[-1]["definitions"].append(d)
            else:
                if gc:
                    a=dr[d[0]]["gram_class"]
                    if a!=params["gram_class"]:
                        rve("gram_class",a,params["gram_class"])
                d=d[1]
            for k,v in params.items():
                if k==None or k in ("_verif","gram_class","new") or not v:continue
                
                try:
                    assert params["_verif"]
                    a=d[k]
                    assert a!=None
                except:
                    d[k]=v
                else:
                    if a!=v:
                        rve(k,a,v)
                
        def get_labels(d,idx=3):
            if self.dj:
                return (d["label_info"]["labels"] if "label_info" in d and "labels" in d["label_info"] else None)
            return (d[idx][4]) if (len(d)>idx and len(d[idx])>4) else None
                        
        df={}
        dr=[]
        if defs:
            j=self._request(sl=src,dt="md",q=word,hl=src)
            if self.dj:
                for e in j["definitions"]:
                    g=e["pos"]
                    new=1
                    for d in e["entry"]:
                        add(d["definition_id"],gram_class=g,labels=get_labels(d),definition=d["gloss"],new=new)
                        new=0
            else:
                for e in j[12]:
                    g=e[0]
                    new=1
                    for d in e[1]:
                        add(d[1],gram_class=g,labels=get_labels(d),definition=d[0],new=new)
                        new=0
                    
        if syns:
            j=self._request(sl=src,dt="ss",q=word,hl=src)
            if self.dj:
                for e in j["synsets"] if "synsets" in j else []:
                    g=e["pos"]
                    new=1
                    for d in e["entry"]:
                        r=None
                        a=[]
                        b=d["synonym"]
                        id=d["definition_id"]
                        try:
                            r=d["label_info"]["register"][0]
                        except:pass
                        else:
                            a=df[id][1]["synonyms"]
                            b=[{r:b}]
                            print(b)
                        add(id,gram_class=g,labels=get_labels(d),synonyms=a+b,_verif=not r)
                            
                        new=0
            else:
                for e in j[11] if len(j)>11 else []:
                    g=e[0]
                    new=1
                    for d in e[1]:
                        r=None
                        a=[]
                        b=d[0]
                        try:
                            r=d[2][0][0]
                        except:pass
                        else:
                            a=df[d[1]][1]["synonyms"]
                            b=[{r:b}]
                        add(d[1],gram_class=g,labels=get_labels(d,2),synonyms=a+b,_verif=not (r))
                        new=0
        if ex:
            j=self._request(sl=src,dt="ex",q=word)
            if self.dj:
                if "examples" in j:
                    for e in j["examples"]["example"]:
                        add(e["definition_id"],labels=get_labels(e),example=e["text"].replace("<b>","").replace("</b>",""),new=1)
            else:
                if len(j)>13:
                    for e in j[13][0]:
                        add(e[5],labels=get_labels(d,6),example=e[0].replace("<b>","").replace("</b>",""),new=1)
        dr={"Word":word,"Definitions":dr}
        sa=None
        if seealso:
            j=self._request(sl=src,dt="rw",q=word)
            if self.dj:
                if "related_words" in j:
                    sa=j["related_words"]["word"]
            else:
                if len(j)>14:
                    sa=j[14][0]
        if sa:
            dr["Seealso"]=sa
        return dr
            

t=GoogleTransApi()
#print(t.translate("Unité de mesure",alternative=True))
#print(t.translate("Bonjour"))

